# Architectural Decision Record #002 — EBD-C: CTO Approval of the Post-Activation Governance Reconciliation

**Status:** INVALIDATED FOR CORRECTION RESTART (2026-10-09; Section 9). Originally Approved — records the CTO's `EBD-C` approval of 2026-10-09.
**Version:** 1.1 — adds the invalidation record (Section 9). Sections 1–8 are unchanged.
**Category:** Decision Logs
**Scope:** The CTO's approval, at EBD-002 checkpoint `EBD-C`, of the substantive final state of the post-activation governance reconciliation — a `GOVERNANCE-ONLY` closure under `EBD-010`.
**Non-scope:** Any Founder decision; any independent gate verdict; the Governance Closure Manifest; staging, commit, or push; any engineering batch.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** CTO.
**Effective date:** 2026-10-09.
**Last updated:** 2026-10-09.

---

## 1. Why this record exists

`docs/execution/autonomy/AUTONOMOUS_LOOP.md` §8.4 and
`docs/execution/autonomy/REVIEW_PROTOCOL.md` §9.6 step 2 require a written CTO
approval of the closure documentation before any Governance Closure Manifest
is computed. `docs/governance/EBD-002_GOVERNANCE_MODEL.md` §4.3 makes the CTO
the approver of Current State updates; §5.2 and §10 require the approval to be
written, dated, and named, in a Decision Log entry. This is that entry. It is
the monotonic successor of `ADR-001`, the `EBD-C` record of the bootstrap
closure.

## 2. Checkpoint record

| Field | Value |
|---|---|
| Checkpoint | `EBD-C` |
| Decision | **APPROVED** |
| Approver role | CTO — Chief Technology & Architecture Officer |
| Approver | Claude Cowork |
| Date | 2026-10-09 |
| Scope | Post-Activation Governance Reconciliation |
| Governance Closure Batch | `GOVERNANCE-ONLY` |
| Baseline | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Branch | `claude-safe-review` |
| Proposed commit subject (`EBD-011`) | `Docs: reconcile active Harness governance and formalize governance-only closures` |

## 3. Independent review basis

The independent Codex verdict immediately preceding this approval, as given by
the Founder:

```text
PASS — EBD-011 AND CURRENT CLOSURE STATE VERIFIED — SAFE FOR EBD-C
```

As reported by the Founder, Codex verified that the earlier BLOCKER and MAJOR
findings were resolved, that no Founder decision and no substantive correction
remained, that `EBD-011` is valid and conditional, that the prospective path
set is 14 with ADR-002 the only missing path, that the derived-metadata region
was exactly Idle, and that nothing had been staged, committed, or pushed. The
full verdict text is not held in this repository. This approval was made on
the Founder's instruction.

## 4. What is approved

The substantive governance state of the fourteen paths of the prospective
commit — the thirteen that existed at review, which include `EBD-011`, and
this record:

| # | Status | Path |
|---|---|---|
| 1 | M | `CURRENT_STATE.md` |
| 2 | A | `docs/decisions/ADR-002-post-activation-governance-reconciliation-ebd-c.md` (this record) |
| 3 | A | `docs/decisions/EBD-010-permanent-governance-only-closure-rule.md` |
| 4 | A | `docs/decisions/EBD-011-post-activation-governance-reconciliation-commit-authorization.md` |
| 5 | M | `docs/execution/autonomy/ACTIVE_BATCH.md` |
| 6 | M | `docs/execution/autonomy/AUTONOMOUS_LOOP.md` |
| 7 | M | `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` |
| 8 | M | `docs/execution/autonomy/FOUNDER_REVIEW_PACKAGE_TEMPLATE.md` |
| 9 | M | `docs/execution/autonomy/FOUNDER_STOP_CONDITIONS.md` |
| 10 | A | `docs/execution/autonomy/H0_FOUNDER_REVIEW_PACKAGE.md` |
| 11 | M | `docs/execution/autonomy/NAWA_AUTONOMOUS_DEVELOPMENT_CHARTER.md` |
| 12 | M | `docs/execution/autonomy/REVIEW_PROTOCOL.md` |
| 13 | M | `docs/execution/autonomy/ROLE_MATRIX.md` |
| 14 | M | `docs/execution/autonomy/SESSION_RECOVERY_PROTOCOL.md` |

State at issuance:

