# OME Foundation Plan v1

## Organizational Memory Engine Foundation

The Organizational Memory Engine is the durable memory layer of NAWA.

OME does not replace the existing operational pipeline. It evolves from it.

NAWA already has important foundations: `memory_events`, `memory_facts`, `operational_events`, `operational_situations`, and `situation_events`. These pieces prove that NAWA can store company-scoped memory-like records, operational timelines, and grouped situations.

The next architectural step is to separate responsibilities clearly:

```text
OIE observes and structures operational reality.
OCE builds context and readiness.
NCE reasons and produces decision intelligence.
OME preserves durable organizational memory.
```

OME stores durable organizational memory.

OIE/OCE/NCE do not own long-term memory.

---

## 1. Existing Pieces We Keep

### memory_events

Keep `memory_events` as the existing seed for company memory.

Current role:

- Stores tenant-scoped memory records.
- Stores AI decision events.
- Stores operational updates in some MVP paths.
- Supports recent-event retrieval for prompt continuity.

Future role:

- Serves as a legacy compatibility layer during OME migration.
- Can feed initial OME memory records.
- May later be renamed, wrapped, or superseded by clearer OME tables.

`memory_events` should not become the final OME design by itself because it is too broad, chat-oriented, and weakly typed for situation, decision, outcome, and evidence memory.

### memory_facts

Keep `memory_facts` as the existing lightweight fact store.

Current role:

- Stores durable company facts by `company_id` and `fact_key`.
- Tracks confidence.
- Supports simple company profile building.
- Allows memory facts to be injected into reasoning prompts.

Future role:

- Serves as a lightweight company fact/profile substrate.
- May support OME historical profile memory.
- Should not be treated as the only truth layer.

`memory_facts` is not enough for OME because it does not preserve full evidence lineage, supersession history, contradiction handling, or outcome learning.

### operational_events

Keep `operational_events` as the Live Operational Timeline.

Current role:

- Stores company-scoped operational events.
- Preserves department, user, type, category, priority, timestamp, source, payload, and metadata.
- Provides the chronological operating record.

Future role:

- Remains OIE-owned operational reality.
- Provides source events for OME situation memory and evidence links.
- Should not be renamed into memory.

### operational_situations

Keep `operational_situations` as the OCE/OIE situation substrate.

Current role:

- Groups related operational events into situations.
- Tracks situation type, severity, status, time window, department, and detection source.

Future role:

- Remains the live operational situation layer.
- Provides candidate situations that may later become durable situation memory in OME.
- Should not directly own decisions or outcomes.

### situation_events

Keep `situation_events` as the relationship table between situations and timeline events.

Current role:

- Links an operational situation to the operational events that support it.

Future role:

- Provides a reusable linking pattern for OME evidence/source links.
- Remains OCE/OIE-owned unless copied or referenced by future OME memory-link tables.

---

## 2. What Stays OIE/OCE/NCE

### Stays OIE

OIE owns operational signal creation and normalization.

The following should stay OIE:

- Raw operational event generation.
- File-derived operational records.
- Metrics extracted from reports.
- Operational event drafts.
- Operational signal detection.
- Timeline event creation.
- Classification into operational categories.
- Current operational event payloads and metadata.

OIE answers:

```text
What happened operationally?
What records, metrics, events, and signals can be extracted?
```

### Stays OCE

OCE owns context building before reasoning.

The following should stay OCE:

- Operational situation grouping.
- Evidence readiness.
- Missing evidence detection.
- Context packets.
- Situation-to-event relationships.
- Department/workflow context.
- `context_ready_for_reasoning`.

OCE answers:

```text
Is there enough context to reason?
What evidence exists?
What evidence is missing?
Which departments and workflows are affected?
```

### Stays NCE

NCE owns reasoning and decision intelligence.

The following should stay NCE:

- Hypothesis generation.
- Hypothesis ranking.
- Risk evaluation.
- Confidence calculation.
- Decision options.
- Trade-off reasoning.
- Executive reasoning narrative.

