# ENG-CONF-001 — Constitutional Conformance Remediation (Memory Precedence)

**Document type:** Engineering Task.
**Task ID:** ENG-CONF-001.
**Filed:** `docs/execution/governance_obligations/ENG-CONF-001.md`.
**Created:** 2026-08-07, to satisfy item **R1** of the EFR-EBD-005 Founder Decision.
**Classification:** Standalone Governance Obligation (EFR-EBD-005 §9.2 condition 6), sequenced as an early engineering task per the Founder Decision §6 and §7.

---

## 1. Title

**ENG-CONF-001 — Constitutional Conformance Remediation (Memory Precedence).**

Remediation of CONFLICT-01: the gap between Constitution Article V.2 and the runtime's present handling of conflicts between institutional memory and current evidence.

---

## 2. Authority

This task exists solely by authority of the **EFR-EBD-005 Founder Decision** dated 2026-08-07.

| Field | Value |
|---|---|
| Authorizing instrument | `docs/execution/governance_obligations/EFR-EBD-005_FOUNDER_DECISION.md` |
| Authorizing instrument SHA-256 | `2058577e5d9cd45295d95e0421700222593dfb88df25f108b0da6b8a12de63f9` |
| Governing task | `docs/execution/governance_obligations/EFR-EBD-005.md` |
| Founder ruling | **APPROVED** — "ENG-CONF-001 … is **approved and authorized** as the required engineering remediation for CONFLICT-01. This satisfies §13.4 and converts the conditional proposed task of §9 into an authorized task." (Founder Decision §7) |
| Basis for this file | Founder Decision §10, item **R1** — "Create the ENG-CONF-001 task file in `docs/execution/governance_obligations/` before any execution begins, per Executive Board Directive #001 and §9.2 condition 8. The task file must carry the approved scope S1–S4 and record the two open scope elements at §7.2 as excluded pending decision." |
| Conformance classification of record | **Partially Conformant (§7.2)** |
| Axis dispositions of record | **D1: Not Satisfied. D2: Partially Satisfied** — detection exists but preservation/provenance remains incomplete. **D3: Not Satisfied.** |

**Superseded condition.** EFR-EBD-005 §9.2 condition 1 ("Recommendation does not authorize execution") is recorded in the Founder Decision §7.3 as **superseded** — the Founder has authorized this task.

**No authority is claimed beyond the Founder Decision.** This task introduces no engineering requirement not already approved there. Where the Founder Decision leaves a matter open, this task records it as deferred and does not resolve it.

---

## 3. Objective

Bring the runtime's handling of conflicts between institutional memory and current evidence into conformance with Constitution Article V.2, limited to the gaps both sealed findings evidenced and the Founder approved.

The objective is bounded by the approved scope at §4. Constitutional conformance is **not considered complete until ENG-CONF-001 is complete** (Founder Decision §6, §7).

---

## 4. Approved Scope (S1–S4)

Reproduced exactly as approved at Founder Decision §7.1. Scope is bounded by the gaps both sealed findings evidenced, per EFR-EBD-005 §9.2 condition 4.

| # | Approved scope element | Claude Code | Codex |
|---|---|---|---|
| **S1** | **Durable conflict/resolution representation in OME**, with the schema change required to record resolution basis, sources weighed, residual uncertainty and provenance | items 1, 3 (scope) | items 1, 3 |
| **S2** | **Append-not-substitute semantics** — prior and conflicting fact assertions preserved rather than overwritten, with an appended resolution/supersession record | item 2 | item 2 |
| **S3** | **Retrievability** — conflicts and resolutions queryable after the fact | item 4 | item 4 |
| **S4** | **Tests** covering detection, preservation, provenance, residual uncertainty, retrievability, and D1/D2/D3 behaviour | item 5 | item 6 |

**Rider attached to S2, as approved:** "Coordinated read-path update is included within S2, both reviewers having recorded that append-not-substitute cannot be delivered by write-path change alone. Claude Code names the specific readers requiring update: `get_fact_by_key`, `fetch_facts`, `build_company_profile`."

