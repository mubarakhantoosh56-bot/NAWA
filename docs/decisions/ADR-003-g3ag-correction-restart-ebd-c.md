# Architectural Decision Record #003 — G3a-G Correction Restart EBD-C

**Status:** APPROVED — CTO — 2026-10-09.
**Version:** 1.0
**Category:** Decision Logs
**Scope:** The CTO's approval, at EBD-002 checkpoint `EBD-C`, of the substantive final state of the forward correction draft of the post-activation governance reconciliation, after its `G3a-G` failure and correction restart.
**Non-scope:** Any Founder decision; any independent gate verdict; the Governance Closure Manifest; staging, commit, or push; any engineering batch.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** CTO.
**Effective date:** 2026-10-09.
**Last updated:** 2026-10-09.

---

## 1. Why this record exists

`REVIEW_PROTOCOL.md` §9.6 step 11 requires a new `EBD-C` after a correction
restart, before the region may go from Idle to Finalized. `AUTONOMOUS_LOOP.md`
§8.4 and EBD-002 §4.3, §5.2, and §10 require that approval to be written,
dated, and named in a Decision Log entry. This is that entry. `ADR-002`, the
previous `EBD-C` of this closure, remains historical and INVALIDATED FOR
CORRECTION RESTART; this record does not change it.

## 2. Checkpoint record

| Field | Value |
|---|---|
| Checkpoint | `EBD-C` — G3a-G correction restart |
| Decision | **APPROVED** |
| Approver role | CTO — Chief Technology & Architecture Officer |
| Approver | Claude Cowork |
| Date | 2026-10-09 |
| Governance Closure Batch | `GOVERNANCE-ONLY` |
| Original Governance Closure Baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Forward correction parent | `a5965e0b100c41836c5247c09f84de58f0896105` (failed local commit) |
| Correction commit subject (`EBD-012`) | `Docs: correct Harness recovery state after G3a-G failure` |

## 3. Independent review basis

The independent Codex verdict immediately preceding this approval, as given by
the Founder:

```text
PASS — EBD-012 FORWARD CORRECTION VERIFIED — SAFE FOR ADR-003 / EBD-C
```

As reported by the Founder, Codex verified that no Founder decision and no
substantive correction remained; the correction parent is `a5965e0b…` and the
manifest baseline remains `4aec1e48…`; the correction commit set is exactly 4
paths with ADR-003 the only missing one; the expected corrected-tip divergence
is 2/0; the manifest revision is 2, built from the cumulative diff from the
baseline to the corrected tip, with 16 entries; and the 16-entry manifest does
not breach the four-path commit authorization. The full verdict text is not
held in this repository. This approval was made on the Founder's instruction.

## 4. What is approved

The correction draft is substantively complete. The forward correction commit
is to contain exactly these four paths — no other correction path is
authorized:

| # | Status | Path |
|---|---|---|
| 1 | M | `docs/decisions/ADR-002-post-activation-governance-reconciliation-ebd-c.md` |
| 2 | A | `docs/decisions/ADR-003-g3ag-correction-restart-ebd-c.md` (this record, the fourth path) |
| 3 | A | `docs/decisions/EBD-012-g3ag-forward-correction-commit-authorization.md` |
| 4 | M | `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` |

**Manifest expectations, as independently verified:**

| Item | Value |
|---|---|
| Governance Manifest revision | 2 |
| Manifest baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Manifest source scope | Cumulative diff from the original baseline to the corrected tip |
| Expected manifest entry count | 16 |

The 16 cumulative manifest entries are not the correction commit's path set.
The forward correction commit itself remains exactly four paths.

**State at issuance:**

- the derived-metadata region is Idle;
- the Governance Manifest is NOT YET FINALIZED;
- `EBD-012` is NOT YET EFFECTIVE;
- push is NOT AUTHORIZED;
- Engineering Batch `NONE`; A2 / DEFECT-002 NOT ACTIVATED; Migration
  Authorization NONE.

**Limits of this approval.** It is a CTO approval under EBD-002, not an
independent review and not a gate verdict: the CTO drafted the documents it
approves. It was made without native Git; native computation and verification
belong to manifest finalization, to `EBD-012` conditions 4–7, and to `G3a-G`.

## 5. Decision

**`EBD-C`: APPROVED** — Claude Cowork, CTO, 2026-10-09. ADR-003 is the valid
`EBD-C` of the correction restart.

## 6. Consequences accepted

**What this approval authorizes:** progression to the revision-2 Governance
Closure Manifest finalization (`REVIEW_PROTOCOL.md` §9.6 steps 5–8), natively,
by Claude Code.

**What it does not do.** It does not finalize the manifest, make `EBD-012`
effective, stage, commit, or push, activate A2 or any engineering batch, or
authorize migrations or product changes.

**Substantive freeze.** With this record and the `EBD-C` state in
`CURRENT_AUTONOMOUS_RUN.md` written, the substantive correction state is
frozen. Any substantive change after this approval invalidates this `EBD-C`
and requires the correction-restart lifecycle again.

This record cites no `manifest_id`; none exists for revision 2.

## 7. Ratification

| Role | Record |
|---|---|
| CTO — approver | Claude Cowork, 2026-10-09. `EBD-C` APPROVED. |
| AI Engineering Team — independent review | Codex: `PASS — EBD-012 FORWARD CORRECTION VERIFIED — SAFE FOR ADR-003 / EBD-C`, as given by the Founder. The full verdict text is not held in this repository. |
| Founder & CEO | Not the approver of this checkpoint. Founder decisions this correction depends on: `EBD-010` (with its two supplemental decisions) and `EBD-012`. |
| CPO (Aboura) | No separate written review is held in this repository. |

## 8. Record notes

- **Identifier.** `ADR-003` is the next unused ADR identifier after
  `ADR-002`. It was reserved in `CURRENT_AUTONOMOUS_RUN.md` before this record
  was written.
