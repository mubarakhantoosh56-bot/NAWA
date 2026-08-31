# M9 Slice 1 — Action Persistence Foundation

**Priority:** P0. First slice of M9 — Decision Execution Foundation.
**Owner:** AI Engineering Team (Claude Code).
**Ownership layer:** Persistence (migration + domain models only).
**Repository First Policy compliance:** This document is filed retroactively relative to the code — Slice 1 implementation began under explicit Founder activation before this task document existed. It is created now, before commit, to close that governance gap per the Architecture Contract's own requirement (§28: "No slice may begin without explicit Founder activation **and a task document** under `docs/execution/`"; §32: "a new `docs/execution/m9/` task folder (required before any slice begins)"). No further Slice 1 work occurs without this document existing; it is a precondition for review and commit, not merely a record of what already happened.

---

## Governance status

| Item | Status |
|---|---|
| M9 — Decision Execution Foundation | **ACTIVE** |
| M9 Architecture Contract | `docs/architecture/NAWA_M9_DECISION_EXECUTION_FOUNDATION_ARCHITECTURE_CONTRACT_v1.md` — **FOUNDER ACCEPTED** |
| M9 Slice 1 — Action Persistence Foundation | **ACTIVE — IMPLEMENTATION VALIDATED / UNDER INDEPENDENT REVIEW / NOT CLOSED** |
| M9 Slice 2 — Repository, Domain Service & API | **PROPOSED — NOT ACTIVATED** |
| M9 Slice 3 — Frontend Human-Governed Action Recording | **PROPOSED — NOT ACTIVATED** |
| M9 Slice 4 — Golden Path E2E & Hardening | **PROPOSED — NOT ACTIVATED** |
| Starting checkpoint | `4e1650e957f8c6d337ec43adef014aa9411aed17` (branch `claude-safe-review`) |

## Objective

Implement the minimum durable persistence foundation for M9 Decision Execution: current Action execution state, and an immutable append-only Action change ledger (status transitions + assignment changes), per the Founder-accepted Architecture Contract's Option M9-2 (architecture substance ratified through v1.3, Founder-acceptance amendment, remote checkpoint closed at `4e1650e957f8c6d337ec43adef014aa9411aed17`; a v1.4 status-only amendment recording Slice 1's activation exists on disk, uncommitted).

## Scope

Per Architecture Contract §28's own Slice 1 row:

> "Migration 015 (two additive tables incl. nullable `assigned_user_id` and the discriminated change ledger, constraints, indexes); `app/ome/models/action.py`, `action_change_event.py`. **No repository, service, API, or wiring — mirroring M8 Slice 1 exactly**."

This governs scope over the broader activation prompt's "allowed" list (which permitted, but did not require, repositories/transaction primitives). Implemented:

- `migrations/015_decision_execution_foundation.sql` — `ome_actions`, `ome_action_change_events`.
- `app/ome/models/action.py` — `Action` domain model.
- `app/ome/models/action_change_event.py` — `ActionChangeEvent` domain model.
- `app/ome/models/__init__.py` — additive exports only.
- Focused unit + schema-contract tests.
- This task document, `CURRENT_STATE.md`, `docs/execution/EXECUTION_BOARD.md`/`EXECUTION_INDEX.md`, and a narrow status-only amendment to the Architecture Contract itself — the minimum governance-truthfulness updates the contract requires on activation.

**Not in scope** (deferred to later slices, per §27/§28): repository, domain service, API routes, frontend, `due_at`, `failed`, `OutcomeMemory.action_id`, OM retrieval change, Operational Event emission, Company Brain mutation, any automation, Track A/B activation, durable OME registry.

## Expected Deliverable

Migration 015 (reviewed, corrected, applied to and live-local validated against the existing project-local `nawa-postgres` PostgreSQL 16 / pgvector development instance — not yet committed, not yet pushed, not applied to any production or shared database), `Action`/`ActionChangeEvent` domain models with CHECK-mirroring `__post_init__` validation, and passing focused tests — ready for independent review before commit.

## Dependencies

Migration 014 (`ome_decision_memories`, `ome_reasoning_receipts`) — composed against tenant-safely, unmodified.

## Blockers

None. (See Persistence Correction Log below for issues found and resolved during this slice.)

## Acceptance Criteria (Architecture Contract §28 exit condition)

- Migration applies cleanly and is reproducible.
- Models round-trip `from_row`/`to_dict`.
- Every CHECK re-validated in Python, including the change-event shape CHECK.
- Cross-company decision FK insert rejected by the database in a test.

## Persistence Correction Log

