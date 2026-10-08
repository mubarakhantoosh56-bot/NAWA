# Founder Review Package — `H0` / NAWA Autonomous Development Harness v1 — Bootstrap / Activation Closure

**Batch:** `H0` — Harness setup (H0, H0.1, H0.1-R1, H0.1-R2) and the bootstrap governance closure. A setup batch, not an engineering batch.
**Prepared by:** Claude Cowork
**Date:** 2026-10-08
**Activation record:** `docs/execution/autonomy/ACTIVE_BATCH.md` as of `4aec1e48a7ee9aac71d2769f11643ebb450b5959` (setup authorization on record; no engineering activation)
**Task document:** NONE — H0 has no task document. Its record is the Charter (§15–§19), the Decision Log entries `EBD-007`, `EBD-008`, `EBD-009`, `ADR-001`, and `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md`.

**Status:** Prepared for Founder review. Produced from `FOUNDER_REVIEW_PACKAGE_TEMPLATE.md` (`AUTONOMOUS_LOOP.md` stage 22).
**Version:** 1.0
**Category:** Agent Instructions (autonomous-run operational record)
**Scope:** The Founder's closing review of H0 — the creation, ratification, bootstrap governance closure, and activation of the NAWA Autonomous Development Harness v1.
**Non-scope:** Any engineering batch, any product change, and the next phase (H0.2 or A2), which needs its own Founder decision.
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10.
**Approval authority:** Founder.
**Effective date:** 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. Executive Summary

- The harness is **ACTIVE** since 2026-10-08. Its governance commit
  `4aec1e48a7ee9aac71d2769f11643ebb450b5959` (parent
  `9e2463fda8dad102601296f7e5bec33da5d68757`) passed `G3a-G`, was pushed as a
  normal fast-forward, and passed `G3b-G`.
- H0 changed documentation only: 16 paths, 3172 insertions, no deletions. No
  product code, test, migration, data, knowledge, or secret changed.
- Engineering Batch **NONE**; A2 / DEFECT-002 **NOT ACTIVATED**; Migration
  Authorization **NONE**.
- Founder decisions needed (Section 16): how the post-activation
  reconciliation is committed, and whether the next phase is H0.2 or A2.

## 2. Original Defect

NOT APPLICABLE — H0 addressed no product defect. Its purpose, as recorded in
Charter §1: the repository, not a conversation or the Founder's memory, is the
shared source of truth for autonomous execution, so the Founder no longer
relays prompts and state between agents. The H0 authorization (Founder,
2026-10-03) is recorded in `ACTIVE_BATCH.md`.

## 3. Root Cause

NOT APPLICABLE — no defect.

## 4. Architecture Decision

H0 is a governance design, not a product architecture change. Its main
choices, each in the committed harness:

- EBD-002 is not amended; run roles are mapped onto its seats
  (`ROLE_MATRIX.md` §1).
- Six independent gates with fixed ids — `G1`, `G2`, `G3a-E`, `G3b-E`,
  `G3a-G`, `G3b-G` — plus three CTO checkpoints, `EBD-A`, `EBD-B`, `EBD-C`
  (`REVIEW_PROTOCOL.md` §2, `AUTONOMOUS_LOOP.md` §8).
- Exact content equivalence through canonical manifests (schema 2), with a
  normalized-content identity for the run file (`REVIEW_PROTOCOL.md` §9).
- Every Git history rewrite is Founder-protected; forward correction is the
  default (Charter §9, FSC-09).
- LIMITED autonomy: every gate needs a Founder-initiated Codex invocation
  (Charter §14).
- **Bootstrap exception — one time only** (`EBD-008`;
  `REVIEW_PROTOCOL.md` §9.2): the initial harness closure used baseline
  `9e2463fda8dad102601296f7e5bec33da5d68757` and `batch: NONE`. The exception
  ended when that closure passed `G3b-G`.

`G1` and `EBD-A`: NOT APPLICABLE — no engineering batch. The design was
corrected after independent review in H0.1-R1 and H0.1-R2 (Charter §16–§17).

## 5. Implementation

Behaviour changes for agents, not for the product: every agent reads the
Charter, then `ACTIVE_BATCH.md`, then `CURRENT_AUTONOMOUS_RUN.md` (pointers in
`AGENTS.md` and `CLAUDE.md`); no engineering batch runs without a Founder
activation record; each independent gate waits for a Founder-initiated Codex
invocation; Cowork does not mutate Git, and Claude Code stages, commits, and
pushes only when authorized.

