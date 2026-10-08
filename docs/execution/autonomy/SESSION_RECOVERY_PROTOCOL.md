# Session Recovery Protocol

**Status:** Founder-ratified on 2026-10-08 (`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`). Not ACTIVE until `G3b-G` PASS on the harness governance commit.
**Version:** 1.0
**Category:** Agent Instructions
**Scope:** How any agent session resumes an autonomous run after an interruption, using repository state alone.
**Non-scope:** Recovering lost uncommitted work, and database or environment recovery.
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10.
**Approval authority:** Founder (scope and authority rules).
**Effective date:** On successful remote verification (`G3b-G`) of the harness governance commit. Founder-ratified 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. When this applies

Every time a session starts on a run it did not itself leave seconds ago,
including after:

- a Claude Code session ending
- a Cowork session ending
- a usage limit
- a machine restart
- a VS Code crash
- a repository move
- a network interruption

A new session has no memory. It reads the documents first, then Git. Where
they disagree, Git is the fact and the disagreement is classified in Section 4.

## 2. Rule

**Verify, compare, then act.** No command that changes the repository, the
index, or the remote runs before Section 3 and Section 4 are complete.

## 3. Verify

Read, in order: `NAWA_AUTONOMOUS_DEVELOPMENT_CHARTER.md` → `ACTIVE_BATCH.md` →
`CURRENT_AUTONOMOUS_RUN.md`.

Then read Git directly, in the native repository:

| Check | Command |
|---|---|
| Repository root | `git rev-parse --show-toplevel` |
| Branch | `git rev-parse --abbrev-ref HEAD` |
| HEAD | `git rev-parse HEAD` |
| Parent (when relevant) | `git rev-parse HEAD~1` |
| Worktree | `git status --porcelain=v1 --untracked-files=all` |
| Index | `git diff --cached --name-only` |
| Tracking origin | `git rev-parse --abbrev-ref --symbolic-full-name "@{u}"` and `git rev-parse "@{u}"` |
| Live origin | `git ls-remote origin refs/heads/claude-safe-review` |
| Ahead / behind | `git rev-list --left-right --count "HEAD...@{u}"` |
| In-progress operation | no `MERGE_HEAD`, `REBASE_HEAD`, `CHERRY_PICK_HEAD` in `.git/` |

All of these are read-only.

## 4. Compare and classify

Compare each result with `CURRENT_AUTONOMOUS_RUN.md`.

**If state matches: resume** at `Next Exact Action`.

**If state does not match: STOP and classify the discrepancy.** Resume only if
every discrepancy falls in a benign class.

### 4.1 Benign classes — record, then resume

| Class | Discrepancy | Handling |
|---|---|---|
| B1 | Local HEAD is ahead of the last remotely verified checkpoint, and the run file's `Ahead State` explains it exactly | Apply the ahead-of-checkpoint rule (Section 5); resume at its `Next Required Gate` |
| B2 | Worktree changes exist and equal the recorded `Expected Worktree Delta`, or in-scope work recorded under `Current Work` | Continue from that work; do not discard it |
| B3 | The worktree copy of `CURRENT_AUTONOMOUS_RUN.md` is newer than its committed copy | Expected: run state is updated in the worktree first. The worktree copy is the live record |
| B4 | Tracking origin is stale but live origin equals the expected hash | `git fetch origin`, then re-compare |
| B5 | Live origin equals local HEAD although the run file says the push was pending | The push completed before the interruption. Record it; resume at the remote verification gate for that commit — `G3b-E` for the engineering commit, `G3b-G` for the governance closure commit |
| B6 | Repository path differs; remote URL, branch, and HEAD are identical | Repository moved. Update the `Repository` field and record the move |
| B7 | Line-ending-only differences reported through a non-native mount (for example the Cowork sandbox): `git diff --ignore-cr-at-eol --numstat` shows no content change for those paths | A mount artifact only if the native repository does not report them. Never stage, commit, or normalize them. Confirm with native Git; if native Git reports them too, they are class S4 |

### 4.2 Stop classes — FSC-15, STOP FOR FOUNDER

| Class | Discrepancy |
|---|---|
| S1 | A different branch is checked out |
| S2 | HEAD is not the recorded checkpoint and not a descendant of it |
| S3 | Local HEAD is ahead and `Ahead State` is missing, incomplete, or does not match Git |
| S4 | Staged or unstaged changes outside the expected delta and outside batch scope |
| S5 | Live origin holds commits that local does not (behind > 0), or the histories have diverged |
| S6 | Live origin equals neither the recorded checkpoint nor local HEAD |
| S7 | A merge, rebase, or cherry-pick is in progress |
| S8 | `ACTIVE_BATCH.md` and `CURRENT_AUTONOMOUS_RUN.md` disagree about which batch is active |
| S9 | The run file records a triggered stop condition with no recorded Founder decision |
| S10 | `CURRENT_AUTONOMOUS_RUN.md` is missing, unparseable, or internally contradictory |