**Pass 1.** A first implementation pass was completed and self-reported as "ready for independent review." A correction pass identified and resolved nine issues before this document was created:

1. **Governance state incomplete** — this document, plus `CURRENT_STATE.md` and Architecture Contract status-only amendment, added.
2. **`from_status` had no database CHECK** — added `chk_ome_action_change_events_from_status`, mirroring the pre-existing `to_status` CHECK and the model's pre-existing (already-correct) Python validation.
3. **`changed_at` used `NOW()`** (transaction-start time, which risked a specific audit-order inversion under row-locked concurrent writers) — changed to `clock_timestamp()` (statement-execution time), removing that specific inversion risk. Rationale documented in the migration's header comment.
4. **Ledger shape CHECKs re-reviewed** — confirmed already correct (discriminated union, `IS DISTINCT FROM` no-op guard); no change needed beyond item 2.
5. **Initial-event semantics** — confirmed the schema correctly does *not* attempt to enforce "creation event must be `NULL → pending`" at the CHECK level (a CHECK cannot see sibling rows); documented this as an explicit Slice 2 write-path responsibility, not a schema gap.
6. **Timeline ordering** — added an `id` tie-break to the chronological-read test for deterministic *display* ordering only, with an explicit code comment distinguishing that from real-time insertion order. No UUID-as-sequence claim made anywhere.
7. **Index review** — all five indexes confirmed individually justified by Architecture Contract §21.4's own named access paths (including `idx_ome_actions_company_assigned_user`, which §21.4 explicitly names as MVP-required for "what am I responsible for"); none removed, none speculative.
8. **Append-only overclaim** — migration header and model docstrings corrected to state plainly that append-only is an architecture/domain invariant enforced at the repository/service layer once one exists, not a database trigger/REVOKE at this slice.
9. **Test-result overclaim** — schema-contract tests against a live Postgres were not executable in this environment (`localhost:5433` unreachable); reported honestly as `WRITTEN — NOT EXECUTED SUCCESSFULLY DUE TO UNREACHABLE LOCAL POSTGRES`, not as passed.

**Pass 2 (independent Codex re-review).** A further pass identified and resolved five more issues:

10. **`clock_timestamp()` still overclaimed as causally guaranteed** — prior wording ("observes a strictly later wall-clock value," "causally correct," "guarantee") implied a strict monotonic sequence. Corrected in the migration header/column comment, both schema-test docstrings (`test_full_status_and_assignment_ledger_chronological_read`, `test_changed_at_uses_statement_time_not_transaction_start`), and this document: `clock_timestamp()` removes one specific, identified inversion risk (transaction-start time) and improves audit-time fidelity; it is **not** a strict monotonic causal sequence — wall-clock steps backward and same-resolution ties remain possible, it is not an Action-local sequence counter, and the ledger's persisted from-state/to-state values (not `changed_at`) are the authoritative audit evidence. No sequence/version/ordinal/Lamport-clock column was added — none is authorized in Slice 1.
11. **Obsolete M8 "no migration 015" tripwires** — found in 7 files (`test_m8_cb_provenance_foundation.py`, `test_m8_slice3a_live_reasoning_receipts.py`, `test_m8_slice3b1_human_decision_api.py`, `test_m8_slice3c1_human_outcome_api.py`, `test_m8_slice4a_organizational_memory_retrieval.py`, `test_m8_slice4b_live_organizational_memory_reasoning.py`, `test_m8_slice4c1_organizational_memory_explainability.py`), each asserting migration 015 must never exist — now obsolete since Slice 1 correctly creates it. Corrected to assert migration 014's continued presence instead (the real M8 invariant), never a claim that no future milestone may add a migration. `test_no_migration_015` renamed to `test_migration_014_still_present` in the four files where that was its only assertion; `test_migrations_still_001_through_014` (already a non-obsolescing name) had only its obsolete inner assertion removed in the other three. All 7 corrected tests pass.
12. **Governance docs claimed "not yet pushed" for an already-closed remote checkpoint** — `EXECUTION_BOARD.md`, `EXECUTION_INDEX.md`, and `CURRENT_STATE.md` described commits `8cdb8d5`/`63aa9ff`/`4e1650e` as local-only. Verified via `git ls-remote` that `origin/claude-safe-review` is in fact `4e1650e957f8c6d337ec43adef014aa9411aed17` — identical to local HEAD, divergence 0/0. Corrected all three documents to state the remote checkpoint is closed at `4e1650e`, and that only the (still-uncommitted) Slice 1 implementation and the Architecture Contract's v1.4 status amendment exist beyond it.
13. **Architecture Contract §28 internally inconsistent** — its per-slice status table still labeled Slice 1 `PROPOSED — NOT ACTIVATED` while the header/§1/§32 said Slice 1 was active. Corrected §28's intro sentence and Slice 1 row's Status column only, to `ACTIVE — IMPLEMENTATION UNDER REVIEW / NOT CLOSED`; Slice 1's scope text and Slices 2–4 rows are unchanged. v1.4's Appendix A entry updated in place (no v1.5 created — the amendment is still uncommitted).
14. **An 8th obsolete migration-frontier tripwire, missed by the initial grep** — found only by running the full suite against a live database: `tests/test_m8_slice1_ome_schema.py::test_migration_014_file_exists_and_is_next_after_013` asserted `files[-1] == "014_organizational_memory.sql"` (014 is the LAST migration file) — a different phrasing of the same obsolete class than item 11's, so it wasn't caught by the `startswith("015")`/`test_no_migration_015` search pattern. Renamed to `test_migration_014_exists_in_contiguous_sequence`; now asserts 014 is present and the full sequence remains contiguously numbered (both real, non-obsolescing invariants), without asserting 014 is the last file. This is direct evidence for why live-suite execution, not pattern search alone, was required before commit.

