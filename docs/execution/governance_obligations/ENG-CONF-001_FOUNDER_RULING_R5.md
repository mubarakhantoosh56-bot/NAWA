# ENG-CONF-001 — Founder Ruling R5

**Document type:** Founder Ruling record.
**Instrument ID:** ENG-CONF-001_FOUNDER_RULING_R5.
**Filed:** `docs/execution/governance_obligations/ENG-CONF-001_FOUNDER_RULING_R5.md`.

> **What this document is not.** This is **not** an Executive Board Directive. It is **not** a governance amendment. It is **not** an engineering task. It amends, revises, and supersedes nothing. It records one Founder ruling and nothing else.

---

## 1. Title

**Founder Ruling R5 — Implementation Approach for ENG-CONF-001 (Full Schema Migration Required; Interim MVP Not Approved).**

Issued to resolve item **R5** of the EFR-EBD-005 Founder Decision for **ENG-CONF-001 only**.

---

## 2. Authority

Issued by the **Founder**, under the authority reserved at **EFR-EBD-005 §13.4** and carried forward as deferred item **R5** at EFR-EBD-005 Founder Decision §10, which records that "Whether an interim MVP is acceptable ahead of the full schema change requires a ruling before implementation approach is fixed," with **Owner: Founder**.

| Field | Value |
|---|---|
| Issuing authority | Founder |
| Reserved power exercised | EFR-EBD-005 Founder Decision §10, item **R5**; basis Q5, Q10 |
| Instrument being completed | `EFR-EBD-005_FOUNDER_DECISION.md`, item **R5** |
| Founder Decision SHA-256 | `2058577e5d9cd45295d95e0421700222593dfb88df25f108b0da6b8a12de63f9` |
| Affected task | `ENG-CONF-001.md` — Constitutional Conformance Remediation (Memory Precedence) |
| ENG-CONF-001 SHA-256 | `5640d3b66ae01983a574e05440c5e4b82fa6044031a95e5da07e834b639bbba9` |
| Related record | `EFR-EBD-005_FOUNDER_EXCEPTION_R2.md` — resolves R2 only; expressly does not resolve R5 |

**Source documents read in preparing this record — these three only:**

1. `docs/execution/governance_obligations/ENG-CONF-001.md`
2. `docs/execution/governance_obligations/EFR-EBD-005_FOUNDER_DECISION.md`
3. `docs/execution/governance_obligations/EFR-EBD-005_FOUNDER_EXCEPTION_R2.md`

**Recording limits observed.** No runtime code was inspected. No engineering review was performed. No existing document was modified. No matter other than R5 is decided.

---

## 3. Purpose

To fix the implementation approach for ENG-CONF-001, thereby resolving deferred item **R5** of the EFR-EBD-005 Founder Decision.

**The item being resolved.** Founder Decision §10, item **R5**: "**Rule on the interim-MVP question.** Codex records that `memory_events.logic_json` / `context` 'could host an MVP append-only record without migration,' while noting it 'would likely not satisfy retrievability and provenance threshold T1-T6.' Claude Code states a schema migration is required and offers no no-migration path. Whether an interim MVP is acceptable ahead of the full schema change requires a ruling before implementation approach is fixed."

**The state being cleared.** ENG-CONF-001 §12 records **Implementation approach: "Not fixed — pending R5."** ENG-CONF-001 §6.2 records R5 as **Open**, with effect: "Implementation approach for S1 **not fixed** until decided." EFR-EBD-005_FOUNDER_EXCEPTION_R2 §6.1 confirms R5 remained "**Open — unresolved**" after that exception, and §6.1 states the exception "does not fix the implementation approach and does not resolve R5."

This record introduces no scope, imposes no new requirement, and resolves no matter other than R5.

---

## 4. Founder Ruling — R5

> ## **FULL SCHEMA MIGRATION REQUIRED — INTERIM MVP NOT APPROVED**

**The Founder rules as follows:**

1. **ENG-CONF-001 shall use the full schema-migration approach required by approved scope S1** — the durable conflict/resolution representation in OME, with the schema change required to record resolution basis, sources weighed, residual uncertainty and provenance.

2. **The interim MVP approach relying only on `memory_events.logic_json` without the required schema migration is NOT approved for ENG-CONF-001.**

3. **This ruling selects the implementation approach only. It does not expand ENG-CONF-001 scope.**

**Effects, stated explicitly:**

| # | Effect |
|---|---|
| E1 | Deferred item **R5** of the EFR-EBD-005 Founder Decision is **RESOLVED**. |
| E2 | The implementation approach for ENG-CONF-001 is **FIXED**: full schema migration, as required by approved scope element **S1**. |
| E3 | The no-migration interim MVP path is **NOT AVAILABLE** to ENG-CONF-001. It may not be adopted, substituted, or delivered as partial satisfaction of S1. |
| E4 | ENG-CONF-001 §12 — "Implementation approach: Not fixed — pending R5" — is answered by this ruling. |
| E5 | Approved scope **S1–S4** is unchanged in content by this ruling. |

**What this ruling does not do.** It does not ratify EBD-005. It does not ratify the Tier 1 unfreeze — ratification occurs at gate 5 under EBD-003 §17.1, after Product review, and only by the Founder. It does not reopen EFR-EBD-005. It does not disturb the conformance classification of record (**Partially Conformant, §7.2**) or the axis dispositions of record (**D1 Not Satisfied; D2 Partially Satisfied; D3 Not Satisfied**).

