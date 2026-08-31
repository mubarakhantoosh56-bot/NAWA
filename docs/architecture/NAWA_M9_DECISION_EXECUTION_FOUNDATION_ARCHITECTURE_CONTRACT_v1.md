# NAWA M9 — Decision Execution Foundation Architecture Contract v1

**Status:** FOUNDER ACCEPTED — Architecture Contract.
**Implementation Status:** ACTIVE — SLICE 1 ONLY (Action Persistence Foundation: migration + domain models, live-local validated, **committed locally in `09ac78d56e64c36263f5d3f4d0120904503b88a1`, not yet pushed**, awaiting independent post-commit verification, not closed). **Slices 2–4 remain PROPOSED — NOT ACTIVATED. Slice 1 activation does not imply engineering authorization for any other slice.**
**Version:** 1.5 — Post-Commit State Reconciliation Amendment applied (see Appendix A).
**Category:** Architecture Document (per NAWA Documentation Standard v1 §3.1).
**Subordinate to:** NAWA Reasoning Constitution v1.0; EBD-003 Architecture Freeze v1.0; EBD-004 Engine Definitions (MVP Edition); NAWA Deferred Architecture Pack v1.3.
**Scope:** Forward architecture contract for M9 — Decision Execution Foundation. Domain model, state machine, governance, security, persistence shape, API and frontend direction, options analysis, proposed slices, acceptance gate.
**Non-scope:** Implementation, SQL, migration 015, API code, frontend code, slice activation, Track A activation, Track B activation, SituationMemory.
**Owner:** Founder & CEO (Mubarak).
**Approval authority:** Founder & CEO.
**Repository grounding:** `migrations/014_organizational_memory.sql`, `migrations/001_saas_foundation_schema.sql`, `migrations/002_saas_foundation_indexes.sql`, `app/ome/**`, `app/api/decisions.py`, `app/api/outcomes.py`, `app/core/role_permissions.py`, `frontend/src/components/chat/RecordDecision.tsx`. Verified at `claude-safe-review` @ `8cdb8d5fdba76fbaf2227535e5db0a61a10242d0`.
**Last updated:** 2026-09-01.

> **Founder Decision Amendment (v1.1).** Two Founder decisions are recorded in this version and bind the rest of the document:
>
> 1. **Assignee included.** `assigned_user_id` **IS** in the M9 MVP, nullable, as a plain `users(id)` FK plus mandatory domain-service validation that the user holds at least one active membership in the Action's company. The absence of a clean composite database FK is an accepted trust-boundary decision, not a reason to remove accountability from Decision Execution.
> 2. **`due_at` deferred.** Removed from the M9 MVP persistence contract, API, Golden Path and acceptance gate. Reclassified `LIKELY FUTURE REQUIREMENT`.
>
> Consequent design decision resolved in this version: assignment changes are audited in the **same** append-only Action change ledger as status changes (Option B, §9.4). No slice is activated. No milestone is created. No engineering work is authorized.

> **Reading contract.** Nothing here is a task. Every recommendation is a proposal for Founder ratification. Numeric or enumerated values that are policy rather than architecture are labeled `PROPOSED`. A future engineer should be able to implement Slice 1 from this document without redesigning; nobody should be able to read it as authorization to start.

---

## 1. Executive Decision

**Recommended architecture: OPTION M9-2 — a separate, Decision-linked `Action` entity holding current execution state, plus a lightweight immutable append-only change ledger covering status transitions and assignment changes.**

M9 adds exactly two durable tables, one domain service, five narrow endpoints, and one frontend affordance. It adds no autonomy, no scheduling, no retrieval change, no Company Brain mutation, and no new provenance duplication.

The contract's four load-bearing calls:

1. **A separate Action entity, always anchored to a `DecisionMemory`.** Not a field on `DecisionMemory` (which is append-only and would be corrupted by mutable execution state), and not a generic Task (which is how NAWA would quietly become a project-management tool).
2. **Execution state and Outcome state stay in different vocabularies and different tables.** `pending / in_progress / completed / cancelled` describes *what happened to the work*. `positive / negative / mixed / unknown` describes *what happened as a result*. These must never share an enum, a column, or a UI control.
3. **A lightweight change ledger, not event sourcing and not current-state-only.** The Action row stays the authoritative current state; one append-only side ledger records who changed what and when — status transitions and assignment changes, in one chronological history. Without it, "when did this start, who cancelled it, who handed it to whom" is unrecoverable — and auditable human governance is the entire product claim.
4. **`assigned_user_id` is included, nullable, and validated in the domain service.** Accountability — *who is responsible for executing this* — is part of what M9 means, not generic task management. The database can prove the user exists; only the service can prove the user is an active member of this company, because `users` carries no `company_id` and every `memberships` uniqueness index is partial and therefore unusable as an FK target (§11.2). That split is an **accepted, documented trust boundary**, and it costs almost nothing to honour: `MembershipRepository.get_active_membership(company_id, user_id)` already exists in the repository and implements the required predicate exactly.

**`due_at` is deferred** (Founder Decision 2) — useful, but not required to prove the domain loop, and the field most likely to pull M9 toward scheduling behaviour.

**Status returned: M9 ARCHITECTURE CONTRACT FOUNDER ACCEPTED — SLICE 1 ACTIVE, LIVE-LOCAL VALIDATED, AND COMMITTED LOCALLY, SLICES 2–4 NOT ACTIVATED.** Codex's final architecture review passed (v1.2); the Founder accepted the contract as a whole (v1.3); the Founder then explicitly activated Slice 1 only (v1.4) — migration 015 and the `Action`/`ActionChangeEvent` domain models were applied to and validated against the existing project-local `nawa-postgres` development instance (36/36 live schema tests, 1092/1092 full backend suite, zero failures); the Founder has since authorized staging and committing that validated package (v1.5) in commit `09ac78d56e64c36263f5d3f4d0120904503b88a1` — **committed locally, not yet pushed, not applied to any production or shared database, awaiting independent post-commit verification, not closed.** Activating and committing Slice 1 is not a re-opening of the contract's architecture and does not activate Slice 2, 3, or 4, Track A, Track B, or any autonomous execution. The Founder Decision register (§31) is unchanged: two decisions are ratified and closed, eight remain open with recommended defaults, none of them blocking.

---

## 2. Why M9 Exists

The organizational memory loop closed at M8 is:

```
AI Recommendation → Human Decision → [ GAP ] → Human Outcome → Organizational Memory
```

Today a company can record what NAWA advised, what a human decided, and what eventually happened — but nothing about **what was actually done in between**. The loop asserts causality it cannot show its work for: an Outcome floats directly off a Decision with no record of whether the Decision was executed at all, by whom, or when.

M9 fills that gap with one link:

```
AI Recommendation → Human Decision → Human-Governed Action → Execution State → Human Outcome → Organizational Memory
```

The value is not task tracking. It is that **"we decided X and it didn't work" becomes distinguishable from "we decided X and never did it."** Those two are the most commonly confused facts in any operating company, they produce opposite corrective actions, and NAWA currently cannot tell them apart. That single distinction is the whole justification for M9, and it is the thing the acceptance gate (§29) must prove.

**What M9 must not become:** a project-management system, a task suite, an autonomous agent platform, a workflow engine, an ERP, or a to-do app. Every scope question in this contract is decided against that list.

---

## 3. Domain Laws

Restated and binding on every section below. Unchanged by M9.

| Law | M9 implication |
|---|---|
| AI Recommendation ≠ Human Decision | AI-generated action text never becomes an Action without an explicit human act (§5) |
| Human Decision ≠ Action | Action is a separate entity; a Decision with no Action is a valid, meaningful state |
| Action ≠ Execution State | Execution state is a mutable attribute of an Action, tracked with its own history |
| Execution State ≠ Outcome | Separate vocabularies, separate tables, separate UI. `completed` is not `positive` (§13) |
| Outcome ≠ causal proof | A completed Action followed by a negative Outcome proves nothing about causation |
| Historical Memory ≠ Current Truth | Action state is *current operational state*, not historical memory (§16) |
| Historical Decision ≠ Current Company Brain policy | Unchanged |
| No automatic Company Brain mutation | No Action state, count, or pattern may alter Company Brain (§17) |
| No automatic organizational learning | Repeated completions are not a learned policy (§17) |

**One new law proposed by this contract:**

> **M9-L1 — Execution state is asserted by a human, never inferred.** No Action transitions state because of elapsed time, an AI conclusion, an operational event, or any system inference. Every transition — and every assignment change — is written by an identified human. Nothing in M9 schedules, watches a clock, or acts on a deadline; `due_at` is deferred out of MVP precisely so no such mechanism has an anchor to attach to.

---

## 4. Current Foundation

Verified in the repository, not assumed.

**Existing OME persistence** (`migrations/014_organizational_memory.sql`):

| Table | Nature | Key fields |
|---|---|---|
| `ome_reasoning_receipts` | Immutable, server-created | `response_snapshot` JSONB, `evidence_refs` JSONB, `created_by_user_id` |
| `ome_decision_memories` | Human-recorded, append-only + supersession | `reasoning_receipt_id` (NOT NULL), `situation_id` (NULL), `decision_text`, `rationale`, `decided_by_user_id`, `decided_at`, `status active\|superseded`, `superseded_by` |
| `ome_outcome_memories` | Human-recorded, append-only + supersession | `decision_memory_id` (NOT NULL), `outcome_summary`, `result_state positive\|negative\|mixed\|unknown`, `recorded_by_user_id`, `observed_at`, supersession pair |

**Established patterns M9 must follow (all verified in 014):**

- Every table: `UUID` PK with `gen_random_uuid()`, `company_id UUID NOT NULL → companies(id)`.
- Every OME→OME and OME→operational reference: **composite `(id, company_id)` foreign key**, backed by a `UNIQUE (id, company_id)` constraint on the target. Cross-company links are rejected by the database, not by convention.
- Actor columns (`created_by_user_id`, `decided_by_user_id`, `recorded_by_user_id`): plain FK to `users(id)`, **not** company-scoped — because these are always JWT-derived, never client-supplied.
- **No `ON DELETE` clauses anywhere.** Hard deletion is not supported; a referenced row is simply not deletable.
- Status/supersession consistency enforced by CHECK constraints in SQL *and* re-checked in Python `__post_init__` (fail closed at both boundaries).
- Indexes are consistently `(company_id, <discriminator>)` or `(company_id, <timestamp> DESC)`.

**Existing service/API patterns:**

- `app/ome/errors.py` — six shallow error classes, and deliberately **no** `CrossTenantReference` error: a tenant-scoped lookup that finds nothing must never distinguish "does not exist" from "belongs to another company". Both resolve to 404.
- `app/api/decisions.py` — `POST /decisions`, permission `memory.write`, Pydantic `extra="forbid"`, `company_id` and acting user **always** from `AuthContext`, never client-supplied.
- `DecisionMemoryService.record_decision` validates `situation_id` by loading it **through a company-scoped repository call** before use — application-layer validation layered on top of the database composite FK.
- `app/api/README.md` router registration in `app/main.py`; latest migration is **014**.

**Existing precedent for an append-only history side-table:** `migrations/013_memory_fact_history.sql`. M9's status ledger is the same shape, not a new idea.

**What does not exist:** any `Action`, `ExecutiveAction`, `Task`, or execution-tracking entity. Confirmed — no such table, model, repository, service, route, or frontend component.

