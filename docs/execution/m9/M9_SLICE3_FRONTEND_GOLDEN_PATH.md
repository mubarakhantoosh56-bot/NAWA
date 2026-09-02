# M9 Slice 3 — Frontend Golden Path

**Priority:** P0. Third slice of M9 — Decision Execution Foundation.
**Owner:** AI Engineering Team (Claude Code).
**Ownership layer:** Frontend Golden Path UI plus one bounded, read-only, Founder-approved backend member-source bridge (`GET /company/members`). Not frontend-only after the completion pass below.
**Repository First Policy compliance:** This task document is filed per the Architecture Contract's own requirement (§28/§32) before the slice closes; the completion pass below is recorded alongside the implementation it describes.

---

## Governance status

| Item | Status |
|---|---|
| M9 — Decision Execution Foundation | **ACTIVE** |
| M9 Architecture Contract | `docs/architecture/NAWA_M9_DECISION_EXECUTION_FOUNDATION_ARCHITECTURE_CONTRACT_v1.md` — v1.6, **FOUNDER ACCEPTED** |
| M9 Slice 1 — Action Persistence Foundation | **CLOSED** |
| M9 Slice 2 — Backend Service / API | **CLOSED — REMOTE CHECKPOINT VERIFIED** (commit `3618470f5f044bfbe8b6d1227fe7441b903e44f5`) |
| M9 Slice 3 — Frontend Golden Path | **ACTIVE — IMPLEMENTED / UNDER REVIEW / NOT COMMITTED / NOT CLOSED** |
| M9 Slice 4 — Golden Path E2E & Hardening | **PROPOSED — NOT ACTIVATED** |
| Starting checkpoint | `3618470f5f044bfbe8b6d1227fe7441b903e44f5` (branch `claude-safe-review`) |

## Objective

Implement the minimum frontend UI required to operate the five Slice 2 Action endpoints, anchored to the existing Human Decision UI: create an Action from a recorded Decision, assign/reassign/unassign a responsible company member, track it through its execution-status lifecycle, and inspect its change history. Golden path: **AI Recommendation → Human Decision → Create Action → Assign Responsible Person → Track Execution Status → Inspect Action History.** Not "Recommendation → autonomous AI execution" — every mutation in this slice is a human-initiated click against an already-authorized backend endpoint.

## History of this slice

1. **First pass** (2026-09-02): implemented the full Golden Path except a named-assignee picker. Discovery found no safe company-member data source anywhere (frontend `User`/`Membership` types in `lib/types.ts` were dead scaffolding with zero live usage; all 14 backend routers enumerated, none exposed a members/users listing endpoint). Per that activation's explicit instruction, no backend endpoint was added silently — the gap was flagged for Founder review instead, and everything not depending on it (create Unassigned, status transitions, Unassign, history) was delivered and evidenced.
2. **Completion pass** (this document, 2026-09-02): the Founder reviewed the flagged gap and explicitly approved the smallest option identified — a bounded, read-only `GET /company/members` endpoint. That endpoint was added, and the frontend was completed to use it: a named-assignee selector at creation, and full assign/reassign/unassign at any point while an Action is non-terminal. Two additional frontend-history defects found during review of the first pass were corrected in the same pass (see below).

## Founder-approved member source

Architecture Contract §23 already named this exact gap and its resolution: *"The member list needs a company-members read; if no suitable endpoint exists, adding one is in Slice 3 scope and is a plain company-scoped read."* The first pass deliberately did not act on that blanket pre-authorization without a fresh, explicit go-ahead; this pass carries that explicit Founder approval.

