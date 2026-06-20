from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LayerOut(BaseModel):
    code: str
    name: str


class ZipSummaryOut(BaseModel):
    zip_code: str
    lat: float | None = None
    lon: float | None = None
    signal_score: float
    avg_download_mbps: float
    avg_upload_mbps: float
    avg_latency_ms: float
    consistency_score: float
    provider_count: int
    hospital_count: int
    healthcare_access_score: float
    estimated_patient_burden: int
    chronic_data_year: int | None = None
    chronic_burden_score: float | None = None
    estimated_chronic_patients: int | None = None
    diabetes_prevalence_pct: float | None = None
    hypertension_prevalence_pct: float | None = None
    obesity_prevalence_pct: float | None = None
    chd_prevalence_pct: float | None = None
    copd_prevalence_pct: float | None = None
    stroke_prevalence_pct: float | None = None
    population_total: int
    median_income: int
    age_0_17: int
    age_18_34: int
    age_35_64: int
    age_65_plus: int
    network_opportunity_score: float
    market_attractiveness_score: float
    overall_score: float
    updated_at: datetime


class ZipCompareRequest(BaseModel):
    zip_codes: list[str] = Field(min_length=2, max_length=5)


class ZipCompareResponse(BaseModel):
    results: list[ZipSummaryOut]


class ExportCreateRequest(BaseModel):
    dataset_code: str = Field(min_length=3, max_length=100)


class ExportJobOut(BaseModel):
    job_id: str
    tenant_id: str
    dataset_code: str
    status: str
    output_uri: str | None
    created_at: datetime


class ExportJobPageOut(BaseModel):
    items: list[ExportJobOut]
    limit: int
    offset: int
    returned: int


class UsageOut(BaseModel):
    tenant_id: str
    requests_this_month: int
    exports_this_month: int


class AuditEventOut(BaseModel):
    tenant_id: str
    action: str
    endpoint: str
    outcome: str
    reason: str | None
    created_at: datetime


class AuditEventPageOut(BaseModel):
    items: list[AuditEventOut]
    limit: int
    offset: int
    returned: int


class ApiKeyCreateRequest(BaseModel):
    tenant_id: str = Field(min_length=3, max_length=120)
    plan: str = Field(min_length=3, max_length=30)
    expires_in_seconds: int | None = Field(default=None, ge=0)


class ApiKeyRotateRequest(BaseModel):
    expires_in_seconds: int | None = Field(default=None, ge=0)


class ApiKeyOut(BaseModel):
    api_key: str
    tenant_id: str
    plan: str
    status: str
    expires_at: datetime | None


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=6, max_length=200)


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    plan: str
    email: str


class SessionMeOut(BaseModel):
    email: str
    tenant_id: str
    plan: str


class AuthUserOut(BaseModel):
    email: str
    tenant_id: str
    plan: str
    status: str


class AuthUserCreateRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=6, max_length=200)
    tenant_id: str = Field(min_length=3, max_length=120)
    plan: str = Field(min_length=3, max_length=30)


class AuthUserPasswordResetRequest(BaseModel):
    password: str = Field(min_length=6, max_length=200)
