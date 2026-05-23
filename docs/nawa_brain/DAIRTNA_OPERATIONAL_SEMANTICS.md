# Dairtna Operational Semantics

**Status:** Design — awaiting field validation with Dairtna staff before any executable use.
**Phase:** 2A — Operational Intelligence Grounding
**Scope:** Dairtna Poultry division only. Does not cover Caesar Juice or any other division.
**Last updated:** 2026-05-23

---

## 1. Problem Statement

NAWA can now read Dairtna files and extract numbers — mortality counts, flock sizes, egg figures, feed weights, cost lines. But the system has no understanding of **what the operational words around those numbers actually mean** in Dairtna's day-to-day reality.

Concrete failure modes already observed or expected:

- A line item mentioning "feed" in a routine grinder report gets reasoned about as if it were a feed shortage signal.
- A "medicine" line in a veterinary log gets framed as a disease outbreak.
- An "egg warehouse cost" entry gets escalated to "financial risk" by generic FMCG reasoning.
- A "hall report" is read as if any deviation from prior days is an operational issue.
- Routine operational vocabulary ("hall," "grinder," "vaccine schedule," "transfer to warehouse") is treated as risk vocabulary by default.

The interpretation doctrine (`DAIRTNA_OPERATIONAL_INTERPRETATION.md`) governs numerical thresholds and signal levels *after* a metric is recognized. This document governs the layer **before** that: what the words, entities, and file types actually mean, and what conclusions are and are not permitted from each.

Without this layer, threshold discipline cannot save us. The reasoning engine will misclassify routine operational data as risk data before any threshold is consulted.

---

## 2. Core Invariant

> **Operational vocabulary is not risk vocabulary. A term, file, or line item is only a risk signal when an explicit rule in this document or the interpretation doctrine says so.**

Corollaries:

- Routine reporting is the default reading. Risk reading requires explicit evidence.
- A mention of an entity (feed, medicine, hall, warehouse) is not a statement about that entity's condition.
- A cost report describes spending, not financial distress, unless paired with an explicit deviation signal.
- A file that exists at its normal cadence is *evidence the operation ran*, not evidence it ran abnormally.
- The AI never converts the presence of an operational entity into a problem statement about that entity.

---

## 3. Position in the NAWA Brain Stack

```
Ingestion (JANNAT_INGESTION_PLAYBOOK.md)
        │
        ▼
SEMANTICS — this document
        │   What entities and files actually mean.
        │   What conclusions are and are not permitted.
        ▼
INTERPRETATION (DAIRTNA_OPERATIONAL_INTERPRETATION.md)
        │   Numerical thresholds, signal levels, CEO-response constraints.
        ▼
CEO Response Layer
```

Semantics defines the vocabulary the interpreter operates on. The interpreter applies thresholds *within* the boundaries the semantics layer permits. The CEO response layer is constrained by both.

A metric that has no semantic definition here cannot be interpreted. An entity that has no semantic definition here cannot appear in CEO reasoning as a named operational object.

---

## 4. Operational Entities

Each entity is defined with: what it is, what it produces, what it is **not**, and what the AI is permitted to conclude from a mention of it alone.

### 4.1 Halls (صالات / قاعات)

- **What it is:** Physical poultry housing units. Each hall contains one flock at a time. Halls are the primary unit of daily operational reporting.
- **What it produces:** Daily hall reports (mortality, feed consumed, water consumed, environmental notes, sometimes egg counts for layer halls).
- **What it is NOT:** A financial unit. A sales unit. A risk unit.
- **From a mention alone, the AI may conclude:** That a hall is operational and reporting. Nothing else.
- **Required baselines for interpretation:** Hall ID, flock assignment, breed type, flock age, current flock size.
- **TO CONFIRM with field staff:** Exact number of halls, layer/broiler split, hall naming convention used in reports.

### 4.2 Flocks

