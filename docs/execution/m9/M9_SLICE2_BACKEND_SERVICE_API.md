# M9 Slice 2 — Backend Service / API

**Priority:** P0. Second slice of M9 — Decision Execution Foundation.
**Owner:** AI Engineering Team (Claude Code).
**Ownership layer:** Repository, domain service, API routes (backend execution-control only — no frontend).
**Repository First Policy compliance:** This task document is filed per the Architecture Contract's own requirement (§28/§32: a task document under `docs/execution/` is required before any slice begins). Filed before implementation work began.

---

## Governance status

| Item | Status |
|---|---|
| M9 — Decision Execution Foundation | **ACTIVE** |
| M9 Architecture Contract | `docs/architecture/NAWA_M9_DECISION_EXECUTION_FOUNDATION_ARCHITECTURE_CONTRACT_v1.md` — v1.6, **FOUNDER ACCEPTED** |
| M9 Slice 1 — Action Persistence Foundation | **CLOSED** (commit `89991dd37799cdea7420ecdcc2ff7df318516cf7`) |
| M9 Slice 2 — Backend Service / API | **ACTIVE — IMPLEMENTATION UNDER REVIEW, NOT CLOSED, NOT COMMITTED** |
| M9 Slice 3 — Frontend Human-Governed Action Recording | **PROPOSED — NOT ACTIVATED** |
| M9 Slice 4 — Golden Path E2E & Hardening | **PROPOSED — NOT ACTIVATED** |
| Starting checkpoint | `89991dd37799cdea7420ecdcc2ff7df318516cf7` (branch `claude-safe-review`) |

## Objective

Implement the repository/service/API layer required to safely operate the Action persistence foundation Slice 1 already closed: create Actions, list/read them, and transition their status/assignee, exactly as specified by Architecture Contract §22 (API Contract Direction) and §24/§24.1 (Concurrency).

## Scope

Per Architecture Contract §28's Slice 2 row and §22's five-endpoint surface:

- `app/ome/repositories/action_repository.py` — `ActionRepository` (create, get_by_id, list_by_decision, list_change_events, change_status, change_assignee).
- `app/ome/services/action_service.py` — `ActionService` (create_action, list_actions, get_action, change_status, change_assignee).
- `app/api/actions.py` — five endpoints: `POST /actions`, `GET /actions`, `GET /actions/{id}`, `PATCH /actions/{id}/status`, `PATCH /actions/{id}/assignee`.
- `app/ome/errors.py` — three new classes: `ActionNotFound`, `InvalidActionTransition`, and (see Architecture Decision below) `InvalidAssignee`.
- `app/main.py` — router registration, after `outcomes_router` per §22.
- Focused tests: `tests/test_m9_slice2_action_service_api.py`.
- This task document and minimum governance updates (`CURRENT_STATE.md`, `EXECUTION_BOARD.md`, `EXECUTION_INDEX.md`).

