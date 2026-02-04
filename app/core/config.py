from dotenv import load_dotenv
from dataclasses import dataclass
import os

load_dotenv()

@dataclass(frozen=True)
class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    APP_TITLE: str = "AIMX API"
    MODEL: str = "gpt-4o-mini"

settings = Settings()