- **What it is:** A cohort of birds of the same breed and age, housed in one hall. A flock has a lifecycle (placement → growth → production or finishing → depopulation).
- **What it produces:** Daily mortality, daily feed/water consumption, daily egg production (for layers), final dressing weight (for broilers).
- **What it is NOT:** Interchangeable with halls. One hall hosts a sequence of flocks over time. A flock identifier is required to attribute daily numbers correctly.
- **From a mention alone, the AI may conclude:** That a flock exists and is being tracked. Nothing about its health or productivity.
- **Required baselines for interpretation:** Flock ID, placement date, breed, initial flock size, current flock size, age in days.
- **TO CONFIRM with field staff:** How flock identity is recorded across reports (Arabic naming? Hall ID + cycle number? Date-based?).

### 4.3 Egg Warehouse (مخزن البيض)

- **What it is:** Storage and grading facility for eggs collected from layer halls before distribution.
- **What it produces:** Daily intake (eggs received from halls), grading distribution (XL/L/M/S/cracked), outgoing shipments, storage cost reports, sometimes loss/breakage figures.
- **What it is NOT:** A production unit (production happens in halls). Not a sales unit (sales happen in distribution).
- **From a mention alone, the AI may conclude:** That eggs are being stored and tracked. Not that there is a storage problem, a financial issue, or a distribution problem.
- **Required baselines for interpretation:** Expected daily intake range, expected grade distribution by source flock, expected outgoing cadence, storage cost baseline.
- **TO CONFIRM with field staff:** Whether the warehouse tracks cost separately from operations, who owns the cost reporting, and how cracked/lost eggs are recorded.

### 4.4 Feed / Grinder (العلف / الطاحونة)

- **What it is:** Feed preparation operation. Grinder mills raw inputs (corn, soy, additives) into formulated feed for each flock age. Often on-site at large operations like Jannat.
- **What it produces:** Daily grinder reports (raw input consumed, output produced, formula by flock age), feed distribution logs (which hall received how much).
- **What it is NOT:** A risk indicator by default. A grinder report exists every day the operation runs. Its existence is not a signal.
- **From a mention alone, the AI may conclude:** That feed is being prepared. Not that there is a feed shortage, a quality problem, a supply chain issue, or a cost overrun.
- **Required baselines for interpretation:** Expected daily output per flock age, expected raw input ratios, expected cost per kg.
- **TO CONFIRM with field staff:** Whether Dairtna operates its own grinder or buys formulated feed, whether reports include raw input vs. output separately, and what "feed shortage" language would actually look like in a report (it is rarely written that way — usually it shows as a delivery delay or a substitution note).

### 4.5 Veterinary / Medicine (البيطرة / الأدوية)

- **What it is:** Health management function. Includes vaccination schedules, routine prophylactic treatments, water-administered medications, and reactive treatment for outbreaks.
- **What it produces:** Vaccination logs (scheduled doses), treatment logs (reactive), medicine purchase/consumption records, sometimes mortality cause notes.
- **What it is NOT:** A disease alarm by default. A medicine mention is overwhelmingly routine (vaccinations and prophylactics are scheduled). Reactive medication is the exception, not the rule.
- **From a mention alone, the AI may conclude:** That health management activity occurred. Not that there is a disease outbreak, a health crisis, or elevated mortality risk.
- **Required baselines for interpretation:** Scheduled vaccination calendar by flock age, expected prophylactic consumption baseline, what constitutes a *reactive* (not scheduled) treatment entry.
- **TO CONFIRM with field staff:** How vet logs distinguish scheduled from reactive treatments, who authorizes reactive treatments, and the local vocabulary used when an actual disease event is being reported (this is critical — the language of a real outbreak is different from a routine vaccine log, and we need to know what the difference looks like in the file).

### 4.6 Production

