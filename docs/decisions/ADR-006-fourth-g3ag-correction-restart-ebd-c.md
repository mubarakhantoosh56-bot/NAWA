# Architectural Decision Record #006 — Fourth G3a-G Correction Restart EBD-C

**Status:** INVALIDATED FOR CORRECTION RESTART (2026-10-15; Section 9). Originally APPROVED — CTO — 2026-10-15.
**Version:** 1.1 — adds the invalidation record (Section 9). Sections 1–8 are unchanged.
**Category:** Decision Logs
**Scope:** The CTO's approval, at EBD-002 checkpoint `EBD-C`, of the substantive final state of the fifth forward correction draft of the post-activation governance reconciliation, after its fourth `G3a-G` failure and correction restart.
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
`ADR-003`, `ADR-004`, and `ADR-005`, the earlier `EBD-C` records of this
closure, remain historical and INVALIDATED FOR CORRECTION RESTART; this record
does not change them. `ADR-006` is the new valid `EBD-C` of this closure.

## 2. Checkpoint record

| Field | Value |
|---|---|
| Checkpoint | `EBD-C` — fourth G3a-G correction restart |
| Decision | **APPROVED** |
| Approver role | CTO — Chief Technology & Architecture Officer |
| Approver | Claude Cowork |
| Date | 2026-10-15 |
| Governance Closure Batch | `GOVERNANCE-ONLY` |
| Original Governance Closure Baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Forward correction parent | `e1cce4fe2aa2e4604d2ba01b05d8917db266f240` (fourth local commit) |
| Correction commit subject (`EBD-015`) | `Docs: reconcile Harness live state after fourth G3a-G failure` |

## 3. Independent review basis

The independent Codex verdict immediately preceding this approval, as given by
the Founder:

```text
PASS — EBD-015 FOCUSED RE-REVIEW PASSED — SAFE FOR ADR-006 / EBD-C
```

As reported by the Founder, Codex confirmed that the earlier MINOR finding
(the stale `Last updated` header of `CURRENT_AUTONOMOUS_RUN.md`) is resolved,
with `Last updated` 2026-10-15; that no stale authoritative field, no S10
condition, no open Founder decision, and no substantive correction remained;
that the correction commit set is exactly 4 paths with ADR-006 the only
missing one; that the correction parent is `e1cce4fe…` and the baseline
remains `4aec1e48…`; that the expected post-correction / pre-push divergence
is 5/0; and that the manifest is revision 5, built from the cumulative diff
from the original baseline to the prospective fifth corrected tip, with 22
entries that do not breach the four-path commit authorization. The full
verdict text is not held in this repository. This approval was made on the
Founder's instruction.

## 4. What is approved

The correction draft is substantively complete. The forward correction commit
is to contain exactly these four paths — no fifth correction path is
authorized:

| # | Status | Path |
|---|---|---|
| 1 | M | `docs/decisions/ADR-005-third-g3ag-correction-restart-ebd-c.md` |
| 2 | A | `docs/decisions/ADR-006-fourth-g3ag-correction-restart-ebd-c.md` (this record) |
| 3 | A | `docs/decisions/EBD-015-fourth-g3ag-forward-correction-commit-authorization.md` |
| 4 | M | `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` |

**Manifest and topology expectations, as independently verified:**

| Item | Value |
|---|---|
| Manifest revision | 5 |
| Manifest baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Manifest source scope | CUMULATIVE ORIGINAL BASELINE → PROSPECTIVE FIFTH CORRECTED TIP |
| Expected manifest entry count | 22 |
| Expected post-correction / pre-push divergence | 5/0 |

The fifth forward correction commit delta is exactly 4 paths; the cumulative
Governance Manifest has 22 entries. The 22 entries do not expand the
authorized correction commit path set. Relative to the original baseline,
ADR-005 remains one cumulative entry and `CURRENT_AUTONOMOUS_RUN.md` one
cumulative normalized entry; only ADR-006 and EBD-015 add new unique
cumulative paths.

**`EBD-015` condition state at issuance:**

| # | Condition | State |
|---|---|---|
| 1 | Independent pre-`EBD-C` review PASS | SATISFIED |
| 2 | ADR-006 / new `EBD-C` issued | SATISFIED |
| 3 | Substantive correction state frozen | SATISFIED |
| 4 | Revision-5 Governance Manifest finalized | NOT YET SATISFIED |
| 5 | Derived-metadata region Idle → Finalized | NOT YET SATISFIED |
| 6 | Manifest integrity and normalized identity verified | NOT YET SATISFIED |
| 7 | Native Windows Git exact authorized four-path verification | NOT YET SATISFIED |

**State at issuance:**

- the derived-metadata region is Idle;
- the Governance Manifest is NOT YET FINALIZED;
- `EBD-015` is APPROVED CONDITIONALLY — NOT YET EFFECTIVE; its stage and
  commit authorization are NOT YET EFFECTIVE;
- push is NOT AUTHORIZED;
- A2 / DEFECT-002 NOT ACTIVATED; Migration Authorization NONE.

