from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class ZipSummary:
    zip_code: str
    signal_score: float
    avg_download_mbps: float
    avg_upload_mbps: float
    avg_latency_ms: float
    consistency_score: float
    provider_count: int
    hospital_count: int
    healthcare_access_score: float
    population_total: int
    median_income: int
    age_0_17: int
    age_18_34: int
    age_35_64: int
    age_65_plus: int
    network_opportunity_score: float
    market_attractiveness_score: float
    overall_score: float
    home_ownership_rate: float
    vacancy_rate: float
    median_home_value: int
    avg_household_size: float
    updated_at: datetime


@dataclass
class ExportJob:
    job_id: str
    tenant_id: str
    dataset_code: str
    status: str
    output_uri: str | None
    created_at: datetime


@dataclass
class ApiPrincipal:
    api_key: str
    tenant_id: str
    plan: str
    status: str = "active"
    expires_at: datetime | None = None


@dataclass
class AuthUser:
    email: str
    tenant_id: str
    plan: str
    status: str = "active"


@dataclass
class AuditEvent:
    tenant_id: str
    action: str
    endpoint: str
    outcome: str
    reason: str | None
    created_at: datetime


class SummaryStore(Protocol):
    def get_zip_summary(self, zip_code: str) -> ZipSummary | None:
        ...

    def compare_zip_summaries(self, zip_codes: list[str]) -> list[ZipSummary]:
        ...


class CatalogStore(Protocol):
    def get_layers(self) -> list[dict[str, str]]:
        ...


class ExportStore(Protocol):
    def create_export_job(self, tenant_id: str, dataset_code: str) -> ExportJob:
        ...

    def get_export_job(self, job_id: str) -> ExportJob | None:
        ...

    def list_export_jobs(
        self,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[ExportJob]:
        ...

    def process_export_job(self, job_id: str) -> ExportJob | None:
        ...

    def fail_export_job(self, job_id: str) -> ExportJob | None:
        ...

    def retry_export_job(self, job_id: str) -> ExportJob | None:
        ...

    def process_pending_export_jobs(self, limit: int = 50) -> list[ExportJob]:
        ...


class UsageStore(Protocol):
    def get_usage(self, tenant_id: str) -> dict[str, int]:
        ...

    def record_request(self, tenant_id: str, endpoint: str) -> None:
        ...


class AuthStore(Protocol):
    def get_principal(self, api_key: str) -> ApiPrincipal | None:
        ...

    def is_allowed(self, principal: ApiPrincipal, action: str) -> bool:
        ...

    def create_api_key(
        self,
        tenant_id: str,
        plan: str,
        expires_at: datetime | None = None,
    ) -> ApiPrincipal:
        ...

    def list_api_keys(self, tenant_id: str | None = None) -> list[ApiPrincipal]:
        ...

    def revoke_api_key(self, api_key: str) -> ApiPrincipal | None:
        ...

    def rotate_api_key(self, api_key: str, expires_at: datetime | None = None) -> ApiPrincipal | None:
        ...

    def authenticate_user(self, email: str, password: str) -> AuthUser | None:
        ...

    def list_users(self, tenant_id: str | None = None) -> list[AuthUser]:
        ...

    def create_user(self, email: str, password: str, tenant_id: str, plan: str) -> AuthUser:
        ...

    def disable_user(self, email: str) -> AuthUser | None:
        ...

    def set_user_password(self, email: str, password: str) -> AuthUser | None:
        ...


class AuditStore(Protocol):
    def record_event(
        self,
        tenant_id: str,
        action: str,
        endpoint: str,
        outcome: str,
        reason: str | None = None,
    ) -> None:
        ...

    def list_events(
        self,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        outcome: str | None = None,
    ) -> list[AuditEvent]:
        ...
