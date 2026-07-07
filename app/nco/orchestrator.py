"""NAWA Cognitive Orchestrator Lite.

The orchestrator coordinates existing NAWA services. It does not reason, parse
domain rules itself, create API routes, or own database schema.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.company_input.models import CompanyInput
from app.company_input.services import (
    CompanyInputClassification,
    CompanyInputClassifier,
    map_excel_upload_to_company_input,
)
from app.nco.pipeline import (
    NCOLitePipeline,
    NCOExecutionResult,
)


class NCOLiteOrchestrator:
    """First MVP orchestration layer for upload-completed flows."""

    def __init__(
        self,
        pipeline: NCOLitePipeline | None = None,
        classifier: CompanyInputClassifier | None = None,
    ) -> None:
        self.pipeline = pipeline or NCOLitePipeline()
        self.classifier = classifier or CompanyInputClassifier()

    async def run_upload_completed(
        self,
        *,
        source_path: str | Path,
        company_id: str | None = None,
        department_id: str | None = None,
        user_id: str | None = None,
        original_filename: str | None = None,
        mime_type: str | None = None,
        session_id: str = "nco-lite",
        store_memory: bool = True,
    ) -> NCOExecutionResult:
        """Coordinate the MVP upload-completed sequence.

        Flow:
        Upload completed -> KAE -> OIE -> OCE.

        If OCE is not ready for reasoning, the orchestrator applies the MVP
        evidence policy. It can continue only when missing evidence is optional.
        """
        if company_id:
            company_input = map_excel_upload_to_company_input(
                company_id=UUID(company_id),
                department_id=UUID(department_id) if department_id else None,
                user_id=UUID(user_id) if user_id else None,
                source_path=source_path,
                original_filename=original_filename or Path(source_path).name,
                mime_type=mime_type,
            )
            return await self.run_company_input(
                company_input=company_input,
                session_id=session_id,
                store_memory=store_memory,
            )

        return await self._run_excel_poultry_report(
            source_path=source_path,
            company_id=company_id,
            session_id=session_id,
            store_memory=store_memory,
        )

    async def run_company_input(
        self,
        *,
        company_input: CompanyInput,
        session_id: str = "nco-lite",
        store_memory: bool = True,
    ) -> NCOExecutionResult:
        """Coordinate one canonical CompanyInput through NCO Lite."""
        classification = self.classifier.classify(company_input)
        source_path = company_input.raw_storage_path or ""

        if classification.requires_human_confirmation:
            return NCOExecutionResult(
                status="waiting_for_input_confirmation",
                source_path=source_path,
                company_input=company_input,
                classification=classification,
            )

        if classification.probable_pipeline != "excel_poultry_report":
            return NCOExecutionResult(
                status="unsupported_input_pipeline",
                source_path=source_path,
                company_input=company_input,
                classification=classification,
            )

        return await self._run_excel_poultry_report(
            source_path=source_path,
            company_id=str(company_input.company_id),
            session_id=session_id,
            store_memory=store_memory,
            company_input=company_input,
            classification=classification,
        )

    async def _run_excel_poultry_report(
        self,
        *,
        source_path: str | Path,
        company_id: str | None,
        session_id: str,
        store_memory: bool,
        company_input: CompanyInput | None = None,
        classification: CompanyInputClassification | None = None,
    ) -> NCOExecutionResult:
        """Run the existing poultry report path after NCO classification."""
        kae_output = self.pipeline.run_kae(source_path)
        oie_output = self.pipeline.run_oie(kae_output.records)
        oce_output = self.pipeline.run_oce(
            oie_output=oie_output,
            records=kae_output.records,
        )

        if not oce_output.contexts:
            return NCOExecutionResult(
                status="stopped_no_context",
                source_path=kae_output.source_path,
                company_input=company_input,
                classification=classification,
                kae=kae_output,
                oie=oie_output,
                oce=oce_output,
                missing_evidence=[],
            )

        evidence_policy = self.pipeline.evaluate_mvp_evidence_policy(oce_output)

        if not evidence_policy.allowed_to_continue:
            return NCOExecutionResult(
                status="waiting_for_missing_evidence",
                source_path=kae_output.source_path,
                company_input=company_input,
                classification=classification,
                kae=kae_output,
                oie=oie_output,
                oce=oce_output,
                evidence_policy=evidence_policy,
                missing_evidence=oce_output.missing_evidence,
            )

        nce_output = self.pipeline.run_nce_lite(oce_output)
        executive_output = self.pipeline.run_executive_intelligence(
            oie_output.situations,
            evidence_policy=evidence_policy,
        )
        ome_output = None
        if store_memory:
            ome_output = await self.pipeline.store_ome_foundation(
                company_id=company_id,
                session_id=session_id,
                source_path=kae_output.source_path,
                oie_output=oie_output,
                oce_output=oce_output,
                executive_output=executive_output,
            )

        return NCOExecutionResult(
            status="completed",
            source_path=kae_output.source_path,
            company_input=company_input,
            classification=classification,
            kae=kae_output,
            oie=oie_output,
            oce=oce_output,
            nce=nce_output,
            executive=executive_output,
            ome=ome_output,
            evidence_policy=evidence_policy,
            missing_evidence=oce_output.missing_evidence,
        )
