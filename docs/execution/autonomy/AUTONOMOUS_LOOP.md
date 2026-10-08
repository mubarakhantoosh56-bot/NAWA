# Autonomous Loop

**Status:** Founder-ratified on 2026-10-08 (`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`). ACTIVE since 2026-10-08 — `G3b-G` PASS on the harness governance commit `4aec1e48a7ee9aac71d2769f11643ebb450b5959`.
**Version:** 1.0
**Category:** Agent Instructions
**Scope:** The fixed sequence an activated engineering batch follows from Founder activation to STOP.
**Non-scope:** How to engineer the change itself — `CLAUDE.md`, `ARCHITECTURE_RULES.md`, `CODING_STANDARDS.md` and `AI_AGENT_WORKFLOW.md` govern that.
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10.
**Approval authority:** Founder (scope and authority rules).
**Effective date:** 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. The loop

```text
Founder Activation
        ↓
Baseline Verification
        ↓
Evidence / Reproduction
        ↓
Architecture Investigation
        ↓
Gate 1 — Architecture Review                                    [G1]     Codex
        ↓
EBD-002 checkpoint — CTO Freeze determination and design approval  [EBD-A]  CTO
        ↓
Implementation
        ↓
Testing / validation
        ↓
Gate 2 — Final Implementation / Pre-Commit Review               [G2]     Codex
        ↓
EBD-002 checkpoint — CTO runtime validation acceptance           [EBD-B]  CTO
        ↓
Engineering Commit
        ↓
Gate 3a-E — Engineering Post-Commit / Pre-Push Verification      [G3a-E]  Codex
        ↓
Engineering Push
        ↓
Gate 3b-E — Engineering Remote Verification                      [G3b-E]  Codex
        ↓
Governance Closure Documentation
        ↓
EBD-002 checkpoint — CTO approval of closure documentation       [EBD-C]  CTO
        ↓
Governance Closure Manifest finalization                         Claude Code
        ↓
Governance Closure Commit
        ↓
Gate 3a-G — Governance Post-Commit / Pre-Push Verification       [G3a-G]  Codex
        ↓
Governance Push
        ↓
Gate 3b-G — Governance Remote Verification                       [G3b-G]  Codex
        ↓
Founder Review Package
        ↓
STOP
```

The loop runs only when `ACTIVE_BATCH.md` holds a complete activation record.
It never starts itself and never restarts itself.

Engineering closure (stages 11–14) and governance closure (stages 15–21) are
two distinct sequences. Each has its own commit, its own post-commit
verification, its own push, and its own remote verification.

## 2. Stages

Stage ids in square brackets are fixed and are the values used in
`CURRENT_AUTONOMOUS_RUN.md`.

