from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.core.config import settings

app = FastAPI(title=settings.APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # مؤقتاً للتجربة
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# هنا الـ prefix الوحيد
app.include_router(chat_router, prefix="/ai")
app.include_router(health_router)

@app.get("/")
def root():
    return {"status": "AIMX is alive"}
