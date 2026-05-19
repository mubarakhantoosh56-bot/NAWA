"""Temporary debug snapshots for NAWA decision-context generation."""

from __future__ import annotations

import logging
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_SNAPSHOTS = 25
_SNAPSHOTS: deque[dict[str, Any]] = deque(maxlen=_MAX_SNAPSHOTS)


def decision_debug_enabled() -> bool:
    return bool(getattr(settings, "DECISION_CONTEXT_DEBUG", False))


def build_prompt_diagnostics(
    *,
    messages: list[dict[str, str]],
    decision_context_block: str,
) -> dict[str, Any]:
    """Inspect ordering and likely truncation risk before model generation."""

    contents = [message.get("content", "") for message in messages]
    final_prompt = "\n\n".join(contents)
    root_pos = final_prompt.find('"root_cause_reasoning"')
    formatting_pos = final_prompt.find("generic executive formatting")
    if formatting_pos == -1:
        formatting_pos = final_prompt.find("Response format")
    decision_context_pos = final_prompt.find("DECISION CONTEXT ENGINE")
    required_markers = [
        '"root_cause_reasoning"',
        '"detected_patterns"',
        '"operational_events"',
        '"key_kpis"',
        '"company_profile"',
        '"response_enforcement"',
    ]
    missing_markers = [marker for marker in required_markers if marker not in final_prompt]

    return {
        "message_count": len(messages),
        "final_prompt_chars": len(final_prompt),
        "decision_context_block_chars": len(decision_context_block),
        "decision_context_present": decision_context_pos >= 0,
        "root_cause_reasoning_present": root_pos >= 0,
        "root_cause_before_formatting": root_pos >= 0 and (formatting_pos == -1 or root_pos < formatting_pos),
        "response_enforcement_present": "MANDATORY OPERATIONAL RESPONSE ENFORCEMENT" in final_prompt,
        "required_context_markers_present": not missing_markers,
        "missing_context_markers": missing_markers,
        "older_generic_override_detected": _detect_generic_override(contents),
        "likely_truncated": bool(missing_markers),
    }


def start_decision_debug_snapshot(
    *,
    company_id: str,
    session_id: str,
    decision_context: dict[str, Any],
    messages: list[dict[str, str]],
    decision_context_block: str,
) -> dict[str, Any] | None:
    if not decision_debug_enabled():
        return None

    snapshot = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "company_id": company_id,
        "session_id": session_id,
        "decision_context": deepcopy(decision_context),
        "final_prompt_messages": deepcopy(messages),
        "final_prompt": "\n\n".join(message.get("content", "") for message in messages),
        "prompt_diagnostics": build_prompt_diagnostics(
            messages=messages,
            decision_context_block=decision_context_block,
        ),
        "raw_model_response": None,
        "raw_model_response_before_regeneration": None,
        "operational_regeneration": {
            "attempted": False,
            "missing_elements": [],
            "raw_response": None,
        },
    }
    _SNAPSHOTS.append(snapshot)
    logger.warning("decision_context_debug_prompt", extra={"decision_debug_snapshot": snapshot})
    return snapshot


def update_decision_debug_snapshot(snapshot: dict[str, Any] | None, **updates: Any) -> None:
    if not snapshot:
        return
    snapshot.update(updates)
    logger.warning("decision_context_debug_update", extra={"decision_debug_update": updates})


def list_decision_debug_snapshots(
    *,
    company_id: str,
    session_id: str | None = None,
) -> list[dict[str, Any]]:
    if not decision_debug_enabled():
        return []

    results: list[dict[str, Any]] = []
    for snapshot in reversed(_SNAPSHOTS):
        if snapshot.get("company_id") != company_id:
            continue
        if session_id and snapshot.get("session_id") != session_id:
            continue
        results.append(deepcopy(snapshot))
    return results


def _detect_generic_override(contents: list[str]) -> bool:
    generic_override_phrases = (
        "ignore the decision context",
        "ignore operational context",
        "use generic executive summary",
        "do not use root_cause_reasoning",
    )
    combined = "\n".join(contents).lower()
    return any(phrase in combined for phrase in generic_override_phrases)
