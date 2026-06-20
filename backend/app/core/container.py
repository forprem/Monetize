from __future__ import annotations

from app.adapters.auth_in_memory import InMemoryAuthStore
from app.adapters.contracts import AuditStore, AuthStore, CatalogStore, ExportStore, SummaryStore, UsageStore
from app.adapters.in_memory import InMemoryAuditStore, InMemoryCatalogStore, InMemoryExportStore, InMemorySummaryStore, InMemoryUsageStore
from app.adapters.minio_export import MinioExportWriter
from app.adapters.postgres import (
    PostgresAuditStore,
    PostgresAuthStore,
    PostgresCatalogStore,
    PostgresContext,
    PostgresExportStore,
    PostgresSummaryStore,
    PostgresUsageStore,
)
from app.adapters.redis_usage import RedisUsageStore
from app.core.settings import settings


class ServiceContainer:
    def __init__(self) -> None:
        if settings.storage_mode == "postgres":
            ctx = PostgresContext(settings.database_url)
            minio_writer = None
            if settings.minio_enabled:
                minio_writer = MinioExportWriter(
                    endpoint=settings.minio_endpoint,
                    access_key=settings.minio_access_key,
                    secret_key=settings.minio_secret_key,
                    bucket=settings.minio_bucket,
                    secure=settings.minio_secure,
                )

            self.summary_store = PostgresSummaryStore(ctx)
            self.catalog_store = PostgresCatalogStore(ctx)
            self.export_store = PostgresExportStore(ctx, minio_writer=minio_writer)
            self.auth_store = PostgresAuthStore(ctx)
            self.audit_store = PostgresAuditStore(ctx)

            if settings.redis_enabled:
                self.usage_store = RedisUsageStore(settings.redis_url)
            else:
                self.usage_store = PostgresUsageStore(ctx)
        else:
            self.summary_store = InMemorySummaryStore(census_api_key=settings.census_api_key)
            self.catalog_store = InMemoryCatalogStore()
            self.export_store = InMemoryExportStore()
            self.usage_store = InMemoryUsageStore()
            self.auth_store = InMemoryAuthStore()
            self.audit_store = InMemoryAuditStore()

        self.summary_store: SummaryStore
        self.catalog_store: CatalogStore
        self.export_store: ExportStore
        self.usage_store: UsageStore
        self.auth_store: AuthStore
        self.audit_store: AuditStore


container = ServiceContainer()
