# Dairtna Operational Interpretation Layer

**Status:** Design — approved for implementation  
**Phase:** 2A — Operational Intelligence Grounding  
**Scope:** Dairtna Poultry division only  
**Last updated:** 2026-05-23

---

## 1. Problem Statement

NAWA now extracts real numbers from uploaded Dairtna field reports (mortality counts,
egg production figures, flock sizes) and surfaces them in CEO chat responses. However,
the system has no concept of what those numbers mean in a poultry-field context. It
feeds raw numbers directly into a generic FMCG reasoning chain designed around
sales-fulfillment-margin bottlenecks.

**Concrete example:**
12 deaths in a flock of 77,005 birds (0.016% daily mortality) was classified as a
production bottleneck causing sales failure and financial risk. This is factually
incorrect. A 0.016% daily mortality is within the normal range for a broiler operation
of this scale.

The root cause is a missing interpretation step:

```
Current:  RAG number  →  generic FMCG reasoning  →  CEO conclusion
Required: RAG number  →  domain interpreter  →  calibrated signal  →  bounded reasoning  →  CEO conclusion
```

The interpreter is the missing link. It sits between extraction and reasoning, and it
prevents the reasoning engine from escalating facts beyond what the domain evidence
supports.

---

## 2. Core Invariant

> **The interpreter only escalates what the threshold supports.**

This is non-negotiable and governs every rule in this document.

Corollaries:

- A `normal` signal is never presented as a risk, bottleneck, or warning.
- A `watch` signal is noted but does not trigger cross-department language.
- A `warning` signal may reference production impact within the poultry operation.
- A `critical` signal may escalate to cross-department reasoning, but only when the
  threshold explicitly supports it.
- An `unknown` signal is reported as missing baseline. The AI does not infer from it.
- No signal level is ever upgraded by the AI reasoning layer without new evidence.

---

## 3. Interpretation Signal Levels

> **Vocabulary note — two separate label sets, not interchangeable.**
>
> **Event severity labels** (`info / watch / concern / critical`) are attached to raw
> ingested operational events in the capture pipeline. They describe how a human
> reporter or the ingestion layer categorized an event at the moment of capture.
>
> **Interpreter signal levels** (`normal / watch / warning / critical / unknown`) are
> produced by this interpreter after domain-calibrated computation against a threshold.
> They describe what a measurement means for this operation, not how it was filed.
>
> These two vocabularies must not be mixed. A raw event tagged `concern` does not
> produce a `warning` signal unless the computed metric crosses the `warning` threshold.
> A raw event tagged `info` can produce a `warning` or `critical` signal if the numbers
> support it. Signal level is always determined by computation, never inherited from the
> capture label.
>
> This interpreter and the signal levels below govern Dairtna operational measurements
> only. Other divisions may define their own interpreter doctrine independently.

Five levels are defined. Each has a strict behavioral rule for the CEO response layer.

| Level | Meaning | CEO response behavior |
|---|---|---|
| `normal` | Metric is within expected operating range | State the fact. Do not frame as risk, issue, or bottleneck. |
| `watch` | Metric is at the edge of normal range; worth monitoring | Note the metric. Do not escalate to cross-department language. |
| `warning` | Metric is outside normal range; operational attention required | Name the affected operational area. May reference production impact within the division. Cross-department only if explicitly supported. |
| `critical` | Metric is significantly outside range; immediate action required | Name root cause, affected departments, and recommended action. Cross-department escalation is permitted. |
| `unknown` | Baseline is missing or data is insufficient to evaluate | State "baseline not available for this metric." Do not infer signal level. Do not connect to other departments. |

---

## 4. First Metrics

### 4.1 Mortality Rate

**Formula:** `mortality_rate = daily_deaths / current_flock_size × 100`

**Required inputs:**
- `daily_deaths` — count of birds that died that day
- `current_flock_size` — total live birds in the flock at start of day

**Signal thresholds (PROVISIONAL — see Section 5):**

| Mortality rate | Signal |
|---|---|
| < 0.05% | normal |
| 0.05% – 0.10% | watch |
| 0.10% – 0.20% | warning |
| > 0.20% | critical |

**Cross-department escalation rule:**  
Only when `critical` AND sustained for ≥ 3 consecutive days. A single-day critical
reading does not trigger cross-department language without additional evidence.

**Missing baseline behavior:**  
If `current_flock_size` is not known, signal = `unknown`, basis =
`baseline_missing — flock size not available`.

**Worked example:**  
12 deaths / 77,005 birds = 0.016% → `normal`  
CEO response: state the mortality figure as an observed fact. Do not frame as
production bottleneck. Do not connect to sales or distribution.

---

### 4.2 Production Percentage

**Applies to:** Layer flocks only. Not applicable to broiler flocks.

**Formula:**  
`production_pct = eggs_collected / (laying_hens × expected_hen_day_pct) × 100`

