"""
Dairtna Operational Interpretation Layer — Phase 1.

Stateless, no DB dependency, no side effects.
Phase 1 supports mortality_rate only.

All thresholds are PROVISIONAL and must be validated against Jannat Al-Firdaws
field data before being treated as authoritative.
See: docs/nawa_brain/DAIRTNA_OPERATIONAL_INTERPRETATION.md
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# PROVISIONAL thresholds — mortality rate (%)
# Source: DAIRTNA_OPERATIONAL_INTERPRETATION.md §4.1
# Validate against Jannat Al-Firdaws field data before confirming.
# ---------------------------------------------------------------------------
_MORTALITY_NORMAL_MAX: float = 0.05   # < this → normal
_MORTALITY_WATCH_MAX: float = 0.10    # < this → watch
_MORTALITY_WARNING_MAX: float = 0.20  # < this → warning
                                       # >= this → critical

# ---------------------------------------------------------------------------
# Regex patterns — Arabic + English
# ---------------------------------------------------------------------------

# Deaths / mortalities: match number before a death/mortality keyword.
# Allows up to 2 common English modifier words between the number and the keyword
# (e.g., "12 daily mortalities", "12 confirmed deaths") while still matching
# direct adjacency ("12 mortalities", "12 وفاة", "12 حالة وفاة").
_RE_DEATHS = re.compile(
    r"(\d[\d,]*)"
    r"\s+"
    r"(?:(?:daily|confirmed|recorded|reported|total)\s+){0,2}"
    r"(?:"
    r"deaths?"
    r"|mortalities?"
    r"|وفاة"
    r"|نفوق"
    r"|حالات?\s+وفاة"
    r"|حالة\s+وفاة"
    r"|طيور?\s+نافقة?"
    r"|نافق"
    r")",
    re.IGNORECASE | re.UNICODE,
)

# Flock size after "out of" / "من أصل" / "من" followed by bird-count word
_RE_FLOCK_POSTFIX = re.compile(
    r"(?:out\s+of|من\s+أصل|من)\s+([\d,]+)\s*(?:birds?|طيور?|طير|رأس)",
    re.IGNORECASE | re.UNICODE,
)

# Flock size as a standalone bird count (fallback — used only if postfix fails)
_RE_FLOCK_PREFIX = re.compile(
    r"([\d,]+)\s*(?:birds?|طيور?|طير|رأس)",
    re.IGNORECASE | re.UNICODE,
)

# Date hint — DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
_RE_DATE = re.compile(r"\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}")


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------

@dataclass
class _MortalityReading:
    deaths: int
    flock_size: Optional[int]
    date_hint: str
    source_summary: str


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_int(raw: str) -> int:
    return int(raw.replace(",", ""))


def _extract_date_hint(text: str) -> str:
    m = _RE_DATE.search(text)
    return m.group(0) if m else ""


def _parse_mortality_reading(summary: str, title: str) -> Optional[_MortalityReading]:
    """Return a _MortalityReading if a death count can be parsed from the text."""
    combined = f"{title} {summary}"

    deaths_match = _RE_DEATHS.search(combined)
    if not deaths_match:
        return None
    deaths = _parse_int(deaths_match.group(1))

    # Prefer explicit "out of N birds" pattern
    flock_match = _RE_FLOCK_POSTFIX.search(combined)
    if flock_match:
        flock_size: Optional[int] = _parse_int(flock_match.group(1))
    else:
        # Fallback: find all standalone bird counts, pick the largest that exceeds deaths
        candidates = [
            _parse_int(m.group(1))
            for m in _RE_FLOCK_PREFIX.finditer(combined)
            if _parse_int(m.group(1)) != deaths
        ]
        valid = [c for c in candidates if c > deaths]
        flock_size = max(valid) if valid else None

    return _MortalityReading(
        deaths=deaths,
        flock_size=flock_size,
        date_hint=_extract_date_hint(combined),
        source_summary=summary[:200],
    )


# ---------------------------------------------------------------------------
# Signal classification
# ---------------------------------------------------------------------------

def _classify_mortality(rate_pct: float) -> str:
    if rate_pct < _MORTALITY_NORMAL_MAX:
        return "normal"
    if rate_pct < _MORTALITY_WATCH_MAX:
        return "watch"
    if rate_pct < _MORTALITY_WARNING_MAX:
        return "warning"
    return "critical"


def _format_mortality_signal(reading: _MortalityReading) -> str:
    date_str = f" on {reading.date_hint}" if reading.date_hint else ""
    observed = f"{reading.deaths} bird deaths recorded{date_str}"

    if reading.flock_size is None:
        return (
            f"metric: mortality_rate\n"
            f"observed_fact: {observed}\n"
            f"signal_level: unknown\n"
            f"signal_basis: baseline_missing — flock size not found in uploaded file\n"
            f"interpretation: Cannot compute mortality rate without current flock size. "
            f"Baseline not configured. Do not infer a signal level from the raw count alone.\n"
            f"cross_dept_flag: false\n"
            f"thresholds: PROVISIONAL"
        )

    rate = reading.deaths / reading.flock_size * 100
    signal = _classify_mortality(rate)

    # Single-day reading never triggers cross-department per doctrine §4.1
    cross_dept = "false"

    if signal == "normal":
        interpretation = (
            f"{rate:.3f}% daily mortality is within the expected operating range "
            f"for a flock of {reading.flock_size:,} birds. "
            f"No production impact indicated. "
            f"Do not frame as bottleneck, crisis, or risk (عنق زجاجة، أزمة، تأخير إنتاجي)."
        )
    elif signal == "watch":
        interpretation = (
            f"{rate:.3f}% daily mortality is at the edge of the normal range. "
            f"Monitor over the next 24–48 hours. "
            f"No cross-department escalation warranted from this reading alone."
        )
    elif signal == "warning":
        interpretation = (
            f"{rate:.3f}% daily mortality exceeds the normal operating range. "
            f"Flag for veterinary review within the Dairtna production domain. "
            f"Do not connect to sales or distribution without additional evidence."
        )
    else:  # critical
        interpretation = (
            f"{rate:.3f}% daily mortality is above the critical threshold. "
            f"Requires immediate veterinary and production management attention. "
            f"Cross-department escalation is permitted only if sustained for ≥ 3 consecutive days."
        )

    return (
        f"metric: mortality_rate\n"
        f"observed_fact: {observed} out of {reading.flock_size:,} birds\n"
        f"computed_rate: {rate:.3f}%\n"
        f"signal_level: {signal}\n"
        f"signal_basis: provisional_threshold_applied\n"
        f"interpretation: {interpretation}\n"
        f"cross_dept_flag: {cross_dept}\n"
        f"thresholds: PROVISIONAL — validate against Jannat Al-Firdaws field data before treating as authoritative"
    )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def interpret_dairtna_measurements(drafts: list[dict]) -> str:
    """
    Parse pending draft rows and return a DAIRTNA OPERATIONAL SIGNAL INTERPRETATION block.

    Phase 1: mortality_rate only.
    Returns empty string if no parseable mortality data is found.

    No database calls. No side effects. Deterministic.

    Args:
        drafts: List of dicts with keys: proposed_title, proposed_summary.
                Matches the shape of asyncpg Row objects from operational_event_drafts.

    Returns:
        Formatted signal block string for injection into the CEO prompt context,
        or empty string if no signals were produced.
    """
    signals: list[str] = []

    for row in drafts:
        title = str(row.get("proposed_title") or "")
        summary = str(row.get("proposed_summary") or "")
        reading = _parse_mortality_reading(summary, title)
        if reading is not None:
            signals.append(_format_mortality_signal(reading))

    if not signals:
        return ""

    header = (
        "DAIRTNA OPERATIONAL SIGNAL INTERPRETATION\n"
        "Signals computed from uploaded file data using domain-specific poultry thresholds.\n"
        "All thresholds are PROVISIONAL — see DAIRTNA_OPERATIONAL_INTERPRETATION.md.\n"
        "\n"
        "HARD CONSTRAINTS for CEO response:\n"
        "  1. Do NOT escalate any metric beyond its stated signal_level.\n"
        "  2. If signal_level is 'normal', do NOT frame the metric as a bottleneck, "
        "crisis, production delay, or sales risk (عنق زجاجة، أزمة، تأخير إنتاجي).\n"
        "  3. If signal_level is 'unknown', state that baseline data is missing. Do not infer.\n"
        "  4. Do NOT connect mortality to sales, distribution, or finance unless "
        "cross_dept_flag is true AND a human-confirmed operational event supports it.\n"
        "  5. Cite the computed_rate alongside the raw count when referencing mortality.\n"
    )

    body = "\n\n".join(f"[Signal {i + 1}]\n{s}" for i, s in enumerate(signals))
    return f"{header}\n{body}"