A stop here follows `FOUNDER_STOP_CONDITIONS.md` §5. The discrepancy is never
"fixed" by reset, checkout, stash, clean, amend, rebase, or force — those
destroy the evidence the Founder needs, and any of them that changes commit
lineage is itself FSC-09, whether or not the commits were ever pushed.

## 5. Ahead-of-checkpoint rule

Local HEAD may legitimately be ahead of the last remotely verified checkpoint
only inside one of the loop's two commit-to-push windows:

- **Engineering window** — the engineering commit exists locally and `G3a-E`
  has not yet passed, or `G3a-E` has passed and the engineering push is pending
  or was interrupted;
- **Governance window** — the governance closure commit exists locally and
  `G3a-G` has not yet passed, or `G3a-G` has passed and the governance push is
  pending or was interrupted.

The two windows never overlap: the governance closure commit is not created
until `G3b-E` has verified the engineering commit on the remote.

It is legitimate **only if** `CURRENT_AUTONOMOUS_RUN.md` carries an explicit
`Ahead State` block with all five entries:

| Entry | Content |
|---|---|
| `Expected Local Commit` | Full hash of each local commit ahead of the remote checkpoint, in order |
| `Expected Remote Checkpoint` | Full hash of the last remotely verified commit |
| `Why Ahead` | The loop stage that produced the ahead state |
| `Push Authorized` | `YES` or `NO`, and the basis — which gate verdict, or which Founder instruction |
| `Next Required Gate` | The gate id that must run next: `G3a-E`, `G3b-E`, `G3a-G`, or `G3b-G` |

On recovery, and at `G3a-E` and `G3a-G`, all of these must hold:

1. `git rev-parse HEAD` equals `Expected Local Commit`.
2. `Expected Remote Checkpoint` is an ancestor of HEAD
   (`git merge-base --is-ancestor <checkpoint> HEAD`).
3. `git rev-list <checkpoint>..HEAD` lists exactly the expected commits and
   nothing else.
4. Live origin equals `Expected Remote Checkpoint` — or equals
   `Expected Local Commit`, which means the push completed (class B5).

A missing or incomplete block, or any mismatch, is class S3 (FSC-15).
**Unexplained divergence is never normalized**: no agent edits the
`Ahead State` after the fact to fit what Git shows, and no agent pushes,
amends, rebases, or resets to make the divergence disappear. A local commit
whose identity differs from the one recorded is treated as a possible history
rewrite (FSC-09), not as a newer version of the same commit.

**Writing order.** A file cannot contain the hash of the commit that carries
it. So the `Ahead State` is written to the worktree copy of the run file
immediately after the commit it describes and before anything else happens;
that worktree update is expected (class B3) and is committed with the next
governance commit. When the commit being described is the one that carries the
run file itself, `Expected Local Commit` identifies it beforehand by parent
hash, subject, and exact file list instead of by hash.

When local HEAD equals the remote checkpoint, the block reads
`NONE — local HEAD equals the remote checkpoint`.

## 6. Authority to resume

A new Claude Code or Cowork session may resume an already activated batch
**without fresh Founder authorization** if all three are true:

- `ACTIVE_BATCH.md` proves the authorization (complete activation record);
- Git state matches the recorded checkpoint, or differs only by benign classes;
- no Founder Stop Condition has occurred.

If any is false, the session does not resume. With no engineering batch active
(`ACTIVE AUTONOMOUS ENGINEERING BATCH: NONE`) there is nothing to resume: the
session reports the state and waits for the Founder.

Resuming never widens authority. A resumed session has exactly the scope in the
activation record — no more because time has passed, and no more because the
previous session "was about to" do something.

## 7. Scenario notes

| Interruption | Specific risk | Check first |
|---|---|---|
| Claude Code session ended | Uncommitted in-scope work in the worktree | Worktree vs. `Current Work` (B2) |
| Cowork session ended | Run file not updated for the last stage | Git vs. the run file (B1, B3, B5); a stale `Ahead State` is S3, not something to patch |
| Usage limit | Stopped mid-stage, mid-edit | Worktree; re-run the stage's tests before trusting partial work |
| Machine restart | Stale `.git/index.lock`; lost local services | No Git process running, then the lock may be removed by Claude Code and recorded; restart local services before tests |
| VS Code crash | Unsaved editor buffers, half-written files | Re-read every file listed under `Current Work`; re-run tests |
| Repository move | Paths in records are stale | Class B6 |
| Network interruption | Unknown push outcome | Live origin vs. local HEAD (B5, S6) |

Tests recorded as passing before an interruption are re-run if the worktree
changed afterwards or cannot be shown unchanged.

## 8. After resuming

Update `CURRENT_AUTONOMOUS_RUN.md` immediately: what was verified, which benign
classes were found, and the new `Last Updated By`. Recovery that leaves no
record did not happen.