- **What it is:** The aggregate output function — eggs from layer halls, finished birds from broiler halls. Production is *measured* in halls but *reported* in division-level summaries.
- **What it produces:** Daily production reports (eggs collected per hall, broiler weight gain, mortality-adjusted output).
- **What it is NOT:** A standalone department. Production language describes the *outcome* of hall operations, not a separate operational unit.
- **From a mention alone, the AI may conclude:** That production output was recorded. Not that production is above or below target — that requires baseline comparison per §4.2 of the interpretation doctrine.
- **Required baselines for interpretation:** Per the interpretation doctrine (breed-specific expected hen-day production, expected dressing weights by flock age).

### 4.7 Distribution

- **What it is:** Outbound logistics — moving eggs from warehouse to customers, moving finished broilers from halls to processors or wholesale buyers.
- **What it produces:** Delivery logs, customer order fulfillment records, route reports, sometimes return/rejection logs.
- **What it is NOT:** A signal of customer health, brand performance, or market demand. Distribution data describes logistics execution, not market outcomes.
- **From a mention alone, the AI may conclude:** That outbound activity occurred. Not that there is a customer complaint, a fulfillment failure, or a sales risk — those require explicit human-source evidence (per `JANNAT_INGESTION_PLAYBOOK.md` source tiering).
- **Required baselines for interpretation:** Expected daily outbound volume, customer cadence, normal return/rejection rate.
- **TO CONFIRM with field staff:** Whether Dairtna handles distribution in-house or through third parties, how customer complaints are reported (if at all), and where rejection/return data lives if it exists.

---

## 5. File Type Semantics

For each file type Dairtna currently uploads (or is expected to upload), the same four questions are answered: what can be extracted, what can be safely concluded, what must NOT be concluded, what baselines are required.

### 5.1 Hall Report

- **Purpose:** Daily operational status of a single hall.
- **Fields to extract:** Hall ID, date, flock ID, flock age, current flock size, daily deaths, feed consumed, water consumed, environmental notes (temperature, ventilation flags).
- **What can be concluded safely:** Mortality rate (per the interpretation doctrine §4.1, live). Daily presence of a report confirms hall is operational on that date.
- **What must NOT be concluded:** Feed shortage, water shortage, environmental crisis, disease outbreak, production problem — none of these can be concluded from a single hall report without baseline comparison and explicit signals.
- **Required baselines:** Flock size, breed, age, prior-day mortality history (3-day minimum for trend), feed standard per bird per age (for §4.3, design only), water rolling average (for §4.4, design only).
- **Missing baseline behavior:** If flock size is missing, mortality cannot be computed — declare `unknown / baseline_missing` per interpretation doctrine §6. Do not estimate.

### 5.2 Egg Warehouse Cost / Report

- **Purpose:** Records warehouse intake, grading distribution, outgoing shipments, and operating costs.
- **Fields to extract:** Date, intake volume, grade distribution counts, outgoing volume, cost lines (electricity, packaging, labor, transport-out, breakage).
- **What can be concluded safely:** That eggs were received, graded, and dispatched. Aggregate intake matches or diverges from layer-hall total output (data quality check, not a risk signal).
- **What must NOT be concluded:** Financial distress, cost overrun, margin pressure, sales decline. None of these can be concluded from a warehouse cost report alone. Cost lines are operational data, not risk data.
- **Required baselines:** Expected daily intake range, expected grade distribution by source flock age, expected cost lines (mean and acceptable variance), expected breakage rate.
- **Missing baseline behavior:** If grade-distribution standard is not configured, do not flag distribution as abnormal — declare `unknown` per interpretation doctrine §4.5 (design only).

### 5.3 Grinder / Feed Report

- **Purpose:** Records feed preparation activity — raw inputs consumed, formulated output produced, distribution to halls.
- **Fields to extract:** Date, raw input volumes by type, output volume by formula/age group, distribution log (hall, volume, formula).
- **What can be concluded safely:** That feed was prepared on that date. That a specific volume was sent to a specific hall.
- **What must NOT be concluded:** Feed shortage, supply chain risk, quality problem, cost overrun. None of these are visible in a routine grinder report. A feed shortage would appear as a missing distribution entry to a hall, a substitution note, or a procurement log entry — *not* as the presence of a grinder report.
- **Required baselines:** Expected daily output per flock age, expected raw input ratios, expected cost per kg of formulated feed, hall-by-hall expected consumption.
- **Missing baseline behavior:** Without a hall-level feed standard (per interpretation doctrine §4.3, design only), feed consumption cannot be evaluated — declare `unknown / baseline_missing`.

