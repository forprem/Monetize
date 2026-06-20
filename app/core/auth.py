from __future__ import annotations

from typing import Callable

from fastapi import Header, HTTPException, Request

from app.adapters.contracts import ApiPrincipal
from app.core.container import container
from app.core.entitlements import PLAN_LIMITS
from app.core.session_auth import principal_from_access_token
from app.core.settings import settings


def _audit(
    tenant_id: str,
    action: str,
    endpoint: str,
    outcome: str,
    reason: str | None = None,
) -> None:
    container.audit_store.record_event(
        tenant_id=tenant_id,
        action=action,
        endpoint=endpoint,
        outcome=outcome,
        reason=reason,
    )


def _enforce_quotas(principal: ApiPrincipal, action: str) -> None:
    if not settings.enforce_quotas:
        return

    usage = container.usage_store.get_usage(principal.tenant_id)
    limits = PLAN_LIMITS.get(principal.plan, PLAN_LIMITS["enterprise"])

    if usage["requests_this_month"] >= limits["requests_per_month"]:
        raise HTTPException(status_code=429, detail="Monthly request quota exceeded")

    if action == "export:create" and usage["exports_this_month"] >= limits["exports_per_month"]:
        raise HTTPException(status_code=429, detail="Monthly export quota exceeded")


def authorize(
    action: str,
    x_api_key: str | None,
    authorization: str | None,
    endpoint: str,
) -> ApiPrincipal:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        principal = principal_from_access_token(token)
        if principal is None:
            _audit("unknown", action, endpoint, "denied", "invalid_bearer_token")
            raise HTTPException(status_code=401, detail="Invalid access token")

        if not container.auth_store.is_allowed(principal, action):
            _audit(principal.tenant_id, action, endpoint, "denied", "plan_forbidden")
            raise HTTPException(status_code=403, detail="Plan does not allow this action")

        try:
            _enforce_quotas(principal, action)
        except HTTPException as exc:
            _audit(principal.tenant_id, action, endpoint, "denied", str(exc.detail))
            raise

        _audit(principal.tenant_id, action, endpoint, "allowed")
        return principal

    if not x_api_key:
        _audit("unknown", action, endpoint, "denied", "missing_api_key")
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    principal = container.auth_store.get_principal(x_api_key)
    if principal is None:
        _audit("unknown", action, endpoint, "denied", "invalid_api_key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not container.auth_store.is_allowed(principal, action):
        _audit(principal.tenant_id, action, endpoint, "denied", "plan_forbidden")
        raise HTTPException(status_code=403, detail="Plan does not allow this action")

    try:
        _enforce_quotas(principal, action)
    except HTTPException as exc:
        _audit(principal.tenant_id, action, endpoint, "denied", str(exc.detail))
        raise

    _audit(principal.tenant_id, action, endpoint, "allowed")

    return principal


def require_action(action: str) -> Callable[[Request, str | None, str | None], ApiPrincipal]:
    def dependency(
        request: Request,
        x_api_key: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> ApiPrincipal:
        return authorize(action, x_api_key, authorization, str(request.url.path))

    return dependency
