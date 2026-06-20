from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Header, Query

from app.adapters.zip_coords import resolve_zip_coordinates
from app.adapters.zip_boundaries import get_zip_boundary
from app.adapters.telegram_notifier import notify_zip_search
from app.adapters.contracts import ApiPrincipal
from app.core.auth import require_action
from app.core.container import container
from app.core.session_auth import identity_from_access_token, issue_access_token
from app.core.settings import settings
from app.schemas.zip import (
    AuthUserCreateRequest,
    AuthUserOut,
    AuthUserPasswordResetRequest,
    ApiKeyCreateRequest,
    ApiKeyRotateRequest,
    ApiKeyOut,
    AuditEventOut,
    AuditEventPageOut,
    ExportCreateRequest,
    ExportJobPageOut,
    ExportJobOut,
    LayerOut,
    LoginOut,
    LoginRequest,
    SessionMeOut,
    UsageOut,
    ZipCompareRequest,
    ZipCompareResponse,
    ZipSummaryOut,
)

router = APIRouter()


def _estimate_patient_burden(
    age_0_17: int,
    age_18_34: int,
    age_35_64: int,
    age_65_plus: int,
) -> int:
    """Heuristic estimate of residents likely to need recurring care."""
    weighted = (
        age_0_17 * 0.06
        + age_18_34 * 0.08
        + age_35_64 * 0.18
        + age_65_plus * 0.35
    )
    return max(0, int(round(weighted)))


def _serialize_zip_summary(summary) -> ZipSummaryOut:
    coords = resolve_zip_coordinates(summary.zip_code)
    payload = summary.__dict__.copy()
    payload["lat"] = coords[0] if coords else None
    payload["lon"] = coords[1] if coords else None
    payload["estimated_patient_burden"] = _estimate_patient_burden(
        payload.get("age_0_17", 0),
        payload.get("age_18_34", 0),
        payload.get("age_35_64", 0),
        payload.get("age_65_plus", 0),
    )
    return ZipSummaryOut(**payload)


def _resolve_expiration(expires_in_seconds: int | None) -> datetime | None:
    if expires_in_seconds is None:
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/login", response_model=LoginOut)
def login(payload: LoginRequest) -> LoginOut:
    user = container.auth_store.authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = issue_access_token(user)
    return LoginOut(
        access_token=token,
        tenant_id=user.tenant_id,
        plan=user.plan,
        email=user.email,
    )


@router.get("/auth/me", response_model=SessionMeOut)
def auth_me(authorization: str | None = Header(default=None)) -> SessionMeOut:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    identity = identity_from_access_token(authorization[7:].strip())
    if identity is None:
        raise HTTPException(status_code=401, detail="Invalid access token")
    return SessionMeOut(email=identity.email, tenant_id=identity.tenant_id, plan=identity.plan)


@router.post("/auth/logout")
def logout() -> dict[str, str]:
    # Stateless bearer token flow: logout is handled client-side by dropping token.
    return {"status": "ok"}


@router.get("/map/layers", response_model=list[LayerOut])
def get_layers(principal: ApiPrincipal = Depends(require_action("map:read"))) -> list[LayerOut]:
    container.usage_store.record_request(principal.tenant_id, "GET /map/layers")
    return [LayerOut(**layer) for layer in container.catalog_store.get_layers()]


@router.get("/map/boundary/{zip_code}")
def get_map_boundary(
    zip_code: str,
    principal: ApiPrincipal = Depends(require_action("map:read")),
) -> dict:
    container.usage_store.record_request(principal.tenant_id, "GET /map/boundary/{zip}")
    boundary = get_zip_boundary(zip_code)
    if boundary is None:
        raise HTTPException(status_code=404, detail="ZIP boundary not found")
    return boundary


@router.get("/zip/{zip_code}/summary", response_model=ZipSummaryOut)
def get_zip_summary(
    zip_code: str,
    principal: ApiPrincipal = Depends(require_action("zip:summary:read")),
) -> ZipSummaryOut:
    container.usage_store.record_request(principal.tenant_id, "GET /zip/{zip}/summary")
    summary = container.summary_store.get_zip_summary(zip_code)
    if summary is None:
        raise HTTPException(status_code=503, detail="Service is down. Please try again later.")
    if settings.telegram_enabled:
        notify_zip_search(settings.telegram_bot_token, settings.telegram_chat_id, summary)
    return _serialize_zip_summary(summary)