**Not in scope** (per §27/§28 and this activation's explicit exclusion list): frontend, Slice 3, Slice 4, `due_at`, `priority`, `tags`, `failed` status, `OutcomeMemory.action_id`, OM retrieval, Operational Event emission, Company Brain mutation, Track A/B, automation, AI assignment/prefill, migration 016.

## Architecture Decision (flagged, not a blocker)

**One error class beyond the two the contract names.** §22 says: *"extend `app/ome/errors.py` minimally — `ActionNotFound`, `InvalidActionTransition`."* Neither of those two fits the case where a target `assigned_user_id` fails §11.3 validation (nonexistent user / no active membership / cross-company membership) — that case must resolve to a generic 404 (§11.3), distinct from both "the Action wasn't found" and "the transition is a conflict." Reusing `ActionNotFound` for an assignee problem would be semantically wrong and would break the codebase's existing one-class-per-concern convention (`ReceiptNotFound`/`DecisionNotFound`/`OutcomeNotFound` are each entity-specific). A third class, `InvalidAssignee`, was added — same HTTP mapping (404), same generic-safe non-disclosure behavior, correctly named. This is a naming-precision addition, not a scope or semantic change: no new validation rule, no new endpoint, no new field. Flagged here per the activation's own instruction to report any architecture ambiguity before proceeding, though it did not block implementation.

**GET /actions/{id} history inclusion.** §22 states the endpoint returns "one action, optionally with its status history" without specifying a query-parameter mechanism anywhere in the contract. Implemented as: the response always includes the full chronological `events` list (no `?include_history=` toggle invented) — the simplest reading consistent with the contract's own emphasis (§29 acceptance criterion 13) that "who changed what and when" must be reconstructible from persisted rows in one chronological read.

## Domain Laws Preserved (Architecture Contract Sec 3–19)

- Action belongs to exactly one company; DecisionMemory and Action share a company (validated in the service before any write).
- `decision_memory_id`, `company_id`, `created_by_user_id`, `title`, `instructions` are immutable after creation — no generic `PATCH /actions/{id}` exists.
- Only `status` and `assigned_user_id` mutate, each through its own purpose-named endpoint.
- No hard delete endpoint exists.
- No `OutcomeMemory.action_id`, no OM retrieval change, no Operational Event emission, no Company Brain mutation, no AI assignment, `due_at`, or `failed` status.
- No sequence/version field added.

## Status Vocabulary and Transition Matrix (unchanged from Slice 1)

`pending`, `in_progress`, `completed`, `cancelled`. Allowed: `pending→in_progress`, `pending→completed`, `pending→cancelled`, `in_progress→completed`, `in_progress→cancelled`. Terminal (`completed`, `cancelled`) never transitions again, including reopening. Self-transitions rejected. All enforced in `ActionRepository.ALLOWED_STATUS_TRANSITIONS`, applied against the row read under `SELECT ... FOR UPDATE` — never a client-supplied prior status.

## Concurrency / Atomicity (Architecture Contract Sec 24 / 24.1)

- `ActionRepository.create` — Action row, initial status event (`NULL→pending`), and (if assigned) initial assignment event (`NULL→assigned_user_id`) are written in one transaction; membership validation for a non-null initial assignee also runs inside that same transaction.
- `ActionRepository.change_status` and `ActionRepository.change_assignee` — both lock the Action row (`SELECT ... FOR UPDATE`) before reading current state, mirroring `DecisionMemoryRepository.supersede_with_new_decision`'s proven pattern exactly. `from_status`/`from_assigned_user_id` are read from the locked row only, never from client input. A rejected mutation writes no event and makes no row change (proven by dedicated tests).
- Membership validation (`MembershipRepository.get_active_membership`) is invoked with the transaction's own connection (`MembershipRepository(conn)`), not a separate pool connection — keeping the whole sequence inside one atomic unit exactly as §24.1 specifies.

## Authorization / Tenancy

Reuses the existing `memory.write` permission (no new permission introduced), matching `app/api/decisions.py`/`app/api/outcomes.py` exactly. `company_id` and the acting user identity are always JWT-derived (`AuthContext`), never client-supplied. Every repository read/write is company-scoped; a cross-company Action, Decision, or assignee resolves to a generic 404 with no existence disclosure (Founder Correction 3, unchanged).

## Tests

`tests/test_m9_slice2_action_service_api.py` — 50 tests, all passing against the live `nawa-postgres` instance: Action creation (unassigned/assigned, initial ledger events, no fake NULL→NULL event, cross-company/nonexistent decision rejection, blank-title rejection, one-decision-many-Actions), assignee validation (active/suspended/no-membership/cross-company/unassigned), the full status-transition matrix plus self-transition and terminal-reopen rejection, assignment mutation (NULL↔user, user↔user, no-op and terminal rejection), tenancy isolation at both the service and HTTP layer, atomicity (rejected mutations write zero events), locked-row concurrency-semantics evidence (sequential transitions/reassignments prove `from_status`/`from_assigned_user_id` always reflect the row's real prior state, never a stale value), a full HTTP golden path (`POST → GET list → GET detail with history → PATCH status → PATCH assignee → terminal → rejected reopen/reassign`) plus 403/422/404 status-code mapping, **genuine transaction-rollback tests** for creation/status/assignment (a test-only connection wrapper injects a failure into the change-event `INSERT` after the real row mutation, inside the real transaction, proving asyncpg's own rollback — not a mock of the repository), and **server-derived-field injection tests** (`company_id`, `created_by_user_id`, initial `status`, `changed_by_user_id` all rejected with 422 and zero mutation/event side effects). `assigned_user_id` on `PATCH /actions/{id}/assignee` is a required (non-defaulted) nullable field — an omitted body (`{}`) is 422; an explicit `{"assigned_user_id": null}` remains a valid unassign. An autouse module fixture resets the shared `app.state.auth_db_pool`/`ai_engine` binding before *and* after every test in this file (not just before each HTTP call, which `_with_permission` already did) — closing a test-isolation gap where the last HTTP call in a test left a pool bound to that test's own (about-to-close) event loop for the next test in the suite to inherit and fail on.

## Migration Safety

`migrations/015_decision_execution_foundation.sql` was **not modified**. No new migration was required — Slice 1's schema (`ome_actions`, `ome_action_change_events`) is sufficient for every Slice 2 operation.

---

## Execution Result

**Status:** Implementation complete, focused tests passing, **under review — not closed, not committed**.
**Started:** 2026-09-01 (Founder Slice 2 activation).
**Commit(s):** None — working tree only, per explicit "do not stage/commit/push" authorization scope.
**Reviewer:** Pending independent pre-commit review.
**Validation:** 50/50 focused Slice 2 tests passing (repository/service + HTTP API layers, including genuine rollback and server-derived-field-injection coverage added in a targeted correction pass) against the live `nawa-postgres` instance. Relevant M8/M9 regression (Decision API, Outcome API, Slice 1 models/schema): 165/165 passing. A subsequent test-isolation correction pass fixed an ordering-dependent full-suite failure in an unrelated file (`tests/test_tenant_isolation.py`) caused by this file's HTTP tests leaving a stale `app.state.auth_db_pool` binding behind — see the corresponding evidence reports for exact full-suite counts at each pass.
**Follow-up:** Slice 3 (Frontend) remains `PROPOSED — NOT ACTIVATED` and requires its own explicit Founder activation and task document.
**Notes:** This slice does not close until independent review passes and the Founder authorizes staging/commit. Migration 015 remains byte-identical to its Slice 1 closure state; checksum unchanged.
