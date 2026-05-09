from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a lightweight service health response."""

    return {"status": "ok"}