- **Endpoint:** `GET /company/members` (`app/api/company_members.py`), registered in `app/main.py` after `actions_router`.
- **Read-only.** The router exposes exactly one `GET` route — proven by a dedicated test (`test_router_exposes_no_mutation_route`) that enumerates its routes' HTTP methods.
- **Authorization:** reuses the existing `memory.write` permission (the same one every Action endpoint already requires) — no new permission introduced, no RBAC architecture change.
- **Tenancy:** `company_id` is always derived from `AuthContext` (JWT) — the route takes no `company_id` input of any kind, so there is nothing for a client to smuggle. Proven by `test_api_get_company_members_scope_is_token_derived_not_query`, which attempts exactly that and shows it has no effect.
- **Eligibility law:** a user is returned if and only if they hold at least one membership with `status = 'active'` and `deleted_at IS NULL` in the authenticated company — the identical predicate `MembershipRepository.get_active_membership` already used for assignee validation on `POST /actions` / `PATCH /actions/{id}/assignee`. A user with only an `invited`, `suspended`, or `revoked` membership, or a membership only in another company, never appears. A user holding two active memberships in one company (company-wide plus one department-scoped row) is deduplicated to exactly one result row.
- **Response shape:** `{"id": <user UUID>, "full_name": <string>, "email": <string>}` per member, nothing else — no membership id, `company_id`, role/permissions, department, invitation metadata, or any other profile field.
- **Repository:** `MembershipRepository.list_active_company_members` (`app/repositories/membership_repository.py`) — one new read method, `SELECT DISTINCT ON (users.id) ... JOIN users ...`, ordered deterministically by `full_name`, then `email`, then `id`.
- **No migration.** Uses the existing `users`/`memberships` schema exactly as-is; migration 015 remains unmodified and no migration 016 was created.
- **Scope discipline:** this is not a people directory, HR endpoint, org chart, employee search, or role/permission API — it exists for exactly one purpose, populating the Action assignee selector, and returns nothing beyond what that selector needs.

## Frontend history corrections (Founder-identified, this pass)

