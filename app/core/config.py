from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path
import os

# نطلع من app/core → app → project root
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

@dataclass(frozen=True)
class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    APP_TITLE: str = "NAWA API"
    MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    RAG_RETRIEVAL_MODE: str = os.getenv("RAG_RETRIEVAL_MODE", "semantic")

settings = Settings()
