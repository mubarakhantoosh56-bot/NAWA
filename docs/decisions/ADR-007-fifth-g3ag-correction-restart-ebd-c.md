# Architectural Decision Record #007 — Fifth G3a-G Correction Restart EBD-C

**Status:** APPROVED — CTO — 2026-10-16.
**Version:** 1.0
**Category:** Decision Logs
**Scope:** The CTO's approval, at EBD-002 checkpoint `EBD-C`, of the substantive final state of the sixth forward correction draft of the post-activation governance reconciliation, after its fifth `G3a-G` failure and correction restart.
**Non-scope:** Any Founder decision; any independent gate verdict; the Governance Closure Manifest; staging, commit, or push; any engineering batch.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** CTO.
**Effective date:** 2026-10-16.
**Last updated:** 2026-10-16.

---

## 1. Why this record exists

`REVIEW_PROTOCOL.md` §9.6 step 11 requires a new `EBD-C` after a correction
restart, before the region may go from Idle to Finalized. `AUTONOMOUS_LOOP.md`
§8.4 and EBD-002 §4.3, §5.2, and §10 require that approval to be written,
dated, and named in a Decision Log entry. This is that entry. `ADR-002`,
`ADR-003`, `ADR-004`, `ADR-005`, and `ADR-006`, the earlier `EBD-C` records of
this closure, remain historical and INVALIDATED FOR CORRECTION RESTART; this
record does not change them. `ADR-007` is the new valid `EBD-C` of this
closure.

## 2. Checkpoint record

| Field | Value |
|---|---|
| Checkpoint | `EBD-C` — fifth G3a-G correction restart |
| Decision | **APPROVED** |
| Approver role | CTO — Chief Technology & Architecture Officer |
| Approver | Claude Cowork |
| Date | 2026-10-16 |
| Governance Closure Batch | `GOVERNANCE-ONLY` |
| Original Governance Closure Baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Forward correction parent | `9a5759fcdcadda313620f3c3106e96ecbd77f34d` (fifth local commit) |
| Correction commit subject (`EBD-016`) | `Docs: reconcile Harness live and historical state after fifth G3a-G failure` |

## 3. Independent review basis

The independent Codex verdict immediately preceding this approval, as given by
the Founder:

```text
PASS — EBD-016 SIXTH FORWARD CORRECTION VERIFIED — SAFE FOR ADR-007 / EBD-C
```

As reported by the Founder, Codex confirmed current-state consistency and
temporal/deictic integrity: no stale authoritative field and no unqualified
historical live or current assertion remained; no Founder decision, no
substantive correction, and no extra path was required. It confirmed that the
correction commit set is exactly 4 paths with ADR-007 the only missing one;
that the correction parent is `9a5759fc…` and the baseline remains
`4aec1e48…`; that the expected post-correction / pre-push divergence is 6/0;
and that the manifest is revision 6, built from the cumulative diff from the
original baseline to the prospective sixth corrected tip, with 24 entries that
do not breach the four-path commit authorization. The full verdict text is not
held in this repository. This approval was made on the Founder's instruction.

The CTO's own authoritative-state and temporal/deictic sweep of
`CURRENT_AUTONOMOUS_RUN.md`, run after the post-EBD-C transition and before
this decision was declared, also passed: no stale current field, and every
historical live or current statement is bound to an explicit checkpoint. That
sweep is internal work, not an independent review.

## 4. What is approved

The sixth-correction draft is substantively complete. The forward correction
commit is to contain exactly these four paths — no fifth correction path is
authorized:

| # | Status | Path |
|---|---|---|
| 1 | M | `docs/decisions/ADR-006-fourth-g3ag-correction-restart-ebd-c.md` |
| 2 | A | `docs/decisions/ADR-007-fifth-g3ag-correction-restart-ebd-c.md` (this record) |
| 3 | A | `docs/decisions/EBD-016-fifth-g3ag-forward-correction-commit-authorization.md` |
| 4 | M | `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` |

**Manifest and topology expectations, as independently verified:**