**AI advisory action text that already exists** (advisory only, never materialized): `CEOBrief.recommended_next_actions`, `CEOBrief.executive_actions`, `logic_json.solution_generator`, `logic_json.execution_engine`, `ceo_text` "Recommended Actions" prose. `frontend/src/components/chat/RecordDecision.tsx` requires human-authored text and prefills nothing.

---

## 5. Decision → Action Boundary

**ACTION CREATION LAW (binding):** an AI recommendation must never become an Action without an explicit, deliberate human act. No code path from `openai_client.py`, `chat.py`, `CEOBrief`, `logic_json`, or `ceo_text` may reach the Action write path — mirroring the isolation already enforced between chat and `DecisionMemoryService`.

Three separate authorship facts, none of which may be collapsed:

| Fact | Recorded by | Where |
|---|---|---|
| NAWA suggested something | The reasoning pipeline | `ome_reasoning_receipts.response_snapshot` |
| A human decided something | An explicit human `POST /decisions` | `ome_decision_memories.decision_text` |
| A human authorized work | An explicit human `POST /actions` | `ome_actions.title` |

**AI text may be *displayed* next to the Action form as reference context. It may never be *written into* the Action record silently.** See §23 for why prefill is refused even behind a button in the first slice.

**Why `decision_memory_id` is required (Decision 2 = YES).** An Action with no Decision is a task. A product that accepts orphan tasks is a task tracker, and NAWA would arrive there through a nullable column rather than through a strategy meeting. Requiring the link is the single cheapest structural guard against the scope drift §2 forbids — one `NOT NULL`.

The honest cost, stated: a user who wants to record work that no NAWA decision produced cannot. That is intentional. If it becomes a real complaint from a real pilot, the correct response is to ask *why* that work has no recorded decision — not to relax the constraint.

---

## 6. Proposed Action Domain Model

```
ome_reasoning_receipts (immutable, server-created)
        │  1
        │  N
ome_decision_memories (human, append-only)
        │  1                          │  1
        │  N                          │  N
   ome_actions ──────────────▶ ome_outcome_memories
        │  1                    (evaluates the DECISION,
        │  N                     not one Action — §13)
ome_action_change_events (append-only: status + assignment)
```

- **`DecisionMemory` 1 → N `Action`** (Decision 3 = YES). One decision routinely requires several actions across departments. A one-to-one assumption would be wrong on the first real Jannat decision and would be expensive to unwind after data exists.
- **`Action` 1 → N `ActionStatusEvent`**, append-only.
- **`OutcomeMemory` remains attached to `DecisionMemory`**, not to `Action` (Decision 13 = NO).
- **No `Action` → `ReasoningReceipt`** and **no `Action` → `situation_id`** direct links (§12).

**Module placement:** `app/ome/models/action.py`, `app/ome/repositories/action_repository.py`, `app/ome/services/action_service.py`, `app/api/actions.py` — mirroring the existing OME package layout exactly.

---

## 7. Field Contract

The Founder's proposed field list was reviewed field by field rather than accepted.

### 7.1 `ome_actions` — recommended MVP columns

| Field | Type | Null | Verdict / rationale |
|---|---|---|---|
| `id` | UUID PK | NO | Standard |
| `company_id` | UUID → `companies(id)` | NO | Standard tenant anchor |
| `decision_memory_id` | UUID | NO | Composite FK `(decision_memory_id, company_id) → ome_decision_memories(id, company_id)`. Required (§5) |
| `title` | TEXT | NO | The human's operational instruction, one line. Non-blank enforced in SQL and Python |
| `instructions` | TEXT | YES | Optional detail. Deliberately **not** required — forcing prose produces filler |
| `status` | TEXT | NO | `DEFAULT 'pending'`, CHECK against the four states (§8) |
| `created_by_user_id` | UUID → `users(id)` | NO | JWT-derived, never client-supplied. Plain FK, matching the 014 actor-column precedent |
| `created_at` | TIMESTAMPTZ | NO | `DEFAULT NOW()` |
| `updated_at` | TIMESTAMPTZ | NO | `DEFAULT NOW()`; touched on every status transition |
| `assigned_user_id` | UUID → `users(id)` | **YES** | Plain FK (composite is structurally unavailable — §11.2). Same-company active-membership validated in the domain service on every write. NULL = responsibility not yet assigned (§7.3) |
| `completed_at` | TIMESTAMPTZ | YES | Set **only** on transition to `completed`; NULL otherwise (§7.4) |
| `cancelled_at` | TIMESTAMPTZ | YES | Set **only** on transition to `cancelled`; NULL otherwise |

**On `cancelled_at`:** the Founder's list placed it under "defer by default". This contract recommends **including** it, for symmetry with `completed_at` and because a CHECK constraint pairing each terminal state with its timestamp is what makes the terminal-state invariant enforceable in SQL rather than only in code — the same discipline as `chk_ome_decision_memories_status_supersession_consistent`. It costs one nullable column. `cancellation_reason` stays deferred (Decision: no reason required — §7.4).

### 7.2 Deferred fields — confirmed

`due_at`, `approved_by_user_id`, `reasoning_receipt_id`, `situation_id`, `department_id`, `priority`, `comments`, `attachments`, `recurrence`, `subtasks`, `failure_reason`, workflow graph, dependencies, automation metadata, agent execution metadata, external integrations — **all deferred**. Three notes:

- **`due_at` — `LIKELY FUTURE REQUIREMENT`** (Founder Decision 2). Deferred not because it is useless but because it is unnecessary to prove the domain loop, and because a stored deadline is the natural anchor for the first scheduler anyone proposes. Removing it removes the anchor. When it returns it stays inert by M9-L1: read by humans, acted on by nobody. Its return is a one-column additive change with no lifecycle consequence.

- `department_id` is the most likely first addition, because `ome_decision_memories` already carries the same documented gap (company-scoped authority, no department scoping — `app/api/decisions.py` header). When department scoping arrives it should arrive for both tables in one change, not for Actions alone.
- `priority` is refused specifically: it is the field that most reliably turns an execution record into a project-management backlog.

### 7.3 `assigned_user_id` — INCLUDED, NULLABLE (Founder Decision 1)

**Included in the M9 MVP.** Nullable (Decision 4 = YES): an Action recorded without a named owner is a real and common state, and forcing an assignee would manufacture false ownership data.

**`created_by_user_id` and `assigned_user_id` are never conflated:**

| | `created_by_user_id` | `assigned_user_id` |
|---|---|---|
| Meaning | The human who explicitly recorded and authorized the Action | The human responsible for executing it |
| Source | JWT `AuthContext` — never client-supplied | Client-supplied, explicitly chosen by a human |
| Nullable | No | **Yes** |
| Mutable | No — authorship is fixed | **Yes**, while the Action is non-terminal (§7.5) |
| Tenant guard | Plain FK; trusted because JWT-derived | Plain FK **plus** mandatory service-layer membership validation (§11) |

They may be the same person. They routinely are.

**What NULL means:** responsibility has not yet been assigned in the persisted Action. It does **not** mean the AI is responsible, NAWA is responsible, or that anything may execute automatically. There is no code path in M9 by which an unassigned Action does anything at all.

### 7.5 Assignee mutability

**Reassignment is allowed** (Founder direction): responsibility can legitimately move without changing the human-authorized Action itself. Two constraints keep that honest:

1. **Reassignment never rewrites authorization content.** `title`, `instructions`, `decision_memory_id` and `created_by_user_id` remain immutable (§21.5). Only `assigned_user_id` and `updated_at` change.
2. **Reassignment is only permitted while the Action is non-terminal** (`pending` or `in_progress`). Reassigning a `completed` or `cancelled` Action is meaningless and would retroactively imply someone was responsible for work already closed out. `PROPOSED`: reject with `409`, matching the terminal-state rule in §8.

Every reassignment — including assigning from NULL and clearing back to NULL — is recorded in the change ledger (§9.4). Silent reassignment is forbidden.

### 7.4 Semantics

- `created_at` — when the Action record was written. Not when work began.
- `updated_at` — last mutation of the row (status transitions only; §22 forbids editing title/instructions).
- `completed_at` — the instant of the transition to `completed`. **Never treated as evidence that an Outcome occurred** (§13). Set by the service from the transaction clock, never client-supplied.
- `cancelled_at` — the instant of the transition to `cancelled`.
- There is no deadline field in MVP (§7.2). Nothing in M9 reads a clock.

---

## 8. Execution State Machine

**Recommended states (Decision 5):** `pending` → `in_progress` → `completed`, with `cancelled` as the terminal alternative.

```
                   ┌──────────────┐
      ┌───────────▶│   pending    │◀── created here, always
      │            └──────┬───────┘
      │           ┌───────┴────────┐
   (none — no     ▼                ▼
    re-entry)  in_progress ───▶ cancelled  ● terminal
                   │                ▲
                   └────▶ completed ┘ (no transition between terminals)
                            ●  terminal
       pending ──▶ completed  ALLOWED (direct)
       pending ──▶ cancelled  ALLOWED
```

**Allowed transitions (Decision 7 = YES for direct completion):**

| From | To | Allowed | Note |
|---|---|---|---|
| `pending` | `in_progress` | ✅ | |
| `pending` | `completed` | ✅ | Small actions genuinely finish in one step. Forcing `in_progress` manufactures a state that never occurred — worse data than allowing the shortcut |
| `pending` | `cancelled` | ✅ | Decided against before starting |
| `in_progress` | `completed` | ✅ | |
| `in_progress` | `cancelled` | ✅ | |
| `in_progress` | `pending` | ❌ | Un-starting is not a real operational event |
| `completed` → anything | ❌ | Terminal (Decision 8) |
| `cancelled` → anything | ❌ | Terminal (Decision 8) |
| any | same state | ❌ | A no-op transition is rejected, not silently recorded (§24) |

**Reopening (Decision 8 = NO).** Terminal is terminal, matching the append-only philosophy of the entire OME schema. A mistaken terminal state is corrected by recording a **new Action** against the same Decision, leaving the erroneous one visible in history — exactly how `DecisionMemory` handles a wrong decision via supersession rather than edit.

The honest cost: a mis-clicked "completed" is permanent. Mitigations that belong in the UI, not the schema: an explicit confirmation step on terminal transitions, and terminal buttons visually distinct from `in_progress`. Accepted.

### 8.1 `failed` — DEFERRED (Decision 6 = NO), with the tradeoff stated plainly

**The argument for deferring.** `failed` sits exactly on the seam this contract is built to protect. "It failed" is usually an *outcome* judgement wearing an *execution* costume, and `ome_outcome_memories.result_state = 'negative'` already exists to carry it. Adding `failed` invites every negative result to be logged as an execution state, and within a quarter the two vocabularies are interchangeable in practice regardless of what the schema says.

**The argument against deferring — which is real, and is not dismissed.** "We tried and could not finish" is genuinely different from "we called it off." Forcing the first into `cancelled` loses information, and `cancelled` actively implies a decision to stop that never happened. There is a real gap here.

**Why deferral still wins:** the asymmetry of cost. Adding a state later is a widened CHECK constraint plus a UI option — additive, no data migration, no reinterpretation of existing rows. Removing a state later requires reinterpreting every row already written under it. Under that asymmetry, the correct MVP move is to start narrow and let field use prove the need.

