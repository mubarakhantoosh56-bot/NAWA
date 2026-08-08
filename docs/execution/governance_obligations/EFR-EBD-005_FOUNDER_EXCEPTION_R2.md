# EFR-EBD-005 — Founder Exception R2

**Document type:** Founder Exception record.
**Instrument ID:** EFR-EBD-005_FOUNDER_EXCEPTION_R2.
**Filed:** `docs/execution/governance_obligations/EFR-EBD-005_FOUNDER_EXCEPTION_R2.md`.

> **What this document is not.** This is **not** an Executive Board Directive. It is **not** a governance amendment. It is **not** an engineering task. It amends, revises, and supersedes nothing. It records one Founder decision and nothing else.

---

## 1. Title

**Founder Exception R2 — Explicit Exception Permitting Implementation of ENG-CONF-001 Before EBD-005 Ratification.**

Issued to resolve item **R2** of the EFR-EBD-005 Founder Decision and to satisfy **EFR-EBD-005 §9.2 condition 3** for ENG-CONF-001 only.

---

## 2. Authority

Issued by the **Founder**, under the authority reserved at **EFR-EBD-005 §9.2 condition 3** — which provides that no runtime implementation begins before EBD-005 ratification "unless the Founder grants an **explicit exception**" — and at **§13.5**, which reserves to the Founder the decision to "grant or withhold an explicit exception permitting runtime implementation before EBD-005 ratification."

| Field | Value |
|---|---|
| Issuing authority | Founder |
| Reserved power exercised | EFR-EBD-005 §9.2 condition 3; §13.5 |
| Instrument being completed | `EFR-EBD-005_FOUNDER_DECISION.md`, item **R2** |
| Founder Decision SHA-256 | `2058577e5d9cd45295d95e0421700222593dfb88df25f108b0da6b8a12de63f9` |
| Affected task | `ENG-CONF-001.md` — Constitutional Conformance Remediation (Memory Precedence) |
| ENG-CONF-001 SHA-256 | `5640d3b66ae01983a574e05440c5e4b82fa6044031a95e5da07e834b639bbba9` |

**Source documents read in preparing this record — these two only:**

1. `docs/execution/governance_obligations/EFR-EBD-005_FOUNDER_DECISION.md`
2. `docs/execution/governance_obligations/ENG-CONF-001.md`

---

## 3. Purpose

To record the explicit Founder exception contemplated by EFR-EBD-005 §9.2 condition 3, thereby resolving deferred item **R2** and removing the sole blocking precondition on ENG-CONF-001.

**The condition being satisfied.** The EFR-EBD-005 Founder Decision §7.3 recorded condition 3 as **Open**: "No runtime implementation before EBD-005 ratification, absent explicit Founder exception … **This decision does not record an explicit exception.**" Its §11 confirmed the decision "does not by itself satisfy §9.2 condition 3."

**The item being resolved.** Founder Decision §10, item **R2**: "Founder to grant or withhold the explicit exception permitting runtime implementation before EBD-005 ratification, per §9.2 condition 3. ENG-CONF-001 is authorized but this condition is unresolved; ratification occurs at gate 5 under EBD-003 §17.1. Sequencing ENG-CONF-001 as an early task makes this decision time-sensitive." Recorded there as "the nearest-term item."

**The precondition being cleared.** ENG-CONF-001 §6.1 precondition **P4** — "Explicit Founder exception permitting runtime implementation before EBD-005 ratification" — recorded as **⛔ Not granted**, and identified at ENG-CONF-001 §12 as the blocking item holding execution status at **AUTHORIZED — NOT STARTED**.

This record introduces no scope, imposes no new requirement, and resolves no matter other than R2.

---

## 4. Founder Exception

> ## **EXCEPTION GRANTED**

**The Founder grants an explicit exception under EFR-EBD-005 §9.2 condition 3.**

**Implementation of ENG-CONF-001 is explicitly authorized to proceed before EBD-005 ratification.**

Accordingly:

| # | Effect |
|---|---|
| E1 | Deferred item **R2** of the EFR-EBD-005 Founder Decision is **RESOLVED**. |
| E2 | **EFR-EBD-005 §9.2 condition 3 is SATISFIED** with respect to ENG-CONF-001. |
| E3 | ENG-CONF-001 precondition **P4 is SATISFIED**. |
| E4 | ENG-CONF-001 acceptance criterion **A10** — "Precondition P4 satisfied at the time execution began — either EBD-005 ratified, or an explicit Founder exception recorded" — is satisfied by the recording of this exception. |
| E5 | ENG-CONF-001 execution constraint **C2** is satisfied by this exception and no longer bars execution of ENG-CONF-001. |
| E6 | ENG-CONF-001 is **no longer blocked** on this ground. |

**This exception does not ratify EBD-005.** Ratification occurs at gate 5 under EBD-003 §17.1, after Product review, and only by the Founder. This record permits implementation to precede that ratification for ENG-CONF-001; it does not substitute for it, anticipate it, or bind it.

---

## 5. Scope of Exception

**The exception applies to ENG-CONF-001 only.**

| Applies to | Does not apply to |
|---|---|
| ENG-CONF-001 — Constitutional Conformance Remediation (Memory Precedence), within its approved scope **S1–S4** as recorded at ENG-CONF-001 §4 | Any other task, obligation, sprint, or work item |
| | Sprint EX-2 or any Sprint EX-2 work item |
| | The two scope elements excluded pending decision at ENG-CONF-001 §5.2 |
| | Adjacent finding **AF-1** |
| | Any work outside ENG-CONF-001's approved scope |

**Boundaries, stated explicitly:**