**Scope may not be exceeded.** EFR-EBD-005 §9.2 condition 4 is recorded as **in force**: scope is bounded by the evidenced scope, and expansion requires a new Founder decision.

---

## 5. Explicit Out-of-Scope Items

### 5.1 Excluded by the Founder Decision

| # | Excluded item | Source |
|---|---|---|
| X1 | **Adjacent finding AF-1** — the general absence of fact-history preservation on non-conflicting `memory_facts` update paths. "Claude Code's AF-1 is excluded." Does not expand EBD-005. | Founder Decision §7.3 cond. 5; EFR-EBD-005 §9.2 cond. 5, §3.3 |
| X2 | **Runtime Component additions** | Founder Decision §9 |
| X3 | **Runtime Component removals** | Founder Decision §9 |
| X4 | **Runtime Component renaming** | Founder Decision §9 |
| X5 | **Runtime Component reordering** | Founder Decision §9 |
| X6 | **Architecture Freeze escalation** — no advance to Freeze v2.0 is approved | Founder Decision §8 |
| X7 | **Restructuring in response to contract-versus-code gaps.** The Founder Decision records these observations and states they are "**not** approval to add, rename, or reorder any component in response." | Founder Decision §9 |

On X2–X5, the Founder Decision states: "Any future proposal that would add, remove, rename, or reorder a Runtime Component is **outside ENG-CONF-001 scope** and requires a new Founder decision. It may not be introduced through ENG-CONF-001 implementation."

### 5.2 Excluded pending a Founder scope decision

Recorded per R1's requirement to "record the two open scope elements at §7.2 as excluded pending decision." The Founder Decision states these are "**not approved or declined**."

| Element | Held by | Status |
|---|---|---|
| **Source-provenance signal threaded from call sites to `upsert_fact()`**, so the mechanism can distinguish current validated input from institutional memory | Claude Code only | **Open — scope decision required.** Excluded from this task pending decision |
| **Integrate OCE / NCE / NCO responsibilities** into conflict handling without changing the nine-component architecture | Codex only | **Open — scope decision required.** Excluded from this task pending decision |

Per Founder Decision §10 item R3: "Neither may be implemented under ENG-CONF-001 until decided, per §9.2 condition 4."

---

## 6. Preconditions

### 6.1 Preconditions to execution

| # | Precondition | Status |
|---|---|---|
| P1 | **Task file exists** in `docs/execution/governance_obligations/` before any execution begins, per Executive Board Directive #001 and EFR-EBD-005 §9.2 condition 8 | ✅ **Satisfied by this file** (R1) |
| P2 | **Founder authorization** | ✅ **Granted** — Founder Decision §7 |
| P3 | **Scheduling set** — "Scheduling to be set when ENG-CONF-001 is sequenced as an early task" | ⏳ **Pending** |
| P4 | **Explicit Founder exception permitting runtime implementation before EBD-005 ratification**, per EFR-EBD-005 §9.2 condition 3 | ⛔ **Not granted.** See deferred item R2 |

**P4 is blocking.** The Founder Decision §7.3 records condition 3 as "**Open**… This decision does not record an explicit exception," and §11 states the decision "does not by itself satisfy §9.2 condition 3." Ratification occurs at gate 5 under EBD-003 §17.1.

### 6.2 Deferred Founder items — recorded, not resolved

Recorded exactly as carried in the Founder Decision §10. **None is resolved by this task.** Each remains a Founder decision.