## 6. Files Changed

Governance commit `4aec1e48a7ee9aac71d2769f11643ebb450b5959`
(`git show --stat`):

| Path | Change | Why |
|---|---|---|
| `AGENTS.md` | modified (+9) | Pointer to the harness entry documents |
| `CLAUDE.md` | modified (+12) | Same pointer |
| `CURRENT_STATE.md` | modified (+12) | Harness milestone entry |
| `docs/decisions/ADR-001-harness-v1-bootstrap-closure-ebd-c.md` | added (190) | `EBD-C` CTO approval |
| `docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md` | added (113) | Founder Ratification |
| `docs/decisions/EBD-008-harness-bootstrap-amendment.md` | added (129) | Bootstrap Amendment |
| `docs/decisions/EBD-009-harness-governance-commit-authorization.md` | added (138) | Conditional stage/commit authorization |
| `docs/execution/autonomy/ACTIVE_BATCH.md` | added (178) | Activation record |
| `docs/execution/autonomy/AUTONOMOUS_LOOP.md` | added (312) | Loop |
| `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` | added (316) | Run checkpoint |
| `docs/execution/autonomy/FOUNDER_REVIEW_PACKAGE_TEMPLATE.md` | added (193) | This template |
| `docs/execution/autonomy/FOUNDER_STOP_CONDITIONS.md` | added (101) | Stop conditions |
| `docs/execution/autonomy/NAWA_AUTONOMOUS_DEVELOPMENT_CHARTER.md` | added (336) | Charter |
| `docs/execution/autonomy/REVIEW_PROTOCOL.md` | added (712) | Review protocol |
| `docs/execution/autonomy/ROLE_MATRIX.md` | added (232) | Role matrix |
| `docs/execution/autonomy/SESSION_RECOVERY_PROTOCOL.md` | added (189) | Session recovery |

Total: 16 files, 3172 insertions, 0 deletions. The post-activation
reconciliation that produced this package is in the worktree and is not
committed (Section 16).

## 7. Tests

| Suite | Result | Count |
|---|---|---|
| Focused | NOT RUN — documentation only | 0 |
| Regression | NOT RUN — documentation only | 0 |
| Full | NOT RUN — documentation only | 0 |

No test was added. Recorded in `CURRENT_AUTONOMOUS_RUN.md` (Claude Code): both
`REVIEW_PROTOCOL.md` test vectors (§9.2, §9.5) were reproduced before the
manifest was computed, and the `manifest_id` was recomputed independently and
matched.

## 8. Real Pilot Evidence

NONE — H0 touched no runtime path, pilot tenant, or pilot data.

## 9. Independent Review Results and EBD-002 Approvals

### 9.1 Ledger

| Id | Gate / checkpoint | Issued by | Date | Object | Result |
|---|---|---|---|---|---|
| `G1` | Gate 1 — Architecture Review | Codex | — | — | NOT APPLICABLE — no engineering batch |
| `EBD-A` | CTO Freeze determination and design approval | Cowork as CTO | — | — | NOT APPLICABLE — no engineering implementation |
| `G2` | Gate 2 — Final Implementation / Pre-Commit Review | Codex | — | — | NOT APPLICABLE — no engineering batch |
| `EBD-B` | CTO runtime validation acceptance | Cowork as CTO | — | — | NOT APPLICABLE — no runtime validation |
| `G3a-E` | Gate 3a-E — Engineering Post-Commit / Pre-Push Verification | Codex | — | — | NOT APPLICABLE — no engineering commit |
| `G3b-E` | Gate 3b-E — Engineering Remote Verification | Codex | — | — | NOT APPLICABLE — no engineering commit |
| `EBD-C` | CTO approval of closure documentation | Cowork as CTO | 2026-10-08 | `docs/decisions/ADR-001-harness-v1-bootstrap-closure-ebd-c.md` | APPROVED |
| `G3a-G` | Gate 3a-G — Governance Post-Commit / Pre-Push Verification | Codex | 2026-10-08 | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` | PASS (re-run; first invocation FAIL) |
| `G3b-G` | Gate 3b-G — Governance Remote Verification | Codex | 2026-10-08 | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` | PASS |

A Codex `PASS` is not an EBD-002 approval, and a CTO approval is not a gate
verdict. They are recorded in separate rows and never substituted.

