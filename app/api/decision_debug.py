from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.services.decision_debug import decision_debug_enabled, list_decision_debug_snapshots

router = APIRouter(prefix="/ai/debug", tags=["AI Debug"])


@router.get("/decision-context")
async def get_decision_context_debug(
    session_id: str | None = None,
    auth_context: AuthContext = Depends(require_permission("ai.chat")),
) -> dict[str, object]:
    """Temporary operational reasoning inspection endpoint."""

    if not decision_debug_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision context debug mode is disabled",
        )

    snapshots = list_decision_debug_snapshots(
        company_id=auth_context.company_id,
        session_id=session_id,
    )
    return {
        "enabled": True,
        "company_id": auth_context.company_id,
        "session_id": session_id,
        "snapshots": snapshots,
    }