- the derived-metadata region of `CURRENT_AUTONOMOUS_RUN.md` is Idle;
- the Governance Manifest is NOT YET FINALIZED;
- the `EBD-011` stage/commit authorization is APPROVED CONDITIONALLY — NOT YET
  EFFECTIVE;
- push is NOT AUTHORIZED;
- Engineering Batch `NONE`; A2 / DEFECT-002 NOT ACTIVATED; Migration
  Authorization NONE.

**Limits of this approval.** It is a CTO approval under EBD-002, not an
independent review and not a gate verdict: the CTO drafted the documents it
approves. It was made without native Git; native computation and verification
belong to manifest finalization, to `EBD-011` condition 6, and to `G3a-G`.

## 5. Decision

**`EBD-C`: APPROVED** — Claude Cowork, CTO, 2026-10-09.

## 6. Consequences accepted

**What this approval authorizes:** progression to Governance Closure Manifest
finalization (`REVIEW_PROTOCOL.md` §9.6 steps 5–8) with `batch:
GOVERNANCE-ONLY` and baseline `4aec1e48a7ee9aac71d2769f11643ebb450b5959`,
natively, by Claude Code.

**What it does not do.** It does not finalize the manifest, make the `EBD-011`
authorization effective, stage, commit, or push, activate A2 or any
engineering batch, or authorize migrations or product changes.

**Substantive freeze.** With this record and the `EBD-C` state in
`CURRENT_AUTONOMOUS_RUN.md` written, the substantive governance state is
frozen. The only change permitted before the commit is the deterministic
`Idle → Finalized` insertion into the derived-metadata region. Any substantive
content change after this `EBD-C` invalidates it and requires the approved
correction-restart lifecycle (`REVIEW_PROTOCOL.md` §9.5, §9.6 steps 4 and 11)
before `EBD-C` is issued again.

This record cites no `manifest_id`; none exists.

## 7. Ratification

| Role | Record |
|---|---|
| CTO — approver | Claude Cowork, 2026-10-09. `EBD-C` APPROVED. |
| AI Engineering Team — independent review | Codex: `PASS — EBD-011 AND CURRENT CLOSURE STATE VERIFIED — SAFE FOR EBD-C`, as given by the Founder. The full verdict text is not held in this repository. |
| Founder & CEO | Not the approver of this checkpoint. Founder decisions this closure depends on: `EBD-010` (with its two supplemental decisions) and `EBD-011`. |
| CPO (Aboura) | No separate written review is held in this repository. EBD-002 §5.1 and Appendix A list no mandatory reviewer for a Current State update. |

## 8. Record notes

- **Identifier.** `ADR-002` is the next unused ADR identifier after
  `ADR-001`. It was reserved in `CURRENT_AUTONOMOUS_RUN.md` before this record
  was written.

## 9. Invalidation record — INVALIDATED FOR CORRECTION RESTART (2026-10-09)

This section is appended; Sections 1–8 above are the original approval and are
not rewritten. The approval of 2026-10-09 stands as a historical fact.

- **Status:** `EBD-C` for the post-activation governance reconciliation is
  INVALIDATED FOR CORRECTION RESTART, under the `EBD-010` Second Supplemental
  Decision (`REVIEW_PROTOCOL.md` §9.6 step 11).
- **Why:** `G3a-G` failed — `FAIL — G3a-G GOVERNANCE COMMIT NOT SAFE FOR PUSH`,
  as stated by the Founder — on the governance commit
  `a5965e0b100c41836c5247c09f84de58f0896105` (parent
  `4aec1e48a7ee9aac71d2769f11643ebb450b5959`). As reported, the committed
  governance snapshot verified successfully, but the live checkpoint in the
  worktree copy of `CURRENT_AUTONOMOUS_RUN.md` contradicted itself: its
  `Local HEAD` and `Ahead Behind` fields still read
  `4aec1e48a7ee9aac71d2769f11643ebb450b5959` and `0 / 0`, while Git and the
  file's own `Ahead State` showed HEAD `a5965e0b…` and 1/0.
- **Push:** never occurred. The closure is NOT PUSHABLE.
- **Baseline:** unchanged — `4aec1e48a7ee9aac71d2769f11643ebb450b5959`.
- **History:** the failed local commit remains in history and is not amended,
  rebased, reset, or otherwise rewritten. Any correction is a forward commit
  above it.
- **Next:** correction restart under `EBD-010`. A new `EBD-C` is required after
  the correction; it will have its own Decision Log record.