**Harness reviews before ratification** (not loop gates; Codex; as given by
the Founder): H0.1 — FAIL (four MAJOR, one MINOR); H0.1-R1 re-review — FAIL
(two MAJOR, one MINOR); H0.1-R2 focused re-review — FAIL (one MINOR
stale-state finding); final confirmation — FAIL (stale state references
only); final verdict — `PASS — H0.1-R2 HARNESS SAFE FOR FOUNDER RATIFICATION`.
Then: Bootstrap Amendment review — substantive checks PASSED, one MINOR state
inconsistency; `PASS — BOOTSTRAP CHECKPOINT STATE SAFE — PROCEED TO EBD-C`;
`PASS — PRE-EBD-C CLOSURE STATE VERIFIED — CTO MAY PERFORM EBD-C`.

**Founder decisions:** Ratification 2026-10-08 (`EBD-007`); Bootstrap
Amendment 2026-10-08 (`EBD-008`); conditional stage/commit authorization
2026-10-08 (`EBD-009`, no push).

Correction cycles: `G3a-G` — one; the first invocation failed only because the
class B3 post-commit `Ahead State` update had not yet been written to the
worktree run file (as reported by the Founder); the re-run passed. No gate
reached the two-cycle reassessment threshold. A first `EBD-C` review was
withheld by the CTO on 2026-10-08 and repeated after correction under
`EBD-009`.

How each gate was invoked: Founder-initiated (LIMITED autonomy, Charter §14).

### 9.2 Evidence record — Engineering Gate 3a (`G3a-E`)

NOT APPLICABLE — no engineering commit exists in the bootstrap closure
(`EBD-008`).

### 9.3 Evidence record — Engineering Gate 3b (`G3b-E`)

NOT APPLICABLE — no engineering commit exists in the bootstrap closure.

### 9.4 Evidence record — Governance Gate 3a (`G3a-G`)

- Reviewer, date: Codex, 2026-10-08.
- Governance closure commit verified (full hash), parent, author:
  `4aec1e48a7ee9aac71d2769f11643ebb450b5959`, parent
  `9e2463fda8dad102601296f7e5bec33da5d68757`, Mubarak Hantoosh,
  2026-10-08 03:09:19 +0300.
- Governance Closure Manifest compared (`manifest_id` — SHA-256 of the
  canonical body — revision, `baseline_commit`):
  `8d771114223044399ae7141c7f99a53d8aa625fa61bcbd435ea594a9bf310a5d`,
  revision 1, `baseline_commit` `9e2463fda8dad102601296f7e5bec33da5d68757`,
  kind `GOVERNANCE-CLOSURE`, batch `NONE`, 16 entries.
- Canonical body byte-for-byte equal / lineage match / documentation-only:
  covered by the `PASS` as reported by the Founder; the item-level results
  are UNVERIFIED in this repository. Repository facts: one commit in
  `9e2463f..4aec1e4`; every path in it is documentation.
- Normalized-content identity of `CURRENT_AUTONOMOUS_RUN.md` recomputed and
  equal: manifest value
  `nsha256:aec4a2cdaffeacc581c669f76f4e306086eae340f9f3b2c9884f8a5eaac52caf`;
  recomputation at the gate UNVERIFIED in this repository.
- Derived-metadata region equal to the reconstructed manifest: UNVERIFIED in
  this repository (covered by the reported `PASS`).
- `EBD-C` record present, and written before the manifest: present in the
  commit (`ADR-001`); the run file records `EBD-C` approved before manifest
  finalization.
- Closure claims checked against evidence: covered by the reported `PASS`.
- Verdict, verbatim: UNVERIFIED — the verdict text is not held in this
  repository. Result as given by the Founder: `PASS`.

### 9.5 Evidence record — Governance Gate 3b (`G3b-G`)

- Reviewer, date: Codex, 2026-10-08.
- Commit hash expected (from `G3a-G`):
  `4aec1e48a7ee9aac71d2769f11643ebb450b5959`.
- Live origin hash observed, fast-forward, ahead/behind:
  `4aec1e48a7ee9aac71d2769f11643ebb450b5959`; fast-forward — the
  remote-tracking ref moved from `9e2463fda8dad102601296f7e5bec33da5d68757`,
  the commit's parent, by push at 2026-10-08 18:51:58 +0300; ahead/behind
  `0 0`. Live origin also read with `git ls-remote` by Claude Cowork on
  2026-10-08.