@router.post("/zip/compare", response_model=ZipCompareResponse)
def compare_zips(
    payload: ZipCompareRequest,
    principal: ApiPrincipal = Depends(require_action("zip:compare:read")),
) -> ZipCompareResponse:
    container.usage_store.record_request(principal.tenant_id, "POST /zip/compare")
    results = container.summary_store.compare_zip_summaries(payload.zip_codes)
    if not results:
        raise HTTPException(status_code=503, detail="Service is down. Please try again later.")
    return ZipCompareResponse(results=[_serialize_zip_summary(item) for item in results])


@router.post("/export", response_model=ExportJobOut)
def create_export(
    payload: ExportCreateRequest,
    principal: ApiPrincipal = Depends(require_action("export:create")),
) -> ExportJobOut:
    container.usage_store.record_request(principal.tenant_id, "POST /export")
    job = container.export_store.create_export_job(
        tenant_id=principal.tenant_id,
        dataset_code=payload.dataset_code,
    )
    if settings.auto_process_exports:
        processed_job = container.export_store.process_export_job(job.job_id)
        if processed_job is not None:
            job = processed_job
    return ExportJobOut(**job.__dict__)


@router.get("/exports", response_model=ExportJobPageOut)
def list_my_exports(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    principal: ApiPrincipal = Depends(require_action("export:read")),
) -> ExportJobPageOut:
    container.usage_store.record_request(principal.tenant_id, "GET /exports")
    jobs = container.export_store.list_export_jobs(
        tenant_id=principal.tenant_id,
        limit=limit,
        offset=offset,
        status=status,
    )
    items = [ExportJobOut(**job.__dict__) for job in jobs]
    return ExportJobPageOut(items=items, limit=limit, offset=offset, returned=len(items))


@router.get("/exports/{job_id}", response_model=ExportJobOut)
def get_export_job(
    job_id: str,
    principal: ApiPrincipal = Depends(require_action("export:read")),
) -> ExportJobOut:
    container.usage_store.record_request(principal.tenant_id, "GET /exports/{id}")
    job = container.export_store.get_export_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Export job not found")
    if job.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=403, detail="Not authorized for this export job")
    return ExportJobOut(**job.__dict__)


@router.post("/admin/exports/{job_id}/process", response_model=ExportJobOut)
def process_export_job(
    job_id: str,
    principal: ApiPrincipal = Depends(require_action("admin:exports:process")),
) -> ExportJobOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/exports/{job_id}/process")
    job = container.export_store.process_export_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Export job not found")
    return ExportJobOut(**job.__dict__)


@router.post("/admin/exports/process-pending", response_model=ExportJobPageOut)
def process_pending_export_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    principal: ApiPrincipal = Depends(require_action("admin:exports:process-batch")),
) -> ExportJobPageOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/exports/process-pending")
    jobs = container.export_store.process_pending_export_jobs(limit=limit)
    items = [ExportJobOut(**job.__dict__) for job in jobs]
    return ExportJobPageOut(items=items, limit=limit, offset=0, returned=len(items))


@router.get("/admin/exports", response_model=ExportJobPageOut)
def list_all_exports(
    tenant_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    principal: ApiPrincipal = Depends(require_action("admin:exports:read")),
) -> ExportJobPageOut:
    container.usage_store.record_request(principal.tenant_id, "GET /admin/exports")
    jobs = container.export_store.list_export_jobs(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
        status=status,
    )
    items = [ExportJobOut(**job.__dict__) for job in jobs]
    return ExportJobPageOut(items=items, limit=limit, offset=offset, returned=len(items))


@router.post("/admin/exports/{job_id}/fail", response_model=ExportJobOut)
def fail_export_job(
    job_id: str,
    principal: ApiPrincipal = Depends(require_action("admin:exports:fail")),
) -> ExportJobOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/exports/{job_id}/fail")
    job = container.export_store.fail_export_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Export job not found")
    return ExportJobOut(**job.__dict__)


@router.post("/admin/exports/{job_id}/retry", response_model=ExportJobOut)
def retry_export_job(
    job_id: str,
    principal: ApiPrincipal = Depends(require_action("admin:exports:retry")),
) -> ExportJobOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/exports/{job_id}/retry")
    job = container.export_store.retry_export_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Export job not found")
    return ExportJobOut(**job.__dict__)


@router.get("/usage/me", response_model=UsageOut)
def get_usage_me(principal: ApiPrincipal = Depends(require_action("usage:read"))) -> UsageOut:
    container.usage_store.record_request(principal.tenant_id, "GET /usage/me")
    usage = container.usage_store.get_usage(principal.tenant_id)
    return UsageOut(tenant_id=principal.tenant_id, **usage)


