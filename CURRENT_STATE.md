# NAWA – Current State

## Current Product Direction
NAWA is an AI Operational Intelligence Platform and AI Workforce Platform for Arabic companies.

It is not a chatbot and not a traditional ERP.

NAWA acts as the operational intelligence layer inside a company, connecting company knowledge, departments, decisions, events, and AI agents into one execution system.

## Current Stage
MVP Infrastructure Phase.

The project has already passed the basic chat / memory / company workspace foundation and is now moving toward live operational intelligence.

## Completed Systems
- Organizational Intelligence
- Decision Context Engine
- Pattern Detection
- Root Cause Reasoning
- Unified Data Capture
- Company Brain Workspace
- Jannat Al-Firdaws reference environment
- Deployment preparation

## Current Priority
1. Live Operational Timeline
2. Intelligence Event Correlation
3. AI Actions Layer

## Approved Architecture
- FastAPI backend
- PostgreSQL database
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

## Current Focus
Build the Live Operational Timeline as the next core infrastructure layer.

This timeline should capture operational events from all departments and make them available for analysis, correlation, and AI actions.

## Next Immediate Goal
Implement the operational event infrastructure incrementally:

1. Add operational_events data model.
2. Add repository layer with strict company_id filtering.
3. Add service layer for business logic.
4. Add API routes.
5. Add tests or manual curl examples.
6. Preserve existing APIs.
7. Do not modify unrelated systems.

## Next Phase After Timeline
After the timeline is stable, build Intelligence Event Correlation.

This should connect related events across departments and detect operational patterns, risks, bottlenecks, and root causes.

## Future Phase
After event correlation, build the AI Actions Layer.

This layer should allow NAWA to recommend or prepare actions such as:
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