| # | Stage | Owner | Exit condition |
|---|---|---|---|
| 1 | Founder Activation | Founder | Complete activation record in `ACTIVE_BATCH.md` |
| 2 | Baseline Verification | Claude Code | Repository root, branch, HEAD, parent, worktree, index, tracking origin, live origin and ahead/behind match the activation record |
| 3 | Evidence / Reproduction | Claude Code | The defect is reproduced, or its non-reproduction is evidenced, in the batch task document |
| 4 | Architecture Investigation | Claude Code, coordinated by Cowork | Root cause and proposed design are written down, with files to change and files deliberately untouched |
| 5 | `[G1]` Gate 1 — Architecture Review | Codex | Independent verdict `PASS` recorded |
| 6 | `[EBD-A]` CTO Freeze determination and design approval | Cowork as CTO | Written, dated CTO determination — and approval where EBD-002 requires one — on record (Section 8.2) |
| 7 | Implementation | Claude Code | Change implemented inside the approved design and scope |
| 8 | Testing / validation | Claude Code | Focused tests pass; regression suite passes; full suite when the batch touches shared paths; runtime validation evidence recorded where the batch requires it |
| 9 | `[G2]` Gate 2 — Final Implementation / Pre-Commit Review | Codex | Independent verdict `PASS` recorded, containing the Gate 2 Review Manifest |
| 10 | `[EBD-B]` CTO runtime validation acceptance | Cowork as CTO | Written, dated CTO acceptance on record, or a written `NOT APPLICABLE` with reason (Section 8.3) |
| 11 | Engineering Commit | Claude Code | A commit containing exactly the manifest's engineering paths; `Ahead State` written to `CURRENT_AUTONOMOUS_RUN.md` immediately afterwards |
| 12 | `[G3a-E]` Gate 3a-E — Engineering Post-Commit / Pre-Push Verification | Codex | Independent verdict `PASS`: committed content equals the Gate 2 Review Manifest exactly; lineage and `Ahead State` verified |
| 13 | Engineering Push | Claude Code | Normal push to `origin/claude-safe-review` accepted as fast-forward |
| 14 | `[G3b-E]` Gate 3b-E — Engineering Remote Verification | Codex | Independent verdict `PASS`: live origin equals the commit verified at `G3a-E` |
| 15 | Governance Closure Documentation | Cowork | Closure documents at their substantive final state: batch task document, `CURRENT_STATE.md`, execution trackers, run state — including the prospective `Ahead State` for the governance commit (`SESSION_RECOVERY_PROTOCOL.md` §5). Derived-metadata region Idle. No manifest is computed at this stage |
| 16 | `[EBD-C]` CTO approval of closure documentation | Cowork as CTO | Written, dated CTO approval of that substantive state on record, written before any final manifest computation (Section 8.4) |
| 17 | Governance Closure Manifest finalization | Claude Code, natively | Final manifest computed after a valid `EBD-C`; canonical `manifest_id` computed; derived metadata inserted; normalized identity confirmed (`REVIEW_PROTOCOL.md` §9.6 steps 5–8). No substantive content changed since `EBD-C` |
| 18 | Governance Closure Commit | Claude Code | A commit containing exactly the manifest's documentation paths |
| 19 | `[G3a-G]` Gate 3a-G — Governance Post-Commit / Pre-Push Verification | Codex | Independent verdict `PASS`: the canonical manifest reconstructed from the commit equals the finalized Governance Closure Manifest byte for byte, including the normalized identity of the run file and the derived metadata; closure claims match evidence |
| 20 | Governance Push | Claude Code | Normal push accepted as fast-forward |
| 21 | `[G3b-G]` Gate 3b-G — Governance Remote Verification | Codex | Independent verdict `PASS`: live origin equals the commit verified at `G3a-G` |
| 22 | Founder Review Package | Cowork | Package produced from `FOUNDER_REVIEW_PACKAGE_TEMPLATE.md`, with separate evidence records for `G3a-E`, `G3b-E`, `G3a-G`, and `G3b-G` |
| 23 | STOP | all | `ACTIVE_BATCH.md` returns to `NONE`; the team waits |

No stage begins until the exit condition of the stage before it is on record.
`CURRENT_AUTONOMOUS_RUN.md` is updated at every stage transition. Staging,
committing, and pushing are done natively by Claude Code; Cowork orchestrates
and does not mutate Git.

## 3. Routing a FAIL from Codex

```text
Codex verdict = FAIL
        │
        ├─ failure is within the active batch scope
        │        → bounded correction, automatically
        │        → re-run the affected tests
        │        → return to the gate named in REVIEW_PROTOCOL.md §3.1
        │
        └─ failure triggers a Founder Stop Condition
                 → STOP FOR FOUNDER
```

"Within scope" means the finding can be closed without any change to scope,
schema, migrations, architecture contract, or anything else listed in
`FOUNDER_STOP_CONDITIONS.md`.

A failed `G3a-E` returns to `G2`, not to `G3a-E`: the content must be reviewed
again before it can be verified again. A failed `G3a-G` is never pushed; it
follows the correction restart in `REVIEW_PROTOCOL.md` §9.6 step 11 — `EBD-C`
invalidated, forward correction, a new `EBD-C`, manifest finalization, and
`G3a-G` again on the corrected tip.

**Corrections after a commit are forward commits.** A reviewed commit is never
amended, rebased, reset, or recreated to make a gate pass. Any such rewrite
needs explicit Founder authorization (Charter §9, FSC-09).

Two unsuccessful correction cycles at the same gate are a **reassessment
threshold, not an automatic stop**. Cowork performs a root-cause reassessment,
and the loop continues without the Founder while the issue stays inside the
batch, architecture stays closed, no scope expansion or stop condition is
involved, and measurable progress is being made. It escalates to the Founder
when repeated failure reveals unresolved architecture uncertainty, material
scope expansion, contradictory reviewer requirements, no credible bounded
correction path, or another stop condition. Full rule: `REVIEW_PROTOCOL.md` §8.