- Verdict, verbatim (as given by the Founder):

```text
PASS — G3b-G REMOTE VERIFIED — NAWA AUTONOMOUS DEVELOPMENT HARNESS v1 ACTIVATION CONDITION SATISFIED
```

The governance closure commit is verified only by `G3a-G` and `G3b-G`. Records
9.2 and 9.3 say nothing about it.

## 10. Engineering Commit

NONE — the bootstrap closure has no engineering commit (`EBD-008`).

## 11. Governance Closure Commit

- Hash: `4aec1e48a7ee9aac71d2769f11643ebb450b5959`
- Parent: `9e2463fda8dad102601296f7e5bec33da5d68757`
- Subject: `Docs: add NAWA Autonomous Development Harness v1 (Founder-ratified, bootstrap closure)`
- Author: Mubarak Hantoosh, 2026-10-08 03:09:19 +0300 (created by Claude Code
  under `EBD-009`, per the run file)
- Contents: the 16 entries of the Governance Closure Manifest, listed in
  Section 6.

## 12. Remote State

- **After the engineering push** — NOT APPLICABLE; no engineering push.
- **After the governance push** — branch `claude-safe-review`; local HEAD,
  tracking origin, and live origin all
  `4aec1e48a7ee9aac71d2769f11643ebb450b5959`; ahead/behind `0 0`; as verified
  at `G3b-G` on 2026-10-08, and re-read by Claude Cowork on 2026-10-08.

**Live-state handling (B3/B5).** The committed run file could not record its
own commit. Immediately after the commit, the worktree copy received the
`Ahead State` with the commit hash (class B3). After the push, live origin
equalled local HEAD (class B5), and the worktree copy recorded the push,
both gate results, and activation. That worktree copy is newer than its
committed copy and is committed with the next governance commit.

## 13. Remaining Risks

- **LIMITED autonomy.** Codex automation is not proven; every gate needs a
  Founder-initiated invocation.
- **Verdict text outside the repository.** The `G3a-G` verdict and several
  earlier Codex verdicts are held only as relayed by the Founder.
- **Push authorization outside the repository.** The Founder's push
  authorization is not recorded in a repository file. The push itself is
  evidenced by Git.
- **Governance-only commits after activation — resolved.** The bootstrap
  rule (`batch: NONE`) ended with the bootstrap closure, which left
  governance-only closures without a defined manifest form. Founder decision
  `EBD-010` (2026-10-08) resolved it with the permanent `batch:
  GOVERNANCE-ONLY` rule (`REVIEW_PROTOCOL.md` §9.2, version 1.2).

## 14. Deliberately Unchanged Scope

Product code, tests, migrations, schema, data, Company Brain knowledge,
secrets; `docs/governance/` (EBD-002 included); `docs/execution/EXECUTION_INDEX.md`
and `EXECUTION_BOARD.md`; the historical wording of `EBD-007`, `EBD-008`,
`EBD-009`, and `ADR-001`; the A2 requirement for an Architecture Gate before
activation.

## 15. Deferred Findings

1. Decision Log entries for EBDs before `EBD-007` were never created (record
   note in `EBD-007`); pre-existing, not addressed by H0.
2. The Documentation Standard §9.1 folder structure does not list
   `docs/execution/` (note in `CURRENT_AUTONOMOUS_RUN.md`).
3. The `Effective date` header of the harness documents was set to
   2026-10-08 on Founder instruction.
4. The governance-only closure gap in Section 13 (last bullet) — resolved by
   `EBD-010`.

## 16. Founder Decisions Required

1. **How to commit the post-activation reconciliation — decided.** Founder
   decision `EBD-010` (2026-10-08): a permanent `GOVERNANCE-ONLY` closure.
   Still required: focused independent review, `EBD-C`, the manifest, a
   separate Founder stage/commit authorization, `G3a-G`, a separate Founder
   push authorization, and `G3b-G`.
2. **Next phase.** H0.2 Codex Bridge / autonomy integration, or A2
   activation under the active harness. Neither starts without the Founder.

## 17. Next Eligible Batch

A2 / DEFECT-002. Before activation it needs a complete Founder activation
record in `ACTIVE_BATCH.md` and its Architecture Gate (race-safe exact-content
deduplication is architecture-unproven). **Eligibility is not activation.** No
next batch has started.
