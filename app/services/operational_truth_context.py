"""M4 Slice 2: bridge existing KAE/OIP -> OCE evidence into the live chat
reasoning path.

This module is integration glue only. It does not create a Truth Engine,
does not add a Runtime Component, and does not modify OIP/OCE/NCO - it
calls their existing public methods exactly as designed (the same way
app/nco/pipeline.py already does) and maps their existing output
(``Evidence.to_dict()``, already built for this purpose in M4 Slice 1) into
a bounded list of dicts that ``decision_context.build_decision_context()``
can consume.

Nothing here is persisted. Per EBD-004, KAE's Truth Layer output is "for
the current runtime execution" - this module recomputes it fresh, in
memory, on demand, exactly like every other OIP/OCE call site in this
codebase (there is no cache/DB table for Evidence/OperationalContext
anywhere in the repo).

Company isolation: this integration only ever applies to the one pilot
tenant (Jannat Al-Firdaws / Dairtna poultry) that KAE/OIP/OCE currently
have real parsing/evidence logic for. Every other company gets
status="not_applicable" - never a Jannat file gets read into any other
tenant's reasoning context.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.oce.collectors.poultry_context_collector import PoultryContextCollector
from app.oce.models.operational_context import OperationalContext
from app.oip.models.derived_artifacts import OperationalMetric
from app.oip.models.operational_record import PoultryOperationalRecord
from app.oip.models.operational_situation import OperationalSituation
from app.oip.services.operational_pipeline_service import OperationalPipelineService
from app.oip.validators.poultry_validator import PoultryValidationError

logger = logging.getLogger(__name__)

POULTRY_OPERATIONS_DIR = (
    Path("data_sources") / "jannat_al_firdaws" / "2026_06" / "poultry_operations"
)

# A synthetic situation type used only to reuse PoultryContextCollector.collect()
# when no rule-triggered situation (e.g. production_declining_trend) currently
# exists for a file - so evidence that isn't trend-gated (e.g. a plain
# production/water/Feed Mill reading) can still reach reasoning. This is not a
# new OIP concept; OperationalContextService.build_contexts() is untouched and
# still only routes "poultry_production_drop" - this module calls the
# collector directly instead, exactly as OperationalContextService itself does.
SNAPSHOT_SITUATION_TYPE = "operational_snapshot"

JANNAT_TENANT_TERMS = ("jannat", "firdaws")
JANNAT_TENANT_TERM_AR = "الفردوس"
POULTRY_DEPARTMENT_TERMS = ("dairtna", "deirtna", "ديرتنا", "poultry", "دواجن")

# Prompt-size bounds (mirrors the existing _compact_operational_events /
# _compact_memory_events [:5]/[:10] convention in decision_context.py).
# Sized generously enough that the current real pilot dataset (6 poultry
# files x up to ~11 evidence types, deduplicated, plus up to 2 headline
# metrics x ~4 distinct entities) is never truncated - in particular,
# company-wide items like Feed Mill inventory must never be pushed out by
# earlier per-entity items sharing this bound.
MAX_AVAILABLE_EVIDENCE_ITEMS = 30
MAX_MISSING_EVIDENCE_ITEMS = 6

# PoultryContextCollector's existing evidence types are all trend/presence/
# document-level (situation, *_trend, daily_report, company_decision_rules,
# ...) - none of them is a direct single OBSERVED production reading
# (Golden Pilot Scenario A). Rather than modifying OCE to add a new
# evidence type, the headline OBSERVED metrics below are read directly from
# the same OperationalMetric list OCE itself already consumes, and mapped
# into the identical bounded item shape as Evidence.to_dict() - no new
# schema, no OCE change.
HEADLINE_OBSERVED_METRIC_FIELDS = ("bird_balance", "daily_production_rate")

STATUS_OK = "ok"
STATUS_NO_EVIDENCE = "no_evidence"
STATUS_NOT_APPLICABLE = "not_applicable"


def is_jannat_tenant(company: dict[str, Any] | None) -> bool:
    """Mirror app/api/files.py::_is_jannat_company's exact matching rule.

    Duplicated locally rather than imported: the API layer must depend on
    the service layer, not the reverse.
    """
    if company is None:
        return False
    haystack = " ".join(
        str(company.get(field_name) or "").strip().lower().replace("_", " ").replace("-", " ")
        for field_name in ("slug", "name")
    )
    return (all(term in haystack for term in JANNAT_TENANT_TERMS)) or JANNAT_TENANT_TERM_AR in haystack


def is_poultry_department_scope(aimx_department: dict[str, Any] | None) -> bool:
    """True when an explicit department scope is the Dairtna poultry
    operations department. The caller decides what "no department" (a
    CEO/company-wide chat) means - this function only classifies an
    explicit, RBAC-verified department dict, never user message text.
    """
    if not isinstance(aimx_department, dict):
        return False
    haystack = " ".join(
        str(aimx_department.get(field_name) or "").strip().lower().replace("_", " ").replace("-", " ")
        for field_name in ("name", "department_type", "slug")
    )
    return any(term in haystack for term in POULTRY_DEPARTMENT_TERMS)


@dataclass(frozen=True)
class TruthContextResult:
    """Bounded result of one truth-context assembly attempt."""

    status: str  # "ok" | "no_evidence" | "not_applicable"
    evidence_count: int
    items: list[dict[str, Any]] = field(default_factory=list)


def assemble_truth_context(
    *,
    company: dict[str, Any] | None,
    aimx_department: dict[str, Any] | None,
) -> TruthContextResult:
    """Build the bounded Operational Truth Context for the current chat
    request, or explain why none applies.

    Raises on genuinely unexpected failures (a real collector/service bug)
    so the caller can distinguish that from the expected degraded states
    returned here (not_applicable / no_evidence) - see
    AIService._load_truth_context for how the caller separates the two.
    """
    if not is_jannat_tenant(company):
        return TruthContextResult(STATUS_NOT_APPLICABLE, 0)

    if aimx_department is not None and not is_poultry_department_scope(aimx_department):
        return TruthContextResult(STATUS_NOT_APPLICABLE, 0)

    contexts, headline_metrics = _collect_operational_contexts()
    items = _bounded_evidence_items(contexts, headline_metrics)
    if not items:
        return TruthContextResult(STATUS_NO_EVIDENCE, 0)

    return TruthContextResult(STATUS_OK, len(items), items)


def _collect_operational_contexts() -> tuple[list[OperationalContext], list[OperationalMetric]]:
    """Run KAE (translate) -> OIE (derive/situations) -> OCE (collect) for
    every currently available pilot poultry file, reusing existing
    services exactly as app/nco/pipeline.py already does.

    Also returns every OBSERVED headline metric encountered (see
    HEADLINE_OBSERVED_METRIC_FIELDS) so Scenario A (a directly observed
    production claim) can reach Truth Context without modifying OCE.

    A single malformed file (PoultryValidationError - an expected, already
    -named M3 outcome) is skipped with a warning so one bad file cannot
    hide evidence from the rest. Any other exception is a real bug and is
    left to propagate, per Step 12's expected-vs-unexpected distinction.
    """
    if not POULTRY_OPERATIONS_DIR.exists():
        return [], []

    pipeline = OperationalPipelineService()
    collector = PoultryContextCollector()
    contexts: list[OperationalContext] = []
    headline_metrics: list[OperationalMetric] = []

    for path in sorted(POULTRY_OPERATIONS_DIR.glob("*.xlsx")):
        try:
            records = pipeline.parse_poultry_daily_report(path)
        except PoultryValidationError:
            logger.warning("truth_context_skipped_invalid_file", extra={"path": str(path)})
            continue
        if not records:
            continue

        artifacts = pipeline.derivation_service.derive(records)
        headline_metrics.extend(
            metric
            for metric in artifacts.metrics
            if metric.metric_name in HEADLINE_OBSERVED_METRIC_FIELDS
            and metric.epistemic_origin == "observed"
        )
        situations = pipeline.situation_service.generate_situations(artifacts.signals)

        if situations:
            contexts.extend(
                pipeline.operational_context_service.build_contexts(
                    situations=situations,
                    metrics=artifacts.metrics,
                    events=artifacts.events,
                    signals=artifacts.signals,
                    records=records,
                )
            )
            continue

        snapshot = _snapshot_situation(records)
        if snapshot is None:
            continue
        contexts.append(
            collector.collect(
                situation=snapshot,
                metrics=artifacts.metrics,
                events=artifacts.events,
                signals=artifacts.signals,
                records=records,
            )
        )

    if not contexts:
        # No poultry hall data produced any context at all (not expected
        # with the real pilot dataset, but kept as a safety net) - still
        # give company-wide evidence (e.g. Feed Mill) one chance to surface.
        fallback = _snapshot_situation([])
        if fallback is not None:
            contexts.append(
                collector.collect(
                    situation=fallback, metrics=[], events=[], signals=[], records=[]
                )
            )

    return contexts, headline_metrics


def _snapshot_situation(records: list[PoultryOperationalRecord]) -> OperationalSituation | None:
    """Build a minimal situation carrying only a date window and entity -
    the two things PoultryContextCollector.collect() needs - covering the
    records as a whole. Returns None if there is no dated record at all
    (nothing to window around); a company-wide fallback with no records is
    handled separately by the caller.
    """
    dated_records = [record for record in records if record.date is not None]
    if records and not dated_records:
        return None

    if dated_records:
        start_date = min(record.date for record in dated_records)
        end_date = max(record.date for record in dated_records)
        entity_types = {record.entity_type for record in records}
        entity_references = {record.entity_reference for record in records}
        entity_type = next(iter(entity_types)) if len(entity_types) == 1 else None
        entity_reference = next(iter(entity_references)) if len(entity_references) == 1 else None
        summary = (
            f"Snapshot of currently available operational records from "
            f"{start_date.isoformat()} to {end_date.isoformat()}."
        )
    else:
        start_date = end_date = None
        entity_type = None
        entity_reference = None
        summary = "Company-wide operational snapshot (no dated hall records)."

    return OperationalSituation(
        situation_type=SNAPSHOT_SITUATION_TYPE,
        severity="info",
        title="Current operational snapshot",
        summary=summary,
        evidence=[],
        recommended_next_checks=[],
        start_date=start_date,
        end_date=end_date,
        entity_type=entity_type,
        entity_reference=entity_reference,
    )


def _bounded_evidence_items(
    contexts: list[OperationalContext],
    headline_metrics: list[OperationalMetric],
) -> list[dict[str, Any]]:
    """Flatten available/missing evidence across all contexts, plus the
    headline OBSERVED metrics, into a bounded list of items sharing the
    same Evidence.to_dict() field shape - the same bounded, already-built
    representation from M4 Slice 1, never a new schema.

    Deduplicated so identical company-wide claims (Feed Mill inventory,
    knowledge documents) collapse to one entry instead of repeating once
    per hall file, while genuinely distinct per-entity claims (hall 2's
    water reading vs hall 3's) are kept separate. Headline metrics are
    deduplicated to the single most recent reading per
    (metric_name, entity_type, entity_reference).
    """
    available: list[dict[str, Any]] = []
    seen_available: set[tuple[Any, ...]] = set()
    missing: list[dict[str, Any]] = []
    seen_missing: set[str] = set()

    latest_headline: dict[tuple[Any, Any, Any], OperationalMetric] = {}
    for metric in headline_metrics:
        key = (metric.metric_name, metric.entity_type, metric.entity_reference)
        current = latest_headline.get(key)
        if current is None or (metric.date is not None and (current.date is None or metric.date > current.date)):
            latest_headline[key] = metric
    for metric in latest_headline.values():
        available.append(_metric_to_truth_item(metric))

    for context in contexts:
        for evidence in context.available_evidence:
            key = (
                evidence.type,
                evidence.entity_type,
                evidence.entity_reference,
                evidence.source_file,
                evidence.source_row_number,
            )
            if key in seen_available:
                continue
            seen_available.add(key)
            available.append(evidence.to_dict())

        for evidence in context.missing_evidence:
            if evidence.type in seen_missing:
                continue
            seen_missing.add(evidence.type)
            missing.append(evidence.to_dict())

    return available[:MAX_AVAILABLE_EVIDENCE_ITEMS] + missing[:MAX_MISSING_EVIDENCE_ITEMS]


def _metric_to_truth_item(metric: OperationalMetric) -> dict[str, Any]:
    """Map one OperationalMetric into the same bounded item shape as
    Evidence.to_dict() (status/type/canonical_field/normalized_value/
    source_label/raw_source_value/source_file/sheet_name/
    source_row_number/report_shape/entity_type/entity_reference/
    source_time/source_time_status/provenance_warnings), so the prompt
    formatter in decision_context.py can render both uniformly without
    knowing which one it is.
    """
    return {
        "source": metric.source_file,
        "type": metric.metric_name,
        "status": "available",
        "description": f"Observed {metric.metric_name} reading.",
        "date_range": {
            "start": metric.date.isoformat() if metric.date else None,
            "end": metric.date.isoformat() if metric.date else None,
        },
        "epistemic_origin": metric.epistemic_origin,
        "canonical_field": metric.metric_name,
        "normalized_value": metric.value,
        "source_label": metric.source_label,
        "raw_source_value": metric.raw_source_value,
        "source_file": metric.source_file,
        "sheet_name": metric.sheet_name,
        "source_row_number": metric.source_row_number,
        "report_shape": metric.report_shape,
        "entity_type": metric.entity_type,
        "entity_reference": metric.entity_reference,
        "source_time": metric.date.isoformat() if metric.date else None,
        "source_time_status": "authoritative" if metric.date is not None else "unresolved",
        "provenance_warnings": (),
    }
