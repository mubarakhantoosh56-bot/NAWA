"""OME internal typed structures (M8 Slice 2).

A new file rather than a Slice 1 model change, per Founder direction
(prefer a new file over modifying app/ome/models/* for one helper type).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Literal
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

# The Truth-category discriminator for the provenance union persisted in
# ome_reasoning_receipts.evidence_refs (shared with CompanyBrainProvenanceRef,
# category="company_brain" - see below). Owned by EvidenceRef itself: every
# EvidenceRef.to_dict() always carries it, and from_dict() always requires
# it, so callers never need to inject or strip it by hand.
EVIDENCE_REF_CATEGORY: Literal["truth"] = "truth"


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
    category: Literal["truth"] = EVIDENCE_REF_CATEGORY

    def __post_init__(self) -> None:
        if self.type not in EVIDENCE_REF_TYPES:
            raise InvalidMemoryInput(f"Unsupported EvidenceRef type: {self.type!r}")
        if self.category != EVIDENCE_REF_CATEGORY:
            raise InvalidMemoryInput(f"EvidenceRef.category must be {EVIDENCE_REF_CATEGORY!r}, got {self.category!r}")

    def to_dict(self) -> dict[str, str]:
        """JSON-friendly representation for JSONB persistence - always
        carries the "truth" category discriminator, never left to the
        caller (e.g. ReasoningReceiptService) to inject."""
        return {"category": self.category, "type": self.type, "id": str(self.id)}

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "EvidenceRef":
        """Parse one evidence ref from a plain dict (e.g. a JSONB row
        value already decoded to Python, or a caller-constructed literal).
        Fails closed on any malformed or unsupported entry - never
        guesses. Requires category == "truth" exactly: there are zero
        live persisted receipts and no untagged-shape backfill concern, so
        the discriminated-union shape is enforced from day one, never
        silently accepted without it."""
        if not isinstance(value, dict):
            raise InvalidMemoryInput(f"EvidenceRef must be an object, got {type(value).__name__}")
        raw_category = value.get("category")
        if raw_category != EVIDENCE_REF_CATEGORY:
            raise InvalidMemoryInput(f"EvidenceRef.category must be {EVIDENCE_REF_CATEGORY!r}, got {raw_category!r}")
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


_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

# The Company Brain-category discriminator, mirroring EVIDENCE_REF_CATEGORY
# above (see EvidenceRef) - the other half of the discriminated provenance
# union persisted in ome_reasoning_receipts.evidence_refs.
COMPANY_BRAIN_PROVENANCE_CATEGORY: Literal["company_brain"] = "company_brain"


@dataclass(frozen=True)
class CompanyBrainProvenanceRef:
    """One server-resolved, self-contained snapshot of the exact Company
    Brain material a reasoning turn actually cited (pre-Slice-3 foundation).

    Deliberately independent of the ephemeral, request-local CB# label
    (see display_label below) and independent of the CURRENT state of the
    underlying knowledge source: content_sha256/text_snapshot are always
    computed from the exact statement text the reasoning layer was shown
    in that one request (see from_internal_source_item) - never from
    rereading a knowledge file or any later source state. This is what
    lets a receipt prove "the model saw exactly this text" even after the
    underlying Company Brain document has since changed, been renamed, or
    been deleted.

    display_label ("CB1", "CB2", ...) is preserved only as a request-local
    debug/audit convenience for matching this ref back to the reasoning
    result that cited it - it is explicitly NOT identity. source_key +
    item_key (never the label) are the durable, tenant-scoped identity.
    """

    company_id: UUID
    source_key: str
    item_key: str
    content_sha256: str
    text_snapshot: str
    display_label: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.company_id, UUID):
            raise InvalidMemoryInput("CompanyBrainProvenanceRef.company_id must be a UUID")
        if not isinstance(self.source_key, str) or not self.source_key.strip():
            raise InvalidMemoryInput("CompanyBrainProvenanceRef.source_key must be a non-blank string")
        if not isinstance(self.item_key, str) or not self.item_key.strip():
            raise InvalidMemoryInput("CompanyBrainProvenanceRef.item_key must be a non-blank string")
        if not isinstance(self.text_snapshot, str):
            raise InvalidMemoryInput("CompanyBrainProvenanceRef.text_snapshot must be a string")
        if not isinstance(self.content_sha256, str) or not _SHA256_HEX_RE.match(self.content_sha256):
            raise InvalidMemoryInput("CompanyBrainProvenanceRef.content_sha256 must be a valid SHA-256 hex digest")
        if self.display_label is not None and (
            not isinstance(self.display_label, str) or not self.display_label.strip()
        ):
            raise InvalidMemoryInput(
                "CompanyBrainProvenanceRef.display_label must be a non-blank string when present"
            )

    @classmethod
    def from_internal_source_item(
        cls,
        *,
        company_id: UUID,
        internal_source_item: dict[str, Any],
        display_label: str | None = None,
    ) -> "CompanyBrainProvenanceRef":
        """Construct from one trusted
        reasoning_reference_catalog["company_brain"][CB#]["internal_source_item"]
        snapshot (app/services/decision_context.py) - the exact item the
        reasoning layer was actually shown this turn. content_sha256 is
        always computed HERE, internally, from that exact statement text -
        callers never supply a hash directly, and this never rereads a
        knowledge file or any other source of truth.
        """
        if not isinstance(internal_source_item, dict):
            raise InvalidMemoryInput("internal_source_item must be an object")

        source_key = internal_source_item.get("source")
        if not isinstance(source_key, str) or not source_key.strip():
            raise InvalidMemoryInput("internal_source_item.source must be a non-blank string")

        item_key = internal_source_item.get("key")
        if not isinstance(item_key, str) or not item_key.strip():
            raise InvalidMemoryInput("internal_source_item.key must be a non-blank string")

        statement = internal_source_item.get("statement")
        if not isinstance(statement, str):
            raise InvalidMemoryInput("internal_source_item.statement must be a string")

        content_sha256 = hashlib.sha256(statement.encode("utf-8")).hexdigest()

        return cls(
            company_id=company_id,
            source_key=source_key,
            item_key=item_key,
            content_sha256=content_sha256,
            text_snapshot=statement,
            display_label=display_label,
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation for JSONB persistence, explicitly
        category-tagged so it can share ome_reasoning_receipts.evidence_refs
        with Truth EvidenceRef entries without ambiguity."""
        payload: dict[str, Any] = {
            "category": COMPANY_BRAIN_PROVENANCE_CATEGORY,
            "company_id": str(self.company_id),
            "source_key": self.source_key,
            "item_key": self.item_key,
            "content_sha256": self.content_sha256,
            "text_snapshot": self.text_snapshot,
        }
        if self.display_label is not None:
            payload["display_label"] = self.display_label
        return payload

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CompanyBrainProvenanceRef":
        """Parse one Company Brain provenance ref from a plain dict (e.g. a
        JSONB row value already decoded to Python). Fails closed on any
        malformed entry - never guesses. Requires
        category == "company_brain" exactly, for the same reason
        EvidenceRef.from_dict requires category == "truth": there are zero
        live persisted receipts, so the discriminated-union shape is
        enforced from day one, never silently accepted without it."""
        if not isinstance(value, dict):
            raise InvalidMemoryInput(f"CompanyBrainProvenanceRef must be an object, got {type(value).__name__}")
        raw_category = value.get("category")
        if raw_category != COMPANY_BRAIN_PROVENANCE_CATEGORY:
            raise InvalidMemoryInput(
                f"CompanyBrainProvenanceRef.category must be {COMPANY_BRAIN_PROVENANCE_CATEGORY!r}, "
                f"got {raw_category!r}"
            )
        raw_company_id = value.get("company_id")
        try:
            company_id = raw_company_id if isinstance(raw_company_id, UUID) else UUID(str(raw_company_id))
        except (ValueError, AttributeError, TypeError) as exc:
            raise InvalidMemoryInput(
                f"CompanyBrainProvenanceRef.company_id is not a valid UUID: {raw_company_id!r}"
            ) from exc
        return cls(
            company_id=company_id,
            source_key=value.get("source_key"),
            item_key=value.get("item_key"),
            content_sha256=value.get("content_sha256"),
            text_snapshot=value.get("text_snapshot"),
            display_label=value.get("display_label"),
        )


# The Organizational Memory-category discriminator (M8 Slice 4B), the third
# variant of the discriminated provenance union persisted in
# ome_reasoning_receipts.evidence_refs alongside EvidenceRef (category=
# "truth") and CompanyBrainProvenanceRef (category="company_brain").
ORGANIZATIONAL_MEMORY_PROVENANCE_CATEGORY: Literal["organizational_memory"] = "organizational_memory"


@dataclass(frozen=True)
class OrganizationalMemoryProvenanceRef:
    """One durable reference to human-authored Organizational Memory
    actually CITED by the final accepted reasoning result via a
    request-local OM# label (M8 Slice 4B).

    Founder Correction 1: this represents explicit CITED basis, never
    unverifiable hidden model influence - Organizational Memory may be
    present in a prompt without being cited, and only cited OM# labels
    ever become receipt provenance (see app/ome/provenance.py's
    build_organizational_memory_provenance_refs, the only intended way to
    construct these).

    Deliberately references only durable, already-persisted, append-only
    OME ids - no text_snapshot, no content hash, no reasoning_receipt_id,
    no situation_id, no AI response text, no company_id, no user id, no
    score, no confidence. Unlike CompanyBrainProvenanceRef (whose source
    can be edited/deleted at its origin, requiring a frozen text snapshot
    to prove exactly what was shown), DecisionMemory/OutcomeMemory rows
    are themselves already immutable/append-only persisted historical
    objects with no hard-delete path (M8 OME schema) - the id alone
    remains a durable, permanently-resolvable reference to the exact
    content cited, even after supersession.

    outcome_memory_ids carries ONLY the outcome ids actually RENDERED to
    the model for this OM# (Founder Correction 2) - if the source
    aggregate had more active outcomes than the prompt-rendering budget
    allowed, this tuple equals exactly the rendered subset, never the full
    aggregate. This is what keeps receipt provenance truthful about what
    the model actually received under this OM# label.
    """

    decision_memory_id: UUID
    outcome_memory_ids: tuple[UUID, ...]
    category: Literal["organizational_memory"] = ORGANIZATIONAL_MEMORY_PROVENANCE_CATEGORY

    def __post_init__(self) -> None:
        if not isinstance(self.decision_memory_id, UUID):
            raise InvalidMemoryInput("OrganizationalMemoryProvenanceRef.decision_memory_id must be a UUID")
        if not isinstance(self.outcome_memory_ids, tuple) or not self.outcome_memory_ids:
            raise InvalidMemoryInput(
                "OrganizationalMemoryProvenanceRef.outcome_memory_ids must be a non-empty tuple of UUIDs"
            )
        for outcome_id in self.outcome_memory_ids:
            if not isinstance(outcome_id, UUID):
                raise InvalidMemoryInput(
                    "OrganizationalMemoryProvenanceRef.outcome_memory_ids entries must all be UUIDs"
                )
        if self.category != ORGANIZATIONAL_MEMORY_PROVENANCE_CATEGORY:
            raise InvalidMemoryInput(
                f"OrganizationalMemoryProvenanceRef.category must be "
                f"{ORGANIZATIONAL_MEMORY_PROVENANCE_CATEGORY!r}, got {self.category!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation for JSONB persistence, sharing
        ome_reasoning_receipts.evidence_refs with Truth/Company Brain
        entries via the "category" discriminator."""
        return {
            "category": self.category,
            "decision_memory_id": str(self.decision_memory_id),
            "outcome_memory_ids": [str(outcome_id) for outcome_id in self.outcome_memory_ids],
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "OrganizationalMemoryProvenanceRef":
        """Parse one Organizational Memory provenance ref from a plain
        dict. Fails closed on any malformed entry - never guesses.
        Requires category == "organizational_memory" exactly, same
        discipline as EvidenceRef.from_dict/CompanyBrainProvenanceRef.from_dict."""
        if not isinstance(value, dict):
            raise InvalidMemoryInput(
                f"OrganizationalMemoryProvenanceRef must be an object, got {type(value).__name__}"
            )
        raw_category = value.get("category")
        if raw_category != ORGANIZATIONAL_MEMORY_PROVENANCE_CATEGORY:
            raise InvalidMemoryInput(
                f"OrganizationalMemoryProvenanceRef.category must be "
                f"{ORGANIZATIONAL_MEMORY_PROVENANCE_CATEGORY!r}, got {raw_category!r}"
            )
        raw_decision_id = value.get("decision_memory_id")
        try:
            decision_memory_id = (
                raw_decision_id if isinstance(raw_decision_id, UUID) else UUID(str(raw_decision_id))
            )
        except (ValueError, AttributeError, TypeError) as exc:
            raise InvalidMemoryInput(
                f"OrganizationalMemoryProvenanceRef.decision_memory_id is not a valid UUID: {raw_decision_id!r}"
            ) from exc

        raw_outcome_ids = value.get("outcome_memory_ids")
        if not isinstance(raw_outcome_ids, list) or not raw_outcome_ids:
            raise InvalidMemoryInput(
                "OrganizationalMemoryProvenanceRef.outcome_memory_ids must be a non-empty list"
            )
        outcome_ids: list[UUID] = []
        for raw_outcome_id in raw_outcome_ids:
            try:
                outcome_ids.append(
                    raw_outcome_id if isinstance(raw_outcome_id, UUID) else UUID(str(raw_outcome_id))
                )
            except (ValueError, AttributeError, TypeError) as exc:
                raise InvalidMemoryInput(
                    "OrganizationalMemoryProvenanceRef.outcome_memory_ids entry is not a valid UUID: "
                    f"{raw_outcome_id!r}"
                ) from exc

        return cls(decision_memory_id=decision_memory_id, outcome_memory_ids=tuple(outcome_ids))