1. **`changed_at` now visibly rendered.** Every history line (`ActionsPanel.tsx`'s `HistoryLine`) now includes a locale-aware formatted timestamp (`formatDateTime`, `Date.prototype.toLocaleString` with `dateStyle: "medium", timeStyle: "short"`, English or Arabic per the active language) — previously omitted.
2. **Status-domain `null` no longer renders "Unassigned".** A status event's `from_status = null` (the initial status event — there is no prior status because the Action was just created) now renders **Initial** (`t("actionStatusInitial")`) via a dedicated `statusLabelOrInitial` helper, kept structurally separate from the assignment-domain helper (`assigneeDisplayLabel`) that still renders `null` as **Unassigned** for assignment events. The two domains never share a null-rendering path again.

## Discovery preserved from the first pass

- Decision UI: `frontend/src/components/chat/RecordDecision.tsx` — disclosure-pattern component (collapsed button → inline form → success badge), no modal/dialog infrastructure exists anywhere in this frontend.
- Outcome UI: `frontend/src/components/chat/RecordOutcome.tsx` — same pattern, plus a button-group selector for a closed enum and a "record another" re-open flow.
- Integration point: `frontend/src/components/chat/ChatPanel.tsx`, gated by `canRecordDecisions && turn.response.meta.recorded_decision_id` — the exact spot `RecordOutcome` is already anchored.
- API-client convention: `apiRequest<T>()` + `ApiError`; per-domain thin wrapper modules, token-authenticated, no client-supplied `company_id`.
- Existing native `<select>` convention for "pick one company entity from a fetched list, empty = a default state" (`ManualOperationalEventPanel.tsx`'s department selector) — followed exactly for the new assignee selector rather than inventing a new picker pattern.

## Scope

- `app/repositories/membership_repository.py` — new `list_active_company_members` method.
- `app/api/company_members.py` — new router, `GET /company/members`, `CompanyMemberResponse` model.
- `app/main.py` — router registration.
- `tests/test_m9_slice3_company_members_api.py` — new, focused backend test file (13 tests).
- `frontend/src/lib/types.ts` — `ActionAssignableMember`; `ActionCreateRequest.assigned_user_id` now optional (present only on explicit human selection).
- `frontend/src/lib/api/company-members.ts` — `listCompanyMembers`.
- `frontend/src/components/chat/ActionsPanel.tsx` — member fetch/state, assignee selector at creation, unified assign/reassign/unassign selector for non-terminal Actions, resolved-name display with safe fallback, the two history corrections above, member-source-failure resilience.
- `frontend/src/components/chat/ActionsPanel.test.tsx` — expanded focused test file (33 tests, up from 23).
- `frontend/src/lib/i18n/dictionaries/{en,ar}.ts` — additional Action/member-family keys.
- This task document and minimum governance updates (`CURRENT_STATE.md`, `EXECUTION_BOARD.md`, `EXECUTION_INDEX.md`).

**Not in scope** (unchanged, per this activation's explicit exclusion list): a generic Tasks/people-directory/HR page, member CRUD/invites/role or permissions editor, departments UI, kanban/calendar/priority board, `due_at`/`priority`/`tags`/subtasks/comments/attachments/reminders, a `failed`/`paused`/`blocked` status, AI-generated Action content or AI-suggested/ranked assignee, autonomous execution of any kind, `OutcomeMemory.action_id` or any Outcome-flow change, Organizational Memory retrieval changes, Operational Event emission, Company Brain mutation, migration 016, Slice 4 closure work.

## Product law preserved

- An Action is always rendered attached to its parent Decision — no standalone Actions surface exists anywhere in this frontend.
- No AI prefill: `title`/`instructions` are always blank on open; the assignee selector always defaults to Unassigned, never auto-selected, never AI-suggested or ranked.
- No autonomous execution: every mutation is a single authenticated call to an already-authorized backend endpoint, triggered only by a direct human click.
- Status vocabulary and transition matrix unchanged from the first pass; the backend transition check remains authoritative regardless of the client-side mirror.
- Assignment mutation (`Unassigned → user`, `user A → user B`, `user → Unassigned`) is offered only while an Action is non-terminal; a no-op selection (re-selecting the current assignee) is never sent to the backend; an explicit unassign always sends `{"assigned_user_id": null}`, never an omitted field or `{}`.

## Member-source failure resilience

If `GET /company/members` fails, the rest of the panel keeps working: the Action list, status transitions, and history all remain fully functional. Only the named-person selection capability is affected — a safe, generic notice replaces it, an already-assigned non-terminal Action falls back to a plain "Unassign" button (a pure null transition needing no member data), an Unassigned non-terminal Action offers no assignment control at all (nothing to assign to without member data), and Action creation still succeeds as Unassigned. No raw backend error detail is ever rendered.

## Tests

**Backend** — `tests/test_m9_slice3_company_members_api.py`, 13 tests: active same-company member returned; two active memberships for one user dedupe to one row; `invited`/`suspended`/`revoked` memberships each excluded; a membership only in another company excluded; a same-request cross-company leak check (company A's list never contains company B's member); deterministic ordering by `full_name`; response exposes only the three approved fields; HTTP-layer: returns the active member, ignores an attempted `company_id` query-string override (scope is token-derived only), 403 without the required permission, and the router exposes no mutation route.

**Frontend** — `frontend/src/components/chat/ActionsPanel.test.tsx`, 33 tests (up from 23): the full prior matrix, plus — member source loads and Unassigned is the create-form default; a selected member's id is sent as `assigned_user_id`; member-source failure still allows Unassigned creation with a safe notice and no picker; a selector (Unassigned + active members) is offered for a non-terminal Action; no assignee mutation control of any kind for a terminal Action; `Unassigned → user`, `user A → user B`, and `user → Unassigned` all call the backend with the exact expected arguments; a no-op re-selection is never sent; a failed reassignment shows a safe message and never falsely updates the displayed assignee; member-source failure falls back to a plain Unassign button for an already-assigned Action and hides all controls for an Unassigned one; a known current assignee renders its resolved name, never a raw UUID; an assignee no longer in the active member list falls back to a generic label, never a raw UUID; the initial status event renders "Initial → Pending", never "Unassigned → Pending"; an assignment event still renders "Unassigned → <name>"; `changed_at` is visibly rendered; a known actor's name is resolved and prefixed, an unknown actor falls back to a generic phrase, never a raw UUID.

## Regression

- `tests/test_m9_slice3_company_members_api.py`: **13/13 passing.**
- `python -m pytest tests/test_m9_slice1_action_models.py tests/test_m9_slice1_action_schema.py tests/test_m9_slice2_action_service_api.py tests/test_m9_slice3_company_members_api.py tests/test_tenant_isolation.py -q` (relevant backend regression): **149/149 passing.**
- `python -m pytest tests/ -q` (full backend suite): **1155/1155 passing** (was 1142 before this pass; +13 new).
- `frontend/src/components/chat/ActionsPanel.test.tsx`: **33/33 passing.**
- `npx vitest run src/components/chat` (relevant frontend regression): **132/133 passing** (one run) / **133/133 passing** (a repeat run) — the single intermittent failure is the same pre-existing, unrelated `ChatPanel Record Outcome` timing flake documented in the first pass (exercises `RecordOutcome`, no code this pass touched), reconfirmed to pass cleanly with `--testTimeout=20000`.
- `npx vitest run` (full frontend suite): **197/197 passing** (a full run with no flake occurrence).
- `npx tsc --noEmit`: clean.
- `npx eslint .`: clean.
- `npx next build`: succeeds (Turbopack production build, all 4 routes prerendered).

## Browser / E2E boundary

Unchanged: this slice is implementation plus focused component/API tests only. No browser/Playwright E2E was run or added — full Golden Path browser acceptance remains Slice 4 scope.

## Migration / schema safety

Migration 015 was **not modified** (checksum unchanged: `aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a`). No migration 016 was created. No `Action` API semantics changed — `POST /actions` and `PATCH /actions/{id}/assignee` behave exactly as Slice 2 closed them; the frontend simply now populates a field (`assigned_user_id`) those endpoints already accepted.

## Architecture Contract

Not amended in this pass. §23's own sentence anticipating this exact endpoint ("if no suitable endpoint exists, adding one is in Slice 3 scope and is a plain company-scoped read") remains true as written — it was fulfilled, not contradicted, so no correction is due to it. The contract's slice-status table (§28) and header still read Slices 2–4 as `PROPOSED — NOT ACTIVATED`, which has been superseded by the execution-tracker documents (this document, plus `CURRENT_STATE.md`/`EXECUTION_BOARD.md`/`EXECUTION_INDEX.md`) since Slice 2's own activation — consistent with this project's established practice of tracking slice activation/closure state in the execution tracker, not by amending the Architecture Contract for every slice transition (the contract's own amendment log, Appendix A, records only Slice 1's activation/closure, never Slice 2's or Slice 3's). No contract-amendable statement became newly false as a direct result of today's Founder decision, so no amendment was made, per this activation's own instruction not to rewrite the contract merely because the option it already named was exercised.

## Git safety

Working tree contains exactly: the six frontend paths already listed in the first pass, plus `app/repositories/membership_repository.py`, `app/api/company_members.py`, `app/main.py`, `tests/test_m9_slice3_company_members_api.py`, `frontend/src/lib/api/company-members.ts`, this task document, and the three governance updates — on top of the verified Slice 2 checkpoint (`3618470f5f044bfbe8b6d1227fe7441b903e44f5`). Not staged. Not committed. Not pushed.

---

## Execution Result

**Status:** Implementation complete (Golden Path + Founder-approved member source), focused tests passing, **under review — not closed, not committed.**
**Started:** 2026-09-02 (Founder Slice 3 activation); completed 2026-09-02 (Founder member-source approval + completion pass).
**Commit(s):** None — working tree only, per explicit "do not stage/commit/push" authorization scope.
**Reviewer:** Pending independent pre-commit review.
**Validation:** 13/13 focused backend member-source tests; 149/149 relevant backend regression; 1155/1155 full backend suite; 33/33 focused frontend tests; 197/197 full frontend suite (one pre-existing, unrelated, independently-confirmed timing flake seen intermittently); `tsc --noEmit`, `eslint .`, and `next build` all clean.
**Follow-up:** Slice 4 (Golden Path E2E & Hardening) remains `PROPOSED — NOT ACTIVATED` and requires its own explicit Founder activation and task document.
**Notes:** This slice does not close until independent review passes and the Founder authorizes staging/commit. Migration 015 remains byte-identical to its Slice 1 closure state; checksum unchanged. `Action` API semantics unchanged from Slice 2.
