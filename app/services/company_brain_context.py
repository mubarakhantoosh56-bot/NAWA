"""M5: assemble the Company Brain layer for the live chat reasoning path.

Company Brain answers "what does this company believe, prefer, prioritize,
require, prohibit, or normally do?" - never "what is objectively happening
operationally right now?" (that is the Truth Layer, app/services/
operational_truth_context.py). The two are never merged: a Company Brain
item's ``type`` is always one of the eight Layer-2 categories below, never
an operational claim, and nothing here is ever tagged ``epistemic_origin``
or presented as OBSERVED/DERIVED.

Sources classified into Company Brain (Step 1 inventory - see the M5 final
report for the full "what reaches the LLM today" trace):

1. ``memory_facts`` (any tenant) - durable, AI-extracted conversational
   facts. Classified uniformly as INSTITUTIONAL_MEMORY (they are exactly
   that: accumulated institutional memory, not curated policy). Conflict
   state (ENG-CONF-001, read-only here - ``memory_facts``/
   ``memory_fact_history`` semantics are NOT modified) is surfaced, never
   silently resolved.
2. ``knowledge/dairtna/DAIRTNA_COMPANY_BRAIN.md`` and
   ``DAIRTNA_DECISION_RULES.md`` (Jannat/Dairtna pilot tenant only, same
   scope gate as M4 Slice 2's Truth Context) - previously wired into
   nothing but a presence-only boolean Evidence item inside
   PoultryContextCollector (app/oce/collectors/poultry_context_collector.py
   - untouched by this module). Their actual section content reaches the
   LLM here for the first time, deterministically classified by heading
   (never guessed - an unrecognized heading is skipped, not force-fit).
3. ``knowledge/dairtna/DAIRTNA_OPERATIONAL_SEMANTICS.md`` - deliberately
   NOT classified into any Company Brain type (Founder instruction:
   "OPERATIONAL_SEMANTICS describes what company terms mean. It is NOT
   automatically a management preference."). Only its topic headings are
   surfaced, as a distinct, separately-labeled list.

Explicitly NOT duplicated here (Step 7 - avoid duplicate prompt content):
``company_intelligence_profile`` (companies.metadata) and
``build_company_profile()`` (memory_facts folded into a fixed startup-
profile schema) already have their own dedicated, working prompt blocks
(``company_profile_block``/``company_intelligence_profile_block`` in
app/services/openai_client.py) - reused as-is, not re-surfaced here.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.operational_truth_context import is_jannat_tenant

logger = logging.getLogger(__name__)

COMPANY_BRAIN_PATH = Path("knowledge") / "dairtna" / "DAIRTNA_COMPANY_BRAIN.md"
DECISION_RULES_PATH = Path("knowledge") / "dairtna" / "DAIRTNA_DECISION_RULES.md"
OPERATIONAL_SEMANTICS_PATH = Path("knowledge") / "dairtna" / "DAIRTNA_OPERATIONAL_SEMANTICS.md"

# Authoritative real department slug (scripts/seed_jannat.py normalizes
# "Dairtna Poultry" -> "dairtna-poultry" via DepartmentService.normalize_slug
# at tenant bootstrap time - this is the same slug app/api/chat.py places,
# RBAC-verified and non-user-suppliable, into context["aimx_department"]["slug"]).
# The Dairtna static documents are pilot-safe business-unit content only:
# scope = Dairtna Poultry until a separate, explicitly authoritative
# company-wide source exists. Caesar Beverage, Shared Corporate, and an
# unresolved/company-wide (no department selected) scope are excluded by
# default - never inferred from department name/type substrings.
DAIRTNA_POULTRY_DEPARTMENT_SLUG = "dairtna-poultry"

# Deterministic heading -> Company Brain type classification for
# DAIRTNA_COMPANY_BRAIN.md (Step 3/Step 14). An unrecognized heading is
# skipped rather than guessed (Founder instruction: do not invent policy).
COMPANY_BRAIN_HEADING_TYPES: dict[str, str] = {
    "تعريف النجاح": "MANAGEMENT_STANDARD",
    "تعريف الفشل": "MANAGEMENT_STANDARD",
    "المؤشرات اليومية": "OPERATING_PRINCIPLE",
    "المؤشرات الشهرية": "OPERATING_PRINCIPLE",
    "فلسفة الجودة": "OPERATING_PRINCIPLE",
    "فلسفة المخاطرة": "RISK_POSTURE",
    "فلسفة التوسع": "PREFERENCE",
    "فلسفة الاستثمار": "PREFERENCE",
    "أولويات اتخاذ القرار": "POLICY",
    "الخطوط الحمراء": "POLICY",
    "أهداف 2026": "GOAL",
    "أهداف 2027": "GOAL",
    "أهداف 2028": "GOAL",
}
# Every DAIRTNA_DECISION_RULES.md section is, by the document's own title
# and structure (every heading is an IF/THEN rule), a DECISION_RULE - no
# per-heading map needed, unlike the mixed-content Company Brain doc above.
DECISION_RULE_TYPE = "DECISION_RULE"

MAX_STATEMENT_CHARS = 600
MAX_MEMORY_FACT_ITEMS = 8
MAX_COMPANY_BRAIN_ITEMS = 30

STATUS_OK = "ok"
STATUS_NO_EVIDENCE = "no_evidence"

_H2_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_H1_NUMBERED_TOPIC_RE = re.compile(r"^#\s+\d+\.\s*(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class CompanyBrainItem:
    """One bounded Company Brain claim - never an operational observation.

    Field choice mirrors app/oce/models/evidence.py's Evidence.to_dict()
    bounded-item pattern from M4, adapted for Layer 2 semantics: ``type``
    is one of the eight Layer-2 categories (never an operational claim),
    ``authority`` is categorical (never a fabricated percentage), and
    ``conflict_state``/``provenance_note`` surface ENG-CONF-001 conflict
    history conservatively rather than picking a winner.
    """

    type: str
    key: str
    statement: str
    scope: str
    authority: str | None
    source: str
    source_type: str
    status: str = "available"
    conflict_state: str | None = None
    provenance_note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "key": self.key,
            "statement": self.statement,
            "scope": self.scope,
            "authority": self.authority,
            "source": self.source,
            "source_type": self.source_type,
            "status": self.status,
            "conflict_state": self.conflict_state,
            "provenance_note": self.provenance_note,
        }


@dataclass(frozen=True)
class CompanyBrainResult:
    """Bounded result of one Company Brain assembly attempt."""

    status: str  # "ok" | "no_evidence"
    item_count: int
    items: list[dict[str, Any]] = field(default_factory=list)
    # Distinct from `items` on purpose (Step 6): terminology/meaning
    # context, never presented as policy/preference.
    operational_semantics_topics: list[str] = field(default_factory=list)
    dairtna_knowledge_included: bool = False


def assemble_company_brain_context(
    *,
    company: dict[str, Any] | None,
    aimx_department: dict[str, Any] | None,
    memory_facts: list[dict[str, Any]] | None,
) -> CompanyBrainResult:
    """Build the bounded Company Brain Context for the current chat request.

    Unlike Truth Context (M4 Slice 2), this is not gated behind a single
    tenant check: ``memory_facts`` are a generic, per-tenant mechanism and
    are considered for every company. The Jannat/Dairtna knowledge documents
    (POLICY/PREFERENCE/DECISION_RULE/... content) are gated by two distinct
    questions, answered separately and both required:

    1. Entitlement - is this tenant the Jannat/Dairtna pilot company at all?
       (``_is_dairtna_tenant_entitled`` - authoritative, non-spoofable, see
       ``operational_truth_context.is_jannat_tenant``.)
    2. Applicability - is the current reasoning scope Dairtna Poultry
       specifically? (``_is_dairtna_scope_applicable`` - exact department
       slug match only.) Caesar Beverage, Shared Corporate, and an
       unresolved/company-wide scope (no department selected, e.g. the CEO
       workspace) are all NOT applicable by default, so Dairtna material is
       never presented as if it were universal company policy (Scenario G)
       or leaked across business units (Scenario F/H).

    Raises on genuinely unexpected failures (a real classification/parsing
    bug) so the caller can distinguish that from the expected states
    returned here - see AIService._load_company_brain_context.
    """
    items: list[CompanyBrainItem] = list(_memory_fact_items(memory_facts))

    dairtna_knowledge_included = False
    semantics_topics: list[str] = []
    if _is_dairtna_tenant_entitled(company) and _is_dairtna_scope_applicable(aimx_department):
        items.extend(_company_brain_document_items())
        semantics_topics = _operational_semantics_topics()
        dairtna_knowledge_included = True

    bounded_items = items[:MAX_COMPANY_BRAIN_ITEMS]
    payloads = [item.to_dict() for item in bounded_items]
    status = STATUS_OK if (payloads or semantics_topics) else STATUS_NO_EVIDENCE

    return CompanyBrainResult(
        status=status,
        item_count=len(payloads),
        items=payloads,
        operational_semantics_topics=semantics_topics,
        dairtna_knowledge_included=dairtna_knowledge_included,
    )


def _is_dairtna_tenant_entitled(company: dict[str, Any] | None) -> bool:
    """Is this tenant entitled to Dairtna Company Brain material at all?

    Delegates to the authoritative, non-spoofable pilot-tenant check
    (JWT-validated company_id -> DB row -> exact id/slug match). Never
    fuzzy/substring/alias matching, never user message text.
    """
    return is_jannat_tenant(company)


def _is_dairtna_scope_applicable(aimx_department: dict[str, Any] | None) -> bool:
    """Is the current reasoning scope Dairtna Poultry specifically?

    ``aimx_department`` is the RBAC-verified department dict app/api/chat.py
    places into context (never user-suppliable) - None means no department
    was selected (an unresolved/company-wide CEO-scope chat). That case is
    NOT applicable by default: Dairtna is one business unit among several
    (Caesar Beverage, Shared Corporate), and a company-wide chat must not
    silently receive one division's policy as if it were universal.
    """
    if not isinstance(aimx_department, dict):
        return False
    slug = str(aimx_department.get("slug") or "").strip().lower()
    return slug == DAIRTNA_POULTRY_DEPARTMENT_SLUG


def _memory_fact_items(memory_facts: list[dict[str, Any]] | None) -> list[CompanyBrainItem]:
    """Map durable memory_facts into INSTITUTIONAL_MEMORY items.

    Read-only against ENG-CONF-001's conflict machinery: ``has_conflict``/
    ``residual_uncertainty`` are already computed by
    MemoryRepository.fetch_facts() (append-not-substitute semantics,
    conflict resolution, and the memory schema itself are untouched here).
    A conflicted fact is marked ``authority="unresolved"`` and
    ``conflict_state="conflicted"`` rather than presented as settled
    institutional truth (Step 5 / Scenario D) - M5 never picks a winner.
    """
    items: list[CompanyBrainItem] = []
    for fact in (memory_facts or [])[:MAX_MEMORY_FACT_ITEMS]:
        if not isinstance(fact, dict):
            continue
        value = str(fact.get("fact_value") or "").strip()
        if not value:
            continue
        key = str(fact.get("fact_key") or "").strip() or "general_fact"
        has_conflict = bool(fact.get("has_conflict"))
        items.append(
            CompanyBrainItem(
                type="INSTITUTIONAL_MEMORY",
                key=key,
                statement=value[:MAX_STATEMENT_CHARS],
                scope="company",
                authority="unresolved" if has_conflict else "institutional",
                source="memory_facts",
                source_type="memory_fact",
                conflict_state="conflicted" if has_conflict else None,
                provenance_note=(str(fact.get("residual_uncertainty") or "").strip() or None),
            )
        )
    return items


def _company_brain_document_items() -> list[CompanyBrainItem]:
    items: list[CompanyBrainItem] = []

    brain_text = _read_document(COMPANY_BRAIN_PATH)
    for heading, body in _parse_h2_sections(brain_text):
        item_type = COMPANY_BRAIN_HEADING_TYPES.get(heading)
        if item_type is None:
            # Unrecognized heading (e.g. the document gained a new
            # section) - never guessed into a category.
            continue
        items.append(
            CompanyBrainItem(
                type=item_type,
                key=heading,
                statement=body[:MAX_STATEMENT_CHARS],
                scope="company",
                authority="authoritative",
                source="DAIRTNA_COMPANY_BRAIN",
                source_type="company_knowledge_document",
            )
        )

    rules_text = _read_document(DECISION_RULES_PATH)
    for heading, body in _parse_h2_sections(rules_text):
        items.append(
            CompanyBrainItem(
                type=DECISION_RULE_TYPE,
                key=heading,
                statement=body[:MAX_STATEMENT_CHARS],
                scope="company",
                authority="authoritative",
                source="DAIRTNA_DECISION_RULES",
                source_type="company_knowledge_document",
            )
        )

    return items


def _operational_semantics_topics() -> list[str]:
    text = _read_document(OPERATIONAL_SEMANTICS_PATH)
    if not text:
        return []
    return [match.group(1).strip() for match in _H1_NUMBERED_TOPIC_RE.finditer(text)]


def _parse_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split a markdown document into (heading, body) pairs at "## " H2
    boundaries. Empty-bodied sections are skipped."""
    if not text:
        return []
    matches = list(_H2_HEADING_RE.finditer(text))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = " ".join(text[start:end].split())
        if body:
            sections.append((heading, body))
    return sections


def _read_document(path: Path) -> str:
    """Missing/unreadable knowledge documents are an expected degraded
    state (Step 6/Failure rule) - logged and skipped, never a hard
    failure, since they are static repo files that may legitimately be
    absent in some environments (same posture as data_sources/ in M4)."""
    return _read_document_cached(str(path))


@lru_cache(maxsize=8)
def _read_document_cached(path_str: str) -> str:
    try:
        return Path(path_str).read_text(encoding="utf-8")
    except OSError:
        logger.warning("company_brain_document_unreadable", extra={"path": path_str})
        return ""