NCE answers:

```text
What does the evidence mean?
What options exist?
What risks and confidence levels should leadership see?
```

NCE may produce reasoning that OME stores later, but NCE does not own memory persistence.

---

## 3. What Becomes OME

OME owns durable organizational memory after operational reality, context, reasoning, decision, or outcome becomes worth preserving.

OME should own:

- Situation memory.
- Decision memory.
- Outcome memory.
- Evidence/source links.
- Historical baselines.
- Repeated pattern memory.
- Lessons learned.
- Superseded memory records.
- Memory retrieval for future OCE/NCE use.

OME answers:

```text
What should the organization remember?
What happened before in similar situations?
What decisions were made?
What outcomes followed?
What evidence supported the memory?
What should future reasoning learn from this?
```

OME must preserve the distinction between:

- Current operational truth.
- Historical memory.
- AI reasoning.
- Human decision.
- Observed outcome.
- Inferred lesson.

---

## 4. Minimum OME MVP Scope

The MVP scope must be narrow, durable, and directly useful for Jannat Al-Firdaws.

### Situation Memory

Situation memory records operational situations that are important enough to remember after their immediate timeline role.

Minimum fields:

- Company.
- Division or department when known.
- Source `operational_situation`.
- Situation type.
- Severity.
- Status at time of memory capture.
- Time window.
- Summary.
- Evidence count.
- Memory reason.

Situation memory should allow NAWA to recognize similar future situations.

### Decision Memory

Decision memory records the human decision made after a situation, CEO brief, or recommendation.

Minimum fields:

- Company.
- Related situation memory.
- Related CEO brief or reasoning output when available.
- Decision owner.
- Decision text.
- Decision type.
- Chosen option.
- Rejected alternatives when known.
- Rationale.
- Decision timestamp.
- Confidence at decision time.

Decision memory should allow NAWA to answer:

```text
What did leadership decide last time?
Why did they decide it?
What evidence shaped the decision?
```

### Outcome Memory

Outcome memory records what happened after a decision or situation.

Minimum fields:

- Company.
- Related decision memory.
- Outcome status.
- Outcome summary.
- Outcome metrics when available.
- Positive effects.
- Negative effects.
- Unintended consequences.
- Follow-up needed.
- Outcome timestamp.

Outcome memory should allow NAWA to learn from results, not only from recommendations.

### Evidence and Source Links

OME must preserve traceability.

Minimum source links:

- `operational_event` links.
- `operational_situation` links.
- File links when available.
- Raw input links when available.
- Structured draft links when available.
- Reasoning output links when available.
- Human decision links.
- Outcome links.

No durable memory should exist without at least one source link or an explicit human-entered memory reason.

---

## 5. Proposed app/ome Structure

This is a proposed future application structure only. It should not be implemented until the MVP implementation phase explicitly starts.

```text
app/
  ome/
    __init__.py
    models/
      __init__.py
      memory_record.py
      situation_memory.py
      decision_memory.py
      outcome_memory.py
      memory_source_link.py
    repositories/
      __init__.py
      memory_repository.py
      situation_memory_repository.py
      decision_memory_repository.py
      outcome_memory_repository.py
      source_link_repository.py
    services/
      __init__.py
      organizational_memory_service.py
      situation_memory_service.py
      decision_memory_service.py
      outcome_memory_service.py
      memory_retrieval_service.py
      historical_baseline_service.py
    policies/
      __init__.py
      memory_capture_policy.py
      memory_retention_policy.py
      memory_visibility_policy.py
```

### organizational_memory_service

Coordinates OME operations internally.

It should accept memory-worthy inputs from NCO and route them to the correct OME service.

### situation_memory_service

Creates durable memory records from operational situations.

It should not create situations. OCE/OIE create situations.

### decision_memory_service

Stores human decisions and links them to situation memory, evidence, and reasoning.

