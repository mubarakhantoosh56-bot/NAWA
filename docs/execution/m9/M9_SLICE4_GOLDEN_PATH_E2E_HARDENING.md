# M9 Slice 4 — Golden Path E2E & Hardening

**Priority:** P0. Fourth and final slice of M9 — Decision Execution Foundation.
**Owner:** AI Engineering Team (Claude Code).
**Ownership layer:** Browser-level acceptance and hardening only. No new product capability.
**Repository First Policy compliance:** This task document is filed per the Architecture Contract's own requirement, alongside the implementation it describes.

---

## Governance status

| Item | Status |
|---|---|
| M9 — Decision Execution Foundation | **ACTIVE** |
| M9 Architecture Contract | v1.6, **FOUNDER ACCEPTED** |
| M9 Slice 1 — Action Persistence Foundation | **CLOSED** |
| M9 Slice 2 — Backend Service / API | **CLOSED — REMOTE CHECKPOINT VERIFIED** |
| M9 Slice 3 — Frontend Golden Path | **CLOSED — REMOTE CHECKPOINT VERIFIED** (commit `de81441089fc97c8403348e5aafbb4206ba3d761`) |
| M9 Slice 4 — Golden Path E2E & Hardening | **ACTIVE — IMPLEMENTED / UNDER REVIEW / NOT COMMITTED / NOT CLOSED** |
| Starting checkpoint | `de81441089fc97c8403348e5aafbb4206ba3d761` (branch `claude-safe-review`) |

## Objective

Prove the full M9 human-governed loop — **AI Recommendation → Human Decision → Action → Responsible Human → Execution State → Change History** — end to end through a real browser against the real frontend and real backend, with no Action/member API mocked. Hardening is limited to defects browser execution actually exposes.

## Discovery

- Playwright config: `frontend/playwright.config.ts` — `testDir: "./e2e"`, no `webServer` (the orchestrator owns server lifecycle), `baseURL` from `E2E_FRONTEND_PORT`, `fullyParallel: false`, `retries: 0`.
- Existing specs: `frontend/e2e/smoke.spec.ts` (health/login smoke) and `frontend/e2e/golden-a.spec.ts` (M7 Slice 3C — real login → real upload → real chat citation grounding; the only precedent "Golden Path" browser test, explicitly stopping short of Decision recording).
- Orchestrator: `scripts/e2e_orchestrator.py` — validates an isolated `E2E_DATABASE_URL` (must contain "e2e", must differ from ambient `DATABASE_URL`), builds the frontend for production, runs migrations, seeds Jannat Al-Firdaws (`scripts/seed_jannat.py`, idempotent — reused unmodified, no new seed data), starts the real backend (`scripts/e2e_backend_app.py`, which swaps only the OpenAI completion seam for a deterministic fake) and real production frontend, then runs Playwright over the whole `e2e/` directory.
- Auth: real UI login only (`/login` form → real `POST /auth/login`) — no token injection, no localStorage seeding, matching `golden-a.spec.ts` exactly.
- Seed data reused unmodified: one company (Jannat Al-Firdaws), one owner user with an active `memory.write`-bearing membership, four departments. No new product-facing or test-only seed behavior was added.
- No new browser framework introduced — reused Playwright exactly as already configured.

## Golden Path browser flow

New spec: `frontend/e2e/m9-slice4-golden-path.spec.ts`. Real login → real upload (reused only as the deterministic path to a real `reasoning_receipt_id`, since the E2E fake AI client requires usable evidence to respond at all — see Hardening below) → real Company Memory chat → real Record Decision (asserts a blank field, no AI prefill) → real Action creation (asserts blank Title/Instructions, real `GET /company/members`, real named-assignee selection, no default-to-self) → real `pending → in_progress` → real assignment cycle (`user → Unassigned → user`, explicit `null` proven, no-op never sent structurally by construction) → real `in_progress → completed` (terminal — asserts every mutation control disappears) → real history (`GET /actions/{id}`, asserts "Initial → Pending" never "Unassigned → Pending", a resolved assignment name, a visible timestamp, and the complete absence of every raw internal id from the rendered text) → real Record Outcome (proves the Outcome path is unaffected by Action work).

**Decision Anchor Law, browser-proven:** before the Decision is recorded, `Create Action` and the `Actions` section are asserted absent while `Record Decision` is present; only after a real `decision_memory_id` comes back from `POST /decisions` does `Create Action` appear. No arbitrary decision UUID is ever injected into UI state — the id used throughout is the one the real response returned.

