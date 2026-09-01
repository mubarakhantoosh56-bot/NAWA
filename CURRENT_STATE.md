# NAWA – Current State

## Current Execution Status (authoritative — updated 2026-09-01)

This block is the authoritative current-state summary required by
`docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md` §4. It supersedes nothing
below it — the Phase 2A / Dairtna narrative that follows remains valid
historical and contextual material. Full engineering-track detail and
reasoning are preserved in `docs/execution/M8_OME_RECONCILIATION.md`; this
block is a pointer/summary, not a duplicate.

- **M8 (Organizational Memory Engine):** CLOSED.
- **ReasoningReceipt validation hardening (Post-M8):** CLOSED.
- **M1–M8 documentation reconciliation:** CLOSED.
- **Verified remote push checkpoint:** COMPLETED and CLOSED — commit
  `4e1650e957f8c6d337ec43adef014aa9411aed17` confirmed identical between local
  `claude-safe-review` and live `origin/claude-safe-review` (divergence 0/0).
  This checkpoint includes the Deferred Architecture Pack v1.3 and the M9
  Architecture Contract through its v1.3 Founder-acceptance amendment.
- **Sprint EX-1 — Executive Decision Support:** PAUSED — requires explicit
  Founder reactivation.
- **Next milestone:** M9 — Decision Execution Foundation — **ACTIVE.**
  Architecture Contract v1.3 — **FOUNDER ACCEPTED** at the closed remote
  checkpoint above; a v1.4 amendment (Slice 1 activation + persistence
  precision) is **committed locally** in commit
  `09ac78d56e64c36263f5d3f4d0120904503b88a1` — **not yet pushed**
  (`docs/architecture/NAWA_M9_DECISION_EXECUTION_FOUNDATION_ARCHITECTURE_CONTRACT_v1.md`).
  **M9 Slice 1 — Action Persistence Foundation is CLOSED.** Implementation
  committed locally at `09ac78d56e64c36263f5d3f4d0120904503b88a1` (parent
  `4e1650e957f8c6d337ec43adef014aa9411aed17`, subject "M9 Slice 1: add action
  persistence foundation"): migration 015 (`ome_actions`,
  `ome_action_change_events`, checksum
  `aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a`) plus
  `Action`/`ActionChangeEvent` domain models — no repository, service, API, or
  frontend, per the contract's own Slice 1 scope. Closure basis: 36/36 live
  PostgreSQL M9 schema tests, 48/48 DB-independent M9 tests, 1092/1092 full
  backend regression suite (0 failed/skipped/errors), and independent
  post-commit chain verification — all PASS. **The local M9 commit chain
  (`09ac78d` → `d0e5082` → `c30fd22` → `743cc2f`) has NOT been pushed;** live
  `origin/claude-safe-review` remains at the prior checkpoint until the
  Founder authorizes a push (live ahead/behind divergence is verified
  directly from Git at review time, not persisted here as a numeric count).
  Slices 2–4 remain **PROPOSED — NOT ACTIVATED**; Slice 1's closure does not
  activate any of them. See `docs/execution/m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md`.
- **Full EBD-004 compliance:** NOT ESTABLISHED — lifecycle/bounded-growth
  governance for durable OME storage remains unresolved.
- **OME lifecycle / bounded-growth governance:** DEFERRED.
- **Durable Situation Memory:** DEFERRED — NOT MVP BLOCKING.

See `docs/execution/M8_OME_RECONCILIATION.md` for the full reconciliation
record and `docs/execution/EXECUTION_BOARD.md` for the live execution tracker.

## Current Product Direction
NAWA is an AI Operational Intelligence Platform and AI Workforce Platform for Arabic companies.

It is not a chatbot and not a traditional ERP.

NAWA acts as the operational intelligence layer inside a company, connecting company knowledge, departments, decisions, events, and AI agents into one execution system.

## Current Stage
MVP Infrastructure Phase — **Operational Feedback Loop active (Phase 1 complete); Dairtna ingestion surface live at MVP level; Phase 2A first executable grounding layer shipped**.

The project has passed the basic chat / memory / company workspace foundation, established the first working layer of live operational intelligence (events captured, structured, grouped into situations end-to-end), and now has a Dairtna-first ingestion UI in place to begin collecting real operational signal. Phase 2A grounding work and ingestion implementation are running in parallel.