**Required inputs:**
- `eggs_collected` — total eggs collected that day
- `laying_hens` — number of laying-age hens in flock
- `expected_hen_day_pct` — breed and age-specific expected production rate

**Signal thresholds (PROVISIONAL — see Section 5):**

| Deviation from expected | Signal |
|---|---|
| Within ±5% | normal |
| 5% – 10% below expected | watch |
| 10% – 20% below expected | warning |
| > 20% below expected | critical |
| Above expected by > 5% | watch (verify feed/water data) |

**Missing baseline behavior:**  
If `expected_hen_day_pct` or flock age is not configured, signal = `unknown`, basis =
`baseline_missing — breed production curve not configured`. Do not infer production
status from egg count alone.

---

### 4.3 Feed Consumption

**Formula:**  
`feed_ratio = actual_feed_kg / (current_flock_size × age_standard_kg_per_bird)`

**Required inputs:**
- `actual_feed_kg` — feed consumed that day
- `current_flock_size` — live bird count
- `age_standard_kg_per_bird` — breed and age-specific daily feed standard

**Signal thresholds (PROVISIONAL — see Section 5):**

| Feed ratio | Signal |
|---|---|
| 0.90 – 1.10 | normal |
| 0.80 – 0.90 or 1.10 – 1.20 | watch |
| 0.70 – 0.80 or > 1.20 | warning |
| < 0.70 | critical |

**Compound rule:**  
If feed consumption is `watch` or `warning` AND mortality is also `watch` or `warning`,
raise a veterinary flag within the production domain. Do not escalate to sales or
finance without additional evidence.

**Missing baseline behavior:**  
If `age_standard_kg_per_bird` is not configured, signal = `unknown`, basis =
`baseline_missing — feed standard not configured for this flock age`.

---

### 4.4 Water Consumption Trend

**Single-reading water data has no signal value.**  
A single day's water reading cannot be evaluated without a baseline trend. The minimum
required is a 3-day history; 7-day history is preferred.

**Formula:**  
`water_deviation_pct = (today_liters - rolling_avg_liters) / rolling_avg_liters × 100`

**Required inputs:**
- `today_liters` — water consumed today
- `rolling_avg_liters` — 7-day rolling average (minimum 3 days)

**Signal thresholds (PROVISIONAL — see Section 5):**

| Deviation from rolling average | Signal |
|---|---|
| Within ±10% | normal |
| 10% – 25% deviation (either direction) | watch |
| > 25% deviation | warning — potential health or equipment issue |

**Missing baseline behavior:**  
If fewer than 3 prior readings exist, signal = `unknown`, basis =
`insufficient_context — minimum 3-day history required for water trend analysis`.

**Important:** Water deviation alone does not escalate to distribution or sales. It
flags a potential health or equipment issue within the production domain only.

---

### 4.5 Egg Weight / Size Distribution

**Formula:**  
Compare daily distribution of egg grades (XL / L / M / S) against breed and age
standard distribution.

**Required inputs:**
- `grade_distribution` — count or percentage per grade category
- `breed_standard_distribution` — expected grade split by flock age
- `flock_age_days` — current flock age

**Signal thresholds (PROVISIONAL — see Section 5):**

| Deviation from standard distribution | Signal |
|---|---|
| ≤ 15% of eggs outside standard grade | normal |
| 15% – 30% outside standard | watch |
| > 30% outside standard | warning |
| Sudden single-day shift > 10% in any grade | warning — regardless of absolute position |

**Missing baseline behavior:**  
If breed standard distribution or flock age is not configured, signal = `unknown`,
basis = `baseline_missing — breed grade distribution not configured`.

---

## 5. Provisional Rules — Dairtna Only

> **ALL thresholds in Section 4 are PROVISIONAL.**

They are based on general poultry industry reference ranges and must be validated
against actual Jannat Al-Firdaws field data before being treated as authoritative
for this operation.

Required validation steps before marking thresholds as confirmed:

1. Review with Dairtna field manager — confirm thresholds match actual flock
   conditions, breed types, and seasonal patterns.
2. Back-test against at least 30 days of historical Dairtna field reports.
3. Identify any breed-specific or hall-specific variations that require override values.
4. Document confirmed values in `dairtna_field_baselines` table (Phase 2 of
   implementation — see Section 8).

Until validation is complete:
- All interpreter output must be labeled with the `provisional` flag in the signal block.
- The CEO response must not present provisional threshold conclusions as certainties.
- Unknown signals must be labeled as unknown, not inferred.

---

## 6. Missing Baseline Behavior

When a required baseline is not available, the interpreter **must** return:

```
signal_level: unknown
signal_basis: baseline_missing — <specific field that is missing>
interpretation: Cannot evaluate <metric_name> without <missing_input>.
               Baseline not configured.
cross_dept_flag: false
```