**Single-member note:** the E2E seed provisions exactly one company member (the owner). Person-to-person reassignment (`user A → user B`) is therefore not exercised in the browser — it is already proven at the component level (`ActionsPanel.test.tsx`: "reassigns user A → user B by selecting a different member") and the backend level (`test_m9_slice2_action_service_api.py`'s assignment-mutation matrix). This spec instead proves the full `Unassigned ↔ user` cycle with the one real seeded member, keeping the browser Golden Path minimal per this activation's own instruction rather than expanding seed infrastructure solely for this one step.

## Real APIs exercised (none mocked)

`POST /auth/login`, `POST /files/upload`, `POST /ai/chat`, `POST /decisions`, `GET /company/members`, `POST /actions`, `GET /actions?decision_memory_id=...`, `PATCH /actions/{id}/status` (×2), `PATCH /actions/{id}/assignee` (×2), `GET /actions/{id}`, `POST /outcomes`. Every one is asserted on real HTTP status and, where relevant, real response/request JSON shape (e.g., the unassign request body is asserted to be exactly `{"assigned_user_id": null}`, never `{}`).

## Hardening

**One real defect found and corrected — E2E test-infrastructure only, no product/domain code touched.**

- **Defect:** the first orchestrator run (all four specs) failed `golden-a.spec.ts` with a citation mismatch (`source_file_id` from a different upload than the one this test run itself made). Root cause: `fullyParallel: false` only serializes tests *within* one spec file — with two upload-dependent spec files now present (`golden-a.spec.ts` and the new Slice 4 spec), Playwright's default worker count (3, observed in the failing run's log: "Running 4 tests using 3 workers") let two spec files run concurrently in separate workers, racing against the E2E fake AI client's documented single-session assumption (`scripts/e2e_fake_ai_client.py`: `_resolve_hall_citation` reads the *last* globally captured decision-debug snapshot, not one scoped per test — its own docstring states this process "serves exactly one Playwright browser session at a time"). This is a real cross-file concurrency defect in the E2E harness, first exposed only once a second upload-using spec existed — not a flake, not a domain/API defect, and not caused by anything in the Action feature itself.
- **Correction (smallest possible):** `frontend/playwright.config.ts` — added `workers: 1`, pinning the whole `e2e/` suite to serial execution across files as well as within them, matching the fake AI client's already-documented assumption exactly. No test file, fixture, seed script, or production code was touched.
- **Regression coverage:** the fix is itself proven by re-running the full four-spec suite three consecutive times after the change — all green each time (see Browser Reliability below). Per this activation's own guidance ("If correction is browser-only integration: the E2E itself may be the regression"), no additional test was written; the corrected, now-reliable multi-spec run is the regression proof.
- **No architecture change.** This was a test-runner concurrency setting, not a database table, migration, endpoint, state, or authorization change. None of the STOP conditions for architecture change were triggered.

No other defect was found. No M9 Slice 1/2/3 production file was modified in this slice.

## Browser reliability

| Run | golden-a.spec.ts | m9-slice4-golden-path.spec.ts | smoke.spec.ts (×2) | Workers |
|---|---|---|---|---|
| 1 (pre-fix) | **FAIL** (citation cross-talk) | pass | pass | 3 |
| 2 (post-fix) | pass | pass | pass | 1 |
| 3 (post-fix) | pass | pass | pass | 1 |
| 4 (post-fix) | pass | pass | pass | 1 |

Three consecutive clean runs after the `workers: 1` correction — no flakiness observed. The new Slice 4 spec itself passed on every single run, including the one where `golden-a.spec.ts` failed from the cross-file race — it was never the source of the instability.

## Frontend validation

- Focused Slice 3 (`ActionsPanel.test.tsx`): **33/33 passing.**
- Relevant Decision/Outcome/Action regression (`src/components/chat`): passing (see prior Slice 3 evidence; unchanged by this slice — no chat-component file was touched).
- Full Vitest: **197/197 passing** (no flake this run).
- `tsc --noEmit`: clean.
- `eslint .` (including the new spec file, explicitly re-checked): clean.
- `next build`: succeeds (all 4 routes prerendered) — both standalone and as part of every orchestrator run.

## Backend validation

- Focused Slice 3 member-source (`test_m9_slice3_company_members_api.py`): **13/13 passing.**
- Relevant Decision/Outcome/Action/Tenant regression (`test_m9_slice1_action_models.py`, `test_m9_slice1_action_schema.py`, `test_m9_slice2_action_service_api.py`, `test_m9_slice3_company_members_api.py`, `test_tenant_isolation.py`, `test_m8_slice3b1_human_decision_api.py`, `test_m8_slice3c1_human_outcome_api.py`): **232/232 passing.**
- Full backend: **Collected 1155, Passed 1155, Failed 0, Skipped 0, Errors 0, Warnings 282** (pre-existing `datetime.utcnow()` deprecation warnings across many pre-M9 files, unrelated to this slice), **Duration 306.46s.**

## Playwright

- Focused Slice 4 spec: passes in isolation and as part of the full suite, 3/3 consecutive clean runs post-fix.
- Existing complete Playwright suite (`smoke.spec.ts` + `golden-a.spec.ts` + new spec, the entire `e2e/` directory as run by `scripts/e2e_orchestrator.py` / `npm run test:e2e`): **4/4 passing**, 3 consecutive clean runs post-fix.
- Generated artifacts (`frontend/playwright-report/`, `frontend/test-results/`, `frontend/e2e/fixtures/`) remain untracked/ignored per existing `.gitignore` — none committed.

## Migration / architecture safety