The first Phase 2A executable milestone is now in place: uploaded Dairtna XLSX field reports are parsed, interpreted against provisional poultry-domain thresholds, and injected as calibrated operational signals into CEO reasoning — replacing generic FMCG escalation with domain-grounded signal levels. This is Dairtna-only and Phase 1 scope; thresholds are provisional and require field validation.

## Completed Systems
- Organizational Intelligence
- Decision Context Engine
- Pattern Detection
- Root Cause Reasoning
- Unified Data Capture
- Company Brain Workspace
- Jannat Al-Firdaws reference environment
- Deployment preparation
- **Operational Timeline Infrastructure** *(Phase 1)*
- **Operational Situations Foundation** *(Phase 1)*
- **Jannat Al-Firdaws Reference Environment — operational seeding wired** *(Phase 1)*
- **PostgreSQL + pgvector local infrastructure** *(Phase 1)*
- **Rule-based operational grouping** *(Phase 1)*
- **Reference operational event seeding** *(Phase 1)*
- **Dairtna manual structured event forms** — `mortality_report`, `feed_issue`, `veterinary_issue` submitting to `POST /operational-events` *(Phase 2A — MVP)*
- **Natural operational capture** — low-friction "what happened today?" input writing to `POST /operational-events` with `entry_mode=natural_operational_capture` and `needs_classification=true` *(Phase 2A — MVP)*
- **Operational awareness panel** — read-only surface over `GET /operational-events` and `GET /situations`: recent events, items needing classification, missing-info hints, latest situations *(Phase 2A — MVP)*
- **Scoped i18n foundation** — namespaced dictionaries; Dairtna workspace operational UI migrated; AR/EN switching improved; RTL/LTR preserved *(Phase 2A — MVP)*
- **Local dev stabilization** — Docker Postgres + pgvector on `localhost:5433`, FastAPI on `127.0.0.1:8000`, Next.js on `localhost:3000`, dev origin fix for `127.0.0.1` *(Phase 2A — MVP)*
- **Dairtna Operational Interpretation Layer — Phase 1** *(Phase 2A — Grounding)*
  - Stateless mortality interpreter: `app/services/dairtna/interpreter.py` — no DB dependency, stdlib-only, < 1ms
  - Signal calibration against provisional poultry-domain thresholds: `normal / watch / warning / critical / unknown`
  - Mortality rate computed from uploaded draft summaries (`deaths / flock_size × 100`)
  - CEO-response grounding constraints injected before executive reasoning — prevents unsupported escalation for normal-range mortality
  - `_operational_response_missing_elements` skips "bottleneck" requirement when all signals are within normal range
  - Dairtna-only, Phase 1 scope; thresholds provisional; requires field validation before treating as authoritative
  - **Interpretation doctrine** committed: `docs/nawa_brain/DAIRTNA_OPERATIONAL_INTERPRETATION.md`

## Architecture Evolution
The operational data flow has evolved into a layered pipeline:

```
Unified Data Capture
   → Operational Timeline
      → Operational Situations
         → (future) Correlation Intelligence
            → (future) AI Actions Layer
```

Layer responsibilities:

- **Unified Data Capture** — ingests raw inputs from chat, files, structured forms, and (future) integrations into a normalized event representation.
- **Operational Timeline** — chronological, company-scoped record of operational events with classification, source, and entity metadata.
- **Operational Situations** — grouping of related events into situations using rule-based clustering. Implemented in Phase 1.
- **Correlation Intelligence (future)** — cross-department reasoning, signal correlation, hypothesis evaluation. Not started.
- **AI Actions Layer (future)** — tiered actions (alerts → recommendations → guarded autonomous actions). Not started.

## Operational Intelligence Philosophy
These principles govern every decision in the next phases:

- **Proof of mechanism ≠ proof of intelligence.** A working pipeline that produces events and situations only proves the plumbing works. It does not mean NAWA understands the company.
- **NAWA must learn operational reality before autonomous intelligence.** Real density, real entities, real causality from the reference environment come *before* any autonomous decisioning is built.
- **Situation clustering is not yet true intelligence.** Current grouping is rule-based and shallow. It is a substrate, not cognition.
- **Operational hypotheses are preferred over generic correlations in early phases.** Domain-grounded, falsifiable hypotheses (e.g. "mortality rise + feed drop ⇒ health issue") produce higher-signal output than open-ended pattern mining on sparse data.

