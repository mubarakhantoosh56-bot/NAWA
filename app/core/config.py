from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path
import os

# نطلع من app/core → app → project root
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)
import os
print("RAW ENV KEYS:", list(os.environ.keys()))
print("BASE_DIR =", BASE_DIR)
print("ENV_PATH =", ENV_PATH)
print("DATABASE_URL FROM ENV =", os.getenv("DATABASE_URL"))

@dataclass(frozen=True)
class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    APP_TITLE: str = "AIMX API"
    MODEL: str = "gpt-4o-mini"

settings = Settings()