| # | Deferred item | Type | Owner | Effect on this task |
|---|---|---|---|---|
| **R2** | **Founder to grant or withhold the explicit exception** permitting runtime implementation before EBD-005 ratification, per §9.2 condition 3. ENG-CONF-001 is authorized but this condition is unresolved; ratification occurs at gate 5 under EBD-003 §17.1. Sequencing ENG-CONF-001 as an early task makes this decision time-sensitive. | **Open** | Founder | **Blocks execution** (P4). Recorded in the Founder Decision as "the nearest-term item" |
| **R3** | **Founder to fix the two open scope elements** at §7.2 — Claude Code's source-provenance signal threading, and Codex's OCE/NCE/NCO integration. | **Open** | Founder | Both remain **excluded** from scope until decided (§5.2) |
| **R4** | **Classify adjacent finding AF-1** for separate governance handling. AF-1 is excluded from ENG-CONF-001 scope per §9.2 condition 5 and does not expand EBD-005. | **Open** | Founder | AF-1 remains **out of scope** (X1) regardless of outcome |
| **R5** | **Rule on the interim-MVP question** — whether an interim MVP is acceptable ahead of the full schema change. "requires a ruling before implementation approach is fixed." | **Open** | Founder | Implementation approach for S1 **not fixed** until decided |
| **R6** | **Determine disposition of the prompt-layer directional finding.** "Whether this falls in ENG-CONF-001 scope, becomes a separate obligation, or is noted only, is undecided." | **Open** | Founder | **Not in scope** unless and until the Founder rules it in |

---

## 7. Execution Constraints

| # | Constraint | Source |
|---|---|---|
| C1 | **Scope is bounded by S1–S4.** Expansion requires a new Founder decision. | Founder Decision §7.3 cond. 4 |
| C2 | **No runtime implementation before EBD-005 ratification**, absent an explicit Founder exception. | Founder Decision §7.3 cond. 3; §11 |
| C3 | **Implementation stays entirely within the existing nine Runtime Components.** "The nine Runtime Components stand unchanged." | Founder Decision §9 |
| C4 | **No Architecture Freeze escalation.** No advance to Freeze v2.0 is authorized. | Founder Decision §8 |
| C5 | **Adjacent findings excluded.** AF-1 is not to be folded into this task's scope. | Founder Decision §7.3 cond. 5 |
| C6 | **Sprint EX-2 coordination.** "Sprint EX-2 work touching the surfaces listed above must be coordinated with ENG-CONF-001 sequencing. Continuation of Sprint EX-2 is not authorization to modify those surfaces independently of ENG-CONF-001." | Founder Decision §6 |
| C7 | **Sequencing:** ENG-CONF-001 is to be sequenced as an **early engineering task**. No priority beyond this is assigned. | Founder Decision §6, §7 |
| C8 | **This task does not ratify EBD-005 or the Tier 1 unfreeze.** Ratification is reserved to the Founder at gate 5 under EBD-003 §17.1, after Product review. | Founder Decision §8, §11 |

**Surfaces named in the Founder Decision §6 as simultaneously in play, for C6 coordination purposes:**

- `app/services/memory/repository.py` and the `memory_facts` / `memory_events` tables
- `migrations/` — a new migration file
- Every reader of `memory_facts`: `openai_client.py`, `decision_context.py`, and `pipeline.py`'s `store_ome_foundation()`
- OCE context assembly, NCE reasoning prompts/runtime, and NCO orchestration

---

## 8. Acceptance Criteria

ENG-CONF-001 is accepted when **all** of the following hold. Each derives from the approved scope or from a condition the Founder Decision records as in force. No criterion introduces a requirement beyond those.

| # | Criterion | Source |
|---|---|---|
| A1 | **S1 delivered** — a durable conflict/resolution representation exists in OME, with the schema change required to record resolution basis, sources weighed, residual uncertainty and provenance | S1 |
| A2 | **S2 delivered** — append-not-substitute semantics in place: prior and conflicting fact assertions preserved rather than overwritten, with an appended resolution/supersession record | S2 |
| A3 | **S2 read-path rider delivered** — the coordinated read-path update is included, covering the readers named in the approved scope: `get_fact_by_key`, `fetch_facts`, `build_company_profile` | S2 rider |
| A4 | **S3 delivered** — conflicts and resolutions are queryable after the fact | S3 |
| A5 | **S4 delivered** — the required tests at §9 exist and pass | S4 |
| A6 | **Scope not exceeded** — nothing outside S1–S4 was implemented under this task | §9.2 cond. 4 |
| A7 | **Out-of-scope items absent** — X1–X7 were not implemented; no Runtime Component was added, removed, renamed, or reordered; no Freeze escalation was introduced | Founder Decision §8, §9 |
| A8 | **Deferred elements absent** — neither §5.2 element was implemented in the absence of a Founder scope decision | §10 R3 |
| A9 | **Peer engineering review completed** per §10 of this task | §9.2 cond. 7; §10 R10 |
| A10 | **Precondition P4 satisfied** at the time execution began — either EBD-005 ratified, or an explicit Founder exception recorded | §9.2 cond. 3 |