- Migration 015: **not modified.** Checksum unchanged: `aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a`.
- Migration 016: does not exist.
- Schema: unchanged.
- Action API: unchanged — every endpoint behaves exactly as Slice 2 closed it and Slice 3 consumed it.
- No new Action state, no `OutcomeMemory.action_id`, no autonomous execution, no new authorization model, no new endpoint.

## Scope

No generic Task product, kanban, calendar, `due_at`, priority, tags, subtasks, comments, attachments, notifications, reminders, `failed`/`paused`/`blocked` status, workflow engine, scheduler, automation, external execution (email/WhatsApp/ERP/webhooks), AI Action generation/prefill/assignee-ranking, `OutcomeMemory.action_id`, Operational Event emission, OM retrieval change, Company Brain mutation, Track A/B, SituationMemory, new OME registry, or any post-M9/M10 work was added. Unexpected files: none — the working tree contains exactly the new spec file, the one-line hardening correction to `playwright.config.ts`, this task document, and the three minimum governance updates.

## M9 final acceptance checklist

Every item below is now proven by the combined Slice 1–4 evidence (backend unit/integration tests, frontend component tests, and this slice's real-browser run):

| # | Claim | Status |
|---|---|---|
| A | Human Decision can produce one or more Actions | **Proven** |
| B | Action remains distinct from DecisionMemory | **Proven** |
| C | Action belongs to correct company | **Proven** |
| D | Action belongs to correct DecisionMemory | **Proven** (E2E asserts `decision_memory_id` equality) |
| E | Human responsible person can be selected | **Proven** (E2E: real named selection) |
| F | Assignee must be active same-company member | **Proven** |
| G | Action starts Pending | **Proven** |
| H | Initial status event exists | **Proven** (E2E: "Initial → Pending") |
| I | Initial assignment event exists only when assigned | **Proven** |
| J | Unassigned creation creates no fake assignment event | **Proven** |
| K–O | All five valid status transitions | **Proven** (backend full matrix; E2E exercises `pending→in_progress→completed`) |
| P | Terminal Action cannot reopen | **Proven** (E2E: no status buttons after Completed) |
| Q | Terminal Action cannot be reassigned | **Proven** (E2E: no assignee control after Completed) |
| R | Assignment changes are ledgered | **Proven** |
| S | Status changes are ledgered | **Proven** |
| T | Actor is server-derived | **Proven** |
| U | Company is server-derived | **Proven** |
| V | Ledger is append-only through public API | **Proven** (no generic PATCH, no delete) |
| W | UI displays server-confirmed state | **Proven** (no optimistic updates; E2E waits on real responses) |
| X | UI never exposes raw internal UUIDs as normal labels | **Proven** (E2E: explicit absence assertions) |
| Y | Actions remain Decision-anchored | **Proven** (E2E: Decision Anchor Law) |
| Z | No autonomous execution exists | **Proven** |
| AA | Human Outcome remains distinct from Action completion | **Proven** (E2E: Outcome recorded after Action, no linkage) |
| AB | No generic Tasks product introduced | **Proven** |
| AC | No migration 016 | **Proven** |
| AD | No scope expansion | **Proven** |
| AE | Browser Golden Path passes reliably | **Proven** (3 consecutive clean runs) |
| AF | Existing M1–M9 relevant regressions remain healthy | **Proven** |
| AG | Full backend passes | **Proven** (1155/1155) |
| AH | Frontend build/typecheck/lint passes | **Proven** |

Every material item is proven. **M9 closure is a reasonable candidate recommendation**, pending independent review and explicit Founder closure authorization — neither of which this slice grants itself.

## Git safety

Working tree contains exactly: `frontend/e2e/m9-slice4-golden-path.spec.ts` (new), `frontend/playwright.config.ts` (one-line hardening correction, justified above), this task document, and the three minimum governance updates (`CURRENT_STATE.md`, `EXECUTION_BOARD.md`, `EXECUTION_INDEX.md`) — on top of the verified Slice 3 checkpoint (`de81441089fc97c8403348e5aafbb4206ba3d761`). Not staged. Not committed. Not pushed.

---

## Execution Result

**Status:** Golden Path browser acceptance complete, one hardening correction applied and regression-proven, **under review — not closed, not committed.**
**Started:** 2026-09-02 (Founder Slice 4 activation).
**Commit(s):** None — working tree only, per explicit "do not stage/commit/push" authorization scope.
**Reviewer:** Pending independent pre-commit review.
**Validation:** 3/3 consecutive clean full-suite Playwright runs (4/4 specs each); 33/33 focused Slice 3 frontend tests; 13/13 focused Slice 3 backend tests; 232/232 relevant Decision/Outcome/Action/Tenant backend regression; 1155/1155 full backend suite; 197/197 full frontend suite; `tsc --noEmit`, `eslint .`, `next build` all clean.
**M9 closure:** Not marked. All final-acceptance checklist items proven; recommendation is a **closure candidate**, subject to independent review and a separate, explicit Founder closure decision.
**Notes:** Migration 015 byte-identical to its Slice 1 closure state; checksum unchanged. No M9 Slice 1/2/3 production file was modified. The one hardening correction was to E2E test-runner configuration only.
