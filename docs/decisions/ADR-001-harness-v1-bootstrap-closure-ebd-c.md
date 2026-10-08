# Architectural Decision Record #001 — EBD-C: CTO Approval of the Harness v1 Bootstrap Governance Closure

**Status:** Approved. Records the CTO's `EBD-C` approval of 2026-10-08.
**Version:** 1.0
**Category:** Decision Logs
**Scope:** The CTO's approval, at EBD-002 checkpoint `EBD-C`, of the substantive final state of the closure documentation for the initial bootstrap governance closure of the NAWA Autonomous Development Harness v1.
**Non-scope:** Any Founder decision; any independent gate verdict; the Governance Closure Manifest; any push; activation of the harness or of any engineering batch.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** CTO.
**Effective date:** 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. Why this record exists

`docs/execution/autonomy/AUTONOMOUS_LOOP.md` §8.4 and
`docs/execution/autonomy/REVIEW_PROTOCOL.md` §9.6 step 2 require a written CTO
approval of the closure documentation before any Governance Closure Manifest
is computed. `docs/governance/EBD-002_GOVERNANCE_MODEL.md` §4.3 makes the CTO
the approver of Current State updates; §5.2 and §10 require the approval to be
written, dated, and named, in a Decision Log entry at
`docs/decisions/<ID>-<slug>.md`. This is that entry.

## 2. Checkpoint record

| Field | Value |
|---|---|
| Checkpoint | `EBD-C` |
| Decision | **APPROVED** |
| Approver role | CTO — Chief Technology & Architecture Officer |
| Approver | Claude Cowork |
| Date | 2026-10-08 |
| Scope | NAWA Autonomous Development Harness v1 — initial bootstrap governance closure |
| Baseline | `9e2463fda8dad102601296f7e5bec33da5d68757` |
| Batch | `NONE` |
| Branch | `claude-safe-review` |
| Governance commit subject | `Docs: add NAWA Autonomous Development Harness v1 (Founder-ratified, bootstrap closure)` |

## 3. Context

The harness was ratified by the Founder
(`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`),
amended for its own first closure
(`docs/decisions/EBD-008-harness-bootstrap-amendment.md`), and its governance
commit was conditionally authorized
(`docs/decisions/EBD-009-harness-governance-commit-authorization.md`).

A first `EBD-C` review on 2026-10-08 withheld approval because the closure
documents were not yet at their substantive final state. They were then
corrected under `EBD-009`.

The independent Codex verdict immediately preceding this approval, as given by
the Founder:

```text
PASS — PRE-EBD-C CLOSURE STATE VERIFIED — CTO MAY PERFORM EBD-C
```

The full verdict text is not held in this repository. The review was performed
on the Founder's instruction of 2026-10-08.

## 4. What was reviewed

The fifteen closure paths that existed when the review was made. With this
record they are the sixteen paths of the prospective governance commit.

| # | Status | Path |
|---|---|---|
| 1 | M | `AGENTS.md` |
| 2 | M | `CLAUDE.md` |
| 3 | M | `CURRENT_STATE.md` |
| 4 | A | `docs/decisions/ADR-001-harness-v1-bootstrap-closure-ebd-c.md` (this record) |
| 5 | A | `docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md` |
| 6 | A | `docs/decisions/EBD-008-harness-bootstrap-amendment.md` |
| 7 | A | `docs/decisions/EBD-009-harness-governance-commit-authorization.md` |
| 8 | A | `docs/execution/autonomy/ACTIVE_BATCH.md` |
| 9 | A | `docs/execution/autonomy/AUTONOMOUS_LOOP.md` |
| 10 | A | `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` |
| 11 | A | `docs/execution/autonomy/FOUNDER_REVIEW_PACKAGE_TEMPLATE.md` |
| 12 | A | `docs/execution/autonomy/FOUNDER_STOP_CONDITIONS.md` |
| 13 | A | `docs/execution/autonomy/NAWA_AUTONOMOUS_DEVELOPMENT_CHARTER.md` |
| 14 | A | `docs/execution/autonomy/REVIEW_PROTOCOL.md` |
| 15 | A | `docs/execution/autonomy/ROLE_MATRIX.md` |
| 16 | A | `docs/execution/autonomy/SESSION_RECOVERY_PROTOCOL.md` |

The files were read again for this review. Their bytes were compared with the
state left at the end of the closure preparation, and no path had changed.

## 5. CTO review determinations

1. **Founder decisions.** `EBD-007`, `EBD-008`, and `EBD-009` are on record.
   Each quotes the Founder's statement, and they agree with each other and
   with Charter §18 and §19.
