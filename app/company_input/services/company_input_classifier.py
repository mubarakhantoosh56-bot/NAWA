"""Deterministic Company Input classification service.

This service only inspects CompanyInput metadata. It does not reason, read
business rules, generate operational artifacts, call engines, or persist data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.company_input.models import CompanyInput


CONFIRMATION_THRESHOLD = 0.70

EXCEL_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}
PDF_MIME_TYPES = {"application/pdf"}
TEXT_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
}


@dataclass(frozen=True)
class CompanyInputClassification:
    """Metadata-only classification result for NCO routing hints."""

    input_category: str
    media_type: str
    source_type: str
    probable_department: str | None
    probable_pipeline: str
    confidence: float
    requires_human_confirmation: bool
    routing_hints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CompanyInputClassifier:
    """Classify CompanyInput metadata with deterministic MVP rules."""

    def classify(self, company_input: CompanyInput) -> CompanyInputClassification:
        media_type = _detect_media_type(company_input)
        source_type = _detect_source_type(company_input)
        text = _metadata_text(company_input)

        if media_type == "excel":
            return self._classify_excel(company_input, source_type, text)
        if media_type == "pdf":
            return self._classify_pdf(company_input, source_type, text)
        if media_type == "text":
            return self._classify_text(company_input, source_type, text)
        if source_type == "operational_update":
            return _classification(
                input_category="operational",
                media_type=media_type,
                source_type=source_type,
                probable_department=_detect_department(text),
                probable_pipeline="operational_update_intake",
                confidence=0.82,
                routing_hints={"nco_route": "operational_update"},
            )
        return _classification(
            input_category="unknown",
            media_type=media_type,
            source_type=source_type,
            probable_department=_detect_department(text),
            probable_pipeline="needs_classification",
            confidence=0.20,
            routing_hints={"nco_route": "request_classification"},
        )

    def _classify_excel(
        self,
        company_input: CompanyInput,
        source_type: str,
        text: str,
    ) -> CompanyInputClassification:
        department = _detect_department(text)
        if _has_any(text, ("poultry", "dairtna", "deirtna", "ديرتنا")):
            confidence = 0.90 if _has_any(text, ("daily", "report", "technical", "تقرير", "يومي")) else 0.78
            return _classification(
                input_category="operational",
                media_type="excel",
                source_type=source_type,
                probable_department=department or "dairtna_poultry",
                probable_pipeline="excel_poultry_report",
                confidence=confidence,
                routing_hints={
                    "nco_route": "kae_oie_oce",
                    "input_family": "poultry_report",
                },
            )
        if _has_any(text, ("finance", "budget", "invoice", "cost", "accounting")):
            return _classification(
                input_category="financial",
                media_type="excel",
                source_type=source_type,
                probable_department=department or "finance",
                probable_pipeline="financial_spreadsheet_intake",
                confidence=0.76,
                routing_hints={"nco_route": "kae_financial_intake"},
            )
        return _classification(
            input_category="operational",
            media_type="excel",
            source_type=source_type,
            probable_department=department,
            probable_pipeline="spreadsheet_intake",
            confidence=0.62,
            routing_hints={"nco_route": "kae_classification_needed"},
        )

    def _classify_pdf(
        self,
        company_input: CompanyInput,
        source_type: str,
        text: str,
    ) -> CompanyInputClassification:
        department = _detect_department(text)
        if _has_any(text, ("finance", "budget", "invoice", "cost", "accounting")):
            return _classification(
                input_category="financial",
                media_type="pdf",
                source_type=source_type,
                probable_department=department or "finance",
                probable_pipeline="financial_document_intake",
                confidence=0.80,
                routing_hints={"nco_route": "kae_financial_intake"},
            )
        if _has_any(text, ("policy", "sop", "procedure", "manual", "training")):
            return _classification(
                input_category="knowledge",
                media_type="pdf",
                source_type=source_type,
                probable_department=department,
                probable_pipeline="knowledge_document_intake",
                confidence=0.82,
                routing_hints={"nco_route": "kae_knowledge"},
            )
        return _classification(
            input_category="knowledge",
            media_type="pdf",
            source_type=source_type,
            probable_department=department,
            probable_pipeline="document_intake",
            confidence=0.64,
            routing_hints={"nco_route": "kae_classification_needed"},
        )

    def _classify_text(
        self,
        company_input: CompanyInput,
        source_type: str,
        text: str,
    ) -> CompanyInputClassification:
        department = _detect_department(text)
        if source_type == "operational_update" or _has_any(
            text,
            ("daily_update", "issue", "alert", "mortality", "feed", "production"),
        ):
            return _classification(
                input_category="operational",
                media_type="text",
                source_type=source_type,
                probable_department=department,
                probable_pipeline="operational_update_intake",
                confidence=0.84,
                routing_hints={"nco_route": "operational_update"},
            )
        return _classification(
            input_category="knowledge",
            media_type="text",
            source_type=source_type,
            probable_department=department,
            probable_pipeline="text_intake",
            confidence=0.58,
            routing_hints={"nco_route": "kae_classification_needed"},
        )


def classify_company_input(
    company_input: CompanyInput,
) -> CompanyInputClassification:
    """Convenience wrapper for deterministic CompanyInput classification."""
    return CompanyInputClassifier().classify(company_input)


def _classification(
    *,
    input_category: str,
    media_type: str,
    source_type: str,
    probable_department: str | None,
    probable_pipeline: str,
    confidence: float,
    routing_hints: dict[str, Any],
) -> CompanyInputClassification:
    return CompanyInputClassification(
        input_category=input_category,
        media_type=media_type,
        source_type=source_type,
        probable_department=probable_department,
        probable_pipeline=probable_pipeline,
        confidence=confidence,
        requires_human_confirmation=confidence < CONFIRMATION_THRESHOLD,
        routing_hints=routing_hints,
    )


def _detect_media_type(company_input: CompanyInput) -> str:
    mime_type = (company_input.mime_type or "").strip().lower()
    extension = Path(company_input.original_filename or "").suffix.lower()
    declared = (company_input.media_type or "").strip().lower()

    if mime_type in EXCEL_MIME_TYPES or extension in {".xlsx", ".xls"}:
        return "excel"
    if mime_type in PDF_MIME_TYPES or extension == ".pdf":
        return "pdf"
    if mime_type in TEXT_MIME_TYPES or extension in {".txt", ".md", ".csv", ".json"}:
        return "text"
    if declared in {"file", "text", "voice", "image", "video", "machine"}:
        return declared
    return "unknown"


def _detect_source_type(company_input: CompanyInput) -> str:
    source_type = (company_input.source_type or "").strip().lower()
    source = (company_input.source or "").strip().lower()

    if "operational" in source_type and "update" in source_type:
        return "operational_update"
    if "excel" in source_type:
        return "excel_upload"
    if "pdf" in source_type:
        return "pdf_upload"
    if source == "upload":
        return "upload"
    return source_type or source or "unknown"


def _detect_department(text: str) -> str | None:
    if _has_any(text, ("dairtna", "deirtna", "poultry", "ديرتنا", "دواجن")):
        return "dairtna_poultry"
    if _has_any(text, ("finance", "budget", "invoice", "accounting", "cash")):
        return "finance"
    if _has_any(text, ("hr", "human resources", "attendance", "staffing")):
        return "hr"
    if _has_any(text, ("warehouse", "inventory", "stock")):
        return "warehouse"
    if _has_any(text, ("sales", "customer", "distribution")):
        return "sales"
    return None


def _metadata_text(company_input: CompanyInput) -> str:
    parts: list[str] = [
        company_input.source,
        company_input.source_type,
        company_input.media_type,
        company_input.mime_type or "",
        company_input.original_filename or "",
        company_input.raw_storage_path or "",
        company_input.language or "",
    ]
    for key, value in company_input.metadata.items():
        if isinstance(value, (str, int, float, bool)):
            parts.append(f"{key} {value}")
    return " ".join(parts).strip().lower().replace("_", " ").replace("-", " ")


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle.lower() in text for needle in needles)
