"""M7 Slice 3C: deterministic fake AI client for the Golden A browser E2E backend.

Reuses the exact behavioral contract already proven by the backend Golden
Journey test's `_CitationAwareFakeOpenAIClient`
(tests/test_m7_slice1_upload_truth_bridge.py): it never invents a response,
it reads the REAL Decision Context the real AIService.chat() call just
built via the existing, already-shipped DECISION_CONTEXT_DEBUG snapshot
mechanism (app.services.decision_debug), and only then picks a real,
already-resolved T# citation out of that real reference catalog.

Adaptation for a live browser E2E process (vs. an in-process pytest test):
the backend test knows the exact uploaded file_id ahead of time because it
controls the whole flow in one function. This process does not - the
browser uploads through the real UI on its own schedule. So instead of
matching by file_id, this fake matches by hall_number: the real truth item
Operational Truth Context produces never carries the free-text hall_label
through (confirmed by inspecting a real snapshot via the existing GET
/ai/debug/decision-context endpoint) - only `entity_reference`, the hall
NUMBER, survives onto the item. scripts/e2e_golden_fixture.py writes a
fixed, deterministic hall_number (GOLDEN_HALL_NUMBER) for exactly this
reason. Since NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED is set to "false" for
this whole E2E backend process (M7 Slice 3A's own isolation flag), no
static pilot evidence can ever be in the reference catalog to begin with,
so a usable ref whose item's entity_reference matches GOLDEN_HALL_NUMBER
can only have come from this run's real uploaded file.

This module is test-support code, imported only by
scripts/e2e_backend_app.py (never by app/main.py or any production path).
"""
from __future__ import annotations

import json
from typing import Any
from types import SimpleNamespace


def _raw_decision(reasoning_assessment: dict[str, Any]) -> dict[str, Any]:
    """Same structurally-required shape the real /ai/chat parser expects.

    Matches tests/test_m7_slice1_upload_truth_bridge.py's `_raw_decision`
    exactly (duplicated, not imported, for the same reason
    scripts/e2e_golden_fixture.py duplicates its fixture helper).
    """
    return {
        "context_lock": {"missing_fields": [], "is_locked": False, "confidence": 0, "why": ""},
        "problem_classification": {"type": "", "confidence": 0, "why": ""},
        "truth_validation": {"contradictions": [], "trust_score": 0, "notes": ""},
        "root_cause_engine": {"root_causes": [], "why_chain": []},
        "solution_generator": {"urgent_30_days": [], "mid_term_90_days": [], "long_term_6_12_months": []},
        "execution_engine": {
            "priority_order": [], "quick_wins": [], "high_impact_moves": [], "dependencies": [], "risks": []
        },
        "reasoning_assessment": reasoning_assessment,
    }


class E2EGoldenFakeChatCompletions:
    """Deterministic stand-in for AsyncOpenAI's `.chat.completions`.

    Only the LLM completion boundary is replaced; every other real code
    path (route, service, repository, KAE, Truth assembly, reasoning
    reference catalog, provenance validators) still runs for real.
    """

    def __init__(self, *, hall_number: str) -> None:
        self.hall_number = hall_number
        self.messages: list[Any] = []
        self.call_count = 0
        self.reasoning_call_count = 0

    async def create(self, **kwargs: Any) -> SimpleNamespace:
        self.call_count += 1
        messages = kwargs["messages"]
        self.messages.append(messages)

        # AIService._extract_and_upsert_facts issues its own, separate LLM
        # call after the main reasoning response is accepted (see
        # app/services/openai_client.py) - give it a harmless no-op
        # response so it never blocks the reasoning call under test.
        from app.services.openai_client import FACT_EXTRACTOR_SYSTEM

        is_fact_extraction_call = any(
            message.get("role") == "system" and message.get("content") == FACT_EXTRACTOR_SYSTEM
            for message in messages
        )
        if is_fact_extraction_call:
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"facts": []})))]
            )

        self.reasoning_call_count += 1
        chosen_ref = self._resolve_hall_citation()

        reasoning_assessment = {
            "reasoning_state": "aligned",
            "operational_assessment": "Golden journey hall readings observed from the uploaded report.",
            "company_brain_alignment": "n/a",
            "tensions": [],
            "evidence_gaps": [],
            "risk_assessment": "n/a",
            "confidence": 65,
            "recommendation_basis": {
                "evidence_basis": [chosen_ref], "company_basis": [], "missing_evidence": [],
            },
        }
        ai_json = json.dumps({
            # M7 Slice 3C: Golden A asks through company-wide chat (see
            # golden-a.spec.ts's Step 5 comment for why), which real
            # openai_client.py._operational_response_missing_elements
            # enforces mandatory CEO-mode keyword signals for. This text
            # deliberately includes one signal from each of the four
            # required categories (bottleneck/capacity, a cause/effect
            # word, an affected-department name, and an operational-impact
            # word) so the real enforcement accepts it on its own terms -
            # it is not bypassed or weakened.
            "executive_summary": (
                "Executive Summary\n- Golden Journey Hall shows a production capacity bottleneck "
                "in the Dairtna Poultry hall, which drives reduced delivery reliability and "
                "creates downstream operational impact for the production and operations "
                "departments.\n\nRecommended Actions\n- Monitor hall performance and "
                "inventory levels.\n\nPriority Level\n- Medium."
            ),
            "raw_decision": _raw_decision(reasoning_assessment),
        })
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=ai_json))])

    def _resolve_hall_citation(self) -> str:
        """Read the just-built real Decision Context and pick the usable
        T# whose truth item's entity_reference is GOLDEN_HALL_NUMBER.

        Reads app.services.decision_debug's snapshot deque directly rather
        than through list_decision_debug_snapshots(company_id=...): this
        process serves exactly one Playwright browser session at a time
        (playwright.config.ts sets fullyParallel: false), so "most recently
        captured snapshot" is unambiguous, and no company_id is known to
        this fake ahead of the real chat call that produces it.
        """
        from app.services import decision_debug as decision_debug_module

        assert decision_debug_module.decision_debug_enabled(), (
            "DECISION_CONTEXT_DEBUG must be enabled for the Golden A E2E backend"
        )
        assert decision_debug_module._SNAPSHOTS, (
            "no DECISION_CONTEXT_DEBUG snapshot was captured for this chat call"
        )
        decision_context = decision_debug_module._SNAPSHOTS[-1]["decision_context"]
        truth_items = decision_context.get("operational_truth_context") or []
        truth_refs = decision_context["reasoning_reference_catalog"]["truth"]

        usable_refs = [
            ref for index, ref in enumerate(truth_refs, start=1)
            if truth_refs[ref]["is_usable_evidence"]
            and str(truth_items[index - 1].get("entity_reference")) == self.hall_number
        ]
        assert usable_refs, (
            f"the real chat-generated reference catalog has no usable evidence for "
            f"entity_reference {self.hall_number!r} - the just-uploaded Golden A file did not "
            f"reach Operational Truth Context"
        )
        return usable_refs[0]


class E2EGoldenFakeOpenAIClient:
    """Drop-in replacement for AsyncOpenAI at the exact seam the backend
    Golden Journey test uses: `ai_engine.client = <this>`."""

    def __init__(self, *, hall_number: str) -> None:
        self.chat_completions = E2EGoldenFakeChatCompletions(hall_number=hall_number)
        self.chat = SimpleNamespace(completions=self.chat_completions)