It should not generate recommendations. NCE generates decision options.

### outcome_memory_service

Stores observed outcomes and links them to prior decisions and situations.

It should support future learning loops.

### memory_retrieval_service

Retrieves relevant historical memory for OCE and NCE.

It should return memory as context, not as current truth.

### historical_baseline_service

Builds operational baselines over time.

For Jannat Al-Firdaws, this eventually supports poultry-specific memory such as repeated mortality patterns, production drops, feed/water deviations, and recurring operational bottlenecks.

---

## 6. Proposed Future DB Tables

These are proposed future tables only.

No migrations should be implemented from this document yet.

### ome_memory_records

General durable memory envelope.

Possible columns:

- `id`
- `company_id`
- `division_id`
- `department_id`
- `memory_type`
- `title`
- `summary`
- `status`
- `importance`
- `confidence`
- `memory_date`
- `created_by_user_id`
- `created_by_source`
- `metadata`
- `created_at`
- `updated_at`
- `superseded_at`

Possible `memory_type` values:

- `situation`
- `decision`
- `outcome`
- `lesson`
- `pattern`
- `baseline`
- `institutional_knowledge`

### ome_situation_memories

Durable situation memory detail.

Possible columns:

- `id`
- `memory_record_id`
- `operational_situation_id`
- `situation_type`
- `severity`
- `situation_status_at_capture`
- `time_window_start`
- `time_window_end`
- `affected_departments`
- `evidence_summary`
- `missing_evidence_summary`
- `memory_reason`

### ome_decision_memories

Durable decision memory detail.

Possible columns:

- `id`
- `memory_record_id`
- `situation_memory_id`
- `decision_owner_user_id`
- `decision_owner_role`
- `decision_text`
- `decision_type`
- `chosen_option`
- `rejected_options`
- `rationale`
- `confidence_at_decision`
- `decision_timestamp`
- `requires_follow_up`
- `follow_up_due_at`

### ome_outcome_memories

Durable outcome memory detail.

Possible columns:

- `id`
- `memory_record_id`
- `decision_memory_id`
- `situation_memory_id`
- `outcome_status`
- `outcome_summary`
- `outcome_metrics`
- `positive_effects`
- `negative_effects`
- `unintended_consequences`
- `follow_up_needed`
- `observed_at`
- `recorded_by_user_id`

### ome_memory_source_links

Traceability links between OME memory and source artifacts.

Possible columns:

- `id`
- `memory_record_id`
- `source_type`
- `source_id`
- `source_role`
- `evidence_weight`
- `evidence_quality`
- `created_at`

Possible `source_type` values:

- `operational_event`
- `operational_situation`
- `situation_event`
- `memory_event`
- `memory_fact`
- `raw_input`
- `structured_record_draft`
- `file`
- `file_chunk`
- `ceo_brief`
- `nce_reasoning`
- `human_decision`
- `outcome_observation`

### ome_pattern_memories

Future table for repeated patterns and historical learning.

Possible columns:

- `id`
- `memory_record_id`
- `pattern_type`
- `pattern_signature`
- `related_memory_record_ids`
- `first_seen_at`
- `last_seen_at`
- `occurrence_count`
- `confidence`
- `lesson_summary`

### ome_metric_baselines

Future table for historical operational baselines.

Possible columns:

- `id`
- `company_id`
- `division_id`
- `department_id`
- `entity_type`
- `entity_id`
- `metric_name`
- `baseline_window_start`
- `baseline_window_end`
- `baseline_value`
- `baseline_method`
- `sample_count`
- `confidence`
- `metadata`
- `created_at`
- `updated_at`

For Dairtna Poultry, this can eventually support historical comparison for mortality, production percentage, feed consumption, water consumption, egg weight, and related poultry metrics.

---

## 7. Jannat Al-Firdaws MVP Flow

The MVP memory loop for Jannat Al-Firdaws should follow one simple path:

