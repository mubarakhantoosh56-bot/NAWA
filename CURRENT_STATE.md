# NAWA – Current State

## Current Product Direction
NAWA is an AI Operational Intelligence Platform and AI Workforce Platform for Arabic companies.

It is not a chatbot and not a traditional ERP.

NAWA acts as the operational intelligence layer inside a company, connecting company knowledge, departments, decisions, events, and AI agents into one execution system.

## Current Stage
MVP Infrastructure Phase — **Operational Feedback Loop active (Phase 1 complete); Dairtna ingestion surface live at MVP level**.

The project has passed the basic chat / memory / company workspace foundation, established the first working layer of live operational intelligence (events captured, structured, grouped into situations end-to-end), and now has a Dairtna-first ingestion UI in place to begin collecting real operational signal. Phase 2A grounding work and ingestion implementation are running in parallel.

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

## Infrastructure State
- **Docker + pgvector local environment active** — Postgres on `localhost:5433`.
- **FastAPI backend** on `127.0.0.1:8000`; **Next.js frontend** on `localhost:3000`; dev-origin allowance for `127.0.0.1` in place.
- **Migrations validated through 010** — schema for events, situations, and supporting tables is in place and reproducible.
- Backend, repository, and service layers conform to the approved architecture (company_id isolation, async-first, route → service → repository).
- **Scoped i18n foundation** in the frontend — namespaced dictionaries, Dairtna operational UI migrated, AR/EN switching improved, RTL/LTR preserved.

## Known Current Limitations
Honest tracking of what is in motion but not yet production-quality. Not a roadmap — a status list.

1. **OperationalInputPanel upload/save needs cleanup.** File upload backend route exists, but the UI upload/save path is not fully reliable; mixed Arabic/English labels remain inside the panel.
2. **No AI classification yet.** Natural-capture entries are persisted with `needs_classification=true` but are not yet processed downstream.
3. **No correlation engine yet.** Phase 2B has not started.
4. **No autonomous AI actions yet.** Per the explicit warning below.
5. **Natural capture is store-only.** Raw notes are saved without enrichment, classification, or entity resolution.
6. **Structured panels and output panels are Dairtna-first and MVP-level.** No Caesar coverage, no refinement passes.

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