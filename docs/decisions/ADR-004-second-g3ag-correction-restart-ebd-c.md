# Architectural Decision Record #004 — Second G3a-G Correction Restart EBD-C

**Status:** APPROVED — CTO — 2026-10-14.
**Version:** 1.0
**Category:** Decision Logs
**Scope:** The CTO's approval, at EBD-002 checkpoint `EBD-C`, of the substantive final state of the third forward correction draft of the post-activation governance reconciliation, after its second `G3a-G` failure and correction restart.
**Non-scope:** Any Founder decision; any independent gate verdict; the Governance Closure Manifest; staging, commit, or push; any engineering batch.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** CTO.
**Effective date:** 2026-10-14.
**Last updated:** 2026-10-14.

---

## 1. Why this record exists

`REVIEW_PROTOCOL.md` §9.6 step 11 requires a new `EBD-C` after a correction
restart, before the region may go from Idle to Finalized. `AUTONOMOUS_LOOP.md`
§8.4 and EBD-002 §4.3, §5.2, and §10 require that approval to be written,
dated, and named in a Decision Log entry. This is that entry. `ADR-002` and
`ADR-003`, the earlier `EBD-C` records of this closure, remain historical and
INVALIDATED FOR CORRECTION RESTART; this record does not change them.

## 2. Checkpoint record

| Field | Value |
|---|---|
| Checkpoint | `EBD-C` — second G3a-G correction restart |
| Decision | **APPROVED** |
| Approver role | CTO — Chief Technology & Architecture Officer |
| Approver | Claude Cowork |
| Date | 2026-10-14 |
| Governance Closure Batch | `GOVERNANCE-ONLY` |
| Original Governance Closure Baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Forward correction parent | `042af4423159ada092db24c134095ef487e13aed` (second local commit) |
| Correction commit subject (`EBD-013`) | `Docs: reconcile Harness live workflow state after second G3a-G failure` |

## 3. Independent review basis

The independent Codex verdict immediately preceding this approval, as given by
the Founder:

```text
PASS — EBD-013 THIRD FORWARD CORRECTION VERIFIED — SAFE FOR ADR-004 / EBD-C
```

As reported by the Founder, Codex verified that no Founder decision, no
substantive correction, and no stale authoritative workflow field remained;
that the correction commit set is exactly 4 paths with ADR-004 the only
missing one; that the correction parent is `042af442…` and the baseline
remains `4aec1e48…`; that the expected third-tip divergence before push is
3/0; and that the manifest is revision 3, built from the cumulative diff from
the original baseline to the prospective third corrected tip, with 18 entries
that do not breach the four-path commit authorization. The full verdict text
is not held in this repository. This approval was made on the Founder's
instruction.

## 4. What is approved

The correction draft is substantively complete. The forward correction commit
is to contain exactly these four paths — no fifth correction path is
authorized:

| # | Status | Path |
|---|---|---|
| 1 | M | `docs/decisions/ADR-003-g3ag-correction-restart-ebd-c.md` |
| 2 | A | `docs/decisions/ADR-004-second-g3ag-correction-restart-ebd-c.md` (this record) |
| 3 | A | `docs/decisions/EBD-013-second-g3ag-forward-correction-commit-authorization.md` |
| 4 | M | `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` |

**Manifest expectations, as independently verified:**

| Item | Value |
|---|---|
| Manifest revision | 3 |
| Manifest baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Manifest source scope | Cumulative diff from the original baseline to the prospective third corrected tip |
| Expected manifest entry count | 18 |

The forward correction commit path set is exactly 4; the cumulative
Governance Manifest has 18 entries. The 18-entry manifest does not expand the
authorized commit path set. Relative to the original baseline, ADR-003 remains
one cumulative entry and `CURRENT_AUTONOMOUS_RUN.md` one cumulative normalized
entry; only ADR-004 and EBD-013 add new unique cumulative paths.

**State at issuance:**

- the derived-metadata region is Idle;
- the Governance Manifest is NOT YET FINALIZED;
- `EBD-013` is APPROVED CONDITIONALLY — NOT YET EFFECTIVE;
- push is NOT AUTHORIZED;
- A2 / DEFECT-002 NOT ACTIVATED; Migration Authorization NONE.

**Limits of this approval.** It is a CTO approval under EBD-002, not an
independent review and not a gate verdict: the CTO drafted the documents it
approves. It was made without native Git; native computation and verification
belong to manifest finalization, to `EBD-013` conditions 4–7, and to `G3a-G`.

## 5. Decision

**`EBD-C`: APPROVED** — Claude Cowork, CTO, 2026-10-14. ADR-004 is the valid
`EBD-C` of the second correction restart.

## 6. Consequences accepted

**What this approval authorizes:** progression to the revision-3 Governance
Closure Manifest finalization (`REVIEW_PROTOCOL.md` §9.6 steps 5–8), natively,
by Claude Code.

**What it does not do.** It does not finalize the manifest, make `EBD-013`
effective, stage, commit, or push, activate A2 or any engineering batch, or
authorize migrations or product changes.

**Substantive freeze.** With this record and the `EBD-C` state in
`CURRENT_AUTONOMOUS_RUN.md` written, the substantive correction state is
frozen. Any substantive change after this approval invalidates this `EBD-C`
and requires the correction-restart lifecycle again.

This record cites no `manifest_id`; none exists for revision 3.

## 7. Ratification

| Role | Record |
|---|---|
| CTO — approver | Claude Cowork, 2026-10-14. `EBD-C` APPROVED. |
| AI Engineering Team — independent review | Codex: `PASS — EBD-013 THIRD FORWARD CORRECTION VERIFIED — SAFE FOR ADR-004 / EBD-C`, as given by the Founder. The full verdict text is not held in this repository. |
| Founder & CEO | Not the approver of this checkpoint. Founder decisions this correction depends on: `EBD-010` (with its two supplemental decisions) and `EBD-013`. |
| CPO (Aboura) | No separate written review is held in this repository. |

## 8. Record notes

- **Identifier.** `ADR-004` is the next unused ADR identifier after
  `ADR-003`. It was reserved in `CURRENT_AUTONOMOUS_RUN.md` before this record
  was written.
- **Date.** The instruction that requested this approval gave the status date
  2026-10-12; the approval was issued on 2026-10-14, and this record carries
  the date of issuance.
