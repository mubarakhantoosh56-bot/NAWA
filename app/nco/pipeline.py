"""Thin NCO Lite pipeline wrappers around existing NAWA engines.

NCO Lite coordinates existing services. It does not perform reasoning, create
new engine logic, or own persistence beyond calling the legacy memory
foundation when explicitly configured.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from app.company_input.models import CompanyInput
from app.company_input.services import CompanyInputClassification
from app.oce.models.operational_context import OperationalContext
from app.oip.models.ceo_brief import CEOBrief
from app.oip.models.derived_artifacts import (
    OperationalEvent,
    OperationalMetric,
    OperationalSignal,
)
from app.oip.models.operational_record import PoultryOperationalRecord
from app.oip.models.operational_situation import OperationalSituation
from app.oip.services.operational_pipeline_service import OperationalPipelineService
from app.services.memory.repository import MemoryRepository

MVP_OPTIONAL_MISSING_EVIDENCE_TYPES = frozenset(
    {
        "feed_consumption",
        "vet_reports",
        "temperature_ventilation",
    }
)

# KAE structured-ingestion truth states (Codex Round 1 Finding 5). A matched
# shape detector alone is never reported as successful structured ingestion.
KAE_STATE_SUPPORTED_WITH_DATA = "supported_with_data"
KAE_STATE_RECOGNIZED_NO_RECORDS = "recognized_but_no_structured_records"
KAE_STATE_UNSUPPORTED_OR_AMBIGUOUS = "unsupported_or_ambiguous"


@dataclass(frozen=True)
class KAEOutput:
    """Output of the KAE step for one uploaded report."""

    source_path: str
    records: list[PoultryOperationalRecord]
    report_shape: str | None = None
    ingestion_state: str = KAE_STATE_UNSUPPORTED_OR_AMBIGUOUS

    @property
    def structured_ingestion_supported(self) -> bool:
        """True only for the supported_with_data state.

        Kept for backward compatibility; ``ingestion_state`` is the
        authoritative truth signal and distinguishes a recognized shape with
        zero parsed rows from a genuinely unsupported/ambiguous shape - a
        matched shape detector alone is never reported as successful
        structured ingestion.
        """
        return self.ingestion_state == KAE_STATE_SUPPORTED_WITH_DATA

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "record_count": len(self.records),
            "report_shape": self.report_shape,
            "ingestion_state": self.ingestion_state,
            "structured_ingestion_supported": self.structured_ingestion_supported,
            "records": [record.to_dict() for record in self.records],
        }


@dataclass(frozen=True)
class OIEOutput:
    """Output of the OIE step for one uploaded report."""

    metrics: list[OperationalMetric]
    events: list[OperationalEvent]
    signals: list[OperationalSignal]
    situations: list[OperationalSituation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_count": len(self.metrics),
            "event_count": len(self.events),
            "signal_count": len(self.signals),
            "situation_count": len(self.situations),
            "metrics": [metric.to_dict() for metric in self.metrics],
            "events": [event.to_dict() for event in self.events],
            "signals": [signal.to_dict() for signal in self.signals],
            "situations": [situation.to_dict() for situation in self.situations],
        }


@dataclass(frozen=True)
class OCEOutput:
    """Output of the OCE step for one uploaded report."""

    contexts: list[OperationalContext]

    @property
    def context_ready_for_reasoning(self) -> bool:
        return bool(self.contexts) and all(
            context.context_ready_for_reasoning for context in self.contexts
        )

    @property
    def missing_evidence(self) -> list[dict[str, Any]]:
        missing: list[dict[str, Any]] = []
        for context in self.contexts:
            for evidence in context.missing_evidence:
                missing.append(evidence.to_dict())
        return missing

    @property
    def blocking_missing_evidence(self) -> list[dict[str, Any]]:
        return [
            evidence
            for evidence in self.missing_evidence
            if str(evidence.get("type") or "") not in MVP_OPTIONAL_MISSING_EVIDENCE_TYPES
        ]

    @property
    def mvp_evidence_policy_allows_reasoning(self) -> bool:
        return bool(self.contexts) and not self.blocking_missing_evidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_count": len(self.contexts),
            "context_ready_for_reasoning": self.context_ready_for_reasoning,
            "mvp_evidence_policy_allows_reasoning": (
                self.mvp_evidence_policy_allows_reasoning
            ),
            "blocking_missing_evidence": self.blocking_missing_evidence,
            "missing_evidence": self.missing_evidence,
            "contexts": [context.to_dict() for context in self.contexts],
        }


@dataclass(frozen=True)
class NCEOutput:
    """MVP-lite NCE interface output.

    This is intentionally a placeholder. It records that NCO reached the
    reasoning gate without performing AI reasoning itself.
    """

    status: str
    message: str
    context_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "context_count": self.context_count,
        }


@dataclass(frozen=True)
class ExecutiveIntelligenceOutput:
    """Output of the existing Executive Intelligence brief step."""

    ceo_briefs: list[CEOBrief]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ceo_brief_count": len(self.ceo_briefs),
            "ceo_briefs": [brief.to_dict() for brief in self.ceo_briefs],
        }


@dataclass(frozen=True)
class EvidencePolicyOutput:
    """MVP evidence policy decision applied by NCO Lite."""

    policy_name: str
    allowed_to_continue: bool
    confidence: str
    confidence_reduction_reason: str
    missing_evidence: list[dict[str, Any]]
    recommended_company_inputs: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_name": self.policy_name,
            "allowed_to_continue": self.allowed_to_continue,
            "confidence": self.confidence,
            "confidence_reduction_reason": self.confidence_reduction_reason,
            "missing_evidence": self.missing_evidence,
            "recommended_company_inputs": self.recommended_company_inputs,
        }


@dataclass(frozen=True)
class OMEOutput:
    """Result of storing into the legacy OME foundation."""

    attempted: bool
    stored_count: int = 0
    skipped_count: int = 0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempted": self.attempted,
            "stored_count": self.stored_count,
            "skipped_count": self.skipped_count,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class NCOExecutionResult:
    """End-to-end NCO Lite execution result."""

    status: str
    source_path: str
    company_input: CompanyInput | None = None
    classification: CompanyInputClassification | None = None
    kae: KAEOutput | None = None
    oie: OIEOutput | None = None
    oce: OCEOutput | None = None
    nce: NCEOutput | None = None
    executive: ExecutiveIntelligenceOutput | None = None
    ome: OMEOutput | None = None
    evidence_policy: EvidencePolicyOutput | None = None
    missing_evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source_path": self.source_path,
            "company_input": self.company_input.to_dict() if self.company_input else None,
            "classification": (
                self.classification.to_dict() if self.classification else None
            ),
            "kae": self.kae.to_dict() if self.kae else None,
            "oie": self.oie.to_dict() if self.oie else None,
            "oce": self.oce.to_dict() if self.oce else None,
            "nce": self.nce.to_dict() if self.nce else None,
            "executive": self.executive.to_dict() if self.executive else None,
            "ome": self.ome.to_dict() if self.ome else None,
            "evidence_policy": (
                self.evidence_policy.to_dict() if self.evidence_policy else None
            ),
            "missing_evidence": self.missing_evidence,
        }


class NCOLitePipeline:
    """Step-level wrappers around existing KAE/OIE/OCE/Executive/OME pieces."""

    def __init__(
        self,
        operational_pipeline: OperationalPipelineService | None = None,
        memory_repository: MemoryRepository | None = None,
    ) -> None:
        self.operational_pipeline = operational_pipeline or OperationalPipelineService()
        self.memory_repository = memory_repository

    def run_kae(self, source_path: str | Path) -> KAEOutput:
        """Run the existing file load/translation/validation path.

        Known limitation (Codex Round 2, non-blocking for M3): a recognized
        shape whose rows fail PoultryValidator's rules (e.g. missing date or
        non-positive bird_balance) raises PoultryValidationError here rather
        than returning a KAEOutput - validation failure is a fourth,
        exception-shaped state distinct from the three ingestion_state
        values below. This is intentionally not folded into
        ``ingestion_state`` in M3; a caller must catch validation errors
        separately.
        """
        report_path = Path(source_path)
        pipeline = self.operational_pipeline
        sheets = pipeline.loader.load(report_path)
        report_shape = pipeline.translator.detect_shape(sheets)
        records = pipeline.translator.translate(sheets, report_path)
        pipeline.validator.validate_or_raise(records)
        if report_shape is None:
            ingestion_state = KAE_STATE_UNSUPPORTED_OR_AMBIGUOUS
        elif not records:
            ingestion_state = KAE_STATE_RECOGNIZED_NO_RECORDS
        else:
            ingestion_state = KAE_STATE_SUPPORTED_WITH_DATA
        return KAEOutput(
            source_path=report_path.as_posix(),
            records=records,
            report_shape=report_shape,
            ingestion_state=ingestion_state,
        )

    def run_oie(self, records: list[PoultryOperationalRecord]) -> OIEOutput:
        """Run existing OIE artifact and situation generation."""
        artifacts = self.operational_pipeline.derivation_service.derive(records)
        situations = self.operational_pipeline.situation_service.generate_situations(
            artifacts.signals
        )
        return OIEOutput(
            metrics=artifacts.metrics,
            events=artifacts.events,
            signals=artifacts.signals,
            situations=situations,
        )

    def run_oce(
        self,
        *,
        oie_output: OIEOutput,
        records: list[PoultryOperationalRecord],
    ) -> OCEOutput:
        """Run existing OCE context building."""
        contexts = self.operational_pipeline.operational_context_service.build_contexts(
            situations=oie_output.situations,
            metrics=oie_output.metrics,
            events=oie_output.events,
            signals=oie_output.signals,
            records=records,
        )
        return OCEOutput(contexts=contexts)

    def run_nce_lite(self, oce_output: OCEOutput) -> NCEOutput:
        """Run the MVP-lite NCE interface without performing reasoning."""
        return NCEOutput(
            status="ready",
            message=(
                "NCE Lite gate passed. No AI reasoning is performed by NCO Lite."
            ),
            context_count=len(oce_output.contexts),
        )

    def run_executive_intelligence(
        self,
        situations: list[OperationalSituation],
        evidence_policy: EvidencePolicyOutput | None = None,
    ) -> ExecutiveIntelligenceOutput:
        """Run existing CEO brief generation."""
        briefs = self.operational_pipeline.ceo_brief_service.generate_briefs(
            situations
        )
        if evidence_policy is not None:
            briefs = [
                self._apply_evidence_policy_to_brief(brief, evidence_policy)
                for brief in briefs
            ]
        return ExecutiveIntelligenceOutput(
            ceo_briefs=briefs
        )

    def evaluate_mvp_evidence_policy(
        self,
        oce_output: OCEOutput,
    ) -> EvidencePolicyOutput:
        """Apply the Jannat MVP evidence policy without changing OCE contracts."""
        missing = oce_output.missing_evidence
        blocking = oce_output.blocking_missing_evidence
        allowed = oce_output.context_ready_for_reasoning or (
            oce_output.mvp_evidence_policy_allows_reasoning and not blocking
        )
        recommended_inputs = [
            _recommended_company_input(evidence)
            for evidence in missing
        ]
        confidence = "high" if not missing else "reduced"
        reason = (
            "All required evidence is available."
            if not missing
            else (
                "Confidence is reduced because optional evidence is missing: "
                + ", ".join(str(item.get("type") or "unknown") for item in missing)
                + ". The brief uses only available validated evidence."
            )
        )
        if blocking:
            reason = (
                "Reasoning remains blocked because required evidence is missing: "
                + ", ".join(str(item.get("type") or "unknown") for item in blocking)
                + "."
            )
        return EvidencePolicyOutput(
            policy_name="jannat_mvp_evidence_policy",
            allowed_to_continue=allowed,
            confidence=confidence,
            confidence_reduction_reason=reason,
            missing_evidence=missing,
            recommended_company_inputs=recommended_inputs,
        )

    def _apply_evidence_policy_to_brief(
        self,
        brief: CEOBrief,
        evidence_policy: EvidencePolicyOutput,
    ) -> CEOBrief:
        missing_evidence_detail = [
            {
                **item,
                "why_it_matters": {
                    "status": "pending_executive_language",
                    "note": (
                        "Why this evidence matters pending Aboura's Missing "
                        "Evidence language (PDS-001 §5.9)."
                    ),
                },
            }
            for item in evidence_policy.missing_evidence
        ]
        # ENG-EX1-003: category-level statement traceability for the
        # evidence-policy-derived fields this function owns. Accepted
        # vocabulary only (oce_context / traced-coarse-pending); row/file
        # lineage is out of scope here and is never fabricated.
        evidence_policy_trace: list[dict[str, Any]] = [
            {
                "field": "confidence",
                "source_type": "oce_context",
                "source_ref": {"evidence_policy": evidence_policy.policy_name},
                "trace_status": "traced",
            },
            {
                "field": "confidence_explanation",
                "source_type": "oce_context",
                "source_ref": {"evidence_policy": evidence_policy.policy_name},
                "trace_status": "traced",
            },
        ]
        for index, item in enumerate(evidence_policy.missing_evidence):
            evidence_policy_trace.append(
                {
                    "field": f"missing_evidence[{index}]",
                    "source_type": "oce_context",
                    "source_ref": {
                        "source": item.get("source"),
                        "evidence_type": item.get("type"),
                    },
                    "trace_status": "traced",
                }
            )
        for index in range(len(evidence_policy.recommended_company_inputs)):
            related_evidence = (
                evidence_policy.missing_evidence[index]
                if index < len(evidence_policy.missing_evidence)
                else {}
            )
            evidence_policy_trace.append(
                {
                    "field": f"recommended_company_inputs[{index}]",
                    "source_type": "oce_context",
                    "source_ref": {"evidence_type": related_evidence.get("type")},
                    "trace_status": "traced",
                }
            )
        return replace(
            brief,
            confidence=evidence_policy.confidence,
            confidence_explanation=evidence_policy.confidence_reduction_reason,
            recommended_company_inputs=list(evidence_policy.recommended_company_inputs),
            missing_evidence=missing_evidence_detail,
            statement_trace=[*brief.statement_trace, *evidence_policy_trace],
            evidence_summary=[
                *brief.evidence_summary,
                {
                    "evidence_policy": evidence_policy.policy_name,
                    "confidence_reduction_reason": (
                        evidence_policy.confidence_reduction_reason
                    ),
                    "missing_evidence": evidence_policy.missing_evidence,
                },
            ],
        )

    async def store_ome_foundation(
        self,
        *,
        company_id: str | None,
        session_id: str,
        source_path: str,
        oie_output: OIEOutput,
        oce_output: OCEOutput,
        executive_output: ExecutiveIntelligenceOutput,
    ) -> OMEOutput:
        """Store CEO brief memory through the existing legacy memory foundation."""
        if self.memory_repository is None:
            return OMEOutput(
                attempted=False,
                reason="memory_repository_not_configured",
            )
        if not company_id:
            return OMEOutput(
                attempted=False,
                reason="company_id_not_provided",
            )

        stored_count = 0
        skipped_count = 0
        context_payloads = [context.to_dict() for context in oce_output.contexts]
        situation_payloads = [situation.to_dict() for situation in oie_output.situations]

        for index, brief in enumerate(executive_output.ceo_briefs, start=1):
            brief_payload = brief.to_dict()
            idempotency_key = (
                f"nco-lite:{company_id}:{source_path}:{brief.headline}:{index}"
            )
            await self.memory_repository.insert_event(
                {
                    "company_id": company_id,
                    "session_id": session_id,
                    "event_type": "nco_lite.ceo_brief",
                    "user_message": "NCO Lite stored CEO brief from upload flow",
                    "executive_summary": brief.what_happened,
                    "logic_json": {
                        "nco_lite": True,
                        "ceo_brief": brief_payload,
                        "source_path": source_path,
                    },
                    "context": {
                        "source": "nco_lite",
                        "source_path": source_path,
                        "situations": situation_payloads,
                        "operational_contexts": context_payloads,
                    },
                    "tags": [
                        "nco_lite",
                        "ome_foundation",
                        "ceo_brief",
                        brief.severity,
                    ],
                    "idempotency_key": idempotency_key,
                }
            )
            stored_count += 1

        if not executive_output.ceo_briefs:
            skipped_count = 1

        return OMEOutput(
            attempted=True,
            stored_count=stored_count,
            skipped_count=skipped_count,
            reason="stored_via_memory_events",
        )


def _recommended_company_input(evidence: dict[str, Any]) -> str:
    evidence_type = str(evidence.get("type") or "")
    recommendations = {
        "vet_reports": "Veterinary report for the affected poultry hall and date range",
        "temperature_ventilation": (
            "Temperature and ventilation readings for the affected hall and date range"
        ),
        "feed_consumption": "Feed consumption report for the affected hall and date range",
        "water_consumption": "Water consumption report for the affected hall and date range",
        "previous_production_history": "Previous poultry production history report",
    }
    return recommendations.get(
        evidence_type,
        str(evidence.get("description") or "Additional operational evidence"),
    )