2. **`CURRENT_STATE.md`.** One additive entry records the harness milestone.
   It is accurate and changes no other status in the file.
3. **Activation state.** Engineering Batch `NONE`, Product Development
   `NOT ACTIVE`, A2 / DEFECT-002 `NOT ACTIVATED`, Migration Authorization
   `NONE` — stated consistently in `ACTIVE_BATCH.md`,
   `CURRENT_AUTONOMOUS_RUN.md`, and `CURRENT_STATE.md`.
4. **Harness status.** `FOUNDER RATIFIED AS AMENDED — NOT YET ACTIVE`
   throughout. No document states that the harness is ACTIVE.
5. **Bootstrap conditions** (`REVIEW_PROTOCOL.md` §9.2). Engineering Batch is
   `NONE`; no engineering commit exists for the harness run; the closure set
   is documentation only; the baseline contains no file under
   `docs/execution/autonomy/`.
6. **Run state.** The checkpoint records the commit authorization, a complete
   prospective `Ahead State`, and the prospective commit by parent, subject,
   and exact path list. `EBD-A`, `EBD-B`, `G3a-E`, and `G3b-E` are recorded as
   not applicable to this closure. The derived-metadata region is Idle.
7. **Scope.** Documentation only. No product code, test, migration, data,
   knowledge, or secret is in the closure set. No document under
   `docs/governance/` is changed, and EBD-002 is not amended.
8. **Push.** No push authorization is recorded anywhere in the closure set.

**Limits of this review.** It is a CTO approval under EBD-002. It is not an
independent review and not a gate verdict: the CTO drafted the documents it
approves. It was made without native Git; native computation and verification
belong to Governance Closure Manifest finalization and to `G3a-G`.

## 6. Options considered

`APPROVED`, or `CHANGES REQUESTED` with a return to Governance Closure
Documentation (`AUTONOMOUS_LOOP.md` §8.4). No change is requested.

## 7. Decision

**`EBD-C`: APPROVED** — Claude Cowork, CTO, 2026-10-08.

The substantive final state of the closure documentation listed in Section 4
is approved for the initial bootstrap governance closure of the NAWA
Autonomous Development Harness v1.

## 8. Reasoning

The determinations in Section 5 hold, the Founder decisions the closure
depends on are on record, and the independent verification of the pre-`EBD-C`
state passed.

## 9. Consequences accepted

**What this approval authorizes:** progression to Governance Closure Manifest
finalization (`REVIEW_PROTOCOL.md` §9.6 steps 5–8), natively, by Claude Code.

**What it does not do.** It does not:

- activate A2 or any engineering batch
- authorize migrations
- authorize production deployment
- authorize push
- authorize history rewriting
- mark the harness ACTIVE

It is not a Founder approval and not a Codex verdict. The staging and
governance commit authorization is the Founder's, in `EBD-009`, and stays
subject to every execution condition recorded there. The Founder's
Sprint-boundary review of `CURRENT_STATE.md` under EBD-002 §4.3 is unchanged.

**Substantive freeze.** With this record and the `EBD-C` entry in
`CURRENT_AUTONOMOUS_RUN.md` written, no substantive byte of the closure set
may change. The only later change permitted before the commit is the
mechanically derived manifest metadata, inside the derived-metadata region of
`CURRENT_AUTONOMOUS_RUN.md` (`REVIEW_PROTOCOL.md` §9.5). Any other change, for
any reason, invalidates this approval, and `EBD-C` is repeated
(`REVIEW_PROTOCOL.md` §9.6 step 4).

This record cites no `manifest_id`. None existed when it was written: the
approval comes first and the manifest binds it.

## 10. Documents affected

- `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` — the `EBD-C` approval
  recorded under `EBD-002 Approvals`, with the run state that records it.

No other document changes.

## 11. Ratification

| Role | Record |
|---|---|
| CTO — approver | Claude Cowork, 2026-10-08. `EBD-C` APPROVED. |
| AI Engineering Team — independent review | Codex: `PASS — PRE-EBD-C CLOSURE STATE VERIFIED — CTO MAY PERFORM EBD-C`, as given by the Founder. The full verdict text is not held in this repository. |
| Founder & CEO | Not the approver of this checkpoint. The Founder decisions it depends on are `EBD-007`, `EBD-008`, and `EBD-009`. |
| CPO (Aboura) | No separate written review is held in this repository. EBD-002 §5.1 and Appendix A list no mandatory reviewer for a Current State update. |

## 12. Record notes

- **Identifier.** `ADR-001` is the first ADR identifier allocated in this
  repository. It was reserved in `CURRENT_AUTONOMOUS_RUN.md` before this
  record was written.