**Trigger to add `failed`** — one occurrence is enough: a pilot user cancels an Action that was genuinely attempted, or writes "failed" into the title, instructions, or the Outcome summary of an action marked `cancelled`. That is observable in the data without instrumentation. Until then, the honest representation is `cancelled` **plus** an `OutcomeMemory` with `result_state = 'negative'` recording what actually happened.

---

## 9. Action Auditability Model

**Recommended: OPTION M9-2 — Action row (current state) + one immutable append-only change ledger** covering both status transitions and assignment changes (Decision 9 = YES; assignment-audit option resolved in §9.4).

### 9.1 The problem with current-state-only

With M9-1, an Action row that reads `completed` tells you `created_at`, `completed_at`, and `created_by_user_id`. It does not tell you when work started, how long it sat in `pending`, who moved it, or whether it passed through `in_progress` at all. For a product whose claim is *auditable human governance of decisions*, "who changed this and when" is not a nice-to-have — it is the claim.

### 9.2 Why not full event sourcing (M9-3)

Event sourcing makes current state a computed projection. That is heavier to query, heavier to test, breaks the `(company_id, status)` index pattern used everywhere else, and buys nothing here: the Action lifecycle has four states and at most three transitions. It would be sophistication with no payer.

### 9.3 Recommended `ome_action_change_events`

| Field | Type | Null | Note |
|---|---|---|---|
| `id` | UUID PK | NO | |
| `company_id` | UUID → `companies(id)` | NO | |
| `action_id` | UUID | NO | Composite FK `(action_id, company_id) → ome_actions(id, company_id)` |
| `change_type` | TEXT | NO | CHECK `IN ('status','assignment')` — a **closed** two-value enum (§9.5) |
| `from_status` | TEXT | YES | Status events only. NULL on the creation event |
| `to_status` | TEXT | YES | Status events only; NOT NULL when `change_type='status'` |
| `from_assigned_user_id` | UUID → `users(id)` | YES | Assignment events only. NULL when assigning from unassigned |
| `to_assigned_user_id` | UUID → `users(id)` | YES | Assignment events only. NULL when clearing the assignee |
| `changed_by_user_id` | UUID → `users(id)` | NO | JWT-derived |
| `changed_at` | TIMESTAMPTZ | NO | `DEFAULT clock_timestamp()` — not `NOW()`/`CURRENT_TIMESTAMP` (frozen at transaction BEGIN). `clock_timestamp()` is evaluated at statement-execution time, which avoids a specific transaction-start-time inversion risk under a future row-locked concurrent write path (§24.1) and improves audit-time fidelity. It is **not** a monotonic sequence, a causal version, or a guarantee of strictly increasing values — a backward wall-clock step or a same-resolution tie remain possible. The ledger's persisted from-state/to-state values are the authoritative audit evidence, not `changed_at`. No sequence/version/ordinal/Lamport-clock column is introduced by this contract |

Append-only. No update path, no delete path, no reason column, no free text.

**Status-ledger semantics are fully preserved** — they are simply the `change_type = 'status'` subset. Creating an Action writes the first event (`change_type='status'`, `from_status = NULL`, `to_status = 'pending'`) **in the same transaction** as the Action row, so an Action can never exist without a complete history. If the Action is created with an assignee, a second event (`change_type='assignment'`, `from = NULL`, `to = <user>`) is written in that same transaction.

The Action row remains the authoritative current state. The ledger is a side record, never a replay source. Index: `(company_id, action_id, changed_at)`.

Roughly 40 lines of DDL and one repository method, following the `013_memory_fact_history.sql` precedent already in the repo.

### 9.4 Assignment auditability — Option B, resolved

Three options were compared. Full event sourcing was excluded by Founder direction and independently rejected in §9.2.

| | **A** Current `assigned_user_id` only, no history | **B** One ledger, extended to cover assignment | **C** Separate assignment-history table |
|---|---|---|---|
| Prevents silent rewriting of responsibility | **No** — the previous assignee is simply gone | Yes | Yes |
| Tables | 2 | **2** | 3 |
| Repositories / insert paths | 1 | **1** | 2 |
| Unified "what happened to this Action" timeline | n/a | **Single ordered read** | Requires UNION + merge-sort of two tables |
| Constraint complexity | Lowest | Conditional CHECK on a discriminator | Clean NOT NULLs |
| Risk to status-ledger clarity | n/a | Real, and must be managed | None |

**Option A is rejected outright.** It fails the one requirement the Founder named: it permits silent rewriting of historical responsibility. "Who was responsible on the day this stalled" would be unanswerable the moment the Action is reassigned.

**Option B is recommended**, and the usual objection to it does not apply here. The objection to extending a ledger is that it *pollutes existing semantics* — but `ome_action_change_events` **does not exist yet**. There is no migration, no live data, and no established shape to disturb. Choosing a two-variant discriminated ledger now is a design decision, not a retrofit. It buys a single chronological audit of an Action, which is exactly what an audit view needs to render and exactly what a two-table design makes fiddly enough to get skipped.

The conditional CHECK it requires is the same class already in the repository — `chk_ome_decision_memories_status_supersession_consistent` (migration 014) does precisely this kind of conditional field-consistency enforcement. This is an established local pattern, not a new one.

**Option C remains an acceptable fallback** (`ome_action_assignment_events`, minimum schema: `id`, `company_id`, `action_id`, `from_assigned_user_id`, `to_assigned_user_id`, `changed_by_user_id`, `changed_at`). It is architecturally equivalent in what it preserves, costs one more table and one more repository, and loses the unified timeline. Choosing C over B is a Founder preference with no downstream consequence — FD-10 in §31.

**Minimum persisted audit fields for an assignment change (either option):** `action_id`, `from_assigned_user_id`, `to_assigned_user_id`, `changed_by_user_id`, `changed_at`. No reason field. No free text.

### 9.5 Guard against ledger creep

The change ledger must not become a general Action event platform.

- `change_type` is a **closed** enum of exactly two values. Adding a third requires Founder ratification, not an engineering decision.
- The ledger is never a replay source. The Action row is always the authoritative current state.
- No payload column, no free-text column, no JSONB column, ever.
- Nothing but the Action write path writes to it.

---

## 10. Human Governance

| Capability | Who | Rationale |
|---|---|---|
| Create an Action | Any authenticated user with the write permission, scoped to their company | Matches `POST /decisions` exactly |
| Update execution status | Same | In MVP, the creator has no special rights over the assignee or vice versa |
| Cancel | Same (it is a status transition) | No separate authority |
| Mark completed | Same | No separate authority |
| Assign / reassign | Same permission, while the Action is non-terminal (§7.5) | Assignment is arguably a distinct authority; the Founder has ratified reuse of `memory.write` for MVP, and the trigger to split it out is recorded below |
| Delete | **Nobody** (§21.4) | No delete path exists |

**Permission (Decision 10): reuse `memory.write`.**

Rationale: it is the same class of authority — a human recording a governed organizational record — and it is already held by every seeded role except `employee` (`app/core/role_permissions.py`, `migrations/003`, `migrations/004`). Introducing `action.write` would require editing `role_permissions.py` **and** two role-seed migrations, dragging a migration into a slice that should be purely additive, in exchange for a distinction nobody has asked for.

**Security implications, stated honestly:**

- Authority is **company-scoped, not department-scoped** — any `memory.write` holder can record an Action for the whole company. This is the *same* accepted limitation already documented in the `app/api/decisions.py` module header. It is a known MVP limitation, not an oversight.
- `ai.chat` is deliberately **not** the gate. Using the chat feature is not authority to record company execution records — the same reasoning `decisions.py` applies.
- **On the assignment-authority question.** In v1.0 this contract named the arrival of `assigned_user_id` as the trigger to introduce `action.write`. That field has now arrived, and the Founder has ratified reuse of `memory.write` for MVP regardless. That is a defensible call at this scale — every `memory.write` holder is already trusted to record company-wide decisions and outcomes, so trusting them to name an executor is not a widening of real authority. It is recorded here as a **deliberate, accepted MVP position**, not an oversight.
- **Revised trigger to split out `action.write`:** the arrival of `department_id` on Actions, or the first request for a role that may *execute* work without being able to *authorize* it. Either makes "who may assign work to whom" a genuine authority question. Recorded, not scheduled.

---

## 11. Tenant / Assignee Security

### 11.1 The invariant

```
Action.company_id
  == DecisionMemory.company_id
  == AuthContext.company_id (creator)
  == assigned_user's company, when an assignee exists
```

The first three are straightforward and are enforced exactly as `ome_decision_memories` already enforces them: `company_id` from the JWT, never from the client; a composite `(decision_memory_id, company_id)` FK so the database rejects a cross-company decision link; and a service-layer company-scoped load of the Decision before use, mirroring `DecisionMemoryService`'s handling of `situation_id`.

### 11.2 The finding that changes the answer

**A database-level composite FK for `assigned_user_id` is structurally impossible under the current schema.**

Verified, not assumed:

- `users` (`migrations/001`, lines 23–39) **has no `company_id` column.** Company membership lives in a separate `memberships` table.
- A composite FK would therefore have to target `memberships(user_id, company_id)`.
- Every uniqueness index on `memberships` (`migrations/002`, lines 26–34) is **partial** — `WHERE department_id IS NULL AND deleted_at IS NULL` and `WHERE department_id IS NOT NULL AND deleted_at IS NULL`. **PostgreSQL cannot use a partial unique index as the target of a foreign key.**
- Worse, a non-partial `UNIQUE (company_id, user_id)` cannot simply be added: the existing model deliberately permits a user to hold *multiple* membership rows in one company — one company-wide (`department_id IS NULL`) plus one per department. A blanket unique constraint would break that.

So the composite-FK pattern that protects every other cross-reference in OME — the pattern Codex specifically required for `situation_id` in migration 014 — **cannot be applied here.** `assigned_user_id` would be the first client-supplied cross-entity reference in the OME schema with no database-level tenant guard. Note that the existing actor columns (`created_by_user_id`, `decided_by_user_id`) are plain `users(id)` FKs precisely *because* they are JWT-derived and never client-supplied; an assignee is the opposite.

### 11.3 Founder-ratified resolution (Decision 11)

**`assigned_user_id` is included with a plain `users(id)` FK plus mandatory domain-service validation.** The trust boundary is stated explicitly rather than papered over:

> **The database FK proves the user exists. The domain service proves the user is an active member of this company. Neither alone is sufficient, and M9 relies on both.**

**The required invariant, stated as the service must implement it:**

```
if assigned_user_id IS NOT NULL:
    ∃ membership WHERE membership.user_id    = assigned_user_id
                   AND membership.company_id = Action.company_id
                   AND membership.status     = 'active'
                   AND membership.deleted_at IS NULL
```

**This costs almost nothing to implement correctly, because the exact predicate already exists.** `MembershipRepository.get_active_membership(company_id, user_id)` (`app/repositories/membership_repository.py`) queries `WHERE company_id = $1 AND user_id = $2 AND status = 'active' AND deleted_at IS NULL`, ordered `department_id NULLS FIRST, created_at DESC, LIMIT 1` — it already tolerates a user holding several membership rows in one company, which is precisely the semantics the Founder specified. `ActionService` composes that repository and calls it, exactly as `DecisionMemoryService` composes `OperationalSituationRepository` and calls `get_situation` before accepting a `situation_id`. **No new repository method, no new query, no new membership semantics.**

**Validation applies on every write path that sets or changes the assignee** — `POST /actions` and `PATCH /actions/{id}/assignee`. Never only on create.