```text
Situation
    |
    v
CEO Brief
    |
    v
Human Decision
    |
    v
Outcome
    |
    v
Memory
```

### Step 1: Situation

OIE and OCE identify a situation from operational events, poultry reports, manual updates, or future integrations.

Example:

```text
Dairtna production drop detected across a recent reporting window.
```

OME does not detect this situation.

OME waits for NCO to route the memory-worthy situation after OIE/OCE have done their work.

### Step 2: CEO Brief

Executive Intelligence creates a CEO Brief using OCE context and NCE reasoning when readiness allows.

The CEO Brief should explain:

- What happened.
- Why it matters.
- What evidence exists.
- What evidence is missing.
- What decision options exist.
- What confidence NAWA has.

OME does not create the CEO Brief.

OME may later link to it.

### Step 3: Human Decision

An authorized human decision-maker records the decision.

Example:

```text
CEO decides to assign veterinary follow-up and request a feed/water check before changing production assumptions.
```

OME stores the decision memory and links it to the situation, evidence, CEO Brief, and reasoning context.

### Step 4: Outcome

The organization later records what happened.

Example:

```text
Mortality remained normal, feed intake stabilized, and no emergency escalation was needed.
```

OME stores outcome memory and links it to the decision memory.

### Step 5: Memory

OME preserves the full durable memory chain.

```text
Situation memory
    |
    v
Decision memory
    |
    v
Outcome memory
    |
    v
Future retrieval for OCE/NCE
```

In future similar situations, OCE and NCE can retrieve this memory to improve context and reasoning.

OME must present this as historical memory, not current truth.

---

## 8. OME Ownership Rule

OME stores durable organizational memory.

OIE/OCE/NCE do not own long-term memory.

OIE may create operational events.

OCE may create operational context and situation readiness.

NCE may create reasoning, hypotheses, confidence, risks, and decision options.

Executive Intelligence may create CEO-ready outputs.

NCO decides when something should be routed to OME.

OME stores memory only when the system has a memory-worthy artifact:

- A significant situation.
- A human decision.
- An observed outcome.
- A repeated pattern.
- A durable lesson.
- A historical baseline.
- A verified institutional knowledge item.

The memory law is:

```text
Operational signals are not memory by default.
Reasoning is not memory by default.
Recommendations are not memory by default.
Decisions and outcomes become memory when captured with traceable evidence.
```

---

## 9. Migration Philosophy

OME should evolve without breaking the current MVP.

### Keep Now

- Keep `memory_events`.
- Keep `memory_facts`.
- Keep `operational_events`.
- Keep `operational_situations`.
- Keep `situation_events`.
- Keep existing routes and runtime behavior until OME implementation begins.

### Rename Later

- Rename or wrap legacy memory services only after OME service boundaries exist.
- Avoid renaming database tables until compatibility and migration strategy are clear.

### Move Later

- Move durable memory writing out of chat/AI service paths.
- Move decision logging behind OME service boundaries.
- Move memory retrieval behind an OME retrieval contract.

### Build New

- Build OME service layer.
- Build OME repositories.
- Build OME models.
- Build future OME migrations.
- Build memory-source links.
- Build decision and outcome memory capture.
- Build historical baseline retrieval for Dairtna.

---

## 10. MVP Acceptance Criteria

The first OME MVP should be considered successful when NAWA can:

- Store a durable memory record for an operational situation.
- Store a human decision linked to that situation.
- Store an outcome linked to that decision.
- Link memory to operational events and situations.
- Retrieve prior relevant memory for future reasoning.
- Keep historical memory distinguishable from current operational truth.
- Preserve tenant isolation and role visibility.
- Avoid OIE/OCE/NCE owning long-term memory directly.

The first MVP should not attempt broad autonomous learning.

It should prove the memory loop:

```text
Situation -> CEO Brief -> Human Decision -> Outcome -> Memory
```

---

This document is the OME foundation plan for NAWA.

No code, database migration, or runtime implementation is authorized by this document.