## Current Operational Validation Results
Phase 1 end-to-end run:

- **8 operational events seeded** into the timeline.
- **1 operational situation created successfully** via rule-based grouping.
- **Grouping flow validated end-to-end** — ingestion → timeline → situation creation works without manual intervention.

Phase 2A ingestion surface (Dairtna):

- **Manual structured forms** wired to the events API and accepting submissions.
- **Natural capture** wired and tagging entries with `needs_classification=true` for later processing.
- **Awareness panel** rendering recent events, classification queue, missing-info hints, and latest situations from existing endpoints.

This validates the mechanism and the human-facing ingestion path at MVP level. It does not yet validate operational intelligence quality, which requires real data density and classification of natural-capture entries.

Phase 2A grounding interpreter (Dairtna, Phase 1):

- **Real uploaded Dairtna XLSX reports now produce grounded operational interpretation** — mortality figures from field reports are parsed, rates computed, and classified against provisional thresholds before reaching CEO reasoning.
- **Mortality rate validation working** — 12 deaths / 77,005 birds → 0.016% → `signal_level: normal`; 18 deaths / 77,023 birds → 0.023% → `signal_level: normal`. Both correctly classified without triggering false escalation.
- **Generic unsupported escalation reduced** — CEO response no longer frames normal-range mortality as a production bottleneck or financial crisis. "عنق زجاجة" (bottleneck) and "أزمة" (crisis) absent from normal-signal responses.
- **AI now distinguishes normal-range mortality from operational crisis** — signal level is computed deterministically from threshold, not inferred from generic FMCG logic.
- *This does not constitute full operational intelligence. Thresholds are provisional, only mortality is implemented, and multi-signal correlation has not started.*

## Infrastructure State
- **Docker + pgvector local environment active** — Postgres on `localhost:5433`.
- **FastAPI backend** on `127.0.0.1:8000`; **Next.js frontend** on `localhost:3000`; dev-origin allowance for `127.0.0.1` in place.
- **Migrations validated through 010** — schema for events, situations, and supporting tables is in place and reproducible.
- Backend, repository, and service layers conform to the approved architecture (company_id isolation, async-first, route → service → repository).
- **Scoped i18n foundation** in the frontend — namespaced dictionaries, Dairtna operational UI migrated, AR/EN switching improved, RTL/LTR preserved.
- **Dairtna interpreter runtime** — deterministic operational signal blocks computed and injected before executive reasoning on every CEO chat request; no DB dependency in Phase 1; regex + provisional threshold layer operating at < 1ms; `app/services/dairtna/` package in place for future metric expansion.

## Known Current Limitations
Honest tracking of what is in motion but not yet production-quality. Not a roadmap — a status list.

1. **OperationalInputPanel upload/save needs cleanup.** File upload backend route exists, but the UI upload/save path is not fully reliable; mixed Arabic/English labels remain inside the panel.
2. **No AI classification yet.** Natural-capture entries are persisted with `needs_classification=true` but are not yet processed downstream.
3. **No correlation engine yet.** Phase 2B has not started.
4. **No autonomous AI actions yet.** Per the explicit warning below.
5. **Natural capture is store-only.** Raw notes are saved without enrichment, classification, or entity resolution.
6. **Structured panels and output panels are Dairtna-first and MVP-level.** No Caesar coverage, no refinement passes.
7. **Dairtna interpreter thresholds are provisional.** All mortality thresholds (< 0.05% normal, etc.) are based on general poultry industry ranges. They have not been validated against actual Jannat Al-Firdaws field data. Must be reviewed with the Dairtna field manager before treating as authoritative.
8. **Only mortality rate implemented in Phase 1.** Production percentage, feed consumption, water trend, and egg weight / size distribution are specified in the doctrine doc but not yet wired into the interpreter.
9. **No historical baseline memory yet.** The interpreter computes signal from a single reading. It cannot compare against the company's own prior readings or detect sustained trends across days.
10. **No multi-signal correlation yet.** Compound conditions (e.g., mortality `watch` + feed `watch` → veterinary flag) are documented in the doctrine but not implemented. Phase 2B.
11. **No seasonal or breed-specific calibration.** Thresholds apply uniformly regardless of flock age, breed type, or season. These factors affect expected ranges and will require per-flock configuration in a future phase.

