from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ZIP Intelligence Platform API"
    app_version: str = "0.1.0"
    default_api_key: str = "dev_demo_key"
    default_tenant_id: str = "demo-tenant"
    default_plan: str = "pro"
    basic_api_key: str = "dev_basic_key"
    basic_tenant_id: str = "demo-basic-tenant"
    trial_api_key: str = "dev_trial_key"
    trial_tenant_id: str = "demo-trial-tenant"
    admin_api_key: str = "dev_admin_key"
    admin_tenant_id: str = "platform-admin"
    enforce_quotas: bool = True
    auto_process_exports: bool = False
    export_worker_enabled: bool = False
    export_worker_poll_interval_seconds: float = 5.0
    export_worker_batch_size: int = 25

    # Session auth (UI login)
    auth_session_secret: str = "dev_session_secret_change_me"
    auth_session_ttl_seconds: int = 28800

    # Provider modes: inmemory (default), postgres
    storage_mode: str = "inmemory"

    # Postgres
    database_url: str = "postgresql+psycopg://monetize:monetize@localhost:5432/monetize"

    # Redis (optional)
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"

    # MinIO (optional)
    minio_enabled: bool = False
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "exports"

    # External data APIs
    # Census API key is optional but increases rate limits (free at api.census.gov/data/key_signup.html)
    census_api_key: str = ""

    # Telegram bot notifications (optional)
    # Set via .env file or environment variables:
    #   TELEGRAM_ENABLED=false
    #   TELEGRAM_BOT_TOKEN=123456789:AABBccdd...
    #   TELEGRAM_CHAT_ID=123456789
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