@router.get("/admin/usage/{tenant_id}", response_model=UsageOut)
def get_usage_for_tenant(
    tenant_id: str,
    principal: ApiPrincipal = Depends(require_action("admin:usage:read")),
) -> UsageOut:
    container.usage_store.record_request(principal.tenant_id, "GET /admin/usage/{tenant_id}")
    usage = container.usage_store.get_usage(tenant_id)
    return UsageOut(tenant_id=tenant_id, **usage)


@router.get("/admin/api-keys", response_model=list[ApiKeyOut])
def list_api_keys(
    tenant_id: str | None = Query(default=None),
    principal: ApiPrincipal = Depends(require_action("admin:api-keys:read")),
) -> list[ApiKeyOut]:
    container.usage_store.record_request(principal.tenant_id, "GET /admin/api-keys")
    principals = container.auth_store.list_api_keys(tenant_id=tenant_id)
    return [ApiKeyOut(**item.__dict__) for item in principals]


@router.post("/admin/api-keys", response_model=ApiKeyOut)
def create_api_key(
    payload: ApiKeyCreateRequest,
    principal: ApiPrincipal = Depends(require_action("admin:api-keys:write")),
) -> ApiKeyOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/api-keys")
    created = container.auth_store.create_api_key(
        payload.tenant_id,
        payload.plan,
        expires_at=_resolve_expiration(payload.expires_in_seconds),
    )
    return ApiKeyOut(**created.__dict__)


@router.post("/admin/api-keys/{api_key}/rotate", response_model=ApiKeyOut)
def rotate_api_key(
    api_key: str,
    payload: ApiKeyRotateRequest,
    principal: ApiPrincipal = Depends(require_action("admin:api-keys:rotate")),
) -> ApiKeyOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/api-keys/{api_key}/rotate")
    rotated = container.auth_store.rotate_api_key(api_key, expires_at=_resolve_expiration(payload.expires_in_seconds))
    if rotated is None:
        raise HTTPException(status_code=404, detail="API key not found")
    return ApiKeyOut(**rotated.__dict__)


@router.post("/admin/api-keys/{api_key}/revoke", response_model=ApiKeyOut)
def revoke_api_key(
    api_key: str,
    principal: ApiPrincipal = Depends(require_action("admin:api-keys:revoke")),
) -> ApiKeyOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/api-keys/{api_key}/revoke")
    revoked = container.auth_store.revoke_api_key(api_key)
    if revoked is None:
        raise HTTPException(status_code=404, detail="API key not found")
    return ApiKeyOut(**revoked.__dict__)


@router.get("/admin/users", response_model=list[AuthUserOut])
def list_auth_users(
    tenant_id: str | None = Query(default=None),
    principal: ApiPrincipal = Depends(require_action("admin:users:read")),
) -> list[AuthUserOut]:
    container.usage_store.record_request(principal.tenant_id, "GET /admin/users")
    users = container.auth_store.list_users(tenant_id=tenant_id)
    return [AuthUserOut(**user.__dict__) for user in users]


@router.post("/admin/users", response_model=AuthUserOut)
def create_auth_user(
    payload: AuthUserCreateRequest,
    principal: ApiPrincipal = Depends(require_action("admin:users:create")),
) -> AuthUserOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/users")
    try:
        user = container.auth_store.create_user(
            email=payload.email,
            password=payload.password,
            tenant_id=payload.tenant_id,
            plan=payload.plan,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AuthUserOut(**user.__dict__)


@router.post("/admin/users/{email}/disable", response_model=AuthUserOut)
def disable_auth_user(
    email: str,
    principal: ApiPrincipal = Depends(require_action("admin:users:disable")),
) -> AuthUserOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/users/{email}/disable")
    user = container.auth_store.disable_user(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return AuthUserOut(**user.__dict__)


@router.post("/admin/users/{email}/password", response_model=AuthUserOut)
def reset_auth_user_password(
    email: str,
    payload: AuthUserPasswordResetRequest,
    principal: ApiPrincipal = Depends(require_action("admin:users:password")),
) -> AuthUserOut:
    container.usage_store.record_request(principal.tenant_id, "POST /admin/users/{email}/password")
    user = container.auth_store.set_user_password(email, payload.password)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return AuthUserOut(**user.__dict__)


@router.get("/admin/audit/events", response_model=AuditEventPageOut)
def list_audit_events(
    tenant_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    outcome: str | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    principal: ApiPrincipal = Depends(require_action("admin:audit:read")),
) -> AuditEventPageOut:
    container.usage_store.record_request(principal.tenant_id, "GET /admin/audit/events")
    events = container.audit_store.list_events(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
        start_at=start_at,
        end_at=end_at,
        outcome=outcome,
    )
    items = [AuditEventOut(**event.__dict__) for event in events]
    return AuditEventPageOut(items=items, limit=limit, offset=offset, returned=len(items))