### 5.4 Mortality Report

- **Purpose:** Records bird deaths per hall per day. May be standalone or embedded in the hall report.
- **Fields to extract:** Date, hall ID, flock ID, current flock size, daily deaths, cumulative deaths (if present), cause notes (if present).
- **What can be concluded safely:** Daily mortality rate per the interpretation doctrine §4.1 (live, provisional thresholds).
- **What must NOT be concluded:** Disease outbreak, management failure, environmental crisis — these require explicit veterinary or environmental evidence, not just a mortality number. Even a `critical` signal level requires sustained-3-day-critical per interpretation doctrine §4.1 before cross-department escalation.
- **Required baselines:** Current flock size (mandatory). Breed and age (for future calibration).
- **Missing baseline behavior:** No flock size → `signal_level: unknown, signal_basis: baseline_missing — flock size not available`.

### 5.5 Daily Production Report

- **Purpose:** Aggregate output report across one or more halls. Eggs collected (layers) or weight gain (broilers).
- **Fields to extract:** Date, hall/flock breakdown, volume by grade (for eggs) or weight class (for broilers), losses/breakage if present.
- **What can be concluded safely:** That production was recorded on that date. Aggregate volume.
- **What must NOT be concluded:** Production deviation from expected without breed-specific expected production curve configured (interpretation doctrine §4.2, design only). Sales impact, customer impact, financial impact — none of these are visible in a production report.
- **Required baselines:** Per interpretation doctrine §4.2 (breed-and-age-specific expected production).
- **Missing baseline behavior:** No expected production curve configured → `signal_level: unknown, signal_basis: baseline_missing — breed production curve not configured`.

---

## 6. Anti-Hallucination Rules

These are hard prohibitions. They apply to every CEO response that references Dairtna context.

**Rule S1 — Do not infer feed shortage from a feed mention.**
A grinder report, a feed line item, or a feed entry in a hall report is routine operational data. A feed shortage requires either (a) an explicit shortage note in a report, (b) a missing expected distribution entry to a hall, or (c) a human source explicitly stating it. None of these are present in a generic feed mention.

**Rule S2 — Do not infer medicine shortage or disease outbreak from a medicine mention.**
A vaccine log, a treatment log, or a medicine purchase entry is routine. A disease outbreak requires (a) an explicit veterinary diagnosis, (b) elevated mortality signal sustained per interpretation doctrine §4.1, or (c) a reactive (non-scheduled) treatment entry confirmed as such.

**Rule S3 — Do not infer sales or distribution impact without explicit evidence.**
Distribution reports, warehouse cost reports, and production reports do not contain sales or customer information. A sales impact claim requires an explicit human-source signal (Tier 1–2 per `JANNAT_INGESTION_PLAYBOOK.md`) such as a customer complaint, a confirmed lost order, or a manager-reported fulfillment failure.

**Rule S4 — Do not call normal mortality a crisis.**
Already enforced by interpretation doctrine §7 Rule 1 and Rule 3. Restated here because the failure mode is severe: `signal_level: normal` mortality must never be framed as a problem, bottleneck, or crisis regardless of how many other Dairtna mentions appear in the same context.

**Rule S5 — Do not convert routine operational reporting into risk language.**
The presence of a report is not a signal. The mention of an operational entity is not a signal. The use of operational vocabulary (hall, flock, grinder, vaccine, warehouse, distribution) is not a signal. A signal requires either a threshold breach (per interpretation doctrine §4) or an explicit human-source statement (per ingestion playbook).

