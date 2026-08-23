"""M7 Slice 3C: synthetic upload fixture for the Golden A browser E2E spec.

Reuses the exact supported-workbook shape already proven by the backend
Golden Journey test (tests/test_m7_slice1_upload_truth_bridge.py's
_write_supported_workbook / FAMILY1_HEADER_ROW) - duplicated here rather
than imported, matching the existing repository convention of never
importing fixture helpers out of a frozen test file (see
tests/test_m7_slice3a_static_pilot_source_isolation.py's own docstring for
the same rationale). Never real pilot company data - every value here is
synthetic and fabricated.

GOLDEN_MARKER is the single deterministic string that makes this run's
upload unambiguously identifiable to both the chat question asked by
frontend/e2e/golden-a.spec.ts and the deterministic fake AI client in
scripts/e2e_fake_ai_client.py - both read it from the same environment
variable (E2E_GOLDEN_MARKER) that scripts/e2e_orchestrator.py sets from
this module, so there is exactly one place this string is defined.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

GOLDEN_MARKER = "Golden Journey Hall"

# The truth item the real Operational Truth Context assembly produces never
# carries the free-text hall_label through (only entity_reference, the hall
# NUMBER - confirmed by inspecting a real decision-context snapshot via the
# existing GET /ai/debug/decision-context endpoint). GOLDEN_HALL_NUMBER is
# therefore the actual deterministic matching key the fake AI client uses
# (see scripts/e2e_fake_ai_client.py); GOLDEN_MARKER remains the
# human-readable label used in the fixture's hall_label cell and in the
# chat question the Playwright spec asks.
GOLDEN_HALL_NUMBER = "9777"

GOLDEN_FIXTURE_FILENAME = "golden_a_dairtna_poultry_daily_technical_report.xlsx"

_FAMILY1_HEADER_ROW = (
    "التاريخ",
    "اليوم",
    "العمر بالأسبوع",
    "العمر باليوم",
    "رصيد الطيور",
    "الهلاكات اليومية",
    "الهلاكات الأسبوعية",
    "نسبة الهلاكات الأسبوعية",
    "الإنتاج اليومي بالطبق",
    "الإنتاج بالصندوق",
    "نسبة الإنتاج اليومية",
    "نسبة الإنتاج القياسية",
    "كسر",
    "متسخ",
    "الماء المستهلك",
)


def _family1_data_row(day: int) -> tuple:
    return (
        date(2026, 6, day), "الاثنين", 10, 70, 1000 - day, 2, 14, "1.00%",
        450, 37, "75.00%", "80.00%", 1, 1, 6000,
    )


def write_golden_workbook(path: Path, *, hall_number: str = GOLDEN_HALL_NUMBER) -> None:
    """Write the deterministic Golden A synthetic workbook to `path`.

    Same supported shape the real KAE translator already parses in
    production (one title row, one "hall number / hall label" row, the
    real Arabic header row, one data row). The fake AI client matches on
    `hall_number` (surfaced as `entity_reference` on the real truth item -
    see GOLDEN_HALL_NUMBER's docstring above for why hall_label itself
    isn't usable for this); hall_label still carries GOLDEN_MARKER purely
    as the human-readable name a real user would type into chat.
    """
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Hall"
    rows = [
        ("Synthetic Test Company - Daily Technical Report",),
        ("رقم القاعة", hall_number, "اسم الحقل", GOLDEN_MARKER),
        _FAMILY1_HEADER_ROW,
        _family1_data_row(day=1),
    ]
    for row in rows:
        sheet.append(list(row))
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def main() -> int:
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parents[1] / "frontend" / "e2e" / "fixtures" / GOLDEN_FIXTURE_FILENAME
    )
    write_golden_workbook(target)
    print(f"[e2e] Wrote Golden A fixture workbook to {target}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
