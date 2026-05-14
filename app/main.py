from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.departments import router as departments_router
from app.api.files import router as files_router
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
app.include_router(auth_router)
app.include_router(chat_router, prefix="/ai")
app.include_router(departments_router)
app.include_router(files_router)
app.include_router(health_router)


@app.on_event("shutdown")
async def close_auth_pool() -> None:
    """Close the auth database pool if it was initialized."""
    pool = getattr(app.state, "auth_db_pool", None)
    if pool is not None:
        await pool.close()
        app.state.auth_db_pool = None


@app.get("/")
def root():
    return {"status": "AIMX is alive"}