| Item | Value |
|---|---|
| Manifest revision | 6 |
| Manifest baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Manifest source scope | CUMULATIVE ORIGINAL BASELINE → PROSPECTIVE SIXTH CORRECTED TIP |
| Expected manifest entry count | 24 |
| Expected post-correction / pre-push divergence | 6/0 |

The sixth forward correction commit delta is exactly 4 paths; the cumulative
Governance Manifest has 24 entries. The 24 entries do not expand the
authorized correction commit scope of `EBD-016`. Relative to the original
baseline, ADR-006 remains one cumulative entry and `CURRENT_AUTONOMOUS_RUN.md`
one cumulative normalized entry; only ADR-007 and EBD-016 add new unique
cumulative paths.

**`EBD-016` condition state at issuance:**

| # | Condition | State |
|---|---|---|
| 1 | Independent pre-`EBD-C` review PASS | SATISFIED |
| 2 | ADR-007 / new `EBD-C` issued | SATISFIED |
| 3 | Substantive correction state frozen | SATISFIED |
| 4 | Revision-6 Governance Manifest finalized | NOT YET SATISFIED |
| 5 | Derived-metadata region Idle → Finalized | NOT YET SATISFIED |
| 6 | Manifest integrity and normalized identity verified | NOT YET SATISFIED |
| 7 | Native Windows Git exact authorized four-path verification | NOT YET SATISFIED |

**State at issuance:**

- the derived-metadata region is Idle;
- the Governance Manifest is NOT YET FINALIZED;
- `EBD-016` is APPROVED CONDITIONALLY — NOT YET EFFECTIVE; its stage and
  commit authorization are NOT YET EFFECTIVE;
- push is NOT AUTHORIZED;
- A2 / DEFECT-002 NOT ACTIVATED; Migration Authorization NONE.

**Limits of this approval.** It is a CTO approval under EBD-002, not an
independent review and not a gate verdict: the CTO drafted the documents it
approves. It was made without native Git; native computation and verification
belong to manifest finalization, to `EBD-016` conditions 4–7, and to `G3a-G`.

## 5. Decision

**`EBD-C`: APPROVED** — Claude Cowork, CTO, 2026-10-16, declared after the
authoritative-state and temporal sweep passed. ADR-007 is the valid `EBD-C`
of the fifth correction restart.

## 6. Consequences accepted

**What this approval authorizes:** progression to the revision-6 Governance
Closure Manifest finalization (`REVIEW_PROTOCOL.md` §9.6 steps 5–8), natively,
by Claude Code.

**What it does not do.** It does not finalize the manifest, make `EBD-016`
effective, stage, commit, or push, activate A2 or any engineering batch, or
authorize migrations or product changes.

**Substantive freeze.** With this record and the `EBD-C` state in
`CURRENT_AUTONOMOUS_RUN.md` written, the substantive correction state is
frozen. Any substantive edit after this approval invalidates this `EBD-C` and
requires a correction restart.

This record cites no `manifest_id`; none exists for revision 6.

## 7. Ratification

| Role | Record |
|---|---|
| CTO — approver | Claude Cowork, 2026-10-16. `EBD-C` APPROVED. |
| AI Engineering Team — independent review | Codex: `PASS — EBD-016 SIXTH FORWARD CORRECTION VERIFIED — SAFE FOR ADR-007 / EBD-C`, as given by the Founder. The full verdict text is not held in this repository. |
| Founder & CEO | Not the approver of this checkpoint. Founder decisions this correction depends on: `EBD-010` (with its two supplemental decisions) and `EBD-016`. |
| CPO (Aboura) | No separate written review is held in this repository. |

## 8. Record notes

- **Identifier.** `ADR-007` is the next unused ADR identifier after
  `ADR-006`. It was reserved in `CURRENT_AUTONOMOUS_RUN.md` and in `EBD-016`
  before this record was written.
- **Date.** This record carries its actual issuance date, 2026-10-16
  (Asia/Amman). It is not backdated.
