# Executive Board Decision #015 — Fourth G3a-G Forward Correction Commit Authorization

**Status:** Ratified. Records the Founder's decision of 2026-10-15. Authorization status: APPROVED CONDITIONALLY — NOT YET EFFECTIVE.
**Version:** 1.0
**Category:** Decision Logs
**Scope:** The Founder's conditional authorization to stage and create exactly one forward correction governance commit above the fourth local governance commit of the post-activation governance reconciliation.
**Non-scope:** Any push; any other commit; any engineering batch; the content of the correction.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** Founder & CEO.
**Effective date:** 2026-10-15 (the record). The authorization itself takes effect only when every condition in Section 4 holds.
**Last updated:** 2026-10-15.

---

## 1. Why this record exists

`docs/governance/EBD-002_GOVERNANCE_MODEL.md` §4.1 states that a Founder
decision without a Decision Log entry is not an official decision, and §10
requires the entry at `docs/decisions/<ID>-<slug>.md`. This is a new Founder
decision, so it has its own entry. It records the decision; it adds nothing to
it.

## 2. Context

`G3a-G` failed on the first local governance commit
`a5965e0b100c41836c5247c09f84de58f0896105`, on the second
`042af4423159ada092db24c134095ef487e13aed`, on the third
`bc9a269c402451163223c5f7968465c58d455836`, and on the fourth
`e1cce4fe2aa2e4604d2ba01b05d8917db266f240`. Under the `EBD-010` Second
Supplemental Decision the closure entered a fourth correction restart:
`ADR-005` was invalidated, the derived-metadata region was reset to Idle, and
the live state was reconciled. `EBD-014` was consumed by
`e1cce4fe2aa2e4604d2ba01b05d8917db266f240` and authorizes no further commit.

## 3. Options considered

The instruction that recorded the decision lists no alternative, and none is
reconstructed here.

## 4. Decision

**Founder:** Mubarak. **Decision date:** 2026-10-15. **Decision:** APPROVED
CONDITIONALLY.

**Authorized:** staging, and the creation of exactly ONE forward correction
governance commit above the current correction parent
`e1cce4fe2aa2e4604d2ba01b05d8917db266f240`.

**Exact authorized commit subject:**

```text
Docs: reconcile Harness live state after fourth G3a-G failure
```

**Governance Closure Baseline:** remains
`4aec1e48a7ee9aac71d2769f11643ebb450b5959`. It does not move to
`a5965e0b…`, `042af442…`, `bc9a269c…`, `e1cce4fe…`, or to any later local
failed or corrected commit.

**Exact prospective correction commit path set:**

1. `docs/decisions/ADR-005-third-g3ag-correction-restart-ebd-c.md`
2. `docs/decisions/EBD-015-fourth-g3ag-forward-correction-commit-authorization.md`
3. `docs/decisions/ADR-006-fourth-g3ag-correction-restart-ebd-c.md`
4. `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md`

**Conditions — the authorization takes effect only after all of them:**

1. The independent pre-`EBD-C` review is PASS.
2. A new `EBD-C` is issued in `ADR-006`.
3. The substantive correction state is frozen.
4. The Governance Manifest is finalized under `REVIEW_PROTOCOL.md` with
   `batch: GOVERNANCE-ONLY` and baseline
   `4aec1e48a7ee9aac71d2769f11643ebb450b5959`.
5. The derived-metadata region transitions `Idle → Finalized`.
6. Manifest integrity and the normalized run-file identity are verified.
7. Native Windows Git verifies the exact authorized four-path correction set.

**Manifest revision, cumulative manifest entry count, and post-correction
pre-push divergence:** not fixed by this decision. They are derived from
repository governance (`REVIEW_PROTOCOL.md` and the actual Git topology) and
independently verified before `ADR-006` / `EBD-C`.

**Scope stop:** if any additional path or substantive change outside the
four-path correction set is required — STOP FOR FOUNDER.

**Explicitly not authorized:**

- push
- amend
- rebase
- reset
- squash
- history rewrite
- A2
- migrations
- product changes

**Push:** NOT AUTHORIZED. A push requires a separate Founder authorization
after `G3a-G` PASS on the future corrected tip.

**Current status:** APPROVED CONDITIONALLY — NOT YET EFFECTIVE.

## 5. Reasoning

No reasoning beyond the explicit decision was recorded, and none is added.

## 6. Consequences accepted

**What the decision does:** once every condition in Section 4 holds, Claude
Code may stage exactly the four paths above and create one commit with the
subject above, on `claude-safe-review`, with parent
`e1cce4fe2aa2e4604d2ba01b05d8917db266f240`. All four earlier local commits
stay in history beneath it.

**What it does not do:** it authorizes no push, no amend, rebase, reset,
squash, or history rewrite, no A2 activation, no migration, and no product
change.

## 7. Documents affected

- `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` — the current
  authorization state and the prospective fifth forward correction commit.

No harness rule changes. EBD-002 is unchanged.

## 8. Ratification

| Role | Record |
|---|---|
| Founder & CEO — approver | Mubarak, 2026-10-15. Authorization quoted in Section 4. |
| CTO — steward | Claude Cowork drafted this record under Founder instruction. A CTO record is not an independent review and is not an `EBD-C` approval. |
| AI Engineering Team — independent review | None is recorded here. The independent pre-`EBD-C` review is a later step. |
| CPO (Aboura) | No separate written review is held in this repository. |

## 9. Record notes

- **Identifier.** `EBD-015` is the next unused EBD identifier; `EBD-001` to
  `EBD-014` are in use. It is open to correction by the Founder.
- **Reserved EBD-C record.** `ADR-006` is reserved for the `EBD-C` of this
  correction. It is not created by this record.
