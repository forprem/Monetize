from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.adapters.contracts import ApiPrincipal, AuditEvent, AuditStore, AuthStore, AuthUser, CatalogStore, ExportJob, ExportStore, SummaryStore, UsageStore, ZipSummary
from app.adapters.layer_data import LAYER_DATA
from app.adapters.minio_export import MinioExportWriter
from app.core.entitlements import PLAN_PERMISSIONS
from app.core.passwords import hash_password, verify_password
from app.core.settings import settings


class Base(DeclarativeBase):
    pass


class ZipSummaryRow(Base):
    __tablename__ = "zip_summaries"

    zip_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    signal_score: Mapped[float] = mapped_column(Float)
    avg_download_mbps: Mapped[float] = mapped_column(Float)
    avg_upload_mbps: Mapped[float] = mapped_column(Float)
    avg_latency_ms: Mapped[float] = mapped_column(Float)
    consistency_score: Mapped[float] = mapped_column(Float)
    provider_count: Mapped[int] = mapped_column(Integer)
    hospital_count: Mapped[int] = mapped_column(Integer)
    healthcare_access_score: Mapped[float] = mapped_column(Float)
    population_total: Mapped[int] = mapped_column(Integer)
    median_income: Mapped[int] = mapped_column(Integer)
    age_0_17: Mapped[int] = mapped_column(Integer)
    age_18_34: Mapped[int] = mapped_column(Integer)
    age_35_64: Mapped[int] = mapped_column(Integer)
    age_65_plus: Mapped[int] = mapped_column(Integer)
    network_opportunity_score: Mapped[float] = mapped_column(Float)
    market_attractiveness_score: Mapped[float] = mapped_column(Float)
    overall_score: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LayerRow(Base):
    __tablename__ = "layers"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))


class ExportJobRow(Base):
    __tablename__ = "export_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(120), index=True)
    dataset_code: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20))
    output_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSON)


class UsageEventRow(Base):
    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(120), index=True)
    endpoint: Mapped[str] = mapped_column(String(120), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ApiKeyRow(Base):
    __tablename__ = "api_keys"

    api_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(120), index=True)
    plan: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="active")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserAccountRow(Base):
    __tablename__ = "user_accounts"

    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    tenant_id: Mapped[str] = mapped_column(String(120), index=True)
    plan: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="active")


