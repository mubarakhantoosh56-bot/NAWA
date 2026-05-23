"""
Tests for the Dairtna Operational Interpretation Layer — Phase 1 (mortality_rate).

All tests are pure unit tests: no DB, no async, no network.
"""
import pytest
from app.services.dairtna.interpreter import interpret_dairtna_measurements


# ---------------------------------------------------------------------------
# Helper — build a minimal draft row dict
# ---------------------------------------------------------------------------

def _draft(title: str, summary: str) -> dict:
    return {"proposed_title": title, "proposed_summary": summary}


# ---------------------------------------------------------------------------
# Core signal classification
# ---------------------------------------------------------------------------

def test_normal_mortality_arabic():
    """12 deaths / 77005 birds = 0.016% → normal."""
    drafts = [_draft(
        "تقرير الوفيات",
        "12 حالة وفاة يوم 13/05/2026 من أصل 77005 طيور",
    )]
    result = interpret_dairtna_measurements(drafts)
    assert result != ""
    assert "signal_level: normal" in result
    assert "0.016%" in result
    assert "cross_dept_flag: false" in result


def test_normal_mortality_english():
    """12 deaths out of 77005 birds → normal."""
    drafts = [_draft("Mortality Report", "12 deaths out of 77005 birds on 13/05/2026")]
    result = interpret_dairtna_measurements(drafts)
    assert "signal_level: normal" in result
    assert "0.016%" in result


def test_watch_mortality():
    """50 deaths / 77005 birds = 0.065% → watch."""
    drafts = [_draft("Mortality", "50 deaths out of 77005 birds")]
    result = interpret_dairtna_measurements(drafts)
    assert "signal_level: watch" in result
    assert "cross_dept_flag: false" in result


def test_warning_mortality():
    """100 deaths / 77005 birds = 0.130% → warning."""
    drafts = [_draft("Mortality", "100 deaths out of 77005 birds")]
    result = interpret_dairtna_measurements(drafts)
    assert "signal_level: warning" in result
    assert "cross_dept_flag: false" in result


def test_critical_mortality():
    """200 deaths out of 10000 birds = 2.0% → critical."""
    drafts = [_draft("Critical", "200 deaths out of 10000 birds")]
    result = interpret_dairtna_measurements(drafts)
    assert "signal_level: critical" in result
    assert "cross_dept_flag: false" in result  # still false — single-day reading


def test_boundary_exactly_at_normal_max():
    """Exactly 0.05% is the boundary — should be watch, not normal."""
    # 38.5 deaths / 77000 birds ≈ 0.050%: use integer 39 → 0.0506% → watch
    drafts = [_draft("", "39 deaths out of 77000 birds")]
    result = interpret_dairtna_measurements(drafts)
    assert "signal_level: watch" in result


# ---------------------------------------------------------------------------
# Missing baseline behavior
# ---------------------------------------------------------------------------

def test_unknown_when_flock_size_missing_arabic():
    """Deaths found but no flock size → unknown / baseline_missing."""
    drafts = [_draft("18 وفاة", "18 وفاة يوم 12/05/2026")]
    result = interpret_dairtna_measurements(drafts)
    assert "signal_level: unknown" in result
    assert "baseline_missing" in result
    assert "cross_dept_flag: false" in result


def test_unknown_when_flock_size_missing_english():
    """Deaths found but no flock size in English → unknown."""
    drafts = [_draft("Mortality", "18 deaths recorded today")]
    result = interpret_dairtna_measurements(drafts)
    assert "signal_level: unknown" in result
    assert "baseline_missing" in result


# ---------------------------------------------------------------------------
# Non-mortality drafts — should produce no signal
# ---------------------------------------------------------------------------

def test_egg_count_draft_produces_no_signal():
    """Egg production draft has no mortality pattern — returns empty string."""
    drafts = [_draft("Egg Production", "2328 بيضة يوم 12/05/2026")]
    result = interpret_dairtna_measurements(drafts)
    assert result == ""


def test_empty_drafts_list():
    """Empty input returns empty string."""
    result = interpret_dairtna_measurements([])
    assert result == ""


def test_drafts_with_no_parseable_content():
    """Drafts with no numbers at all return empty string."""
    drafts = [_draft("Update", "Everything is fine today")]
    result = interpret_dairtna_measurements(drafts)
    assert result == ""


# ---------------------------------------------------------------------------
# Signal block structure
# ---------------------------------------------------------------------------

def test_signal_block_contains_hard_constraints():
    """The output block must contain the hard CEO constraint rules."""
    drafts = [_draft("Mortality", "12 deaths out of 77005 birds")]
    result = interpret_dairtna_measurements(drafts)
    assert "HARD CONSTRAINTS" in result
    assert "PROVISIONAL" in result


def test_signal_block_contains_observed_fact():
    """The block must cite the raw count alongside the computed rate."""
    drafts = [_draft("", "12 deaths out of 77005 birds on 13/05/2026")]
    result = interpret_dairtna_measurements(drafts)
    assert "12 bird deaths" in result
    assert "77,005" in result
    assert "computed_rate" in result


def test_multiple_mortality_drafts_produce_multiple_signals():
    """Two mortality drafts with flock size → two signals in output."""
    drafts = [
        _draft("Day 1", "12 deaths out of 77005 birds on 13/05/2026"),
        _draft("Day 2", "200 deaths out of 10000 birds on 14/05/2026"),
    ]
    result = interpret_dairtna_measurements(drafts)
    assert "[Signal 1]" in result
    assert "[Signal 2]" in result


def test_normal_signal_interpretation_forbids_bottleneck_language():
    """Normal signal interpretation must explicitly say not to frame as bottleneck."""
    drafts = [_draft("", "12 deaths out of 77005 birds")]
    result = interpret_dairtna_measurements(drafts)
    assert "normal" in result
    assert "bottleneck" in result.lower()  # the constraint text forbids it
    assert "Do not frame as bottleneck" in result or "عنق زجاجة" in result


def test_date_hint_included_when_present():
    """Date found in summary is included in observed_fact."""
    drafts = [_draft("", "12 deaths out of 77005 birds on 13/05/2026")]
    result = interpret_dairtna_measurements(drafts)
    assert "13/05/2026" in result
