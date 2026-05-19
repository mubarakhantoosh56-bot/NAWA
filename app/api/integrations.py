"""Integration architecture foundation routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.core.role_permissions import INTEGRATIONS_INGEST_PERMISSION, INTEGRATIONS_READ_PERMISSION
from app.models.response import IntegrationProviderListResponse
from app.services.integrations.providers import ProviderRegistry

router = APIRouter(prefix="/integrations", tags=["Integrations"])
registry = ProviderRegistry()


@router.get("/providers", response_model=IntegrationProviderListResponse)
async def list_integration_providers(
    _auth_context: AuthContext = Depends(require_permission(INTEGRATIONS_READ_PERMISSION)),
) -> IntegrationProviderListResponse:
    """List planned operational-system providers for the MVP architecture."""
    return IntegrationProviderListResponse.model_validate({"providers": registry.list_providers()})


@router.post("/{provider_key}/ingest")
async def ingest_provider_payload(
    provider_key: str,
    payload: dict[str, object],
    _auth_context: AuthContext = Depends(require_permission(INTEGRATIONS_INGEST_PERMISSION)),
) -> dict[str, object]:
    """Placeholder ingestion endpoint for future ERP/API connectors."""
    provider = registry.get_provider(provider_key)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration provider not found",
        )
    return await provider.ingest(payload)