class AuditEventRow(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(120), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    endpoint: Mapped[str] = mapped_column(String(255))
    outcome: Mapped[str] = mapped_column(String(30), index=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


def summary_to_row(session: Session, summary: ZipSummary) -> None:
    session.merge(ZipSummaryRow(**asdict(summary)))


def row_to_summary(row: ZipSummaryRow) -> ZipSummary:
    return ZipSummary(
        zip_code=row.zip_code,
        signal_score=row.signal_score,
        avg_download_mbps=row.avg_download_mbps,
        avg_upload_mbps=row.avg_upload_mbps,
        avg_latency_ms=row.avg_latency_ms,
        consistency_score=row.consistency_score,
        provider_count=row.provider_count,
        hospital_count=row.hospital_count,
        healthcare_access_score=row.healthcare_access_score,
        population_total=row.population_total,
        median_income=row.median_income,
        age_0_17=row.age_0_17,
        age_18_34=row.age_18_34,
        age_35_64=row.age_35_64,
        age_65_plus=row.age_65_plus,
        network_opportunity_score=row.network_opportunity_score,
        market_attractiveness_score=row.market_attractiveness_score,
        overall_score=row.overall_score,
        updated_at=row.updated_at,
    )


class PostgresContext:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        self._seed_if_needed()

    def _seed_if_needed(self) -> None:
        with Session(self.engine) as session:
            has_layers = session.scalar(select(LayerRow.code).limit(1)) is not None
            if not has_layers:
                for layer in LAYER_DATA:
                    session.add(LayerRow(**layer))

            has_api_keys = session.scalar(select(ApiKeyRow.api_key).limit(1)) is not None
            if not has_api_keys:
                session.add(
                    ApiKeyRow(
                        api_key=settings.default_api_key,
                        tenant_id=settings.default_tenant_id,
                        plan=settings.default_plan,
                        status="active",
                        expires_at=None,
                    )
                )
                session.add(
                    ApiKeyRow(
                        api_key=settings.basic_api_key,
                        tenant_id=settings.basic_tenant_id,
                        plan="basic",
                        status="active",
                        expires_at=None,
                    )
                )
                session.add(
                    ApiKeyRow(
                        api_key=settings.trial_api_key,
                        tenant_id=settings.trial_tenant_id,
                        plan="trial",
                        status="active",
                        expires_at=None,
                    )
                )
                session.add(
                    ApiKeyRow(
                        api_key=settings.admin_api_key,
                        tenant_id=settings.admin_tenant_id,
                        plan="enterprise",
                        status="active",
                        expires_at=None,
                    )
                )

            has_users = session.scalar(select(UserAccountRow.email).limit(1)) is not None
            if not has_users:
                session.add(
                    UserAccountRow(
                        email="admin@zipintel.local",
                        password_hash=hash_password("admin123"),
                        tenant_id=settings.admin_tenant_id,
                        plan="enterprise",
                        status="active",
                    )
                )
                session.add(
                    UserAccountRow(
                        email="pro@zipintel.local",
                        password_hash=hash_password("pro123"),
                        tenant_id=settings.default_tenant_id,
                        plan=settings.default_plan,
                        status="active",
                    )
                )
                session.add(
                    UserAccountRow(
                        email="basic@zipintel.local",
                        password_hash=hash_password("basic123"),
                        tenant_id=settings.basic_tenant_id,
                        plan="basic",
                        status="active",
                    )
                )
                session.add(
                    UserAccountRow(
                        email="trial@zipintel.local",
                        password_hash=hash_password("trial123"),
                        tenant_id=settings.trial_tenant_id,
                        plan="trial",
                        status="active",
                    )
                )

            session.commit()


class PostgresSummaryStore(SummaryStore):
    def __init__(self, ctx: PostgresContext) -> None:
        self.ctx = ctx

    def get_zip_summary(self, zip_code: str) -> ZipSummary | None:
        with Session(self.ctx.engine) as session:
            row = session.get(ZipSummaryRow, zip_code)
            return row_to_summary(row) if row else None

    def compare_zip_summaries(self, zip_codes: list[str]) -> list[ZipSummary]:
        if not zip_codes:
            return []
        with Session(self.ctx.engine) as session:
            rows = session.scalars(select(ZipSummaryRow).where(ZipSummaryRow.zip_code.in_(zip_codes))).all()
            return [row_to_summary(r) for r in rows]


class PostgresCatalogStore(CatalogStore):
    def __init__(self, ctx: PostgresContext) -> None:
        self.ctx = ctx

    def get_layers(self) -> list[dict[str, str]]:
        with Session(self.ctx.engine) as session:
            rows = session.scalars(select(LayerRow)).all()
            return [{"code": r.code, "name": r.name} for r in rows]


class PostgresExportStore(ExportStore):
    def __init__(
        self,
        ctx: PostgresContext,
        output_prefix: str = "s3://mock-exports",
        minio_writer: MinioExportWriter | None = None,
    ) -> None:
        self.ctx = ctx
        self.output_prefix = output_prefix
        self.minio_writer = minio_writer

    def create_export_job(self, tenant_id: str, dataset_code: str) -> ExportJob:
        job_id = str(uuid4())
        created_at = datetime.now(timezone.utc)
        row = ExportJobRow(
            job_id=job_id,
            tenant_id=tenant_id,
            dataset_code=dataset_code,
            status="queued",
            output_uri=None,
            created_at=created_at,
            payload={"tenant_id": tenant_id, "dataset_code": dataset_code},
        )
        with Session(self.ctx.engine) as session:
            session.add(row)
            session.commit()

        return ExportJob(
            job_id=job_id,
            tenant_id=tenant_id,
            dataset_code=dataset_code,
            status="queued",
            output_uri=None,
            created_at=created_at,
        )

    def get_export_job(self, job_id: str) -> ExportJob | None:
        with Session(self.ctx.engine) as session:
            row = session.get(ExportJobRow, job_id)
            if not row:
                return None
            return ExportJob(
                job_id=row.job_id,
                tenant_id=row.tenant_id,
                dataset_code=row.dataset_code,
                status=row.status,
                output_uri=row.output_uri,
                created_at=row.created_at,
            )

    def list_export_jobs(
        self,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[ExportJob]:
        with Session(self.ctx.engine) as session:
            stmt = select(ExportJobRow)
            if tenant_id is not None:
                stmt = stmt.where(ExportJobRow.tenant_id == tenant_id)
            if status is not None:
                stmt = stmt.where(ExportJobRow.status == status)
            rows = session.scalars(
                stmt.order_by(ExportJobRow.created_at.desc()).offset(offset).limit(limit)
            ).all()
        return [
            ExportJob(
                job_id=row.job_id,
                tenant_id=row.tenant_id,
                dataset_code=row.dataset_code,
                status=row.status,
                output_uri=row.output_uri,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def process_export_job(self, job_id: str) -> ExportJob | None:
        with Session(self.ctx.engine) as session:
            row = session.get(ExportJobRow, job_id)
            if row is None:
                return None
            if row.status == "failed":
                return ExportJob(
                    job_id=row.job_id,
                    tenant_id=row.tenant_id,
                    dataset_code=row.dataset_code,
                    status=row.status,
                    output_uri=row.output_uri,
                    created_at=row.created_at,
                )
            if row.status != "done":
                row.status = "running"
                output_uri = f"{self.output_prefix}/{row.tenant_id}/{row.dataset_code}/{row.job_id}.csv"
                if self.minio_writer is not None:
                    output_uri = self.minio_writer.write_export(row.tenant_id, row.dataset_code, row.job_id)
                row.output_uri = output_uri
                row.status = "done"
                session.commit()

            return ExportJob(
                job_id=row.job_id,
                tenant_id=row.tenant_id,
                dataset_code=row.dataset_code,
                status=row.status,
                output_uri=row.output_uri,
                created_at=row.created_at,
            )

    def fail_export_job(self, job_id: str) -> ExportJob | None:
        with Session(self.ctx.engine) as session:
            row = session.get(ExportJobRow, job_id)
            if row is None:
                return None
            if row.status != "done":
                row.status = "failed"
                row.output_uri = None
                session.commit()
            return ExportJob(
                job_id=row.job_id,
                tenant_id=row.tenant_id,
                dataset_code=row.dataset_code,
                status=row.status,
                output_uri=row.output_uri,
                created_at=row.created_at,
            )

    def retry_export_job(self, job_id: str) -> ExportJob | None:
        with Session(self.ctx.engine) as session:
            row = session.get(ExportJobRow, job_id)
            if row is None:
                return None
            if row.status == "failed":
                row.status = "queued"
                session.commit()
            return ExportJob(
                job_id=row.job_id,
                tenant_id=row.tenant_id,
                dataset_code=row.dataset_code,
                status=row.status,
                output_uri=row.output_uri,
                created_at=row.created_at,
            )

    def process_pending_export_jobs(self, limit: int = 50) -> list[ExportJob]:
        with Session(self.ctx.engine) as session:
            rows = session.scalars(
                select(ExportJobRow)
                .where(ExportJobRow.status == "queued")
                .order_by(ExportJobRow.created_at.asc())
                .limit(limit)
            ).all()

            processed: list[ExportJob] = []
            for row in rows:
                row.status = "running"
                output_uri = f"{self.output_prefix}/{row.tenant_id}/{row.dataset_code}/{row.job_id}.csv"
                if self.minio_writer is not None:
                    output_uri = self.minio_writer.write_export(row.tenant_id, row.dataset_code, row.job_id)
                row.output_uri = output_uri
                row.status = "done"
                processed.append(
                    ExportJob(
                        job_id=row.job_id,
                        tenant_id=row.tenant_id,
                        dataset_code=row.dataset_code,
                        status=row.status,
                        output_uri=row.output_uri,
                        created_at=row.created_at,
                    )
                )

            session.commit()
            return processed


class PostgresUsageStore(UsageStore):
    def __init__(self, ctx: PostgresContext) -> None:
        self.ctx = ctx

    def get_usage(self, tenant_id: str) -> dict[str, int]:
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        with Session(self.ctx.engine) as session:
            rows = session.scalars(
                select(UsageEventRow).where(
                    UsageEventRow.tenant_id == tenant_id,
                    UsageEventRow.created_at >= month_start,
                )
            ).all()
            requests_this_month = len(rows)
            exports_this_month = sum(1 for row in rows if row.endpoint == "POST /export")
        return {
            "requests_this_month": requests_this_month,
            "exports_this_month": exports_this_month,
        }

    def record_request(self, tenant_id: str, endpoint: str) -> None:
        with Session(self.ctx.engine) as session:
            session.add(
                UsageEventRow(
                    tenant_id=tenant_id,
                    endpoint=endpoint,
                    created_at=datetime.now(timezone.utc),
                )
            )
            session.commit()


class PostgresAuthStore(AuthStore):
    def __init__(self, ctx: PostgresContext) -> None:
        self.ctx = ctx

    def get_principal(self, api_key: str) -> ApiPrincipal | None:
        with Session(self.ctx.engine) as session:
            row = session.get(ApiKeyRow, api_key)
            if row is None or row.status != "active":
                return None
            if row.expires_at is not None and row.expires_at <= datetime.now(timezone.utc):
                return None
            return ApiPrincipal(
                api_key=row.api_key,
                tenant_id=row.tenant_id,
                plan=row.plan,
                status=row.status,
                expires_at=row.expires_at,
            )

    def is_allowed(self, principal: ApiPrincipal, action: str) -> bool:
        allowed = PLAN_PERMISSIONS.get(principal.plan, set())
        return action in allowed

    def create_api_key(
        self,
        tenant_id: str,
        plan: str,
        expires_at: datetime | None = None,
    ) -> ApiPrincipal:
        api_key = f"live_{token_urlsafe(18)}"
        with Session(self.ctx.engine) as session:
            session.add(
                ApiKeyRow(
                    api_key=api_key,
                    tenant_id=tenant_id,
                    plan=plan,
                    status="active",
                    expires_at=expires_at,
                )
            )
            session.commit()
        return ApiPrincipal(
            api_key=api_key,
            tenant_id=tenant_id,
            plan=plan,
            status="active",
            expires_at=expires_at,
        )

    def list_api_keys(self, tenant_id: str | None = None) -> list[ApiPrincipal]:
        with Session(self.ctx.engine) as session:
            stmt = select(ApiKeyRow)
            if tenant_id is not None:
                stmt = stmt.where(ApiKeyRow.tenant_id == tenant_id)
            rows = session.scalars(stmt.order_by(ApiKeyRow.tenant_id.asc(), ApiKeyRow.plan.asc())).all()
        return [
            ApiPrincipal(
                api_key=row.api_key,
                tenant_id=row.tenant_id,
                plan=row.plan,
                status=row.status,
                expires_at=row.expires_at,
            )
            for row in rows
        ]

    def revoke_api_key(self, api_key: str) -> ApiPrincipal | None:
        with Session(self.ctx.engine) as session:
            row = session.get(ApiKeyRow, api_key)
            if row is None:
                return None
            row.status = "revoked"
            session.commit()
            return ApiPrincipal(
                api_key=row.api_key,
                tenant_id=row.tenant_id,
                plan=row.plan,
                status=row.status,
                expires_at=row.expires_at,
            )

    def rotate_api_key(self, api_key: str, expires_at: datetime | None = None) -> ApiPrincipal | None:
        with Session(self.ctx.engine) as session:
            row = session.get(ApiKeyRow, api_key)
            if row is None:
                return None

            row.status = "revoked"
            new_api_key = f"live_{token_urlsafe(18)}"
            new_expires_at = row.expires_at if expires_at is None else expires_at
            replacement = ApiKeyRow(
                api_key=new_api_key,
                tenant_id=row.tenant_id,
                plan=row.plan,
                status="active",
                expires_at=new_expires_at,
            )
            session.add(replacement)
            session.commit()
            return ApiPrincipal(
                api_key=replacement.api_key,
                tenant_id=replacement.tenant_id,
                plan=replacement.plan,
                status=replacement.status,
                expires_at=replacement.expires_at,
            )

    def authenticate_user(self, email: str, password: str) -> AuthUser | None:
        with Session(self.ctx.engine) as session:
            row = session.get(UserAccountRow, email.lower().strip())
            if row is None or row.status != "active":
                return None
            if not verify_password(password, row.password_hash):
                return None
            return AuthUser(
                email=row.email,
                tenant_id=row.tenant_id,
                plan=row.plan,
                status=row.status,
            )

    def list_users(self, tenant_id: str | None = None) -> list[AuthUser]:
        with Session(self.ctx.engine) as session:
            stmt = select(UserAccountRow)
            if tenant_id is not None:
                stmt = stmt.where(UserAccountRow.tenant_id == tenant_id)
            rows = session.scalars(stmt.order_by(UserAccountRow.tenant_id.asc(), UserAccountRow.email.asc())).all()
            return [
                AuthUser(
                    email=row.email,
                    tenant_id=row.tenant_id,
                    plan=row.plan,
                    status=row.status,
                )
                for row in rows
            ]

    def create_user(self, email: str, password: str, tenant_id: str, plan: str) -> AuthUser:
        normalized_email = email.lower().strip()
        with Session(self.ctx.engine) as session:
            existing = session.get(UserAccountRow, normalized_email)
            if existing is not None:
                raise ValueError("User already exists")
            row = UserAccountRow(
                email=normalized_email,
                password_hash=hash_password(password),
                tenant_id=tenant_id,
                plan=plan,
                status="active",
            )
            session.add(row)
            session.commit()
            return AuthUser(
                email=row.email,
                tenant_id=row.tenant_id,
                plan=row.plan,
                status=row.status,
            )

    def disable_user(self, email: str) -> AuthUser | None:
        with Session(self.ctx.engine) as session:
            row = session.get(UserAccountRow, email.lower().strip())
            if row is None:
                return None
            row.status = "disabled"
            session.commit()
            return AuthUser(
                email=row.email,
                tenant_id=row.tenant_id,
                plan=row.plan,
                status=row.status,
            )

    def set_user_password(self, email: str, password: str) -> AuthUser | None:
        with Session(self.ctx.engine) as session:
            row = session.get(UserAccountRow, email.lower().strip())
            if row is None:
                return None
            row.password_hash = hash_password(password)
            session.commit()
            return AuthUser(
                email=row.email,
                tenant_id=row.tenant_id,
                plan=row.plan,
                status=row.status,
            )


class PostgresAuditStore(AuditStore):
    def __init__(self, ctx: PostgresContext) -> None:
        self.ctx = ctx

    def record_event(
        self,
        tenant_id: str,
        action: str,
        endpoint: str,
        outcome: str,
        reason: str | None = None,
    ) -> None:
        with Session(self.ctx.engine) as session:
            session.add(
                AuditEventRow(
                    tenant_id=tenant_id,
                    action=action,
                    endpoint=endpoint,
                    outcome=outcome,
                    reason=reason,
                    created_at=datetime.now(timezone.utc),
                )
            )
            session.commit()

    def list_events(
        self,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        outcome: str | None = None,
    ) -> list[AuditEvent]:
        with Session(self.ctx.engine) as session:
            stmt = select(AuditEventRow)
            if tenant_id is not None:
                stmt = stmt.where(AuditEventRow.tenant_id == tenant_id)
            if start_at is not None:
                stmt = stmt.where(AuditEventRow.created_at >= start_at)
            if end_at is not None:
                stmt = stmt.where(AuditEventRow.created_at <= end_at)
            if outcome is not None:
                stmt = stmt.where(AuditEventRow.outcome == outcome)

            rows = session.scalars(
                stmt.order_by(AuditEventRow.created_at.desc()).offset(offset).limit(limit)
            ).all()

        return [
            AuditEvent(
                tenant_id=row.tenant_id,
                action=row.action,
                endpoint=row.endpoint,
                outcome=row.outcome,
                reason=row.reason,
                created_at=row.created_at,
            )
            for row in rows
        ]
