# Founder Review Package — Template

**Status:** Founder-ratified on 2026-10-08 (`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`). ACTIVE since 2026-10-08 — `G3b-G` PASS on the harness governance commit `4aec1e48a7ee9aac71d2769f11643ebb450b5959`.
**Version:** 1.0
**Category:** Agent Instructions
**Scope:** The structure of the single document the Founder receives when an autonomous batch reaches STOP.
**Non-scope:** The batch's full evidence, which stays in its task document under `docs/execution/`.
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10.
**Approval authority:** Founder (scope and authority rules).
**Effective date:** 2026-10-08.
**Last updated:** 2026-10-08.

---

## How to use this template

- Prepared by Claude Cowork from the batch task document, Git, and the recorded
  reviewer verdicts.
- The Founder should not need to read agent transcripts. Every claim points to
  a file, a commit, or a test result in the repository.
- Written for a decision, not for completeness: lead each section with the
  conclusion.
- Unknowns are written as `UNVERIFIED`, never smoothed over.
- Reviewer verdicts are quoted verbatim. Cowork does not summarise a verdict
  into a stronger one.
- A package is filled in for one batch. It does not propose activating the
  next one; Section 17 only names what is eligible.

Copy everything below this line.

---

# Founder Review Package — `<batch id>` / `<defect id(s)>`

**Batch:** `<batch id>`
**Prepared by:** Claude Cowork
**Date:** `<YYYY-MM-DD>`
**Activation record:** `docs/execution/autonomy/ACTIVE_BATCH.md` as of `<commit>`
**Task document:** `<path>`

## 1. Executive Summary

Three to six lines: what was wrong, what was done, whether it is closed, and
what the Founder must decide.

## 2. Original Defect

The defect as originally recorded, its observed impact, and where it was
recorded.

## 3. Root Cause

The evidenced cause — and how it was proven, not just asserted.

## 4. Architecture Decision

The design chosen, the alternatives rejected, and why. Reference to the `G1`
verdict and to the CTO's `EBD-A` determination.

## 5. Implementation

What changed in behaviour, in plain operational language.

## 6. Files Changed

| Path | Change | Why |
|---|---|---|
| `<path>` | added / modified | `<reason>` |

Exact list, from `git show --stat <engineering commit>`.

## 7. Tests

| Suite | Result | Count |
|---|---|---|
| Focused | | |
| Regression | | |
| Full | | |

New tests added, and what each proves.

## 8. Real Pilot Evidence

What was verified against real pilot data or the real runtime path, how it was
isolated, and what was not verified. If none: `NONE — <reason>`.

## 9. Independent Review Results and EBD-002 Approvals

Gate ids and checkpoint ids are fixed (`REVIEW_PROTOCOL.md` §2.1,
`AUTONOMOUS_LOOP.md` §8). Every row is filled; none is merged with another.

### 9.1 Ledger

| Id | Gate / checkpoint | Issued by | Date | Object | Result |
|---|---|---|---|---|---|
| `G1` | Gate 1 — Architecture Review | Codex | | design reviewed | |
| `EBD-A` | CTO Freeze determination and design approval | Cowork as CTO | | Decision Log entry | |
| `G2` | Gate 2 — Final Implementation / Pre-Commit Review | Codex | | manifest id, revision | |
| `EBD-B` | CTO runtime validation acceptance | Cowork as CTO | | Decision Log entry | |
| `G3a-E` | Gate 3a-E — Engineering Post-Commit / Pre-Push Verification | Codex | | engineering commit hash | |
| `G3b-E` | Gate 3b-E — Engineering Remote Verification | Codex | | engineering commit hash | |
| `EBD-C` | CTO approval of closure documentation | Cowork as CTO | | Decision Log entry | |
| `G3a-G` | Gate 3a-G — Governance Post-Commit / Pre-Push Verification | Codex | | governance commit hash | |
| `G3b-G` | Gate 3b-G — Governance Remote Verification | Codex | | governance commit hash | |

A Codex `PASS` is not an EBD-002 approval, and a CTO approval is not a gate
verdict. They are recorded in separate rows and never substituted.

Correction cycles: number per gate, the findings closed, and any root-cause
reassessment performed after two unsuccessful cycles.

How each gate was invoked: Founder-initiated or automated.

### 9.2 Evidence record — Engineering Gate 3a (`G3a-E`)

- Reviewer, date:
- Engineering commit verified (full hash), parent, author:
- Gate 2 Review Manifest compared (`manifest_id` — SHA-256 of the canonical
  body — revision, `baseline_commit`):
- Canonical body byte-for-byte equal / lineage match:
- Verdict, verbatim:

### 9.3 Evidence record — Engineering Gate 3b (`G3b-E`)

- Reviewer, date:
- Commit hash expected (from `G3a-E`):
- Live origin hash observed, fast-forward, ahead/behind:
- Verdict, verbatim:

### 9.4 Evidence record — Governance Gate 3a (`G3a-G`)

- Reviewer, date:
- Governance closure commit verified (full hash), parent, author:
- Governance Closure Manifest compared (`manifest_id` — SHA-256 of the
  canonical body — revision, `baseline_commit`):
- Canonical body byte-for-byte equal / lineage match / documentation-only:
- Normalized-content identity of `CURRENT_AUTONOMOUS_RUN.md` recomputed and
  equal:
- Derived-metadata region equal to the reconstructed manifest:
- `EBD-C` record present, and written before the manifest:
- Closure claims checked against evidence:
- Verdict, verbatim:

### 9.5 Evidence record — Governance Gate 3b (`G3b-G`)

- Reviewer, date:
- Commit hash expected (from `G3a-G`):
- Live origin hash observed, fast-forward, ahead/behind:
- Verdict, verbatim:

The governance closure commit is verified only by `G3a-G` and `G3b-G`. Records
9.2 and 9.3 say nothing about it.

## 10. Engineering Commit

Full hash, parent, subject, author. Path list as in the Gate 2 Review Manifest.

## 11. Governance Closure Commit

Full hash, parent, subject, author, and the documents it contains, as in the
Governance Closure Manifest.

## 12. Remote State

Two separate statements, each with its verification date:

- **After the engineering push** — branch, local HEAD, tracking origin, live
  origin, ahead/behind, as verified at `G3b-E`.
- **After the governance push** — the same, as verified at `G3b-G`.

## 13. Remaining Risks

What could still go wrong, how likely, and what would reveal it.

## 14. Deliberately Unchanged Scope

What was left untouched on purpose, so that silence is not mistaken for
coverage.

## 15. Deferred Findings

Issues discovered during the batch and not fixed, each with a proposed home
(existing defect, new defect, or none).

## 16. Founder Decisions Required

Numbered. For each: the decision, the options, the consequence of each, and the
team's recommendation.

## 17. Next Eligible Batch

Which batch is next eligible and what must be true before it can be activated.
**Eligibility is not activation.** No next batch has started.