**Rule S6 — Do not aggregate routine items into a composite risk.**
Three routine reports mentioning feed, medicine, and warehouse do not combine into a "compound operational concern." Compound risk requires individual signals at `watch` or higher per interpretation doctrine §3, AND a documented compound rule (only §4.3 currently has one).

**Rule S7 — Do not import generic FMCG reasoning.**
Dairtna is not a generic FMCG operation. Patterns such as "low feed = supply chain risk," "high cost = margin compression," "high mortality always = disease" are FMCG defaults that do not hold here. The interpreter and these semantics — not generic priors — govern reasoning.

---

## 7. Unknown Behavior

When the semantic context required to evaluate a file, an entity, or a line item is missing, the AI must state that the context is missing rather than substitute an inference.

Concrete patterns:

- File type cannot be identified → `unknown / file_type_unrecognized`. Do not assume a default file type. Do not extract numbers without a recognized type.
- Entity cannot be classified to a known §4 entity → `unknown / entity_unrecognized`. Do not assume the closest match.
- A field required for interpretation is missing → `unknown / baseline_missing — <specific field>` per interpretation doctrine §6.
- A report references a department not yet covered by a semantics entry (e.g., procurement, HR, finance) → out of scope; do not reason about it under Dairtna doctrine.

The unknown response is not a failure mode. It is the **correct** response when context is insufficient.

---

## 8. Integration

### 8.1 Relationship to `DAIRTNA_OPERATIONAL_INTERPRETATION.md`

- Semantics defines what an entity or file means. Interpretation defines what its numbers mean.
- A metric that exists in interpretation but lacks a semantics entry must not be reasoned about until semantics catches up.
- A semantics entry that has no interpretation rule yet (e.g., warehouse cost) is permitted to *exist as operational fact* in CEO context but cannot generate a signal level until the interpretation doctrine adds rules for it.
- This document is the upstream constraint. The interpretation doctrine cannot expand into a metric whose semantic meaning is not defined here.

### 8.2 Relationship to `CURRENT_STATE.md`

- Adds a new design-stage document to the brain stack. Does not change phase status. Does not claim any executable capability beyond what CURRENT_STATE.md already records (mortality interpreter live; all else design).
- Index entry should be added to `00_NAWA_BRAIN_INDEX.md` (reading order, purpose table, architecture relationship map). Index update is a separate task; this document does not perform it.

### 8.3 Relationship to uploaded XLSX reports

- The five file types in §5 are the recognized Dairtna file shapes. An uploaded XLSX that matches one of these types may be parsed for the listed fields under the conclusions and prohibitions stated.
- An uploaded XLSX that does not match any §5 type must be handled per §7 (`unknown / file_type_unrecognized`). It must not be coerced into the nearest match.
- Field extraction rules in §5 are necessary but not sufficient — the interpretation doctrine §4 and the anti-hallucination rules in §6 also apply.

### 8.4 Relationship to future feed/warehouse interpreters

- When the feed-consumption interpreter (interpretation doctrine §4.3) moves from design to live, it must consume its data through the grinder/feed report semantics defined in §5.3 of this document. Field names, baseline requirements, and prohibitions defined here govern.
- When a warehouse interpreter is designed (not yet specified), it must add its semantic entry to §5 of this document *before* any interpretation rule is written. Interpretation cannot lead semantics.
- Any future interpreter that needs a new file type or new entity definition must extend this document first, route through workshop validation per `HYPOTHESIS_PREVALIDATION_WORKSHOP.md`, then update the interpretation doctrine.

---

## 9. Out of Scope

This document does NOT govern:

