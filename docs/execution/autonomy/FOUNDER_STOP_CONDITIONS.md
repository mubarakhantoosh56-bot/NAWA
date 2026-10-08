# Founder Stop Conditions

**Status:** Founder-ratified on 2026-10-08 (`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`). Not ACTIVE until `G3b-G` PASS on the harness governance commit.
**Version:** 1.0
**Category:** Agent Instructions
**Scope:** The conditions under which autonomous execution must stop and wait for the Founder, and the procedure for stopping.
**Non-scope:** Routine engineering failures (a failing test, a bug in the change being built), which are handled inside the loop.
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10.
**Approval authority:** Founder (scope and authority rules).
**Effective date:** On successful remote verification (`G3b-G`) of the harness governance commit. Founder-ratified 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. Rule

If any condition below is met, or would be met by the next action, the team
stops **before** taking that action. An active batch does not relax these: a
batch grants authority only inside its recorded scope and its explicitly
granted exceptions.

Any agent that observes a stop condition declares it. When in doubt whether a
condition applies, it applies.

This list does not narrow EBD-002. A decision or review that
`docs/governance/EBD-002_GOVERNANCE_MODEL.md` reserves to the Founder stops the
run even when no FSC id fits — for example a checkpoint outcome of
`FOUNDER REQUIRED` (`AUTONOMOUS_LOOP.md` §8). It is recorded as
`EBD-002 — Founder decision required` and follows the stop procedure in
Section 5.

**Forward correction is the default.** If a reviewed commit needs correcting,
the correction is a new commit on top, sent through the appropriate review
gates. Amending, rebasing, or resetting it instead is FSC-09 and needs explicit
Founder authorization, even when the commit has never been pushed.

## 2. Mandatory Founder approval (Charter §6)

| ID | Condition | Operational meaning |
|---|---|---|
| FSC-01 | New batch / Slice / Milestone activation | Starting any work not covered by the current activation record, including the "next eligible" batch |
| FSC-02 | Migrations | Creating, editing, renaming, or running any file under `migrations/`, unless the activation record grants that exact migration |
| FSC-03 | Schema changes | Any change to tables, columns, indexes, constraints, or extensions, by any means |
| FSC-04 | Destructive DB operations | `DELETE`, `TRUNCATE`, `DROP`, or bulk `UPDATE` against any database other than a disposable test database created by the test run itself |
| FSC-05 | Historical evidence deletion or rewrite | Deleting or rewriting recorded evidence, review findings, validation artifacts, or closed-batch documentation |
| FSC-06 | Merge to `main` | Any merge, rebase, or push that changes `main` |
| FSC-07 | Production deployment | Any deploy, or any change to deployment configuration that takes effect in production |
| FSC-08 | Force push | Any push that is not a normal fast-forward, including `--force` and `--force-with-lease` |
| FSC-09 | Git history rewrite or lineage replacement — local, unpublished, pushed, or shared | `git commit --amend`; `git rebase`; `git reset` when it changes what commit a branch points to; history filtering or rewriting; deleting or re-pointing a branch or ref; replacing or recreating an already reviewed commit under a new identity. **Not limited to shared history** — a commit that exists only locally is protected the same way |
| FSC-10 | Secrets / credentials changes | Creating, editing, rotating, printing, or copying secrets or credentials; any change to `.env` files |
| FSC-11 | Major architecture-contract changes | Any change that contradicts or amends a ratified architecture contract, freeze, or the Reasoning Constitution |
| FSC-12 | Material scope expansion | The batch cannot meet its acceptance criteria without work outside its recorded scope |
| FSC-13 | Increased autonomous production authority | Any change that lets NAWA or its agents act with more autonomy in production than today |
| FSC-14 | Unresolved material disagreement between implementation and reviewer | The implementer disputes a finding rather than fixes it; reviewer requirements contradict each other; or repeated failure leaves no credible bounded correction path. Two failed correction cycles alone are a reassessment trigger, not a stop (`REVIEW_PROTOCOL.md` §8) |

## 3. Operational stop conditions

Accepted by the Founder (H0.1, 2026-10-05). They exist so the mandatory list
cannot be bypassed indirectly. FSC-17 and FSC-18 restate rules that already
exist in the repository.

| ID | Condition | Source |
|---|---|---|
| FSC-15 | Git state does not match `CURRENT_AUTONOMOUS_RUN.md` and the discrepancy is not a benign class | `SESSION_RECOVERY_PROTOCOL.md` §4 |
| FSC-16 | An autonomy document conflicts with an authoritative NAWA document in a way that affects what may be executed | Charter §3 |
| FSC-17 | A change to the authentication or tenant-isolation boundary that the activation record does not explicitly include | `CLAUDE.md` — Core Principles; "Never without security review" |
| FSC-18 | Any write to the real pilot tenant's durable data that the activation record does not explicitly include | PV1 Slice 3 repo-safety record (`docs/execution/pilot/PV1_SLICE3_REAL_OPERATIONAL_REASONING_VALIDATION.md` §19) |
| FSC-19 | Independent review integrity is compromised — the reviewer implemented part of the change, a recorded verdict does not match the verdict issued, or no independent reviewer is available for a required gate | `REVIEW_PROTOCOL.md` §5 |

## 4. What is not a stop condition

- a failing test in the change under construction
- a bug found and fixed inside scope
- a `FAIL — IN SCOPE` verdict, including a repeated one, while the continuation
  conditions in `REVIEW_PROTOCOL.md` §8 hold
- a session ending, a usage limit, or a restart — these go through
  `SESSION_RECOVERY_PROTOCOL.md`

## 5. Stop procedure

1. **Stop.** Do not take the triggering action. Do not start a workaround.
2. **Leave a safe state.** No partial commit, no push, no half-applied change
   to shared state. Uncommitted in-scope work stays in the worktree, untouched.
3. **Record.** In `CURRENT_AUTONOMOUS_RUN.md` set
   `Founder Stop Condition Triggered?` to `YES — FSC-nn`, and set
   `Next Exact Action` to `STOP FOR FOUNDER`.
4. **Request a decision.** Give the Founder a short Founder Decision Request:
   - which condition, and the evidence
   - what was being attempted
   - the options, with the consequence of each
   - a recommendation, if the team has one
   - what stays untouched until the Founder decides
5. **Wait.** Unrelated in-scope work may not continue as a way of keeping busy
   if the stop affects the batch's design or scope.

## 6. Resuming

Work resumes only when the Founder's decision is recorded — in
`ACTIVE_BATCH.md` if it changes scope or grants an exception, otherwise in
`CURRENT_AUTONOMOUS_RUN.md`. The decision is quoted or precisely referenced,
with date. Silence is not a decision.
