"""Local NAWA OIP orchestration for poultry operational files."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from app.oce.models.operational_context import OperationalContext
from app.oce.services.operational_context_service import OperationalContextService
from app.oip.loaders.excel_loader import ExcelLoader
from app.oip.models.derived_artifacts import PoultryDerivedArtifacts
from app.oip.models.operational_record import PoultryOperationalRecord
from app.oip.services.ceo_brief_service import CEOBriefService
from app.oip.services.poultry_derivation_service import PoultryDerivationService
from app.oip.services.poultry_situation_service import PoultrySituationService
from app.oip.translators.poultry_report_translator import PoultryReportTranslator
from app.oip.validators.poultry_validator import PoultryValidator

DEFAULT_SOURCE_DIR = (
    Path("data_sources")
    / "jannat_al_firdaws"
    / "2026_06"
    / "poultry_operations"
)
DEFAULT_DAILY_TECHNICAL_REPORT = "التقرير_الفني_اليومي_حقول_ديرتنا.xlsx"


@dataclass(frozen=True)
class PoultryPipelineResult:
    """Parsed records plus derived OIP artifacts."""

    records: list[PoultryOperationalRecord]
    artifacts: PoultryDerivedArtifacts
    operational_contexts: list[OperationalContext]


class OperationalPipelineService:
    """Coordinate local file loading, translation, and validation for OIP."""

    def __init__(
        self,
        loader: ExcelLoader | None = None,
        translator: PoultryReportTranslator | None = None,
        validator: PoultryValidator | None = None,
        derivation_service: PoultryDerivationService | None = None,
        situation_service: PoultrySituationService | None = None,
        ceo_brief_service: CEOBriefService | None = None,
        operational_context_service: OperationalContextService | None = None,
    ) -> None:
        self.loader = loader or ExcelLoader()
        self.translator = translator or PoultryReportTranslator()
        self.validator = validator or PoultryValidator()
        self.derivation_service = derivation_service or PoultryDerivationService()
        self.situation_service = situation_service or PoultrySituationService()
        self.ceo_brief_service = ceo_brief_service or CEOBriefService()
        self.operational_context_service = (
            operational_context_service or OperationalContextService()
        )

    def parse_poultry_daily_report(
        self,
        path: str | Path | None = None,
    ) -> list[PoultryOperationalRecord]:
        """Parse and validate the local Dairtna daily technical poultry report."""
        report_path = Path(path) if path is not None else DEFAULT_SOURCE_DIR / DEFAULT_DAILY_TECHNICAL_REPORT
        sheets = self.loader.load(report_path)
        records = self.translator.translate(sheets, report_path)
        self.validator.validate_or_raise(records)
        return records

    def run_poultry_daily_report(
        self,
        path: str | Path | None = None,
    ) -> PoultryPipelineResult:
        """Parse, validate, and derive local OIP artifacts from the poultry report."""
        records = self.parse_poultry_daily_report(path)
        artifacts = self.derivation_service.derive(records)
        situations = self.situation_service.generate_situations(artifacts.signals)
        operational_contexts = self.operational_context_service.build_contexts(
            situations=situations,
            metrics=artifacts.metrics,
            events=artifacts.events,
            signals=artifacts.signals,
            records=records,
        )
        ceo_briefs = self.ceo_brief_service.generate_briefs(situations)
        artifacts = PoultryDerivedArtifacts(
            metrics=artifacts.metrics,
            events=artifacts.events,
            signals=artifacts.signals,
            situations=situations,
            ceo_briefs=ceo_briefs,
        )
        return PoultryPipelineResult(
            records=records,
            artifacts=artifacts,
            operational_contexts=operational_contexts,
        )

    async def parse_poultry_daily_report_async(
        self,
        path: str | Path | None = None,
    ) -> list[PoultryOperationalRecord]:
        """Async-compatible parser for the local Dairtna daily technical poultry report."""
        report_path = Path(path) if path is not None else DEFAULT_SOURCE_DIR / DEFAULT_DAILY_TECHNICAL_REPORT
        sheets = await self.loader.load_async(report_path)
        records = self.translator.translate(sheets, report_path)
        self.validator.validate_or_raise(records)
        return records

    async def run_poultry_daily_report_async(
        self,
        path: str | Path | None = None,
    ) -> PoultryPipelineResult:
        """Async-compatible parser and derivation runner for the poultry report."""
        records = await self.parse_poultry_daily_report_async(path)
        artifacts = self.derivation_service.derive(records)
        situations = self.situation_service.generate_situations(artifacts.signals)
        operational_contexts = self.operational_context_service.build_contexts(
            situations=situations,
            metrics=artifacts.metrics,
            events=artifacts.events,
            signals=artifacts.signals,
            records=records,
        )
        ceo_briefs = self.ceo_brief_service.generate_briefs(situations)
        artifacts = PoultryDerivedArtifacts(
            metrics=artifacts.metrics,
            events=artifacts.events,
            signals=artifacts.signals,
            situations=situations,
            ceo_briefs=ceo_briefs,
        )
        return PoultryPipelineResult(
            records=records,
            artifacts=artifacts,
            operational_contexts=operational_contexts,
        )


def parse_poultry_daily_report(path: str | Path | None = None) -> list[dict[str, object]]:
    """Convenience function returning normalized records as dictionaries."""
    service = OperationalPipelineService()
    return [record.to_dict() for record in service.parse_poultry_daily_report(path)]


async def parse_poultry_daily_report_async(path: str | Path | None = None) -> list[dict[str, object]]:
    """Async convenience function returning normalized records as dictionaries."""
    service = OperationalPipelineService()
    records = await service.parse_poultry_daily_report_async(path)
    return [record.to_dict() for record in records]


def run_poultry_daily_report(path: str | Path | None = None) -> dict[str, object]:
    """Convenience function returning parsed records and derived artifacts."""
    service = OperationalPipelineService()
    result = service.run_poultry_daily_report(path)
    return {
        "records": [record.to_dict() for record in result.records],
        "metrics": [metric.to_dict() for metric in result.artifacts.metrics],
        "events": [event.to_dict() for event in result.artifacts.events],
        "signals": [signal.to_dict() for signal in result.artifacts.signals],
        "situations": [situation.to_dict() for situation in result.artifacts.situations],
        "operational_contexts": [
            context.to_dict() for context in result.operational_contexts
        ],
        "ceo_briefs": [brief.to_dict() for brief in result.artifacts.ceo_briefs],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print normalized NAWA OIP records from a local poultry Excel report.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Optional path to a .xlsx poultry daily technical report.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Number of signals to print. Use 0 for all signals.",
    )
    return parser.parse_args()


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    """Run the local parser and print OIP v0.1 artifact counts and signals."""
    _configure_stdout()
    args = _parse_args()
    service = OperationalPipelineService()
    result = service.run_poultry_daily_report(args.path)
    signals = result.artifacts.signals
    limit = len(signals) if args.limit == 0 else args.limit
    print(f"Parsed records count: {len(result.records)}")
    print(f"Metrics count: {len(result.artifacts.metrics)}")
    print(f"Events count: {len(result.artifacts.events)}")
    print(f"Signals count: {len(signals)}")
    print(f"Situations count: {len(result.artifacts.situations)}")
    print(f"Operational Contexts count: {len(result.operational_contexts)}")
    print(f"CEO Briefs count: {len(result.artifacts.ceo_briefs)}")
    print(f"First {min(limit, len(signals))} signals:")
    for signal in signals[:limit]:
        print(json.dumps(signal.to_dict(), ensure_ascii=False, sort_keys=True))
    print("Generated situations:")
    for situation in result.artifacts.situations:
        print(json.dumps(situation.to_dict(), ensure_ascii=False, sort_keys=True))
    print("Operational Context:")
    for context in result.operational_contexts:
        _print_context(context)
    print("CEO Brief:")
    for brief in result.artifacts.ceo_briefs:
        print(json.dumps(brief.to_dict(), ensure_ascii=False, sort_keys=True))


def _print_context(context: OperationalContext) -> None:
    context_payload = context.to_dict()
    summary = {
        "context_type": context_payload["context_type"],
        "company": context_payload["company"],
        "department": context_payload["department"],
        "related_entities": context_payload["related_entities"],
        "time_window": context_payload["time_window"],
        "recommended_next_data": context_payload["recommended_next_data"],
    }
    print("Context summary:")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    print("Available evidence:")
    for evidence in context.available_evidence:
        print(json.dumps(evidence.to_dict(), ensure_ascii=False, sort_keys=True))
    print("Missing evidence:")
    for evidence in context.missing_evidence:
        print(json.dumps(evidence.to_dict(), ensure_ascii=False, sort_keys=True))
    ready = "YES" if context.context_ready_for_reasoning else "NO"
    print(f"Reasoning Ready: {ready}")


if __name__ == "__main__":
    main()
