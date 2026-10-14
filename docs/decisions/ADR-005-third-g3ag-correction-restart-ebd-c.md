# Architectural Decision Record #005 — Third G3a-G Correction Restart EBD-C

**Status:** APPROVED — CTO — 2026-10-15.
**Version:** 1.0
**Category:** Decision Logs
**Scope:** The CTO's approval, at EBD-002 checkpoint `EBD-C`, of the substantive final state of the fourth forward correction draft of the post-activation governance reconciliation, after its third `G3a-G` failure and correction restart.
**Non-scope:** Any Founder decision; any independent gate verdict; the Governance Closure Manifest; staging, commit, or push; any engineering batch.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** CTO.
**Effective date:** 2026-10-15.
**Last updated:** 2026-10-15.

---

## 1. Why this record exists

`REVIEW_PROTOCOL.md` §9.6 step 11 requires a new `EBD-C` after a correction
restart, before the region may go from Idle to Finalized. `AUTONOMOUS_LOOP.md`
§8.4 and EBD-002 §4.3, §5.2, and §10 require that approval to be written,
dated, and named in a Decision Log entry. This is that entry. `ADR-002`,
`ADR-003`, and `ADR-004`, the earlier `EBD-C` records of this closure, remain
historical and INVALIDATED FOR CORRECTION RESTART; this record does not change
them. `ADR-005` is the new valid `EBD-C` of this closure.

## 2. Checkpoint record

| Field | Value |
|---|---|
| Checkpoint | `EBD-C` — third G3a-G correction restart |
| Decision | **APPROVED** |
| Approver role | CTO — Chief Technology & Architecture Officer |
| Approver | Claude Cowork |
| Date | 2026-10-15 |
| Governance Closure Batch | `GOVERNANCE-ONLY` |
| Original Governance Closure Baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Forward correction parent | `bc9a269c402451163223c5f7968465c58d455836` (third local commit) |
| Correction commit subject (`EBD-014`) | `Docs: reconcile Harness live state after third G3a-G failure` |

## 3. Independent review basis

The independent Codex verdict immediately preceding this approval, as given by
the Founder:

```text
PASS — EBD-014 FOURTH FORWARD CORRECTION VERIFIED — SAFE FOR ADR-005 / EBD-C
```

As reported by the Founder, Codex verified that no Founder decision, no
substantive correction, and no stale authoritative workflow field remained;
that the correction commit set is exactly 4 paths with ADR-005 the only
missing one; that the correction parent is `bc9a269c…` and the baseline
remains `4aec1e48…`; that the expected post-correction / pre-push divergence
is 4/0; and that the manifest is revision 4, built from the cumulative diff
from the original baseline to the prospective fourth corrected tip, with 20
entries that do not breach the four-path commit authorization. The full
verdict text is not held in this repository. This approval was made on the
Founder's instruction.

## 4. What is approved

The correction draft is substantively complete. The forward correction commit
is to contain exactly these four paths — no fifth correction path is
authorized:

| # | Status | Path |
|---|---|---|
| 1 | M | `docs/decisions/ADR-004-second-g3ag-correction-restart-ebd-c.md` |
| 2 | A | `docs/decisions/ADR-005-third-g3ag-correction-restart-ebd-c.md` (this record) |
| 3 | A | `docs/decisions/EBD-014-third-g3ag-forward-correction-commit-authorization.md` |
| 4 | M | `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` |

**Manifest and topology expectations, as independently verified:**

| Item | Value |
|---|---|
| Manifest revision | 4 |
| Manifest baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Manifest source scope | CUMULATIVE ORIGINAL BASELINE → PROSPECTIVE FOURTH CORRECTED TIP |
| Expected manifest entry count | 20 |
| Expected post-correction / pre-push divergence | 4/0 |

The fourth forward correction commit delta is exactly 4 paths; the cumulative
Governance Manifest has 20 entries. The 20 entries do not expand the
authorized correction commit path set. Relative to the original baseline,
ADR-004 remains one cumulative entry and `CURRENT_AUTONOMOUS_RUN.md` one
cumulative normalized entry; only ADR-005 and EBD-014 add new unique
cumulative paths.

**`EBD-014` condition state at issuance:**

| # | Condition | State |
|---|---|---|
| 1 | Independent pre-`EBD-C` review PASS | SATISFIED |
| 2 | ADR-005 / new `EBD-C` issued | SATISFIED |
| 3 | Substantive correction state frozen | SATISFIED |
| 4 | Revision-4 Governance Manifest finalized | NOT YET SATISFIED |
| 5 | Derived-metadata region Idle → Finalized | NOT YET SATISFIED |
| 6 | Manifest integrity and normalized identity verified | NOT YET SATISFIED |
| 7 | Native Windows Git exact authorized four-path verification | NOT YET SATISFIED |

**State at issuance:**

- the derived-metadata region is Idle;
- the Governance Manifest is NOT YET FINALIZED;
- `EBD-014` is APPROVED CONDITIONALLY — NOT YET EFFECTIVE; its stage and
  commit authorization are NOT YET EFFECTIVE;
- push is NOT AUTHORIZED;
- A2 / DEFECT-002 NOT ACTIVATED; Migration Authorization NONE.

**Limits of this approval.** It is a CTO approval under EBD-002, not an
independent review and not a gate verdict: the CTO drafted the documents it
approves. It was made without native Git; native computation and verification
belong to manifest finalization, to `EBD-014` conditions 4–7, and to `G3a-G`.

## 5. Decision

**`EBD-C`: APPROVED** — Claude Cowork, CTO, 2026-10-15. ADR-005 is the valid
`EBD-C` of the third correction restart.

## 6. Consequences accepted

**What this approval authorizes:** progression to the revision-4 Governance
Closure Manifest finalization (`REVIEW_PROTOCOL.md` §9.6 steps 5–8), natively,
by Claude Code.

**What it does not do.** It does not finalize the manifest, make `EBD-014`
effective, stage, commit, or push, activate A2 or any engineering batch, or
authorize migrations or product changes.

**Substantive freeze.** With this record and the `EBD-C` state in
`CURRENT_AUTONOMOUS_RUN.md` written, the substantive correction state is
frozen. Any substantive change after this approval invalidates this `EBD-C`
and requires the correction-restart lifecycle again.

This record cites no `manifest_id`; none exists for revision 4.

## 7. Ratification

| Role | Record |
|---|---|
| CTO — approver | Claude Cowork, 2026-10-15. `EBD-C` APPROVED. |
| AI Engineering Team — independent review | Codex: `PASS — EBD-014 FOURTH FORWARD CORRECTION VERIFIED — SAFE FOR ADR-005 / EBD-C`, as given by the Founder. The full verdict text is not held in this repository. |
| Founder & CEO | Not the approver of this checkpoint. Founder decisions this correction depends on: `EBD-010` (with its two supplemental decisions) and `EBD-014`. |
| CPO (Aboura) | No separate written review is held in this repository. |

## 8. Record notes

- **Identifier.** `ADR-005` is the next unused ADR identifier after
  `ADR-004`. It was reserved in `CURRENT_AUTONOMOUS_RUN.md` and in `EBD-014`
  before this record was written.
- **Date.** This record carries its actual issuance date, 2026-10-15
  (Asia/Amman). It is not backdated.
