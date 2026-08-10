import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str) -> list[str]:
    return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DEMO_OWNER_PASSWORD: str = os.getenv("DEMO_OWNER_PASSWORD", "")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    APP_TITLE: str = "NAWA API"
    MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    RAG_RETRIEVAL_MODE: str = os.getenv("RAG_RETRIEVAL_MODE", "semantic")
    DECISION_CONTEXT_DEBUG: bool = _env_bool("DECISION_CONTEXT_DEBUG")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")
    # Authoritative company id for the Jannat/Dairtna pilot tenant. Gates
    # pilot-specific static sources (M4 Truth Context, M5 Company Brain
    # documents) - see app/services/operational_truth_context.is_jannat_tenant.
    # Absent/malformed/mismatched all fail closed; there is no fallback.
    JANNAT_COMPANY_ID: str = os.getenv("JANNAT_COMPANY_ID", "")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() in {"production", "staging"}

    @property
    def cors_origins(self) -> list[str]:
        configured_origins = _split_csv(self.CORS_ORIGINS)
        if configured_origins:
            return configured_origins
        return _split_csv(self.FRONTEND_URL)

    def validate_database_url(self) -> None:
        if not self.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is required")

        parsed = urlparse(self.DATABASE_URL)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise RuntimeError(
                "DATABASE_URL must use a PostgreSQL URL starting with postgres:// or postgresql://"
            )
        if not parsed.hostname or not parsed.path.strip("/"):
            raise RuntimeError("DATABASE_URL must include a host and database name")

    def validate_required_for_startup(self) -> None:
        missing = [
            name
            for name, value in {
                "DATABASE_URL": self.DATABASE_URL,
                "OPENAI_API_KEY": self.OPENAI_API_KEY,
                "DEMO_OWNER_PASSWORD": self.DEMO_OWNER_PASSWORD,
                "FRONTEND_URL": self.FRONTEND_URL,
                "ENVIRONMENT": self.ENVIRONMENT,
                "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
            }.items()
            if not value.strip()
        ]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required production environment variables: {joined}")

        self.validate_database_url()
        if not self.cors_origins:
            raise RuntimeError("FRONTEND_URL or CORS_ORIGINS must define at least one CORS origin")


settings = Settings()