**Rejection behaviour (generic-safe, per `app/ome/errors.py`):** a nonexistent user, a user with no active membership in the Action's company, and a user belonging to another company **all resolve identically** to the standard generic 404. The response must never distinguish "no such user" from "user exists elsewhere" — that distinction is itself a cross-tenant information leak, and the existing OME error contract deliberately omits a `CrossTenantReference` class for exactly this reason.

**No department semantics.** Membership in the company is the whole test. A company-wide membership (`department_id IS NULL`) and a departmental one are equally valid.

**Explicitly NOT done for M9** (Founder direction): no restructuring of `users`, `memberships`, membership uniqueness, or the department-membership architecture; no database trigger; no new company-user identity table; no new uniqueness model. Any of those would be a schema change to a load-bearing, already-shipped subsystem in service of one nullable column.

**The residual risk, named honestly.** A defect or a bypass in `ActionService` could persist a cross-company assignee that the database would accept, because no constraint stands behind the service. The mitigations are: validation lives in the service layer (not the route), so every caller inherits it; it is a required acceptance criterion, not prose (§29, criteria 7 and 7b); and the gap is documented in the migration header and the `app/api/actions.py` module header, exactly as `app/api/decisions.py` documents its own department-scoping limitation. **This is an accepted MVP trust-boundary decision, ratified by the Founder, recorded so no future reader mistakes it for an omission.**

**If database-level enforcement is ever wanted**, the realistic routes are a non-partial uniqueness structure over active memberships or a denormalized company-user projection. Both carry semantic consequences for the existing membership model. Both are out of M9 scope and are recorded here only so the future decision starts from a known position.

---

## 12. Provenance Model

**Lineage, not duplication:**

```
Action → DecisionMemory → ReasoningReceipt → evidence_refs
Action → DecisionMemory → situation_id (when present)
```

`Action` carries **neither** `reasoning_receipt_id` **nor** `situation_id`. This follows the precedent already ratified in the M8 OME Provenance Integrity Decision and visible in `app/ome/models/decision_memory.py`: *"Authoritative evidence provenance for a decision comes ONLY through reasoning_receipt_id … this model deliberately carries no evidence_refs field of its own."* The same logic applies one level down.

Duplicating either id would create two paths to the same fact, which is two paths to *disagree*. The only cost is a join, and no MVP query is join-sensitive at this volume.

**When duplication would become justified** (recorded, not anticipated): if an Action could ever be created against something other than a Decision, or if a Decision could be re-pointed to a different receipt after Actions exist. Neither is possible under this contract — `decision_memory_id` is required, and a `DecisionMemory` is append-only with supersession rather than mutation.

---

## 13. Relationship to OutcomeMemory

**`OutcomeMemory.action_id` is NOT added (Decision 13 = NO).**

- A Decision may have many Actions and many Outcomes.
- An Outcome usually evaluates the **Decision** — "did the plan work" — not one Action in isolation.
- Adding `action_id` would invite one-to-one causal reading: Action completed + Outcome negative ⇒ *this action failed*. That is precisely the inference `Outcome ≠ causal proof` forbids, and a nullable FK is a poor place to litigate it.

**The domains stay separate at every level:**

| | Execution | Outcome |
|---|---|---|
| Question | Was the work done? | Did it work? |
| Vocabulary | `pending` / `in_progress` / `completed` / `cancelled` | `positive` / `negative` / `mixed` / `unknown` |
| Table | `ome_actions` | `ome_outcome_memories` |
| Anchored to | A Decision, via Action | A Decision, directly |
| Timing | During | After |
| UI | Action panel | Existing `RecordOutcome` — unchanged |

**`completed_at` must never be read as evidence that an Outcome occurred, and marking an Action `completed` must never prompt, prefill, or auto-create an OutcomeMemory.** The existing OM retrieval law — a Decision is retrievable only with ≥1 active Outcome (`organizational_memory_retrieval_service.py`) — stays exactly as it is; a completed Action does not make a Decision retrievable.

**Trigger to revisit:** a real Golden Path requirement where an Outcome must demonstrably attach to one specific Action among several. Not before.

---

## 14. Relationship to Organizational Memory Retrieval

**No change (Decision 14 = NO).**

`OrganizationalMemoryRetrievalService` composes `DecisionMemoryRepository` and `OutcomeMemoryRepository` and returns outcome-backed Decision+Outcome aggregates. M9 does not touch it, does not add an Action repository to it, and does not alter eligibility.

**This is a hard requirement, not a preference.** Changing retrieval would silently alter what every future AI response reasons from, which would make M9 an invisible change to NAWA's recommendation behavior — the opposite of an auditable foundation. Any Action-aware retrieval is a separate, separately-justified decision.

**Naming guard (contract law).** The recommended table names carry the `ome_` prefix (§21.1). That prefix marks the *lineage family* — records anchored to the receipt→decision chain under the composite-FK tenant pattern. **It does not imply retrieval eligibility.** No current or future retrieval path may treat `ome_*` membership as a reason to include Actions in organizational memory retrieval.

**Future value, if it is ever proven:** "we decided this before, here's what we did, here's what happened" is a stronger memory item than "we decided this before, here's what happened." That is a genuine future upside and an explicit non-goal today.

---

## 15. Relationship to Operational Events

**No automatic emission (Decision 15 = NO).** Creating, starting, completing, or cancelling an Action emits no operational event in the foundation.

**Reasoning:** operational events feed situation grouping and, downstream, reasoning. Emitting on Action state changes would inject *NAWA's own internal bookkeeping* into the company's operational signal, where it could form situations and influence recommendations — a feedback loop from the system into its own inputs, created as an unexamined side effect.

**Where it might genuinely be useful later:** a Live Operational Timeline that shows executive activity alongside company activity — "decision recorded, action started, action completed" as a visible governance narrative. That is a *presentation* need and should be met by reading `ome_action_change_events` directly, not by writing into the operational event stream. Deferred, with the preferred solution named.

---

## 16. Relationship to Truth Layer

Action execution state is **current operational state**, not historical memory. It describes what is happening now.

- Action state is **not** injected into AI reasoning in the foundation slice. No `Action` read appears anywhere in the reasoning pipeline.
- Historical organizational memory (Decision + Outcome) stays cleanly separated from current execution state. Mixing them would let "three actions are in progress" read as historical experience.
- **If** Action state is ever surfaced to reasoning, it enters as **Current Truth** — through the Truth Layer / OCE current-state channel — never through the organizational memory channel. Recording that routing now prevents the wrong integration later.
- Plausible future value: NAWA answering "you decided this three weeks ago and the action is still `pending`" — a genuinely useful executive observation, and precisely the kind of thing that must be a *current-state* statement rather than a memory-derived one.

---

## 17. Relationship to Company Brain

**No Action state may mutate Company Brain. Automatically or otherwise.**

- Repeated completions are not a policy.
- Successful Actions are not a policy.
- Cancelled Actions are not a policy change.
- Completion rates, cycle times, and per-user statistics are not organizational learning, and none may be computed into Company Brain.

Any future learning mechanism remains separately governed with human ratification, per the Deferred Architecture Pack (DAP-A-L7) and standing law.

---

## 18. Track A Boundary

Track A remains **DEFERRED — ARCHITECTURE BLUEPRINT READY**. M9 implements **none** of: retention-policy engine, archive framework, compaction, offboarding, governed erasure, OME lifecycle governance.

**Future dependency recorded (not activated):** `ome_actions` and `ome_action_change_events` are new durable, tenant-scoped, lineage-linked records. When Track A activates they should be registered as durable record types with a retention class, and their audit-spine fields identified (`id`, `company_id`, `decision_memory_id`, `created_by_user_id`, timestamps, status-event chain). Adding two more record types to the current keep-everything posture changes nothing structurally — that posture already holds three.

Per the Pack, this **marginally** pulls Track A's volumetric triggers closer. Actions are created by explicit human acts, so their volume is bounded by human effort — far below reasoning-receipt volume. Not a material influence.

---

## 19. Track B Boundary

Track B remains **DEFERRED**. Situation Memory remains **DEFERRED — NOT MVP BLOCKING**. **M9 introduces no durable SituationMemory.**

For M9 provenance, `Action → DecisionMemory → situation_id` is sufficient. The provenance question M9 raises is *"who authorized this work, and on what decision?"* — answered completely by `DecisionMemory`.

**The boundary that keeps it true (binding — §20 of the Pack, restated here as an M9 constraint):**

> **M9 MVP must not introduce deferred or condition-triggered future execution that automatically executes when a later condition becomes true.**

Under autonomous conditional execution, authorization context and execution context diverge, "was this still the right action when it fired?" becomes unanswerable, and Track B reopens (trigger TB-H4). Holding this line is the cheapest way M9 avoids pulling a second deferred track into its own scope.

**Permitted:** human-updated execution status; human-performed reassignment; human-visible information that informs a person without performing anything. No deadline field exists in MVP (§7.2), so nothing has a time anchor to fire from.
**Out of bounds (Decision 18 = NO):** trigger-based dispatch, scheduled auto-fire, agentic execution, automatic external API calls, automatic operational commands, automatic financial transactions, automatic messages or actions on the company's behalf.

The line is **who decides the moment has come.** A human deciding later is fine. A condition deciding later is not.

---

## 20. Durable OME Registry Decision

**Explicitly evaluated. Decision 16 = NO — not required now.**

The question is not "will the registry be useful eventually" but "does Action persistence *genuinely require* it." It does not:

| Registry capability | Does M9 need it? |
|---|---|
| Enumerate durable record types | No — M9 knows its own two tables |
| Attach a retention class per type | No — no retention behavior exists |
| Drive tier transitions | No — no tiers exist |
| Drive offboarding/export enumeration | No — no offboarding exists |
| Declare audit-core fields per type | No — no lifecycle reads them |

A registry pays off only when something **iterates over record types generically** — lifecycle, export, erasure. M9 does none of these. Building it now would be infrastructure created because future tracks might reuse it, which the Pack's minimum-foundation principle explicitly forbids:

> *The first activated capability that genuinely requires the durable OME record registry should build only the minimum extensible registry foundation required for its own scope. Deferred tracks may inherit that foundation later.*

M9 is not that capability. **What M9 owes instead is one paragraph** in whatever registry eventually exists, listing `ome_actions` and `ome_action_change_events` — which §18 has now pre-written.

---

## 21. Persistence / Migration Direction

**Migration 015 has been created as part of ACTIVE Slice 1 (`migrations/015_decision_execution_foundation.sql`), successfully live-local validated against the existing project-local `nawa-postgres` PostgreSQL 16 / pgvector development instance (checksum `aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a`, 36/36 live schema tests passed), and committed locally in `09ac78d56e64c36263f5d3f4d0120904503b88a1`. It is NOT YET PUSHED, and has not been applied to any production or shared database. This section remains the authoritative shape specification the implementation was built against.**

### 21.1 Naming (Founder Decision — low stakes, flagged)

Recommended: **`ome_actions`** and **`ome_action_change_events`**, in `app/ome/`.

Rationale: consistent with `ome_reasoning_receipts` / `ome_decision_memories` / `ome_outcome_memories`; inherits the composite-FK tenant pattern, the error conventions, and the module layout without duplicating any of that plumbing in a parallel package.

