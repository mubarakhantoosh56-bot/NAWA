"""Future operational-system integration provider abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class IntegrationProvider(Protocol):
    key: str
    name: str
    status: str
    ingestion_modes: list[str]
    description: str

    async def ingest(self, payload: dict[str, object]) -> dict[str, object]:
        """Ingest operational data from a provider payload."""


@dataclass(frozen=True)
class PlaceholderProvider:
    key: str
    name: str
    status: str = "planned"
    ingestion_modes: list[str] | None = None
    description: str = "Provider placeholder for future operational data ingestion."

    async def ingest(self, payload: dict[str, object]) -> dict[str, object]:
        return {
            "provider": self.key,
            "status": "accepted_placeholder",
            "records_received": len(payload.get("records", [])) if isinstance(payload.get("records"), list) else 0,
            "message": "MVP placeholder only; no external ERP integration has been executed.",
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "status": self.status,
            "ingestion_modes": self.ingestion_modes or ["api", "csv", "webhook"],
            "description": self.description,
        }


class ProviderRegistry:
    """Registry for current and future ERP/operational providers."""

    def __init__(self) -> None:
        self._providers = {
            provider.key: provider
            for provider in [
                PlaceholderProvider("sap", "SAP"),
                PlaceholderProvider("odoo", "Odoo"),
                PlaceholderProvider("erpnext", "ERPNext"),
                PlaceholderProvider("zoho", "Zoho"),
                PlaceholderProvider("oracle", "Oracle"),
            ]
        }

    def list_providers(self) -> list[dict[str, object]]:
        return [provider.as_dict() for provider in self._providers.values()]

    def get_provider(self, key: str) -> PlaceholderProvider | None:
        return self._providers.get(key.strip().lower())
