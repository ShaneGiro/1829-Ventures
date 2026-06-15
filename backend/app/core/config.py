"""Application settings, loaded from environment variables.

All configuration is environment-driven (12-factor) so the v2 cloud migration is
an env-var change, not a code rewrite. Nothing here hardcodes a hostname, port,
credential, or path.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ─── App ──────────────────────────────────────────────────────────────────
    app_name: str = "1829 Ventures CRM"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    api_v1_prefix: str = "/api"
    frontend_url: str = Field(default="http://localhost:5173")

    # ─── Database ─────────────────────────────────────────────────────────────
    # A single connection string drives both engines; the database module swaps
    # the driver prefix (asyncpg for the API, psycopg2 for workers + Alembic).
    database_url: str = Field(
        default="postgresql://crm:crm@localhost:5432/crm",  # noqa: S106 - dev default
    )
    db_echo: bool = Field(default=False)
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=20)

    # ─── Redis / Celery ───────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_result_backend(self) -> str:
        return self.redis_url

    # ─── Auth ─────────────────────────────────────────────────────────────────
    jwt_secret: str = Field(default="dev-insecure-change-me")  # noqa: S105 - dev default
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=60 * 24)
    # Comma-separated list of eligible RIT Google domains for v1 login.
    allowed_email_domains: str = Field(default="g.rit.edu,rit.edu")
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")  # noqa: S106 - dev default
    google_redirect_uri: str = Field(default="http://localhost:8000/api/auth/callback")
    # Long-lived scoped key for Ritchie (the agent role). Compared by hash.
    agent_api_key: str = Field(default="")
    # kernelbot webhook for outbound event fanout. Empty in local dev = no-op.
    ritchie_webhook_url: str = Field(default="")

    # ─── Object storage (S3-compatible: MinIO in v1, R2 in v2) ────────────────
    s3_endpoint_url: str = Field(default="http://localhost:9000")
    s3_access_key: str = Field(default="minioadmin")
    s3_secret_key: str = Field(default="minioadmin")  # noqa: S106 - dev default
    s3_bucket_documents: str = Field(default="crm-documents")
    s3_region: str = Field(default="us-east-1")

    # ─── Email (SendGrid) ─────────────────────────────────────────────────────
    sendgrid_api_key: str = Field(default="")
    email_from_address: str = Field(default="crm@1829.ventures")
    digest_send_hour: int = Field(default=9)  # 9 AM America/New_York
    timezone: str = Field(default="America/New_York")

    # ─── Search / embeddings ─────────────────────────────────────────────────
    embedding_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_enabled: bool = Field(default=True)
    embedding_batch_size: int = Field(default=32)
    # Company search: cap and minimum cosine similarity for semantic (vector)
    # matches appended after exact matches. Raising the threshold = stricter.
    search_semantic_limit: int = Field(default=25)
    search_semantic_threshold: float = Field(default=0.3)

    # ─── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: str = Field(default="http://localhost:5173")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_domains_list(self) -> list[str]:
        return [d.strip().lower() for d in self.allowed_email_domains.split(",") if d.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        """asyncpg URL for FastAPI request handlers."""
        return str(self.database_url).replace("postgresql://", "postgresql+asyncpg://", 1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        """psycopg2 URL for Celery workers and Alembic migrations."""
        return str(self.database_url).replace("postgresql://", "postgresql+psycopg2://", 1)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Use this everywhere instead of instantiating."""
    return Settings()


settings = get_settings()