The AI reasoning layer must then:
- State that the baseline is not available for this metric.
- Not draw any conclusion from the raw number alone.
- Not connect the missing-baseline metric to other departments.
- Not escalate an unknown metric to a warning or critical level through inference.

**Example output for missing flock size:**
```
metric: mortality_rate
observed_fact: 12 bird deaths recorded on 13/05/2026
signal_level: unknown
signal_basis: baseline_missing — flock size not available in uploaded file
interpretation: Cannot compute mortality rate without current flock size.
cross_dept_flag: false
```

---

## 7. CEO Response Constraints

These are hard rules for the CEO chat response layer when an interpreter signal block
is present in the context.

**Rule 1 — Do not call normal mortality a bottleneck.**  
If `signal_level = normal` for mortality, the response must not use the words
"bottleneck," "crisis," "production delay," or equivalent Arabic equivalents
(عنق زجاجة، أزمة، تأخير إنتاجي) in reference to that mortality figure.

**Rule 2 — Do not connect to sales or distribution without evidence.**  
Cross-department language (sales commitments, fulfillment failure, customer disputes,
distribution delays) is only permitted when `cross_dept_flag = true` in at least one
signal, or when an explicit operational event from a human source confirms the
cross-department impact.

**Rule 3 — Do not say "crisis" without a supported threshold.**  
The word "crisis" (أزمة) or equivalent requires `signal_level = critical`. If the
highest signal level in the context is `watch` or `normal`, the word crisis is
prohibited.

**Rule 4 — If unknown, state that baseline is missing.**  
When `signal_level = unknown`, the response must say something equivalent to: "The
baseline for [metric] is not yet configured — this figure cannot be evaluated without
a reference range." It must not substitute an inference for the missing baseline.

**Rule 5 — Do not upgrade signal level.**  
The AI reasoning layer must not escalate a metric beyond its stated `signal_level`.
If the interpreter says `normal`, the CEO response cannot reframe it as `warning`
through contextual reasoning unless a separate, human-confirmed operational event
supports escalation.

**Rule 6 — State the computed rate, not just the raw count.**  
When the interpreter computes a ratio or percentage, the CEO response must cite the
computed metric (e.g., "0.016% daily mortality") alongside the raw count where
relevant, so the CEO can calibrate the number correctly.

---

## 8. Implementation Plan

### Phase 1 — Stateless interpreter (no DB dependency)

A single pure-Python file with no database calls. All thresholds are constants
embedded in the module, clearly marked as provisional.

**New file:** `app/services/dairtna/interpreter.py`

```
interpret_dairtna_measurements(drafts: list[dict]) -> str
```

- Input: list of pending draft rows (from `operational_event_drafts` table)
- Output: formatted signal block string, or empty string if no parseable metrics
- Dependencies: none (stdlib regex only)
- Latency: < 1ms (pure compute, no I/O)

The function:
1. Parses each draft summary for known metric patterns using regex.
2. Looks up the applicable provisional threshold.
3. Computes the signal level.
4. Returns a formatted DAIRTNA OPERATIONAL SIGNAL INTERPRETATION block.

If parsing fails for any metric, that metric is returned as `unknown /
insufficient_context`. No exception is raised.

### Phase 2 — Baseline table (future)

After provisional thresholds are validated:

New migration: `migrations/012_dairtna_baselines.sql`

```sql
CREATE TABLE dairtna_field_baselines (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id  UUID NOT NULL REFERENCES companies(id),
    division    TEXT NOT NULL DEFAULT 'dairtna',
    metric_key  TEXT NOT NULL,
    baseline_value NUMERIC,
    unit        TEXT,
    notes       TEXT,
    valid_from  DATE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

The interpreter in Phase 2 queries this table first, falls back to provisional
constants if no row exists for a metric, and returns `unknown` if neither applies.

### Files to modify (Phase 1 only)

| File | Change |
|---|---|
| `app/services/dairtna/__init__.py` | New package init (1 line) |
| `app/services/dairtna/interpreter.py` | New stateless interpreter (~120 lines) |
| `app/services/openai_client.py` | Call interpreter after drafts load; inject signal block; add constraint rule to pending_drafts_block header |

**Not modified in Phase 1:** routes, repositories, models, frontend, RAG pipeline,
migrations, any existing endpoint.

---

## 9. Related Documents

- `docs/nawa_brain/04_jannat_alfirdaws_model.md` — Dairtna division structure
- `docs/nawa_brain/06_data_capture_architecture.md` — ingestion pipeline
- `docs/nawa_brain/07_ai_behavior_rules.md` — AI reasoning rules (honest when context is missing)
- `CURRENT_STATE.md` — Phase 2A grounding context and explicit warning against
  building on sparse data

---

*This document must be reviewed and thresholds validated with Jannat Al-Firdaws field
management before any provisional rule is treated as confirmed operational policy.*
