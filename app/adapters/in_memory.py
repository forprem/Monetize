from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.adapters.contracts import AuditEvent, AuditStore, CatalogStore, ExportJob, ExportStore, SummaryStore, UsageStore, ZipSummary
from app.adapters.layer_data import LAYER_DATA
from app.adapters.real_data_enricher import fetch_real_zip_summary


class InMemorySummaryStore(SummaryStore):
    def __init__(self, census_api_key: str = "") -> None:
        self._census_api_key = census_api_key
        self._data: dict[str, ZipSummary] = {}

    def get_zip_summary(self, zip_code: str) -> ZipSummary | None:
        # Live data only: no seed fallback.
        summary = fetch_real_zip_summary(zip_code, self._census_api_key)
        if summary is not None:
            self._data[zip_code] = summary
            return summary
        return None

    def compare_zip_summaries(self, zip_codes: list[str]) -> list[ZipSummary]:
        results = []
        for z in zip_codes:
            summary = self.get_zip_summary(z)
            if summary is not None:
                results.append(summary)
        return results


class InMemoryCatalogStore(CatalogStore):
    def __init__(self) -> None:
        self._layers = LAYER_DATA

    def get_layers(self) -> list[dict[str, str]]:
        return self._layers


class InMemoryExportStore(ExportStore):
    def __init__(self) -> None:
        self._jobs: dict[str, ExportJob] = {}

    def create_export_job(self, tenant_id: str, dataset_code: str) -> ExportJob:
        job_id = str(uuid4())
        job = ExportJob(
            job_id=job_id,
            tenant_id=tenant_id,
            dataset_code=dataset_code,
            status="queued",
            output_uri=None,
            created_at=datetime.now(timezone.utc),
        )
        self._jobs[job_id] = job
        return job

    def get_export_job(self, job_id: str) -> ExportJob | None:
        return self._jobs.get(job_id)

    def list_export_jobs(
        self,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[ExportJob]:
        jobs = list(self._jobs.values())
        if tenant_id is not None:
            jobs = [job for job in jobs if job.tenant_id == tenant_id]
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        jobs.sort(key=lambda job: job.created_at, reverse=True)
        return jobs[offset : offset + limit]

    def process_export_job(self, job_id: str) -> ExportJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if job.status == "done":
            return job
        if job.status == "failed":
            return job

        job.status = "running"
        job.output_uri = f"s3://mock-exports/{job.tenant_id}/{job.dataset_code}/{job.job_id}.csv"
        job.status = "done"
        return job

    def fail_export_job(self, job_id: str) -> ExportJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if job.status == "done":
            return job
        job.status = "failed"
        job.output_uri = None
        return job

    def retry_export_job(self, job_id: str) -> ExportJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if job.status == "failed":
            job.status = "queued"
        return job

    def process_pending_export_jobs(self, limit: int = 50) -> list[ExportJob]:
        pending_jobs = [job for job in self._jobs.values() if job.status == "queued"]
        pending_jobs.sort(key=lambda job: job.created_at)

        processed: list[ExportJob] = []
        for job in pending_jobs[:limit]:
            updated = self.process_export_job(job.job_id)
            if updated is not None:
                processed.append(updated)
        return processed


class InMemoryUsageStore(UsageStore):
    def __init__(self) -> None:
        self._counts: dict[str, dict[str, int]] = {}

    def get_usage(self, tenant_id: str) -> dict[str, int]:
        tenant_counts = self._counts.get(tenant_id, {})
        total = sum(tenant_counts.values())
        return {
            "requests_this_month": total,
            "exports_this_month": tenant_counts.get("POST /export", 0),
        }

    def record_request(self, tenant_id: str, endpoint: str) -> None:
        self._counts.setdefault(tenant_id, {})
        self._counts[tenant_id][endpoint] = self._counts[tenant_id].get(endpoint, 0) + 1


class InMemoryAuditStore(AuditStore):
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record_event(
        self,
        tenant_id: str,
        action: str,
        endpoint: str,
        outcome: str,
        reason: str | None = None,
    ) -> None:
        self.events.append(
            AuditEvent(
                tenant_id=tenant_id,
                action=action,
                endpoint=endpoint,
                outcome=outcome,
                reason=reason,
                created_at=datetime.now(timezone.utc),
            )
        )

    def list_events(
        self,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        outcome: str | None = None,
    ) -> list[AuditEvent]:
        events = self.events
        if tenant_id is not None:
            events = [event for event in events if event.tenant_id == tenant_id]
        if start_at is not None:
            events = [event for event in events if event.created_at >= start_at]
        if end_at is not None:
            events = [event for event in events if event.created_at <= end_at]
        if outcome is not None:
            events = [event for event in events if event.outcome == outcome]

        ordered = list(reversed(events))
        return ordered[offset : offset + limit]
