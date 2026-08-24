"""OME internal typed structures (M8 Slice 2).

A new file rather than a Slice 1 model change, per Founder direction
(prefer a new file over modifying app/ome/models/* for one helper type).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.ome.errors import InvalidMemoryInput

# Only "file" is currently a provable, citable internal source type -
# confirmed directly against app/services/operational_truth_context.py's
# source_file_id/source_company_id/source_department_id fields (the only
# stable internal id shape a real reasoning_reference_catalog entry
# carries - app/services/decision_context.py). Do not add another type
# here without first proving it exists as a stable, citable internal id in
# that same reference catalog - never speculatively.
EVIDENCE_REF_TYPES: frozenset[str] = frozenset({"file"})

EvidenceRefType = Literal["file"]


@dataclass(frozen=True)
class EvidenceRef:
    """One server-resolved evidence reference for a reasoning receipt.

    Constructed only from server-held state (the real reasoning reference
    catalog) - never from a client-supplied value. See
    ReasoningReceiptService.create_receipt for the server-side
    company-scoped verification each ref undergoes before persistence.
    """

    type: EvidenceRefType
    id: UUID

    def __post_init__(self) -> None:
        if self.type not in EVIDENCE_REF_TYPES:
            raise InvalidMemoryInput(f"Unsupported EvidenceRef type: {self.type!r}")

    def to_dict(self) -> dict[str, str]:
        """JSON-friendly representation for JSONB persistence."""
        return {"type": self.type, "id": str(self.id)}

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "EvidenceRef":
        """Parse one evidence ref from a plain dict (e.g. a JSONB row
        value already decoded to Python, or a caller-constructed literal).
        Fails closed on any malformed or unsupported entry - never guesses."""
        if not isinstance(value, dict):
            raise InvalidMemoryInput(f"EvidenceRef must be an object, got {type(value).__name__}")
        raw_type = value.get("type")
        if raw_type not in EVIDENCE_REF_TYPES:
            raise InvalidMemoryInput(f"Unsupported EvidenceRef type: {raw_type!r}")
        raw_id = value.get("id")
        if not raw_id:
            raise InvalidMemoryInput("EvidenceRef.id is required")
        try:
            parsed_id = raw_id if isinstance(raw_id, UUID) else UUID(str(raw_id))
        except (ValueError, AttributeError, TypeError) as exc:
            raise InvalidMemoryInput(f"EvidenceRef.id is not a valid UUID: {raw_id!r}") from exc
        return cls(type=raw_type, id=parsed_id)