## 4. What needs no Founder involvement

Routine debug → test → correct → rerun cycles, by Claude Code, inside scope.
These also do not consume Codex capacity (`REVIEW_PROTOCOL.md` §4).

## 5. What the loop never does

- start without an activation record
- skip or reorder a gate or an EBD-002 checkpoint
- treat an internal check as a gate `PASS`
- treat a Codex `PASS` as an EBD-002 approval, or a CTO approval as a gate
  verdict
- treat the governance closure commit as verified because the engineering
  commit was verified
- continue past a Founder Stop Condition
- continue into the next batch after STOP
- push anything other than a normal fast-forward to `claude-safe-review`
- amend, rebase, reset, or otherwise replace a commit without explicit Founder
  authorization

## 6. Mid-loop session loss

A session that ends mid-loop resumes through
`SESSION_RECOVERY_PROTOCOL.md`. The loop position is whatever
`CURRENT_AUTONOMOUS_RUN.md` records, confirmed against Git — not whatever the
new session assumes.

## 7. Gate handoff — current mechanism

Codex automation is classified
`CODEX_INTERFACE_PRESENT_BUT_AUTOMATION_NOT_PROVEN`
(`REVIEW_PROTOCOL.md` §6). The loop therefore runs as **LIMITED AUTONOMY**:

```text
Claude Code / Cowork reach a gate
        ↓
CURRENT_AUTONOMOUS_RUN.md: "Next Exact Action" names the gate by id
        ↓
Run waits
        ↓
Founder starts Codex with the fixed gate request      (manual step)
        ↓
Codex reads the repository and returns one verdict
        ↓
Verdict recorded verbatim → loop continues or stops
```

Between gates the loop needs no Founder involvement. At each of the six gate
points (`G1`, `G2`, `G3a-E`, `G3b-E`, `G3a-G`, `G3b-G`) it needs one
Founder-initiated Codex invocation. This section is replaced only when an
automated handoff has been authorized and proven.

The three EBD-002 checkpoints need Cowork, as CTO, in session. Claude Code
cannot issue a CTO approval; when Cowork is not in session the run waits at the
checkpoint with `Next Exact Action` naming it.

## 8. EBD-002 approval checkpoints

### 8.1 Rule

An independent Codex `PASS` does not replace an EBD-002 approval. Where
`docs/governance/EBD-002_GOVERNANCE_MODEL.md` makes the CTO the approver, the
loop does not proceed until that approval is on record. These checkpoints add
no authority: each one is an existing EBD-002 requirement placed at the point
in the loop where it applies.

Every approval follows EBD-002 §5.2 and §10: it is **written, dated, and
signed with the approver's name**, in the Decision Log entry for the change
(`docs/decisions/`; `ADR` prefix for CTO decisions, `EDR` for implementation
decisions), and referenced by checkpoint id in the batch task document and in
`CURRENT_AUTONOMOUS_RUN.md`. EBD-002 §5.3
applies: a mandatory reviewer's written review must exist before the approval.

The CTO is Claude Cowork (EBD-002 §4.3). Checkpoint outcomes are:

| Outcome | Meaning | Routing |
|---|---|---|
| `APPROVED` | The CTO approval EBD-002 requires is on record | Proceed |
| `NOT REQUIRED` | EBD-002 assigns this decision to another approver, or the checkpoint does not apply; the CTO records why | Proceed |
| `CHANGES REQUESTED` | Specific, actionable changes (EBD-002 §7.3) | Return to the preceding work stage; a changed design re-enters `G1` |
| `FOUNDER REQUIRED` | EBD-002 names the Founder as approver or mandatory reviewer | STOP FOR FOUNDER |

A disagreement between the CTO and the Engineering Team that is not resolved in
writing follows the EBD-002 §6.1 escalation ladder, which ends with the
Founder.

### 8.2 `EBD-A` — CTO Freeze determination and design approval

- **Position:** after `G1` `PASS`, before Implementation.
- **EBD-002 source:** §12.2 — every proposed change is reviewed by the CTO
  against the Freeze, and the determination is written in the Decision Log
  entry; §5.1 and Appendix A rows 11–14.
- **Mandatory review already on record:** the `G1` verdict is the Engineering
  Team's written review. Where the change is user-facing, EBD-002 also requires
  Aboura's written review (Appendix A row 11); without it the checkpoint cannot
  complete.