---

## 5. Scope Effect

**This ruling applies to ENG-CONF-001 only, and selects approach only.**

| # | Boundary |
|---|---|
| 1 | **No scope expansion.** The approved scope of ENG-CONF-001 remains exactly **S1–S4** as recorded at ENG-CONF-001 §4. This ruling fixes how S1 is to be delivered; it adds nothing to what must be delivered. |
| 2 | **No Architecture Freeze change is authorized.** No advance to Freeze v2.0. Founder Decision §8 remains in force. |
| 3 | **No Runtime Component addition, removal, rename, or reorder is authorized.** The nine Runtime Components stand unchanged. Founder Decision §9 remains in force. |
| 4 | **All existing ENG-CONF-001 constraints remain in force** — execution constraints C1–C8 (ENG-CONF-001 §7), acceptance criteria A1–A10 (§8), required tests T-1 to T-8 (§9), required peer engineering review (§10), and completion criteria (§11). |
| 5 | **Out-of-scope items remain out of scope.** ENG-CONF-001 §5.1 exclusions **X1–X7** are unaffected. |
| 6 | **Deferred scope elements remain excluded.** The two elements at ENG-CONF-001 §5.2 remain excluded pending a Founder scope decision under R3. This ruling does not admit them. |
| 7 | **S1–S4 are not reinterpreted.** This ruling adopts S1 as approved and does not restate, narrow, broaden, or reinterpret S1, S2, S3, or S4. |
| 8 | **Not precedent.** This ruling fixes the approach for ENG-CONF-001 alone and creates no standing rule for any other task, obligation, or sprint. |
| 9 | **No document is modified by this record.** ENG-CONF-001, the Founder Decision, Founder Exception R2, both sealed findings, both custody addenda, the comparison, and the governing task all stand as filed and unaltered. |

---

## 6. Remaining Open Items

**This ruling resolves R5 only.** The following remain **Open**, unresolved, and **excluded from implementation**, reserved to the Founder exactly as recorded in the Founder Decision §10, ENG-CONF-001 §6.2, and Founder Exception R2 §6.1:

| # | Deferred item | Status | Effect on ENG-CONF-001 |
|---|---|---|---|
| **R3** | Founder to fix the two open scope elements at Founder Decision §7.2 — source-provenance signal threading, and OCE/NCE/NCO integration | **Open — unresolved** | Both remain **excluded** from scope and from implementation |
| **R4** | Classify adjacent finding AF-1 for separate governance handling | **Open — unresolved** | AF-1 remains **out of scope** (X1) and excluded from implementation |
| **R6** | Determine disposition of the prompt-layer directional finding | **Open — unresolved** | **Not in scope** and excluded from implementation unless and until the Founder rules it in |

**Previously resolved, recorded for completeness:**

| # | Item | Status |
|---|---|---|
| **R2** | Explicit Founder exception permitting implementation before EBD-005 ratification | **RESOLVED** by `EFR-EBD-005_FOUNDER_EXCEPTION_R2.md`, effective 2026-08-08 |
| **R5** | Interim-MVP question | **RESOLVED** by this record |

**Other matters continuing unchanged.** ENG-CONF-001 §6.1 precondition **P3** (scheduling) remains **Pending**. The Sprint EX-2 coordination constraint at Founder Decision §6 remains **in force**. Peer review under EBD-002 §4.4 remains **required and not yet performed**. **EFR-EBD-005 remains CLOSED**, unchanged by this record.

---

## 7. Effective Date

| Field | Value |
|---|---|
| **Effective date** | **2026-08-08** |
| Founder Decision date | 2026-08-07 |
| ENG-CONF-001 filed | 2026-08-07 |
| Founder Exception R2 effective | 2026-08-08 |
| Duration | Effective from the date above until ENG-CONF-001 reaches completion per ENG-CONF-001 §11, or until withdrawn or superseded by the Founder |

This ruling takes effect immediately on the effective date. It is not retroactive; no implementation performed before this date is authorized or validated by it.

---

## 8. Status

| Field | Value |
|---|---|
| **Ruling status** | **ISSUED — IN FORCE** |
| **R5** | **RESOLVED** |
| **ENG-CONF-001 implementation approach** | **FIXED — full schema migration per approved scope S1** |
| **Interim MVP via `memory_events.logic_json` without schema migration** | **NOT APPROVED** for ENG-CONF-001 |
| **ENG-CONF-001 approved scope** | **S1–S4 — unchanged.** No expansion authorized |
| **Architecture Freeze** | **No change authorized** |
| **Runtime Components** | **No addition, removal, rename, or reorder authorized** |
| **ENG-CONF-001 constraints** | **All remain in force** |
| **R3, R4, R6** | **Open — unresolved.** Excluded from implementation. Not addressed by this record |
| **EBD-005 ratification** | **Not granted.** Reserved to the Founder at gate 5 under EBD-003 §17.1, after Product review |
| **EFR-EBD-005** | **CLOSED** — unchanged by this record |
| **Documents modified by this record** | **None** |

---

**Issued by:** Founder.
**Recorded by:** COWORK (CTO / Chief of Staff), procedural custody under EFR-EBD-005 §12.
**Effective:** 2026-08-08.

---

FOUNDER RULING R5 — ISSUED

Applies to ENG-CONF-001 only. Resolves R5 only. R3, R4, and R6 remain open and excluded. All other conditions of the EFR-EBD-005 Founder Decision remain in force.
