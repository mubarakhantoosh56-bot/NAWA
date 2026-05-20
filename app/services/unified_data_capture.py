"""NAWA Unified Data Capture Architecture MVP."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.repositories.unified_data_capture_repository import UnifiedDataCaptureRepository


ENTITY_TYPES = {
    "hall",
    "product",
    "sku",
    "quantity",
    "date",
    "issue",
    "kpi",
    "department",
    "division",
    "severity",
    "person",
    "customer",
    "supplier",
}

DEPARTMENT_KEYWORDS = {
    "production": ("production", "feed", "hall", "line", "إنتاج", "انتاج", "علف", "قاعة", "دجاج", "الإنتاج", "الانتاج"),
    "sales": ("sales", "customer", "order", "مبيعات", "عميل", "زبون", "طلب", "عملاء"),
    "finance": ("finance", "cash", "collections", "cost", "مالية", "تحصيل", "كلفة", "تكلفة", "نقد"),
    "marketing": ("marketing", "campaign", "تسويق", "حملة", "اعلان", "إعلان"),
    "warehouse": ("warehouse", "stock", "inventory", "silo", "مخزن", "مستودع", "سايلو", "سيايلو", "مخزون"),
    "quality": ("quality", "defect", "جودة", "فحص", "عيب"),
    "veterinary": ("doctor", "vet", "دكتور", "طبيب", "بيطري"),
    "operations": ("operations", "delivery", "distribution", "تشغيل", "توزيع", "توصيل"),
}

ISSUE_WORDS = (
    "delay",
    "delayed",
    "late",
    "mortality",
    "stopped",
    "shortage",
    "increase",
    "decrease",
    "pressure",
    "down",
    "drop",
    "risk",
    "تأخير",
    "تاخير",
    "هلاكات",
    "نفوق",
    "توقف",
    "نقص",
    "ارتفاع",
    "انخفاض",
    "ضغط",
    "نازل",
    "مشكلة",
    "خطر",
)

POSITIVE_WORDS = (
    "improved",
    "better",
    "completed",
    "done",
    "increased production",
    "waste decreased",
    "تحسن",
    "تحسّن",
    "ارتفع الإنتاج",
    "ارتفع الانتاج",
    "انخفض الهدر",
    "تم الإنجاز",
    "تم الانجاز",
    "اكتمل",
)

DATE_WORDS = {
    "today": ("today", "اليوم"),
    "yesterday": ("yesterday", "أمس", "امس", "البارحة"),
    "this_week": ("this week", "هذا الأسبوع", "هذا الاسبوع"),
}

QUANTITY_PATTERN = re.compile(
    r"(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>طن|كيلو|كغ|kg|kgs|kilogram|kilograms|ton|tons|كارتون|carton|cartons|box|boxes)",
    re.IGNORECASE,
)
HALL_PATTERN = re.compile(r"(?:hall|قاعة|القاعة)\s*(?P<hall>\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class CaptureResult:
    raw_input: dict[str, Any]
    entities: list[dict[str, Any]]
    classification: dict[str, Any]
    structured_draft: dict[str, Any]
    should_create_event: bool


class UnifiedDataCaptureService:
    """Stores raw operational input, parses it, classifies it, and drafts structure."""

    def __init__(self, db: Any) -> None:
        self.repo = UnifiedDataCaptureRepository(db)

    async def capture(
        self,
        *,
        company_id: UUID,
        created_by: UUID,
        source_type: str,
        raw_content: str,
        division_id: UUID | None = None,
        department_id: UUID | None = None,
        source_ref: str | None = None,
        file_id: UUID | None = None,
        submitted_category: str | None = None,
        submitted_priority: str | None = None,
        payload: dict[str, Any] | None = None,
        processing_status: str | None = None,
    ) -> CaptureResult:
        text = " ".join((raw_content or "").split())
        language = detect_language(text)
        raw_input = await self.repo.create_raw_input(
            company_id=company_id,
            created_by=created_by,
            source_type=source_type,
            raw_content=text or "[empty input]",
            division_id=division_id,
            department_id=department_id,
            source_ref=source_ref,
            file_id=file_id,
            processing_status=processing_status or "pending",
            language=language,
        )
        raw_input_id = raw_input["id"]
        if processing_status == "failed":
            return CaptureResult(
                raw_input=raw_input,
                entities=[],
                classification={},
                structured_draft={},
                should_create_event=False,
            )

        try:
            entities = extract_entities(text)
            classification = classify_input(
                text=text,
                entities=entities,
                submitted_category=submitted_category,
                submitted_priority=submitted_priority,
            )
            created_entities = await self.repo.create_entities(
                raw_input_id=raw_input_id,
                entities=entities,
            )
            created_classification = await self.repo.create_classification(
                raw_input_id=raw_input_id,
                classification=classification,
            )
            structured_draft = await self.repo.create_structured_record_draft(
                company_id=company_id,
                raw_input_id=raw_input_id,
                created_by=created_by,
                division_id=division_id,
                department_id=department_id,
                record_type=classification["category"],
                extracted_payload={
                    "source_type": source_type,
                    "source_ref": source_ref,
                    "file_id": str(file_id) if file_id else None,
                    "entities": entities,
                    "classification": classification,
                    "payload": payload or {},
                    "raw_summary": text[:500],
                },
            )
            await self.repo.update_raw_input_status(
                company_id=company_id,
                raw_input_id=raw_input_id,
                processing_status="parsed",
                language=language,
            )
            should_create_event = classification["operational_signal"] in {
                "risk",
                "issue",
                "positive",
                "opportunity",
            } or classification["category"] in {"issue", "kpi", "alert", "daily_update"}
            return CaptureResult(
                raw_input={**raw_input, "processing_status": "parsed", "language": language},
                entities=created_entities,
                classification=created_classification,
                structured_draft=structured_draft,
                should_create_event=should_create_event,
            )
        except Exception:
            await self.repo.update_raw_input_status(
                company_id=company_id,
                raw_input_id=raw_input_id,
                processing_status="failed",
                language=language,
            )
            raise


def detect_language(text: str) -> str | None:
    if not text:
        return None
    if re.search(r"[\u0600-\u06ff]", text):
        return "ar"
    return "en"


def extract_entities(text: str) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(entity_type: str, entity_value: str, confidence: int, metadata: dict[str, Any] | None = None) -> None:
        value = " ".join(str(entity_value or "").split())
        if not value or entity_type not in ENTITY_TYPES:
            return
        key = (entity_type, value.lower())
        if key in seen:
            return
        seen.add(key)
        entities.append(
            {
                "entity_type": entity_type,
                "entity_value": value,
                "confidence": confidence,
                "metadata": metadata or {},
            }
        )

    for match in HALL_PATTERN.finditer(text):
        add("hall", match.group("hall"), 96, {"matched_text": match.group(0)})

    for match in QUANTITY_PATTERN.finditer(text):
        add(
            "quantity",
            f"{match.group('value').replace(',', '.')} {match.group('unit')}",
            92,
            {"unit": match.group("unit"), "matched_text": match.group(0)},
        )

    lowered = text.lower()
    for normalized, words in DATE_WORDS.items():
        if any(word.lower() in lowered for word in words):
            add("date", normalized, 86)

    for word in ISSUE_WORDS:
        if word.lower() in lowered:
            add("issue", word, 78)

    for word in POSITIVE_WORDS:
        if word.lower() in lowered:
            add("kpi", word, 76, {"signal": "positive"})

    for department, words in DEPARTMENT_KEYWORDS.items():
        if any(word.lower() in lowered for word in words):
            add("department", department, 82)

    return entities


def classify_input(
    *,
    text: str,
    entities: list[dict[str, Any]],
    submitted_category: str | None = None,
    submitted_priority: str | None = None,
) -> dict[str, Any]:
    entity_types = {entity["entity_type"] for entity in entities}
    departments = [
        entity["entity_value"]
        for entity in entities
        if entity.get("entity_type") == "department"
    ]
    inferred_department = _choose_department(departments, text)
    related_departments = _related_departments(inferred_department, departments)
    has_issue = "issue" in entity_types
    has_positive = any(
        entity.get("metadata", {}).get("signal") == "positive"
        for entity in entities
    )
    has_quantity_or_kpi = bool({"quantity", "kpi"} & entity_types)

    if has_issue:
        category = "issue"
        signal = "risk" if _contains_risk_word(text) else "issue"
    elif has_positive:
        category = "kpi" if has_quantity_or_kpi else "daily_update"
        signal = "positive"
    elif has_quantity_or_kpi:
        category = "kpi"
        signal = "neutral"
    else:
        category = submitted_category or "daily_update"
        signal = "neutral"

    priority = _priority_from_signal(signal, submitted_priority, text)
    confidence = 55 + min(35, len(entities) * 5)
    if submitted_category and submitted_category == category:
        confidence += 5
    return {
        "inferred_department": inferred_department,
        "inferred_division": None,
        "category": category,
        "priority": priority,
        "severity": priority,
        "related_departments": related_departments,
        "operational_signal": signal,
        "confidence": min(confidence, 95),
        "metadata": {
            "submitted_category": submitted_category,
            "submitted_priority": submitted_priority,
            "entity_counts": _entity_counts(entities),
        },
    }


def _choose_department(departments: list[str], text: str) -> str | None:
    lowered = text.lower()
    if "production" in departments:
        return "production"
    if "warehouse" in departments and any(word in lowered for word in ("علف", "feed", "الإنتاج", "الانتاج", "production")):
        return "production"
    return departments[0] if departments else None


def _related_departments(inferred_department: str | None, departments: list[str]) -> list[str]:
    relationships = {
        "production": ["warehouse", "operations", "sales", "finance", "quality", "veterinary"],
        "warehouse": ["production", "sales", "operations", "finance"],
        "sales": ["warehouse", "production", "operations", "finance"],
        "finance": ["sales", "production", "warehouse", "operations"],
        "marketing": ["sales", "production", "warehouse", "finance"],
        "quality": ["production", "warehouse", "operations"],
        "veterinary": ["production", "quality"],
    }
    values = list(dict.fromkeys([item for item in departments if item != inferred_department]))
    values.extend(relationships.get(inferred_department or "", []))
    return list(dict.fromkeys(values))[:6]


def _priority_from_signal(signal: str, submitted_priority: str | None, text: str) -> str:
    submitted = (submitted_priority or "").strip().lower()
    if submitted in {"high", "critical"}:
        return submitted
    lowered = text.lower()
    if any(word in lowered for word in ("critical", "خطر", "توقف", "stopped", "mortality", "هلاكات", "نفوق")):
        return "high"
    if signal in {"risk", "issue"}:
        return submitted if submitted in {"watch", "high", "critical"} else "watch"
    if signal == "positive":
        return submitted if submitted in {"low", "normal", "watch"} else "normal"
    return submitted if submitted in {"low", "normal", "watch", "high", "critical"} else "normal"


def _contains_risk_word(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in ("risk", "ضغط", "توقف", "نقص", "هلاكات", "نازل", "down", "shortage"))


def _entity_counts(entities: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entity in entities:
        entity_type = str(entity.get("entity_type") or "")
        counts[entity_type] = counts.get(entity_type, 0) + 1
    return counts