---

## 9. Required Tests

Reproduced from approved scope element **S4**: tests covering **detection, preservation, provenance, residual uncertainty, retrievability, and D1/D2/D3 behaviour.**

| # | Required test coverage | S4 term |
|---|---|---|
| T-1 | **Detection** — conflict between institutional memory and current evidence is detected | detection |
| T-2 | **Preservation** — the conflict and the prior/conflicting assertions are preserved, not overwritten | preservation |
| T-3 | **Provenance** — resolution basis and sources weighed are recorded | provenance |
| T-4 | **Residual uncertainty** — residual uncertainty is recorded | residual uncertainty |
| T-5 | **Retrievability** — conflicts and resolutions are retrievable after the fact | retrievability |
| T-6 | **D1 behaviour** | D1/D2/D3 behaviour |
| T-7 | **D2 behaviour** | D1/D2/D3 behaviour |
| T-8 | **D3 behaviour** | D1/D2/D3 behaviour |

No test category beyond S4's enumeration is required by this task.

---

## 10. Required Engineering Review

**Peer review under EBD-002 §4.4 applies to ENG-CONF-001 implementation.** Recorded as **in force** at Founder Decision §7.3 condition 7, and as required item **R10** at §10.

| Field | Value |
|---|---|
| Requirement | Peer engineering review under EBD-002 §4.4 |
| Reviewers | **Claude Code** and **Codex** — the two Senior AI Software Engineers named as owners of R10 |
| Status under the Founder Decision | **In force** |

This task adds no review requirement beyond the peer review already required.

---

## 11. Completion Criteria

ENG-CONF-001 is **complete** when:

1. All acceptance criteria **A1–A10** at §8 are satisfied; and
2. The peer engineering review required at §10 is completed.

**Consequence of completion, as recorded in the Founder Decision §6 and §7:** constitutional conformance is not considered complete until ENG-CONF-001 is complete. Completion of this task is the condition the Founder attached to that determination.

**What completion does not do.** Completion of ENG-CONF-001 does not ratify EBD-005, does not ratify the Tier 1 unfreeze, and does not resolve any deferred item at §6.2. Ratification occurs at gate 5 under EBD-003 §17.1, after Product review, and only by the Founder.

---

## 12. Status

| Field | Value |
|---|---|
| **Task status** | **AUTHORIZED — NOT STARTED** |
| **Authorization** | ✅ Granted by the Founder, 2026-08-07 (Founder Decision §7) |
| **Execution status** | ⛔ **Blocked** — precondition P4 unsatisfied; no explicit Founder exception recorded per §9.2 condition 3 |
| **Blocking item** | **R2** — recorded in the Founder Decision as "the nearest-term item" |
| **Sequencing** | Early engineering task (Founder Decision §6, §7). No further priority assigned |
| **Scheduling** | ⏳ Pending (P3) |
| **Scope status** | S1–S4 approved and fixed; two elements excluded pending Founder decision (R3) |
| **Implementation approach** | Not fixed — pending R5 |
| **Open Founder items affecting this task** | R2, R3, R4, R5, R6 |
| **Classification** | Standalone Governance Obligation (§9.2 cond. 6), sequenced as an early engineering task |
| **Peer review** | Required, not yet performed |

---

**Task file created under R1 of the EFR-EBD-005 Founder Decision.**
**No implementation steps, architecture, or priority beyond the approved sequencing are contained in this task.**
**No engineering requirement outside the Founder-approved scope has been introduced.**
