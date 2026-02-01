from fastapi import FastAPI
from app.core.config import OPENAI_API_KEY, APP_TITLE
from app.api.chat import router as chat_router

app = FastAPI(title=APP_TITLE)

# include AI chat router
app.include_router(chat_router)

@app.get("/")
def root():
    return {
        "message": "أنا AIMX، مساعدك الشخصي في مشروعنا الضخم، جاهز للعمل يا CEO",
        "key_loaded": bool(OPENAI_API_KEY)
    }