**The tension, stated:** `ome_` reads as "organizational memory", and an Action is current execution state, not memory. The alternative (`decision_actions`, `execution_actions`, `app/execution/`) is defensible and would make the domain boundary visible in the name. This contract recommends `ome_` plus the explicit naming guard in §14, on the grounds that a rule is a better guard than a prefix and a parallel package duplicates real infrastructure for a semantic signal. **A Founder override here has no architectural consequence** — it is a rename, decided before Slice 1, and nothing else in this contract depends on it.

### 21.2 Keys, FKs, tenancy

- `ome_actions`: PK `id`; FK `company_id → companies(id)`; **composite FK** `(decision_memory_id, company_id) → ome_decision_memories(id, company_id)` — the target `UNIQUE (id, company_id)` already exists in migration 014, so no change to any existing table is required; plain FK `created_by_user_id → users(id)`; **plain FK `assigned_user_id → users(id)`** (composite unavailable — §11.2; service-layer validated); **`UNIQUE (id, company_id)`** so the change-event table can FK tenant-safely.
- `ome_action_change_events`: PK `id`; FK `company_id → companies(id)`; **composite FK** `(action_id, company_id) → ome_actions(id, company_id)`; plain FKs `changed_by_user_id`, `from_assigned_user_id`, `to_assigned_user_id` → `users(id)`.
- **No `ON DELETE` clauses anywhere**, matching 014.
- **Migration 015 is purely additive** — two new tables, zero alterations to existing tables. Unlike 014 (which had to add a UNIQUE constraint to `operational_situations`), M9 needs nothing from any existing table.

### 21.3 Constraints

- `chk_ome_actions_status` — `status IN ('pending','in_progress','completed','cancelled')`.
- `chk_ome_actions_title_not_blank` — non-empty after trim.
- `chk_ome_actions_completed_at_consistent` — `completed_at IS NOT NULL` **iff** `status = 'completed'`.
- `chk_ome_actions_cancelled_at_consistent` — `cancelled_at IS NOT NULL` **iff** `status = 'cancelled'`.
- `chk_ome_action_change_events_change_type` — `change_type IN ('status','assignment')`.
- `chk_ome_action_change_events_shape` — the discriminated-union consistency CHECK, in the same style as `chk_ome_decision_memories_status_supersession_consistent`: a `status` event has `to_status` NOT NULL and both assignee columns NULL; an `assignment` event has both status columns NULL and `from_assigned_user_id IS DISTINCT FROM to_assigned_user_id` (which correctly permits NULL→user and user→NULL while rejecting a no-op).
- `chk_ome_action_change_events_to_status` — four-state CHECK when present.
- `chk_ome_action_change_events_no_self_transition` — `from_status IS NULL OR from_status <> to_status`.
- Every CHECK is **re-validated in Python `__post_init__`**, per the 014 fail-closed-at-both-boundaries discipline.

### 21.4 Indexes

- `(company_id, decision_memory_id)` — the primary access path: list actions for a decision.
- `(company_id, status)` — open-work views.
- `(company_id, created_at DESC)` — recent actions.
- `(company_id, action_id, changed_at)` on the change-event table.
- `(company_id, assigned_user_id)` — included in MVP; drives "what am I responsible for".

### 21.5 Delete / mutation semantics (Decision 12)

**No hard delete. No soft delete. No delete endpoint.** Matching the OME precedent exactly (`app/ome/errors.py`: "OME hard deletion is not supported in MVP").

- Cancellation is a status transition, not a deletion. It is operational history and must remain visible.
- A soft-delete flag is refused: it would create a second, competing "this doesn't count" concept alongside `cancelled` and immediately raise "does a soft-deleted action still show in the decision's action list?" — a question with no good answer.
- Change-event rows are immutable and never removed.
- **`assigned_user_id` is the one client-supplied mutable field**, and only while the Action is non-terminal (§7.5). Every change is validated (§11.3) and ledgered (§9.4).
- Eventual removal is Track A's governed-erasure concern, not M9's (§18).
- **Title and instructions are not editable** (§22). Mutability in M9 is confined to `status` with its paired timestamps, and `assigned_user_id`.

---

## 22. API Contract Direction

**Recommended surface — five endpoints, deliberately narrow:**

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/actions` | Record one human-governed action against a decision |
| `GET` | `/actions` | List, **requires** `decision_memory_id` query param in MVP |
| `GET` | `/actions/{id}` | One action, optionally with its status history |
| `PATCH` | `/actions/{id}/status` | Transition execution state |
| `PATCH` | `/actions/{id}/assignee` | Set, change, or clear the responsible human |

**Two narrow PATCH endpoints, not one generic `PATCH /actions/{id}`.** This is a deliberate narrowing. A generic PATCH would permit editing `title` and `instructions` after the fact, quietly making the human's recorded authorization mutable — the one property that makes an Action auditable. Two purpose-named endpoints make the entire mutable surface readable from the route table: **status, and assignee. Nothing else.**

**`PATCH /actions/{id}/assignee`** accepts a single nullable `assigned_user_id` (explicit `null` clears it) — **the only value the client supplies**. It validates same-company active membership (§11.3), rejects the change if the Action is terminal (`409`), and writes the Action update plus the assignment change-event in one transaction under the locked-row discipline specified normatively in **§24.1**. `POST /actions` accepts the same optional nullable field under the same validation.

The cost, stated: a typo in a title is uncorrectable except by recording a new Action. Consistent with `DecisionMemory`, which has the same property for the same reason. Accepted.

**`GET /actions` requires `decision_memory_id`.** An unfiltered company-wide action list is the first step toward a task-board UI. Requiring the decision anchor keeps the API shaped like the domain. A company-wide view, if ever wanted, is a separate deliberate decision.

**Conventions, all inherited unchanged from `app/api/decisions.py`:**

- **Auth:** `Depends(require_permission("memory.write"))`.
- **`company_id` and acting user:** always from `AuthContext` (JWT). Never client-supplied, never inferred from the Decision's creator.
- **Request models:** Pydantic `ConfigDict(extra="forbid")` — any undeclared field (`company_id`, `created_by_user_id`, `status`, `completed_at`, `created_at`) fails validation with 422 before the handler runs. Nothing silently ignored.
- **404 convention:** a decision, action, or assignee not found inside the caller's company returns a generic 404 with no hint that it exists elsewhere. No `CrossTenantReference` error class is added.
- **Validation:** non-blank title; `decision_memory_id` resolved through a company-scoped repository load before use; status transition validated against §8 in the service, not the route.
- **Errors:** extend `app/ome/errors.py` minimally — `ActionNotFound`, `InvalidActionTransition`. Reuse `InvalidMemoryInput` for input validation rather than adding a parallel class.
- **Service dependency:** the `get_..._service(request)` pool pattern from `decisions.py`.
- **Router registration:** `app.include_router(actions_router)` in `app/main.py`, after `outcomes_router`.

**Status codes:** `201` create; `200` read and transition; `404` not found in company; `409` invalid transition (a real conflict with current state — distinct from `422` malformed input); `422` validation.

---

## 23. Frontend Golden Path

The Founder's candidate flow is sound. Two amendments, both narrowing.

**Recommended Golden Path:**

1. CEO receives an AI recommendation in chat. *(unchanged)*
2. CEO records a Human Decision via the existing `RecordDecision` component. *(unchanged)*
3. After the Decision is recorded, the UI offers **Record Action** — the same disclosure pattern `RecordDecision.tsx` already uses (collapsed affordance → form → submitted state).
4. The human enters **title** (required), **instructions** (optional), and **optionally selects an assignee** from the company's members. **No due date** (Founder Decision 2 — §7.2).
5. Action is saved, linked to the DecisionMemory.
6. The human can later move `pending → in_progress → completed`, or `cancel`. Terminal transitions require a confirmation step (§8). While the Action is non-terminal, the human may also reassign it, or clear the assignee (§7.5).
7. The Action is visibly human-authored: it shows who recorded it and when, and carries no AI attribution.
8. Outcome recording stays exactly where it is, via the unchanged `RecordOutcome` component.

**Amendment 2 — the AI recommendation stays visible but is never a control.** Where the chat response already renders "Recommended Actions" prose, it stays rendered as reference text the human can read while typing. It is not a button, not a checkbox, not a "convert to action" affordance, and not a prefill source.

**Assignee selector requirements:**

- Offers **only** users with an active membership in the current company — the UI list and the server validation must agree, and the server is authoritative regardless.
- **"Unassigned" is a first-class, selectable state**, not an empty error. It is the default.
- `assigned_user_id` is persisted **only** after an explicit human choice. No default-to-self, no default-to-CEO, no most-recent-assignee memory.
- **The AI never selects an assignee**, never suggests one, and never ranks candidates. There is no code path from a recommendation to this control.

**No redesign of the chat UI.** One new component (`RecordAction.tsx`) beside `RecordDecision.tsx`, one API module (`lib/api/actions.ts`) beside `lib/api/decisions.ts`, plus i18n entries in the existing scoped `ar.ts` / `en.ts` dictionaries with RTL/LTR preserved. The member list needs a company-members read; if no suitable endpoint exists, adding one is in Slice 3 scope and is a plain company-scoped read.

### 23.1 No AI prefill (Decision 17 = NO)

Not even behind an explicit "Use recommendation as draft" button, in the first slice.

**Reasoning.** Prefill is not a UI convenience; it is a claim about authorship. Once the field starts pre-filled, the modal human act becomes *accepting AI text*, and `ome_actions.title` silently becomes a copy of `CEOBrief.recommended_next_actions` in most rows. The record would still be technically human-authorized and substantively AI-authored — and nothing in the data would distinguish the two.

**When it could become safe** (deferred, with the conditions named): the record would need to distinguish AI-drafted from human-authored text — an `authorship` marker, or storing the source recommendation reference alongside the human's final text so that any later edit is visible. That is a real design with a real schema cost. It should be considered only after the first slice proves what humans actually type when given a blank field — which is also the cheapest way to learn whether the AI's recommendations are any good.

---

## 24. Concurrency / Idempotency

Minimum safe behavior. No distributed workflow infrastructure.

| Risk | Recommended behavior |
|---|---|
| **Double-click on create** | Accept the duplicate. Two Actions on one Decision is a *valid* domain state (§6), so deduplication would have to guess intent. Mitigate in the UI: disable the submit button while in flight — the pattern `RecordDecision.tsx` already uses via `isSubmitting`. `PROPOSED`: no server-side idempotency key in MVP |
| **Concurrent status transitions** | `SELECT ... FOR UPDATE` on the action row inside the transaction, validate the transition against the locked current state, write the row update and the status event together. This is the exact pattern `DecisionMemoryRepository.supersede_with_new_decision` already uses |
| **Repeat PATCH (same target status)** | Reject with `409`, do not silently succeed. A no-op that reports success would write a misleading "nothing happened" into an audit ledger, or worse, a self-transition event. `chk_ome_action_change_events_no_self_transition` enforces this at the database too |
| **Repeat PATCH (stale client, invalid transition)** | `409` with the current state named, so the UI can refresh rather than retry |
| **Action + first status event atomicity** | Single transaction. An Action without its creation event must be impossible |
| **Concurrent reassignment** | Same locked-row discipline as status, stated normatively in §24.1. The server never trusts a client-supplied prior assignee |
| **Lost update on `updated_at`** | Covered by the row lock; no optimistic-concurrency token in MVP |

### 24.1 Assignment write invariant (normative)

`PATCH /actions/{id}/assignee` and the assignment path of `POST /actions` are held to exactly the same audit-integrity standard as status transitions. **Status concurrency is unchanged** (§24 table row 2); this subsection aligns assignment wording to it.

**Required sequence — one transaction, no exceptions:**

1. **Begin** one database transaction.
2. **Read and lock** the target Action row using the repository's row-locking mechanism (`SELECT ... FOR UPDATE`, the pattern `DecisionMemoryRepository.supersede_with_new_decision` already uses).
3. **Confirm, against the locked row:** the Action belongs to the authenticated company; the Action is non-terminal (§7.5); and the **current `assigned_user_id` is read from the locked row**, never from anywhere else.
4. **If the requested new assignee is non-null**, validate active same-company membership (§11.3) — nonexistent, non-member and other-company all resolve to the generic 404.
5. **Capture `from_assigned_user_id` from the locked row.** See the trust boundary below.
6. **Update** `ome_actions.assigned_user_id` (and `updated_at`).
7. **Insert exactly one** immutable assignment change event: `change_type='assignment'`, `from_assigned_user_id` → `to_assigned_user_id`, with `changed_by_user_id` server-derived from the authenticated user context.
8. **Commit** the row update and the event insert **atomically**.

**Rollback:** if the update or the event insert fails for any reason, the **entire transaction rolls back**. An Action whose `assigned_user_id` changed without a corresponding ledger row — or a ledger row without the corresponding row change — must be impossible, not merely unlikely. This is the same guarantee already required for Action creation and its first status event.

**Client trust boundary — normative:**

| Value | Source | Never |
|---|---|---|
| `from_assigned_user_id` | The **locked persisted Action row**, read inside the transaction | **Never** client authority. A client-supplied "from" value is ignored if present and rejected by `extra="forbid"` |
| `changed_by_user_id` | Server-derived from the authenticated `AuthContext` | Never client-supplied |
| `company_id` | Server-derived from `AuthContext` | Never client-supplied |
| `to_assigned_user_id` | **The only value the client supplies** — a user id, or explicit `null` to clear | — |

**The concurrent-reassignment invariant.** The rule exists to prevent a specific falsified history. Suppose the current assignee is **Ahmed**, and two requests arrive concurrently: one reassigning **Ahmed → Mohammed**, the other **Ahmed → Ali**.

NAWA must **never** produce a ledger containing both `Ahmed → Mohammed` **and** `Ahmed → Ali` as independently valid transitions from the same state. That history is a lie in two directions at once: it claims Ahmed was replaced twice from one starting point, and it makes the actual sequence of responsibility unrecoverable — which is exactly the silent rewriting of historical responsibility the ledger exists to prevent (§9.4).

Because step 5 reads `from_assigned_user_id` from the **locked** row, the second transaction can only observe the serialized post-commit state. Truthful outcomes are therefore:

```
   Ahmed → Mohammed  then  Mohammed → Ali        (serialized, both succeed)
