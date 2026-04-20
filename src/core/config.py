from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["dev", "staging", "prod"] = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8100
    debug: bool = False

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "contractforge"
    postgres_user: str = "cf"
    postgres_password: SecretStr = SecretStr("cf-secret-2026")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}"
            f":{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}"
            f":{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: SecretStr = SecretStr("cf-redis-secret")

    @property
    def redis_url(self) -> str:
        return (
            f"redis://:{self.redis_password.get_secret_value()}"
            f"@{self.redis_host}:{self.redis_port}/0"
        )

    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    @property
    def celery_result_backend(self) -> str:
        return (
            f"redis://:{self.redis_password.get_secret_value()}"
            f"@{self.redis_host}:{self.redis_port}/1"
        )

    minio_endpoint: str = "localhost:9010"
    minio_public_endpoint: str = "http://localhost:9010"
    minio_root_user: str = "minio"
    minio_root_password: SecretStr = SecretStr("minio-secret-2026")
    minio_bucket_contracts: str = "contractforge-files"

    ollama_base_url: str = "http://localhost:11435"
    ollama_chat_model: str = "qwen2.5:14b"
    ollama_embed_model: str = "nomic-embed-text"

    paseto_secret_key: SecretStr = SecretStr("replace-with-32-byte-base64-secret-key")
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 14

    otel_exporter_otlp_endpoint: str = "http://localhost:4318"
    otel_service_name: str = "contractforge-api"

    langfuse_host: str = "http://localhost:3003"
    langfuse_public_key: str = "public-key"
    langfuse_secret_key: SecretStr = SecretStr("secret-key")

    enable_log_masking: bool = True
    cors_allow_origins: str = "http://localhost:3002,http://localhost:8100"
    ai_review_timeout_seconds: int = 90
    hybrid_search_enabled: bool = True
    semantic_search_top_k: int = 8
    semantic_search_min_score: float = 0.60
    renewal_alert_days_before: int = 30
    workflow_sla_warning_minutes: int = 60

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v: str | list[str]) -> str:
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton — call freely, constructed once."""
    return Settings()