**Pass 3 (live PostgreSQL validation — completed after Pass 2).** The existing project-local Docker container `nawa-postgres` (PostgreSQL 16, `pgvector/pgvector:pg16`, already the exact target of this repo's own `DATABASE_URL`, previously stopped) was started — not created — and used to validate the corrected implementation end to end:

15. **Migration 015 applied and recorded.** `scripts.migrate.run_migrations()` ran the real repository migration path: 001–014 checksum/integrity validated with no mismatch, 015 applied cleanly, recorded in `schema_migrations` with checksum `aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a` (verified to match the file on disk). A second run confirmed idempotency — no re-application, no checksum mismatch on 001–015.
16. **Live M9 schema-contract suite: 36/36 passed**, including FK/CHECK behavior for both composite tenant-safety FKs, the documented plain-FK assignee trust-boundary gap, every status/`from_status`/`to_status`/discriminated-shape CHECK, terminal-timestamp CHECKs, the initial status/assignment event paths, Decision 1→N Actions, and the `clock_timestamp()` default (including the statement-time-vs-transaction-start proof).
17. **DB-independent M9 suite: 48/48 passed** (unchanged from Pass 2).
18. **Full backend regression suite: 1092/1092 passed, 0 failed, 0 skipped, 0 errors** (two runs — the first surfaced and this pass's own item 14 fixed the one real failure found; the confirmation rerun was clean).

This closes the "not executed" gap left open at the end of Pass 2. Migration 015 remains uncommitted, unpushed, and applied only to this local development/test instance — never to production or shared infrastructure.

---

## Execution Result

**Status:** Implementation complete, corrected across two independent-review passes, live-local validated (Pass 3), **ACTIVE — IMPLEMENTATION VALIDATED / UNDER INDEPENDENT REVIEW — NOT CLOSED**.
**Started:** 2026-08-31 (Founder Slice 1 activation).
**Corrections applied:** 2026-08-31, Pass 1 and Pass 2 (this document's Persistence Correction Log).
**Live validation completed:** 2026-08-31, Pass 3 (this document's Persistence Correction Log).
**Commit(s):** None yet — working tree only, per explicit "do not stage/commit/push" authorization scope.
**Reviewer:** Pending independent review.
**Validation (current, as of Pass 3):** Migration 015 applied to and validated against the existing project-local `nawa-postgres` PostgreSQL 16 / pgvector development instance — 001–014 integrity confirmed, 015 recorded in `schema_migrations` with checksum `aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a`, rerun confirmed idempotent. Live M9 schema-contract suite: **36/36 passed**. DB-independent M9 suite: **48/48 passed**. Full backend regression suite: **1092/1092 passed, 0 failed, 0 skipped, 0 errors**. (Historical note: earlier in this document's own Pass 1/Pass 2 entries, schema tests against a live Postgres were reported as not executable and the full suite showed 280 DB-connectivity failures — that was the true state at that time, before Pass 3's live database became available; it is superseded by the figures in this paragraph, not contradicted by them.)
**Follow-up:** Slice 2 (Repository, Domain Service & API) remains `PROPOSED — NOT ACTIVATED` and requires its own explicit Founder activation and task document.
**Notes:** This slice does not close until independent review passes and the Founder authorizes commit. Pre-commit live-PostgreSQL validation is complete; no further validation is outstanding on that front.