- Numerical thresholds, signal levels, or CEO-response constraints — those live in `DAIRTNA_OPERATIONAL_INTERPRETATION.md`.
- Ingestion mechanics, source tiering, evidence weighting, or submission discipline — those live in `JANNAT_INGESTION_PLAYBOOK.md`.
- Hypothesis lifecycle, evidence classes, confidence aggregation — those live in `HYPOTHESIS_VALIDATION_PROTOCOL.md`.
- Workshop methodology — that lives in `HYPOTHESIS_PREVALIDATION_WORKSHOP.md`.
- Caesar Juice or any other division — Caesar will receive its own parallel semantics document when in scope. Do not generalize Dairtna semantics to Caesar.
- Code implementation, parsing logic, regex patterns, file format details — this is doctrine, not implementation.

---

## 10. Related Documents

- `docs/nawa_brain/00_NAWA_BRAIN_INDEX.md` — navigation; this document must be added to it.
- `docs/nawa_brain/DAIRTNA_OPERATIONAL_INTERPRETATION.md` — downstream interpretation doctrine.
- `docs/nawa_brain/JANNAT_INGESTION_PLAYBOOK.md` — upstream ingestion playbook.
- `docs/nawa_brain/HYPOTHESIS_PREVALIDATION_WORKSHOP.md` — validation pathway for any field-staff confirmation required by this document.
- `CURRENT_STATE.md` — phase context.

---

## Appendix A — Open Questions for Dairtna Field Staff

These must be answered before this document is treated as field-validated. Each maps to a specific section above.

**Halls & flocks (§4.1, §4.2)**
1. Total hall count, layer/broiler split, and the exact naming convention used in daily reports.
2. How flock identity is recorded across reports — Arabic name, hall + cycle number, placement date, or other.
3. Whether multiple flocks ever share a hall, or whether one hall always equals one flock at a time.

**Egg warehouse (§4.3, §5.2)**
4. Whether warehouse cost reporting is separate from operational reporting, and who produces each.
5. How cracked, lost, and rejected eggs are recorded — single line, separate file, or only in monthly summaries.
6. Whether warehouse outgoing data ties cleanly to customer-side data, or whether there is a gap.

**Feed / grinder (§4.4, §5.3)**
7. Whether Dairtna operates its own grinder on-site or purchases formulated feed.
8. Whether the grinder report separates raw inputs from formulated output, or only records output.
9. What the actual operational language for a *feed shortage* would look like in a real report — substitution note, delivery delay flag, hall-level missing entry, or explicit shortage word.

**Veterinary / medicine (§4.5)**
10. How vet logs distinguish scheduled (vaccination, prophylactic) entries from reactive (treatment) entries.
11. Who authorizes reactive treatments and where that authorization is recorded.
12. The local vocabulary used in real disease-event reporting — we need to be able to tell a real outbreak report apart from a routine vaccine log.

**Production & distribution (§4.6, §4.7, §5.5)**
13. Whether production reports come per-hall, per-flock, division-aggregate, or all three.
14. Whether Dairtna handles distribution in-house, through third parties, or both.
15. Where customer complaints, rejected deliveries, and returns are recorded — if at all.

**Cross-cutting**
16. Which of the five §5 file types are actually uploaded today, which are produced but not uploaded, and which do not exist in current operational practice.
17. Cadence of each file type — daily, weekly, ad-hoc.
18. Who produces each file (named role, not named person) and who is the canonical authority when two reports disagree.

---

## Appendix B — Ownership and Lifecycle

- **Strategic owner:** Mubarak (NAWA founder).
- **Field validation owner:** Dairtna field manager (to be designated).
- **Predecessor:** None — this is the first semantics document in the brain stack.
- **Successor:** None yet. Future divisions (Caesar etc.) will receive parallel semantics documents; they will not modify this one.
- **Amendment process:** Changes routed through `HYPOTHESIS_PREVALIDATION_WORKSHOP.md`. Workshop output amends the relevant §4 entity definition or §5 file-type entry. Anti-hallucination rules in §6 are not amended without explicit founder approval — they are the hard-discipline core of this document.

---

*This document must be field-validated with Dairtna staff before any of its file-type or entity definitions are treated as authoritative for executable interpretation. Until then, it is design-stage doctrine guiding what the system is permitted to assume and conclude.*
