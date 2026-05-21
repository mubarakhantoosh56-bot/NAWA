import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.company_profile import router as company_profile_router
from app.api.decision_debug import router as decision_debug_router
from app.api.departments import router as departments_router
from app.api.files import router as files_router
from app.api.health import router as health_router
from app.api.integrations import router as integrations_router
from app.api.operational_inputs import router as operational_inputs_router
from app.core.config import settings


logger = logging.getLogger("nawa.startup")


def configure_logging() -> None:
    level = logging.INFO if settings.is_production else logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    try:
        if settings.is_production:
            settings.validate_required_for_startup()
        elif settings.DATABASE_URL:
            settings.validate_database_url()

        logger.info(
            "startup_configured environment=%s cors_origins=%s",
            settings.ENVIRONMENT,
            ",".join(settings.cors_origins),
        )
        yield
    except Exception:
        logger.exception("startup_failed")
        raise
    finally:
        pool = getattr(app.state, "auth_db_pool", None)
        if pool is not None:
            await pool.close()
            app.state.auth_db_pool = None
            logger.info("database_pool_closed")


app = FastAPI(title=settings.APP_TITLE, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router, prefix="/ai")
app.include_router(decision_debug_router)
app.include_router(company_profile_router)
app.include_router(departments_router)
app.include_router(files_router)
app.include_router(operational_inputs_router)
app.include_router(integrations_router)
app.include_router(health_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "NAWA is alive"}