or Ahmed → Ali       then  Ali → Mohammed        (serialized, other order)
or Ahmed → Mohammed  and   the competing write fails / retries
```

**Forbidden:**

```
   Ahmed → Mohammed
   Ahmed → Ali            ← both claiming the same prior state
```

The audit history must always reflect the **actual serialized order**. Whether the losing transaction blocks and then proceeds from the updated state, or fails and is retried, is an implementation choice for the chosen transactional strategy — but reading the prior assignee from anywhere other than the locked row is not.

**Assignment and status remain distinct.** They are separate endpoints, separate `change_type` values, separate validation, and separate CHECK branches (§21.3). One transaction never performs both. A reassignment is not a status transition and must never be recorded as one.

---

## 25. Architecture Options Compared

Scores are comparative judgements. **H/M/L**; for complexity and risk, lower is better.

| | **M9-1** Current-state row only | **M9-2** Row + status ledger | **M9-3** Event-sourced | **M9-4** Reuse DecisionMemory fields | **M9-5** Generic Task entity |
|---|---|---|---|---|---|
| Domain integrity | H | **H** | H | **L** — mutable execution state on an append-only record | **L** — no decision anchor |
| Human governance | M | **H** | H | M | L |
| Auditability | **L** — only latest state survives | **H** | H | L | L |
| MVP complexity | **H** (best) | **M** | **L** (worst) | M | M |
| Future extensibility | M | **H** | H | **L** — schema fights back | H |
| Tenant safety | H | **H** | M | H | M — no decision FK to anchor to |
| OME compatibility | H | **H** | M — breaks index/query patterns | L — corrupts supersession semantics | L — sits outside the lineage |
| Risk of becoming project management | M | **L** — decision anchor + narrow API | M | L | **H** — this *is* a task tracker |
| Future automation readiness | M | **H** — a transition ledger is the natural seam | H | L | M |

**Why M9-4 (reuse `DecisionMemory`) is rejected outright.** `ome_decision_memories` is append-only with supersession; a mutable `execution_status` column would mean every status change either mutates an append-only record or creates a superseding decision, making it appear the company changed its *decision* when it only started the *work*. It also caps the model at one action per decision, which §6 shows is wrong. This option corrupts a ratified schema to save one table.

**Why M9-5 (generic Task) is rejected outright.** Without a required decision anchor, NAWA acquires a task tracker. That is the specific product failure §2 names, and it would arrive as a nullable foreign key rather than as a strategy decision.

**Why M9-3 (event sourcing) is rejected.** Sophistication with no payer, at a real cost to query patterns and testability, for a four-state lifecycle.

**Why not M9-1.** It is genuinely tempting — it is the smallest thing that works, and the timestamps recover part of the history. But it cannot answer "who moved this and when", and NAWA's claim is auditable human governance. The delta to M9-2 is one small table with a precedent already in the repo (`013_memory_fact_history.sql`).

---

## 26. Recommended Architecture

**M9-2.** Two additive tables; one domain service enforcing the state machine and assignee validation; five narrow endpoints; one frontend component; nullable service-validated assignee; no `due_at`; no autonomy; no retrieval change; no registry; no lifecycle.

```
POST /decisions ──▶ ome_decision_memories        (exists, unchanged)
                            │
                            │ composite FK (decision_memory_id, company_id)
                            ▼
POST /actions   ──▶ ome_actions                  (new — current execution state,
                            │                     incl. nullable assigned_user_id)
                            │ composite FK (action_id, company_id)
                            ▼
PATCH /actions/{id}/status   ─┐
PATCH /actions/{id}/assignee ─┴▶ ome_action_change_events  (new — one append-only
                                                            ledger: status +
                                                            assignment)