## Current Priority
**Phase 2A — Operational Intelligence Grounding** (next).

Phase 2A is a *grounding* phase, not an engine-building phase. Its purpose is to make Phase 2B (Correlation Intelligence) viable when it begins.

### Phase 2A Goals
1. **Data ingestion strategy** — define how real operational data from Jannat Al-Firdaws (Dairtna fields first, Caesar later) enters NAWA: source priority, sequencing, format normalization, manual vs. automated paths.
2. **Operational taxonomy** — formalize event types, entity types, departments, severity, and lifecycle states. A consistent taxonomy is a prerequisite for meaningful correlation.
3. **Signal quality standards** — minimum fields, freshness, source confidence, and validation rules each event must meet before it counts as a "signal" eligible for correlation.
4. **Department dependency graph** — explicit model of how departments influence each other (HR → Production, Production → Sales, Veterinary → Production, etc.), with edge weights and direction. This is the spine for cross-department reasoning.
5. **Correlation hypothesis library** — seed library of domain-grounded operational hypotheses for the poultry environment (mortality patterns, feed/water deviations, production drops, distribution delays, etc.). Each hypothesis carries trigger conditions, expected signal pattern, and recommended action class.
6. **Confidence scoring philosophy** — define how NAWA expresses certainty: scoring scale, evidence requirements, calibration approach, and how confidence propagates from event → situation → correlation → action.

## Explicit Warning
**Do NOT begin AI Actions implementation before all of the following are in place:**

1. **Operational grounding** — taxonomy, dependency graph, and hypothesis library are defined and reviewed.
2. **Confidence framework** — every AI-produced insight must carry a defensible confidence value with traceable evidence.
3. **Sufficient real operational density** — enough real, structured events from Jannat Al-Firdaws to make correlations and recommendations statistically and operationally meaningful.

Building AI Actions on top of sparse data, undefined confidence, or ungrounded taxonomy will produce confident-sounding but unreliable output. This is the single highest-risk failure mode for NAWA and must be avoided.

## Approved Architecture
- FastAPI backend
- PostgreSQL database (with pgvector)
- Multi-tenant SaaS architecture
- Company-scoped memory
- Route → Service → Repository → Database pattern
- Strict company_id isolation
- JWT company_id as the source of truth
- Async-first implementation
- Pydantic request/response models

## Non-Negotiable Rules
- Do not reset the product vision.
- Do not rebrand NAWA back to AIMX.
- AIMX is legacy reference only.
- Every database query must filter by company_id.
- Never trust company_id from request body without validating against JWT.
- Never put business logic inside API routes.
- Never bypass the repository layer.
- Do not introduce overengineering unless required.
- Preserve existing APIs unless explicitly approved.

## Product Philosophy
NAWA should help company leaders understand what is happening, why it is happening, what it affects, and what should happen next.

The system should move from:
Data → Context → Pattern → Root Cause → Decision → Action.

## Future Phase
After Phase 2A grounding and Phase 2B Correlation Intelligence are validated, build the **AI Actions Layer** in tiers:

- **Tier 1** — Smart alerts with full context and confidence.
- **Tier 2** — Recommended actions with pre-filled workflows, human-approved execution.
- **Tier 3** — Guarded autonomous actions with audit trail and rollback.

Tier 1 must precede Tier 2. Tier 2 must precede Tier 3. No tier may launch before its grounding prerequisites are met.

Possible action types (future scope only):
- notify CEO
- create task
- request missing data
- generate report
- recommend decision
- draft internal message
- escalate operational issue

## Claude / Codex Role
Claude and Codex are engineering execution layers only.

They should implement approved architecture, not redefine product strategy.

Before coding, they must:
1. Read Agent.MD
2. Read CLAUDE.md
3. Read CURRENT_STATE.md
4. Read relevant architecture docs
5. Show implementation plan
6. Wait for approval if the change is risky

## Strategic Owner
The product direction, architecture decisions, roadmap, and prioritization are decided outside the coding agent before implementation.

AI coding agents should execute only the approved scope.