1. **No new scope is introduced.** The approved scope of ENG-CONF-001 remains exactly S1–S4 as recorded at ENG-CONF-001 §4. This exception changes the timing permission only, not the content of the work.
2. **Out-of-scope items remain out of scope.** ENG-CONF-001 §5.1 exclusions **X1–X7** remain in force and are unaffected.
3. **Deferred scope elements remain excluded.** The two elements at ENG-CONF-001 §5.2 remain excluded pending a Founder scope decision. This exception does not admit them.
4. **No component or Freeze change is permitted.** No Runtime Component addition, removal, rename, or reordering is authorized. No Architecture Freeze escalation is authorized.
5. **This exception is not precedent.** It grants no general permission to implement ahead of ratification for any other matter, and creates no standing rule.

---

## 6. Remaining Conditions

**All other conditions of the EFR-EBD-005 Founder Decision remain in force, unchanged.**

### 6.1 Deferred items R3–R6 — NOT resolved

This exception resolves **R2 only**. The following remain **Open** and are reserved to the Founder exactly as recorded in the Founder Decision §10 and ENG-CONF-001 §6.2:

| # | Deferred item | Status |
|---|---|---|
| **R3** | Founder to fix the two open scope elements at Founder Decision §7.2 | **Open — unresolved** |
| **R4** | Classify adjacent finding AF-1 for separate governance handling | **Open — unresolved** |
| **R5** | Rule on the interim-MVP question | **Open — unresolved** |
| **R6** | Determine disposition of the prompt-layer directional finding | **Open — unresolved** |

**R5 continues to affect ENG-CONF-001.** ENG-CONF-001 §12 records implementation approach as "Not fixed — pending R5." This exception removes the ratification-timing bar; it does not fix the implementation approach and does not resolve R5.

### 6.2 Conditions continuing in force

| Source | Condition | Status |
|---|---|---|
| Founder Decision §7.3 cond. 4 | Scope bounded by evidenced scope; expansion requires a new Founder decision | **In force** |
| Founder Decision §7.3 cond. 5 | Adjacent findings excluded from ENG-CONF-001 scope | **In force** |
| Founder Decision §7.3 cond. 6 | Standalone Governance Obligation, sequenced as an early engineering task | **In force** |
| Founder Decision §7.3 cond. 7 | Peer review under EBD-002 §4.4 applies to ENG-CONF-001 implementation | **In force** |
| Founder Decision §8 | No Architecture Freeze escalation approved | **In force** |
| Founder Decision §9 | No Runtime Component additions, removals, renames, or reorderings approved | **In force** |
| Founder Decision §6 | Sprint EX-2 coordination constraint on the named OME surfaces | **In force** |
| ENG-CONF-001 §7 | Execution constraints C1, C3–C8 | **In force** |
| ENG-CONF-001 §8 | Acceptance criteria A1–A9 | **In force** |
| ENG-CONF-001 §9 | Required tests T-1 to T-8 | **In force** |
| ENG-CONF-001 §10 | Required peer engineering review — Claude Code and Codex | **In force** |
| ENG-CONF-001 §11 | Completion criteria | **In force** |
| ENG-CONF-001 §6.1 | Precondition **P3** — scheduling to be set | **Pending** |

**EFR-EBD-005 remains CLOSED.** This exception is issued under a power the Founder Decision expressly left open at R2. It does not reopen EFR-EBD-005, does not disturb the conformance classification of record (**Partially Conformant, §7.2**), and does not disturb the axis dispositions of record (**D1 Not Satisfied; D2 Partially Satisfied; D3 Not Satisfied**).

**No previous document is modified by this record.** The Founder Decision, ENG-CONF-001, both sealed findings, both custody addenda, the comparison, and the governing task all stand as filed and unaltered.

---

## 7. Effective Date

| Field | Value |
|---|---|
| **Effective date** | **2026-08-08** |
| Effective timestamp (local) | 2026-08-08 00:34 +03:00 |
| Effective timestamp (UTC) | 2026-08-07T21:34Z |
| Founder Decision date | 2026-08-07 |
| ENG-CONF-001 filed | 2026-08-07 |
| Duration | Effective from the date above until ENG-CONF-001 reaches completion per ENG-CONF-001 §11, or until withdrawn by the Founder |

This exception takes effect immediately on the effective date. It is not retroactive; no implementation performed before this date is authorized by it.

---

## 8. Status

| Field | Value |
|---|---|
| **Exception status** | **GRANTED — IN FORCE** |
| **R2** | **RESOLVED** |
| **EFR-EBD-005 §9.2 condition 3** | **SATISFIED** for ENG-CONF-001 |
| **ENG-CONF-001 precondition P4** | **SATISFIED** |
| **ENG-CONF-001 execution status** | **UNBLOCKED** on the ratification-timing ground. Remaining open matter: scheduling (P3); implementation approach not fixed pending R5 |
| **Scope of exception** | ENG-CONF-001 only |
| **R3, R4, R5, R6** | **Open — unresolved.** Not addressed by this record |
| **EBD-005 ratification** | **Not granted.** Reserved to the Founder at gate 5 under EBD-003 §17.1, after Product review |
| **EFR-EBD-005** | **CLOSED** — unchanged by this record |
| **Documents modified by this record** | **None** |

---

**Issued by:** Founder.
**Recorded by:** COWORK (CTO / Chief of Staff), procedural custody under EFR-EBD-005 §12.
**Effective:** 2026-08-08.

---

FOUNDER EXCEPTION R2 — GRANTED

Applies to ENG-CONF-001 only. All other conditions of the EFR-EBD-005 Founder Decision remain in force.