ome_outcome_memories  ── still anchored to ome_decision_memories, untouched
OM retrieval          ── untouched
Reasoning pipeline    ── untouched
Company Brain         ── untouched
Operational events    ── untouched
```

---

## 27. MVP Non-Goals

Binding for M9:

no autonomous execution · no condition-triggered execution · no scheduled auto-fire · no agentic execution · no external integration execution · no ERP task engine · no project-management suite · no subtasks · no dependencies · no recurrence · no comments · no attachments · no priority · no AI auto-materialization · no AI prefill · no AI-selected assignee · no `due_at` · no scheduling or deadline behaviour · no reassignment of terminal Actions · no department scoping · no Outcome causality assumption · no `OutcomeMemory.action_id` · no OM retrieval change · no reasoning-pipeline injection · no operational event emission · no Company Brain mutation · no organizational learning · no Track A activation · no Track B activation · no SituationMemory · no durable OME registry · no hard delete · no soft delete · no title/instructions editing · no reopening of terminal states · no company-wide unfiltered action list · no notification system · no `failed` state (yet).

---

## 28. Proposed Implementation Slices

**Status as of v1.5 (Post-Commit State Reconciliation Amendment): Slice 1 is `ACTIVE — IMPLEMENTATION VALIDATED + COMMITTED LOCALLY / AWAITING INDEPENDENT POST-COMMIT VERIFICATION / NOT CLOSED`, committed in `09ac78d56e64c36263f5d3f4d0120904503b88a1`, not pushed; Slices 2–4 remain `PROPOSED — NOT ACTIVATED`.** No slice may begin without explicit Founder activation and a task document under `docs/execution/` (Repository First Policy) — Slice 1's is `docs/execution/m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md`. Slice 1's activation does not activate Slice 2, 3, or 4.

| Slice | Scope | Exit condition | Status |
|---|---|---|---|
| **M9 Slice 1 — Action Persistence Foundation** | Migration 015 (two additive tables incl. nullable `assigned_user_id` and the discriminated change ledger, constraints, indexes); `app/ome/models/action.py`, `action_change_event.py`. No repository, service, API, or wiring — mirroring M8 Slice 1 exactly | Migration applies cleanly and is reproducible; models round-trip `from_row`/`to_dict`; every CHECK re-validated in Python, including the change-event shape CHECK; cross-company decision FK insert rejected by the database in a test | `ACTIVE — IMPLEMENTATION VALIDATED + COMMITTED LOCALLY (09ac78d) / AWAITING POST-COMMIT VERIFICATION / NOT CLOSED` |
| **M9 Slice 2 — Repository, Domain Service & API** | `ActionRepository`, `ActionService` (state machine, assignee validation via the existing `MembershipRepository.get_active_membership`, transactional create-with-first-events, `FOR UPDATE` transitions), `app/api/actions.py` with all five endpoints, router registration, error classes | Transition matrix enforced in the service; invalid transition → 409; cross-company decision link → generic 404; cross-company or non-member assignee → generic 404 on **both** create and reassign; terminal reassignment → 409; `extra="forbid"` proven; chat has zero code paths to the write path | `PROPOSED — NOT ACTIVATED` |
| **M9 Slice 3 — Frontend Human-Governed Action Recording, Assignment & Status Updates** | `RecordAction.tsx`, `lib/api/actions.ts`, optional assignee selector over company members, status controls with terminal confirmation, AR/EN i18n with RTL/LTR, no AI prefill | Golden Path steps 1–8 completable by a human; assignee optional and human-chosen; no prefill and no AI-suggested assignee anywhere; Outcome flow visibly separate | `PROPOSED — NOT ACTIVATED` |
| **M9 Slice 4 — Golden Path E2E & Hardening** | Browser E2E of the full chain; concurrency tests; tenant-isolation tests; acceptance gate (§29) evidence | Every §29 criterion demonstrated on real Jannat data | `PROPOSED — NOT ACTIVATED` |

**Four slices, not five.** M8 split service and API into separate slices; merging them here is safe because `ActionService` is materially thinner than `DecisionMemoryService` — no supersession, no evidence resolution, no provenance construction. **If the Founder prefers strict M8 symmetry, splitting Slice 2 into 2A (service) and 2B (API) is a safe alternative** with no architectural consequence.

**Assignee support adds no slice.** It lands inside the existing three: the column and ledger shape in Slice 1, validation and the reassign endpoint in Slice 2, the selector in Slice 3. The slice count is unchanged at four.

---

## 29. M9 Acceptance Contract

M9 is **not** complete because an actions table exists. The Golden Path, executed on real Jannat Al-Firdaws data, must demonstrate every one of the following:

| # | Criterion | Evidence |
|---|---|---|
| 1 | AI recommendation remained advisory | The recommendation text is unchanged in `response_snapshot`; `ome_actions.title` contains human-typed text that does not match it verbatim |
| 2 | Human Decision remained explicit | A `DecisionMemory` exists with human-authored `decision_text`, created only by `POST /decisions` |
| 3 | Action creation was explicit and human-governed | The Action exists only after a human `POST /actions`; static proof that no chat/reasoning code path reaches `ActionService` |
| 4 | Action links to the correct Decision | `decision_memory_id` resolves to the Decision recorded in step 2 |
| 5 | One Decision supports multiple Actions | Two Actions recorded against one Decision; both persist and list correctly |
| 6 | Tenant isolation held | A company-B Decision id from a company-A session returns a generic 404; a direct cross-company insert is rejected by the database |
| 7 | **Assignee belonged to the same company** | An Action created with `assigned_user_id` persists only after the service confirms an active, non-deleted membership of that user in the Action's company. Proven on both `POST /actions` and `PATCH /actions/{id}/assignee` |
| 7b | **Cross-company assignee attempts fail safely** | A company-B user id supplied from a company-A session is rejected with the **generic 404**, on create and on reassign. The response must not distinguish "no such user" from "user exists elsewhere". A nonexistent user id produces an identical response |
| 7c | **Reassignment is truthfully audited** | Reassigning an Action writes an `assignment` change event carrying `from_assigned_user_id`, `to_assigned_user_id`, `changed_by_user_id`, `changed_at`. The prior assignee remains recoverable from the ledger after the change. Assigning from NULL and clearing to NULL are both ledgered |
| 7d | **Terminal Actions cannot be reassigned** | A reassignment attempt on a `completed` or `cancelled` Action returns 409 and writes no event |
| 7e | **Concurrent reassignment cannot falsify history** | Two concurrent reassignments from the same prior assignee never produce two ledger events claiming the same prior state. `from_assigned_user_id` is proven to come from the locked row, not from the client. The resulting ledger reflects the actual serialized order (§24.1) |
| 8 | Execution state stayed distinct from Outcome | An Action reaches `completed` while its Decision's Outcome is `negative`; both render, neither is derived from the other |
| 9 | No automatic execution occurred | No scheduler, trigger, or job touches Actions. No deadline field exists to fire from. No assignment causes anything to run |
| 10 | No Company Brain mutation | Company Brain byte-identical before and after the full Golden Path |
| 11 | No Track A / Track B side effect | No lifecycle, retention, archival, offboarding, or SituationMemory code or table introduced |
| 12 | OM retrieval unchanged | Retrieval output for a fixed input is identical before and after M9 |
| 13 | Audit provenance intact | For a completed, once-reassigned Action: who created it, which Decision authorized it, every status transition **and every assignment change** with actor and timestamp — all reconstructible from persisted rows alone, in one chronological read |
| 14 | No orphan Actions possible | `decision_memory_id NOT NULL` proven by a rejected insert |
| 15 | Terminal states are terminal | A transition out of `completed` or `cancelled` returns 409 |
| 16 | Action record is substantively immutable | No endpoint can change `title`, `instructions`, `decision_memory_id` or `created_by_user_id` after creation. The only mutable fields are `status` (with its timestamps) and `assigned_user_id` |

Criterion **13** is the milestone's real test. Criteria **7b** and **7c** are the ones that carry the accepted trust-boundary decision of §11.3 — because no database constraint stands behind assignee tenancy, these are not documentation, they are the enforcement. Criteria 10, 11 and 12 are the *negative* tests, and they matter as much as the positive ones: M9 must be provable as a change that added a capability without altering any existing behavior.

---

## 30. Risks / Open Questions

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **Scope drift into project management.** Priority, subtasks, assignees, boards each arrive as "one small field" | **High** | Required `decision_memory_id`; `GET /actions` requires a decision filter; §27 non-goals; every addition needs Founder ratification |
| R2 | **Execution/Outcome conflation in practice**, whatever the schema says — users writing outcome language into action titles | Medium | Separate UI surfaces, separate vocabularies, no shared control; `failed` deferred (§8.1); the trigger in §8.1 is the detector |
| R3 | **Assignee tenant safety has no database-level guard available** (§11.2) — a service-layer defect or bypass could persist a cross-company assignee the database would accept | **Medium–High**, accepted | Validation lives in the service (not the route) via the existing `MembershipRepository.get_active_membership`, so every caller inherits it; enforced as acceptance criteria 7, 7b, 7c, 7d rather than as prose; documented in the migration and `app/api/actions.py` headers, as `decisions.py` documents its own limitation. **Accepted trust-boundary decision, Founder-ratified (§11.3)** |
| R4 | **`memory.write` reuse becomes wrong** — assignment is now in MVP under a memory-writing permission | Low, accepted | Founder-ratified for MVP; every `memory.write` holder already records company-wide decisions, so naming an executor is not a real widening. Revised trigger: `department_id`, or the first execute-but-not-authorize role (§10) |
| R5 | **Pressure to auto-create Actions from AI recommendations** — it will look like an obvious UX win | Medium | §5 creation law; §23.1; the conditions under which prefill could ever be safe are written down so the debate starts from them |
| R6 | **Status ledger judged unnecessary** and dropped to save a table | Medium | §9.1: without it the audit claim is unsupportable; it is ~30 lines of DDL with an in-repo precedent |
| R7 | **Terminal states with no reopening frustrate users** after a mis-click | Low–Medium | UI confirmation on terminal transitions; correction by recording a new Action, mirroring `DecisionMemory` supersession |
| R8 | **Naming (`ome_` prefix) later read as retrieval eligibility** | Low | §14 naming guard as contract law; Founder may rename before Slice 1 at no cost |
| R9 | **Change-ledger creep** — a third `change_type`, then a payload column, then an event platform | Medium | §9.5 guard: closed two-value enum, no payload/JSONB/free-text column ever, never a replay source, Founder ratification required to add a variant |
| R10 | **Assignee read as accountability the product cannot enforce** — a named assignee who never sees the Action | Low–Medium | M9 deliberately ships no notification system (§27). The assignee is a *record of responsibility*, not a delivery mechanism, and the UI should not imply otherwise. Notification is a separate future decision |

**Open questions — none blocking:**

1. Should `GET /actions/{id}` include status history inline, or should history be a separate endpoint? *Recommend inline; the history is at most a handful of rows.*
2. Should the Action list appear inside the chat thread beside the Decision, or in a separate workspace panel? *Frontend detail; recommend beside the Decision for Slice 3, matching where the decision was recorded.*
3. Does the Live Operational Timeline eventually read `ome_action_change_events`? *Likely yes, and §15 states that reading it directly is preferred over emitting operational events.*

---

## 31. Founder Decisions Required

Two decisions are now **RATIFIED** and closed. Eight remain open, all with recommended defaults. **None blocks the contract.**

| # | Decision | Status / Recommended | Consequence if overridden |
|---|---|---|---|
| FD-1 | Approve **M9-2** (row + change ledger) as the architecture | **Approve** | M9-1 saves one table and loses transition and assignment auditability |
| ~~FD-2~~ | ~~Defer `assigned_user_id`~~ | **RATIFIED — REVERSED.** Assignee **included**, nullable, service-validated (§7.3, §11.3) | Closed |
| FD-2b | Approve **deferring `due_at`** | **RATIFIED — Founder Decision 2.** Deferred; `LIKELY FUTURE REQUIREMENT` (§7.2) | Closed |
| FD-3 | Approve **deferring `failed`** | **Approve** | Including it now risks execution/outcome conflation; adding later is cheap |
| FD-4 | Approve **reuse of `memory.write`** | **Approve** | `action.write` requires editing `role_permissions.py` and two role-seed migrations |
| FD-5 | Approve **terminal states are non-reopenable** | **Approve** | Reopening makes `completed_at` ambiguous and needs its own history semantics |
| FD-6 | Approve **`PATCH /actions/{id}/status`** instead of generic PATCH | **Approve** | Generic PATCH makes the human's recorded authorization editable |
| FD-7 | Approve table naming **`ome_actions` / `ome_action_change_events`** | **Approve** | Pure rename; decide before Slice 1; no other dependency |
| FD-8 | Approve **no AI prefill**, including behind an explicit button | **Approve** | Prefill without an authorship marker makes AI-drafted and human-authored text indistinguishable in the data |
| FD-9 | Approve the **four-slice sequence** (vs. M8's five-slice service/API split) | **Approve** | Splitting Slice 2 into 2A/2B is equally safe |
| **FD-10** | Approve **Option B** — one discriminated change ledger for status *and* assignment (§9.4) | **Approve** | Option C (a separate `ome_action_assignment_events` table) preserves the same history at the cost of one more table, one more repository, and a UNION to render a single timeline. Architecturally equivalent; no downstream consequence |
| **FD-11** | Approve **no reassignment of terminal Actions** (§7.5) | **Approve** | Permitting it would let responsibility be attached retroactively to closed work |

---

## 32. Final Architecture Contract

**M9 — Decision Execution Foundation** is a Decision-linked, human-governed Action record with an append-only execution-state ledger. It closes the gap between a recorded human decision and a recorded human outcome, and it closes nothing else.

**Binding contract terms:**

1. A separate `Action` entity — never a `DecisionMemory` field, never a generic Task.
2. `decision_memory_id` is **required**. No orphan Actions, ever.
3. One Decision → **many** Actions.
4. Execution states: `pending`, `in_progress`, `completed`, `cancelled`. Terminal states are terminal. `failed` deferred.
5. Execution state and Outcome state never share a vocabulary, a column, or a control.
6. Every transition is written by an identified human. **Nothing infers state** (M9-L1).
7. Provenance flows by lineage — `Action → DecisionMemory → ReasoningReceipt` — never by duplication.
8. **No autonomous or condition-triggered execution.** This is what keeps Track B deferred.
9. No OM retrieval change, no reasoning-pipeline injection, no operational event emission, no Company Brain mutation.
10. No hard delete, no soft delete, no editing of `title` or `instructions`.
11. `assigned_user_id` is **included and nullable**, with a plain `users(id)` FK plus **mandatory** domain-service validation of active same-company membership on every write. The database proves existence; the service proves tenancy. An accepted, documented trust boundary.
12. Reassignment is permitted while an Action is non-terminal, never rewrites authorization content, and is **always** ledgered. Silent reassignment is forbidden.
13. `due_at` is **not** in M9. Nothing in M9 reads a clock.
14. No durable OME registry, no Track A lifecycle, no SituationMemory.

**Documentation updated now that Slice 1 is active (v1.4):** `CURRENT_STATE.md`, `docs/execution/EXECUTION_BOARD.md`/`EXECUTION_INDEX.md`, and a new `docs/execution/m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md` task document (required before any slice begins) are updated to the minimum truthful status. `docs/execution/SPRINT_HISTORY.md` is **not** updated — the contract's own convention reserves it for slice/milestone *completion*, and Slice 1 is not complete. `app/api/README.md` is **not** updated — no router exists yet (Slice 1 has no API). No `docs/governance/` role documentation changes — no new permission introduced.

**Status as of this amendment:** M9 Architecture Contract v1.5 `FOUNDER ACCEPTED` · M9 implementation `ACTIVE — SLICE 1 ONLY` · Slice 1 `ACTIVE — IMPLEMENTATION VALIDATED + COMMITTED LOCALLY / AWAITING INDEPENDENT POST-COMMIT VERIFICATION / NOT CLOSED` (commit `09ac78d56e64c36263f5d3f4d0120904503b88a1`, parent `4e1650e957f8c6d337ec43adef014aa9411aed17`) · Slices 2–4 `PROPOSED — NOT ACTIVATED` · Migration 015 `CREATED, live-local validated against the existing project-local nawa-postgres development instance (checksum aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a, 36/36 live schema tests passed), and committed locally in 09ac78d — NOT pushed, NOT applied to any production or shared database` · Track A `DEFERRED — ARCHITECTURE BLUEPRINT READY` · Track B `DEFERRED — ARCHITECTURE BLUEPRINT READY` · Situation Memory `DEFERRED — NOT MVP BLOCKING` · Sprint EX-1 `PAUSED` · Full EBD-004 compliance `NOT ESTABLISHED` · Deferred Architecture Pack v1.3 `FOUNDER ACCEPTED`. **Slice 1 activation and its local commit authorize exactly migration 015 plus the two named domain models — nothing else. It does not authorize Slice 2, repositories, services, API, frontend, or any autonomous execution, and it does not authorize pushing to the remote.**

---

## Appendix A — Amendment Log

| Version | Date | Change | Authority |
|---|---|---|---|
| 1.0 | 2026-08-29 | Initial M9 Architecture Contract. Recommends M9-2 (Decision-linked Action + immutable status-transition ledger). Grounded against the repository at `claude-safe-review` @ `8cdb8d5`. Two substantive deviations from the proposed field list, both narrowing: `assigned_user_id` deferred out of M9 (no database-level tenant guard is structurally available — `users` has no `company_id`, and every `memberships` uniqueness index is partial and therefore unusable as an FK target), and `cancelled_at` added for terminal-state CHECK symmetry. Nine Founder decisions listed, all with recommended defaults, none blocking. **No slice activated. No migration created. No engineering authorized.** | CTO (draft); Founder (ratification pending) |
| 1.1 | 2026-08-29 | **Founder Decision Amendment.** (1) **Assignee included** — `assigned_user_id` is in the M9 MVP, nullable, plain `users(id)` FK plus mandatory domain-service validation of at least one active, non-deleted membership in the Action's company. Reverses the v1.0 recommendation to defer it. Repository check confirmed the required predicate already exists as `MembershipRepository.get_active_membership`, so no new query or membership semantics are needed. The absence of a composite FK is recorded as an accepted, Founder-ratified trust boundary, enforced through acceptance criteria 7/7b/7c/7d rather than prose. Reassignment permitted while non-terminal; never rewrites authorization content; always ledgered. (2) **`due_at` deferred** — removed from the persistence contract, API, Golden Path and acceptance gate; reclassified `LIKELY FUTURE REQUIREMENT`. (3) **Assignment auditability resolved as Option B** — the status ledger is generalized at design time into one discriminated `ome_action_change_events` table covering `status` and `assignment` changes; status-ledger semantics (NULL → pending initial event, atomic write, append-only, no replay) are fully preserved, and §9.5 adds an anti-creep guard. Option C recorded as a zero-consequence fallback (FD-10). Sections amended: header, 1, 3, 7.1–7.5, 9, 10, 11.3, 19, 21.1–21.5, 22, 23, 26, 27, 28, 29, 30, 31, 32. All Codex-ratified decisions preserved unchanged. Slice count unchanged at four; assignee support lands inside existing slices. **No slice activated. No migration created. No engineering authorized.** | Founder & CEO (decisions); CTO (amendment) |
| 1.2 | 2026-08-29 | **Final Precision Amendment.** Codex final architecture review passed with two non-blocking precision notes, both corrected here. (1) **Endpoint count corrected** — one live statement in §22 still read "four endpoints" after the assignee endpoint was added in v1.1; it now reads five, matching §1, §26 and §28. No endpoint was added or removed. (2) **Assignment-concurrency invariant made explicit** — new normative §24.1 specifies the single-transaction, locked-row sequence for `PATCH /actions/{id}/assignee`: lock the Action row, verify company and non-terminal state against the locked row, validate membership, capture `from_assigned_user_id` **from the locked row** (never client-supplied, as is `changed_by_user_id`), update the row and insert exactly one assignment event, commit atomically, roll back the whole transaction on any failure. States the concurrent-reassignment invariant with the Ahmed→Mohammed / Ahmed→Ali example and the forbidden dual-origin history, plus new acceptance criterion 7e. Status concurrency unchanged; assignment and status remain distinct endpoints, change types and CHECK branches. **No architecture direction changed. No Founder decision changed. No implementation activated.** | CTO (amendment) |
| 1.3 | 2026-08-29 | **Founder Acceptance Status Amendment.** Codex's final acceptance check passed v1.2 (`PASS — M9 ARCHITECTURE CONTRACT v1.2 READY FOR FINAL FOUNDER ACCEPTANCE`), and the Founder explicitly accepted the M9 Architecture Contract. A post-commit review found the document still carried stale `Draft` / `READY FOR FINAL INDEPENDENT REVIEW` status language dating from before that acceptance. v1.3 corrects only the document's live status: header now reads `Status: FOUNDER ACCEPTED — Architecture Contract` / `Implementation Status: NOT ACTIVATED`; §1's returned status now reads `FOUNDER ACCEPTED — IMPLEMENTATION NOT ACTIVATED`; the closing status line in §32 now names the contract's own acceptance status alongside M9 implementation, Slice 1, and migration 015 status. Founder acceptance of the Architecture Contract is recorded explicitly as **not** an engineering authorization. Sections amended: header, §1, §32. Historical amendment-log entries (1.0–1.2) are left as originally written. **No architecture decision changed. No Founder decision changed. M9 implementation remains NOT ACTIVATED. Slice 1 remains NOT ACTIVATED. Migration 015 remains absent and not authorized.** | Founder & CEO (acceptance); CTO (amendment) |
| 1.4 | 2026-08-31 | **Slice 1 Activation & Persistence Precision Amendment** (corrected in place across three review rounds; subsequently committed locally in `09ac78d56e64c36263f5d3f4d0120904503b88a1` alongside the Slice 1 implementation it describes — see v1.5 below for the post-commit reconciliation). The Founder explicitly activated M9 Slice 1 — Action Persistence Foundation only. Migration 015 and the `Action`/`ActionChangeEvent` domain models were implemented, then corrected and validated across three passes: **(1)** nine persistence/governance findings (`from_status` database CHECK added; `changed_at` switched from `NOW()` to `clock_timestamp()`, removing the transaction-start-time inversion risk for a future row-locked write path; index and append-only-enforcement claims made precise; the `docs/execution/m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md` task document filed per the Repository First Policy this contract itself names); **(2)** a wording-precision pass removing every implication that `clock_timestamp()` is a strict monotonic causal sequence — it is audit/display time that avoids one specific, identified inversion risk, not a formal version counter, and the ledger's persisted from-state/to-state values remain the authoritative audit evidence; plus 8 obsolete M8 migration-frontier tripwire tests corrected (test files only) and stale "not yet pushed" governance-doc wording corrected once the remote checkpoint closed at `4e1650e957f8c6d337ec43adef014aa9411aed17` was verified; **(3)** live-local validation against the existing project-local `nawa-postgres` PostgreSQL 16 / pgvector development instance: migration 015 applied and recorded (checksum `aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a`), 36/36 live M9 schema tests passed, 1092/1092 full backend regression suite passed with 0 failures — never applied to production or shared infrastructure. This documentation-reconciliation round corrected the remaining stale current-state wording this validation surfaced: header now reads `Implementation Status: ACTIVE — SLICE 1 ONLY ... live-local validated`; §1's returned status names Slice 1 active *and validated*; §9.3's `changed_at` field spec corrected from `DEFAULT NOW()` to `DEFAULT clock_timestamp()` with the same non-monotonic precision language used elsewhere; §21's opening line corrected from "Migration 015 is NOT created" to record its creation and validation, still uncommitted/unpushed/not-applied-to-any-shared-database; §28's intro and Slice 1 row now read `ACTIVE — IMPLEMENTATION VALIDATED / UNDER INDEPENDENT REVIEW / NOT CLOSED` (Slices 2–4 rows unchanged); §32's status line corrected to distinguish local-validated from committed/pushed/production-applied; the closing footer's "Slices 2–4 remain SELECTED — NOT ACTIVATED" corrected to `PROPOSED — NOT ACTIVATED` (matching §28, never `SELECTED`, which this contract reserves for M9 itself). Sections amended: header, §1, §9.3, §21, §28, §32, closing footer. Historical amendment-log entries (1.0–1.3) are left as originally written. **No architecture decision changed. No Founder decision changed. No new sequencing/versioning primitive introduced. No API/domain/state-machine expansion. Slice 1 is implemented, corrected, and live-local validated, but not committed, not pushed, and not closed — independent review is still pending. Slices 2–4 remain PROPOSED — NOT ACTIVATED. No autonomous execution, Track A, Track B, or OME registry activated.** | Founder & CEO (activation); CTO (amendment) |
| 1.5 | 2026-09-01 | **Post-Commit State Reconciliation Amendment.** Following Founder stage+commit authorization, the validated v1.4 package (Slice 1 implementation: migration 015, `Action`/`ActionChangeEvent` domain models, tests, and governance documentation as they stood after live-local validation) was staged and committed in exactly one commit: `09ac78d56e64c36263f5d3f4d0120904503b88a1` ("M9 Slice 1: add action persistence foundation," parent `4e1650e957f8c6d337ec43adef014aa9411aed17`, 19 files, containing precisely the validated package). Independent Codex review of that commit found the implementation, migration, tests, package scope, and checksum sound, with one remaining defect: stale post-commit governance wording across this contract and the M9 execution-tracker documents still described Slice 1 / migration 015 as uncommitted or working-tree-only. v1.5 corrects only that wording, in this contract: header (`Implementation Status`, `Version`), §1's returned status, §21's opening line, §28's intro and Slice 1 row, §32's status line, and the closing footer now all state that Slice 1 and migration 015 are **committed locally in `09ac78d`, not yet pushed** (`origin/claude-safe-review` still at `4e1650e957f8c6d337ec43adef014aa9411aed17`), status `ACTIVE — IMPLEMENTATION VALIDATED + COMMITTED LOCALLY / AWAITING INDEPENDENT POST-COMMIT VERIFICATION / NOT CLOSED`. `CURRENT_STATE.md`, `EXECUTION_BOARD.md`, and `EXECUTION_INDEX.md` were corrected identically outside this contract. This amendment records only: the local implementation commit `09ac78d`; that it is not yet pushed; Slice 1's current committed-locally/not-closed status; that Slices 2–4 remain `PROPOSED — NOT ACTIVATED`. **No domain semantics changed. No persistence schema changed. No state machine changed. No API changed. No Founder decision changed. Slice 1 remains NOT CLOSED pending independent post-commit verification; only the Founder may authorize the subsequent closure-state update.** | Founder & CEO (commit authorization); CTO (amendment) |

---

*This document is an architecture contract. Founder acceptance of the contract is a documentation/governance status, not an engineering authorization by itself. M9 Slice 1 — Action Persistence Foundation is ACTIVE — IMPLEMENTATION VALIDATED + COMMITTED LOCALLY / AWAITING INDEPENDENT POST-COMMIT VERIFICATION / NOT CLOSED (migration + domain models only, live-local validated, committed locally in `09ac78d56e64c36263f5d3f4d0120904503b88a1`, not pushed). Slices 2, 3, and 4 each remain PROPOSED — NOT ACTIVATED. No further slice may begin without its own explicit Founder activation and its own task document under `docs/execution/`.*
