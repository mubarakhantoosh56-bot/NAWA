"""Analyzes extracted file text and proposes draft operational events via OpenAI.

Design constraints:
- analyze_and_store() is fire-and-forget safe: it never raises.
- Does NOT store extracted text. Only short evidence_quote fragments.
- Does NOT write to operational_events. Drafts only.
- Confidence < DRAFT_CONFIDENCE_THRESHOLD sets needs_clarification=True.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI

from app.core.config import settings
from app.repositories.operational_event_draft_repository import OperationalEventDraftRepository

logger = logging.getLogger(__name__)

DRAFT_CONFIDENCE_THRESHOLD = 40
_MAX_TEXT_CHARS = 6000
_MAX_PROPOSALS = 5

_VALID_CATEGORIES = frozenset(
    {"daily_update", "kpi", "issue", "decision", "report", "alert", "note"}
)
_VALID_PRIORITIES = frozenset({"low", "normal", "watch", "high", "critical"})

_SYSTEM_PROMPT = """\
You are an operational intelligence analyst reading a document uploaded to a company's operational system.

Your task: identify concrete operational events described in this document that are worth recording in the company's operational timeline.

An operational event is a real occurrence: a mortality incident, a feed or water problem, a veterinary intervention, a production milestone, a delivery delay, a KPI reading, or a daily operational update.

Rules:
- Do NOT speculate. Only report events clearly stated or directly implied by the document.
- Do NOT summarize the whole document as one event. Extract individual distinct events.
- Maximum 5 events. If more exist, return the 5 most operationally significant.
- Return {"events": []} if the document contains no clear operational events.

For each event return exactly these fields:
  proposed_title    (string, max 100 chars): short factual label
  proposed_category (string): one of daily_update | kpi | issue | decision | report | alert | note
  proposed_priority (string): one of low | normal | watch | high | critical
  proposed_summary  (string, max 300 chars): what happened, stated factually
  evidence_quote    (string, max 200 chars): the exact passage from the document supporting this event
  confidence        (integer 0-100):
                      80-100 = explicitly stated in document
                      50-79  = clearly implied
                      20-49  = uncertain, needs human verification
                      0-19   = speculative

Return a JSON object: {"events": [...]}
"""


class FileOperationalAnalyzer:
    """Proposes operational event drafts from file text. Safe to use as a background task."""

    def __init__(self, db: Any, openai_api_key: str) -> None:
        self.draft_repo = OperationalEventDraftRepository(db)
        self.client = AsyncOpenAI(api_key=openai_api_key)

    async def analyze_and_store(
        self,
        *,
        company_id: UUID,
        file_id: UUID,
        department_id: UUID | None,
        created_by_user_id: UUID,
        extracted_text: str,
        filename: str,
    ) -> None:
        """Analyze text and write draft proposals. Catches all exceptions — never raises."""
        try:
            text_sample = (extracted_text or "").strip()
            if not text_sample:
                logger.info(
                    "file_analyzer_skipped_empty",
                    extra={"company_id": str(company_id), "file_id": str(file_id)},
                )
                return

            raw = await self._call_openai(text_sample[:_MAX_TEXT_CHARS], filename)
            proposals = self._parse_proposals(raw)
            if not proposals:
                logger.info(
                    "file_analyzer_no_proposals",
                    extra={"company_id": str(company_id), "file_id": str(file_id)},
                )
                return

            drafts = await self.draft_repo.create_drafts(
                company_id=company_id,
                file_id=file_id,
                department_id=department_id,
                created_by_user_id=created_by_user_id,
                proposals=proposals,
            )
            logger.info(
                "file_analyzer_drafts_created",
                extra={
                    "company_id": str(company_id),
                    "file_id": str(file_id),
                    "draft_count": len(drafts),
                },
            )
        except Exception:
            logger.warning(
                "file_analyzer_failed",
                extra={"company_id": str(company_id), "file_id": str(file_id)},
                exc_info=True,
            )

    async def _call_openai(self, text_sample: str, filename: str) -> list[Any]:
        user_message = f"Document: {filename}\n\nContent:\n\n{text_sample}"
        try:
            response = await self.client.chat.completions.create(
                model=settings.MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            raw = (response.choices[0].message.content or "").strip()
            parsed = json.loads(raw)
            events = parsed.get("events", [])
            return events if isinstance(events, list) else []
        except json.JSONDecodeError as exc:
            logger.warning(
                "file_analyzer_json_error",
                extra={"filename": filename, "error": str(exc)},
            )
            return []
        except Exception as exc:
            logger.warning(
                "file_analyzer_openai_error",
                extra={"filename": filename, "error_type": type(exc).__name__},
            )
            return []

    def _parse_proposals(self, raw: list[Any]) -> list[dict[str, Any]]:
        """Validate and clean raw event dicts. Skips incomplete or malformed entries."""
        proposals: list[dict[str, Any]] = []
        for item in raw[:_MAX_PROPOSALS]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("proposed_title") or "").strip()
            summary = str(item.get("proposed_summary") or "").strip()
            if not title or not summary:
                logger.debug("file_analyzer_skipped_incomplete_proposal")
                continue

            try:
                confidence = max(0, min(100, int(item.get("confidence") or 0)))
            except (TypeError, ValueError):
                confidence = 0

            needs_clarification = confidence < DRAFT_CONFIDENCE_THRESHOLD
            clarification_hint: str | None = None
            if needs_clarification:
                quote_preview = str(item.get("evidence_quote") or "").strip()[:80]
                clarification_hint = (
                    f"Low confidence ({confidence}/100). "
                    "Please verify against the source document"
                    + (f': "{quote_preview}"' if quote_preview else ".")
                )

            category = str(item.get("proposed_category") or "").strip().lower()
            if category not in _VALID_CATEGORIES:
                category = "daily_update"

            priority = str(item.get("proposed_priority") or "").strip().lower()
            if priority not in _VALID_PRIORITIES:
                priority = "normal"

            proposals.append(
                {
                    "proposed_title": title[:240],
                    "proposed_category": category,
                    "proposed_priority": priority,
                    "proposed_summary": summary[:2000],
                    "evidence_quote": str(item.get("evidence_quote") or "").strip()[:400] or None,
                    "confidence": confidence,
                    "needs_clarification": needs_clarification,
                    "clarification_hint": clarification_hint,
                }
            )
        return proposals
