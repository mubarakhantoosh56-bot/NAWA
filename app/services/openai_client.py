from openai import OpenAI
from app.core.config import OPENAI_API_KEY

def get_openai_client() -> OpenAI:
    # OpenAI library reads the key from env, but we verify it exists.
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing. Check your .env file.")
    return OpenAI()