**Limits of this approval.** It is a CTO approval under EBD-002, not an
independent review and not a gate verdict: the CTO drafted the documents it
approves. It was made without native Git; native computation and verification
belong to manifest finalization, to `EBD-015` conditions 4–7, and to `G3a-G`.

## 5. Decision

**`EBD-C`: APPROVED** — Claude Cowork, CTO, 2026-10-15. ADR-006 is the valid
`EBD-C` of the fourth correction restart.

## 6. Consequences accepted

**What this approval authorizes:** progression to the revision-5 Governance
Closure Manifest finalization (`REVIEW_PROTOCOL.md` §9.6 steps 5–8), natively,
by Claude Code.

**What it does not do.** It does not finalize the manifest, make `EBD-015`
effective, stage, commit, or push, activate A2 or any engineering batch, or
authorize migrations or product changes.

**Substantive freeze.** With this record and the `EBD-C` state in
`CURRENT_AUTONOMOUS_RUN.md` written, the substantive correction state is
frozen. Any substantive change after this approval invalidates this `EBD-C`
and requires the correction-restart lifecycle again.

This record cites no `manifest_id`; none exists for revision 5.

## 7. Ratification

| Role | Record |
|---|---|
| CTO — approver | Claude Cowork, 2026-10-15. `EBD-C` APPROVED. |
| AI Engineering Team — independent review | Codex: `PASS — EBD-015 FOCUSED RE-REVIEW PASSED — SAFE FOR ADR-006 / EBD-C`, as given by the Founder (after an earlier focused FAIL on one MINOR stale-header finding, since resolved). The full verdict text is not held in this repository. |
| Founder & CEO | Not the approver of this checkpoint. Founder decisions this correction depends on: `EBD-010` (with its two supplemental decisions) and `EBD-015`. |
| CPO (Aboura) | No separate written review is held in this repository. |

## 8. Record notes

- **Identifier.** `ADR-006` is the next unused ADR identifier after
  `ADR-005`. It was reserved in `CURRENT_AUTONOMOUS_RUN.md` and in `EBD-015`
  before this record was written.
- **Date.** This record carries its actual issuance date, 2026-10-15
  (Asia/Amman). It is not backdated.

## 9. Invalidation record — INVALIDATED FOR CORRECTION RESTART (2026-10-15)

This section is appended; Sections 1–8 above are the original approval and are
not rewritten. The approval of 2026-10-15 stands as a historical fact.

- **Status:** this correction-restart `EBD-C` is INVALIDATED FOR CORRECTION
  RESTART, under the `EBD-010` Second Supplemental Decision
  (`REVIEW_PROTOCOL.md` §9.6 step 11).
- **Why:** `G3a-G` failed on the fifth corrected tip
  `9a5759fcdcadda313620f3c3106e96ecbd77f34d` —
  `FAIL — G3a-G FIFTH CORRECTED TIP NOT SAFE FOR PUSH`, as stated by the
  Founder. As reported, the immutable committed closure verified successfully
  (commit identity, parent and subject, the exact four-path correction delta,
  the five-commit forward-only topology, the revision-5 manifest and its 22
  cumulative entries, the canonical manifest and `manifest_id`, the normalized
  run identity, this record, the consumption of `EBD-015`, derived-region byte
  integrity, the remote state, and the product-safety boundary). The failure
  is confined to the live worktree copy of `CURRENT_AUTONOMOUS_RUN.md`: a
  BLOCKER (`SESSION_RECOVERY_PROTOCOL.md` §4.2, class S10) — the top-level
  `Fourth Corrected Tip` field still declared
  `e1cce4fe2aa2e4604d2ba01b05d8917db266f240` the current local HEAD; and a
  MAJOR — three historical commit blocks still carried an unqualified
  present-tense claim that the live derived-metadata region was Idle, which
  conflicted with the live revision-5 Finalized region.
- **Push:** `9a5759fcdcadda313620f3c3106e96ecbd77f34d` was not pushed. The
  closure is NOT PUSHABLE.
- **Baseline:** unchanged — `4aec1e48a7ee9aac71d2769f11643ebb450b5959`.
- **History:** all five local governance commits —
  `a5965e0b100c41836c5247c09f84de58f0896105`,
  `042af4423159ada092db24c134095ef487e13aed`,
  `bc9a269c402451163223c5f7968465c58d455836`,
  `e1cce4fe2aa2e4604d2ba01b05d8917db266f240`, and
  `9a5759fcdcadda313620f3c3106e96ecbd77f34d` — remain intact and are not
  amended, rebased, reset, squashed, or replaced. No history is rewritten. Any
  correction is a forward-only commit above
  `9a5759fcdcadda313620f3c3106e96ecbd77f34d`.
- **Authorization:** `EBD-015` is consumed by
  `9a5759fcdcadda313620f3c3106e96ecbd77f34d` and authorizes no further commit
  and no push.
- **Next:** a new Founder authorization and a new `EBD-C`, with its own
  Decision Log record, will be required.