| CTO determination | EBD-002 rule | Checkpoint outcome |
|---|---|---|
| Within freeze — architectural change, engine contract, or contract-level technical decision | CTO approves (rows 11–13) | `APPROVED` or `CHANGES REQUESTED` |
| Within freeze — implementation decision only (code-close) | Approver is the engineer closest to the change, with peer review; the CTO never substitutes (row 14) | `NOT REQUIRED` — the determination is still recorded |
| Freeze-adjacent | CTO drafts an ADR; Founder reviews at Sprint boundary (§12.2) | `FOUNDER REQUIRED` — inside an autonomous run, implementation waits for that Founder review |
| Freeze-breaking | Unfreeze process; Founder ratifies (§12.4) | `FOUNDER REQUIRED` (FSC-11) |

### 8.3 `EBD-B` — CTO runtime validation acceptance

- **Position:** after `G2` `PASS`, before the Engineering Commit.
- **EBD-002 source:** §5.1 and Appendix A row 17 — runtime validation
  acceptance: approver CTO; mandatory reviewers Engineering Team, and the
  Founder for milestones.
- **Applies when:** the batch produces a runtime validation result — evidence
  from the running system, such as real-pilot or live-path validation.
  Automated test results are implementation evidence and are reviewed at `G2`.
- **Mandatory review already on record:** the `G2` verdict covers the
  validation evidence.
- **Outcomes:** `APPROVED`; `CHANGES REQUESTED` (returns to Testing /
  validation); `NOT REQUIRED` when the batch produces no runtime validation
  result; `FOUNDER REQUIRED` when the result is a milestone under EBD-002.

### 8.4 `EBD-C` — CTO approval of closure documentation

- **Position:** after Governance Closure Documentation, **before** Governance
  Closure Manifest finalization and before the Governance Closure Commit.
- **EBD-002 source:** §4.3 — the CTO approves Current State updates (with
  Founder review at Sprint boundary) and Runtime Documents.
- **Covers:** the substantive final state of the closure documents — the
  `CURRENT_STATE.md` update and the closure record.
- **Does not cover:** a new or changed Architecture Document or contract-level
  Technical Document. That is a design decision; it belongs at `EBD-A`, before
  implementation, not in closure.
- **Outcomes:** `APPROVED`; `CHANGES REQUESTED` (returns to Governance Closure
  Documentation).

**Ordering — one sequence, defined in `REVIEW_PROTOCOL.md` §9.6:**

1. The closure documents are drafted to their substantive final state.
2. The CTO approves that state. The `EBD-C` approval record is written before
   the final Governance Closure Manifest is computed, and is part of the
   closure content the manifest binds.
3. After `EBD-C`, no substantive governance content may change. Only the
   mechanically derived manifest metadata may be inserted afterwards, and only
   into the derived-metadata region of `CURRENT_AUTONOMOUS_RUN.md`.
4. If `EBD-C` causes, requests, or requires any substantive change — or one
   happens afterwards for any reason — the approval is invalid: the draft is
   updated and `EBD-C` is repeated.
5. Only with a valid `EBD-C` is the final manifest computed, then the commit
   made, then `G3a-G` run.

The manifest is never computed before `EBD-C`, and `EBD-C` never cites a
`manifest_id`: the approval comes first and the manifest binds it.

The Founder's Sprint-boundary review of `CURRENT_STATE.md` under EBD-002 is
unchanged and is not replaced by this checkpoint.

## 9. What each commit contains

| Commit | Contains | Never contains |
|---|---|---|
| Engineering Commit | The engineering paths in the Gate 2 Review Manifest — product code and tests | The batch task document, run state, trackers, Decision Log entries |
| Governance Closure Commit | The documentation paths in the finalized Governance Closure Manifest — batch task document, Decision Log entries (including the `EBD-C` record), `CURRENT_STATE.md`, execution trackers, run state with its Finalized derived-metadata region | Product code, tests, migrations, data, knowledge |

Batch documentation written before the engineering commit stays uncommitted in
the worktree until the governance closure commit. That delta is recorded in
`CURRENT_AUTONOMOUS_RUN.md` under `Expected Worktree Delta`.

The engineering push does not close the batch. Nothing is reported as closed,
shipped, or verified as a whole until `G3b-G` has passed.
