import os
import json
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# TODO(SECURITY-SECRETS-MANAGER): In production environments, replace direct .env / os.environ
# configuration loading with a dedicated secrets manager provider (e.g. AWS Secrets Manager,
# HashiCorp Vault, or Google Secret Manager). Secrets should be fetched at application startup
# or rotated dynamically via IAM role authentication rather than baked into runtime environment variables.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ENVIRONMENT: str = "production"
    ENABLE_DEMO_SUPERADMIN: bool = False
    DEMO_SUPERADMIN_EMAIL: str | None = None
    DEMO_SUPERADMIN_PASSWORD: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENABLE_MFA: bool = False
    CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    ATTENDANCE_CORRECTION_WINDOW_HOURS: int = 24
    MARKS_CORRECTION_WINDOW_HOURS: int = 72
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_USE_TLS: bool = True

    @property
    def demo_superadmin_active(self) -> bool:
        return self.ENABLE_DEMO_SUPERADMIN and self.ENVIRONMENT.lower() in {
            "development",
            "local",
        }

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            normalized = value.strip()
            if normalized.startswith("["):
                value = json.loads(normalized)
            else:
                value = normalized.split(",")
            return [origin.strip() for origin in value if origin.strip()]
        return value


settings = Settings()
