# NAWA Autonomous Development Charter

**Status:** Founder-ratified as amended on 2026-10-08 (`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`; Bootstrap Amendment `docs/decisions/EBD-008-harness-bootstrap-amendment.md`). Not ACTIVE until `G3b-G` PASS on the harness governance commit.
**Version:** 1.0
**Category:** Agent Instructions
**Scope:** How AI agents execute an activated, bounded engineering batch on NAWA without the Founder relaying prompts or state between them.
**Non-scope:** Product architecture, product direction, engineering standards, and current project status — all of which stay in their existing authoritative documents.
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10.
**Approval authority:** Founder (scope and authority rules).
**Effective date:** On successful remote verification (`G3b-G`) of the harness governance commit. Founder-ratified 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. Purpose

The repository is the shared source of truth for autonomous execution. Any agent
— ChatGPT, Claude Cowork, Claude Code, Codex — must be able to learn what is
authorized, what state the work is in, and what happens next by reading the
repository, not a conversation transcript and not the Founder's memory.

## 2. Core principle

**The Founder approves direction and boundaries. The autonomous team owns
execution inside an activated, bounded batch.**

A batch is the unit of authorization. Nothing engineering-related runs outside
one.

## 3. What this Charter does not override

The autonomy documents govern execution *process* only. They create no
architecture truth and no project-status truth.

| Domain | Authoritative source (unchanged) |
|---|---|
| Reasoning philosophy | `docs/governance/NAWA_REASONING_CONSTITUTION_v1.md` |
| Architecture, contracts, freezes | `docs/architecture/`, `docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md` |
| Governance model, documentation rules | `docs/governance/EBD-002_GOVERNANCE_MODEL.md`, `docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md` |
| Current execution state | `CURRENT_STATE.md` (repository root) |
| Execution tracking and batch evidence | `docs/execution/` |
| Agent engineering rules | `AGENTS.md`, `CLAUDE.md`, `ARCHITECTURE_RULES.md`, `CODING_STANDARDS.md`, `AI_AGENT_WORKFLOW.md` |
| Autonomous-run process and authority boundaries | `docs/execution/autonomy/` (this directory) |

If an autonomy document disagrees with any source above, the source above wins.
The disagreement is recorded in `CURRENT_AUTONOMOUS_RUN.md` and, if it affects
what may be executed, it is a Founder Stop Condition (FSC-16).

`CURRENT_AUTONOMOUS_RUN.md` and `ACTIVE_BATCH.md` are operational records. They
are derived from, and subordinate to, `CURRENT_STATE.md`.

**EBD-002 is unchanged.** The harness does not amend
`docs/governance/EBD-002_GOVERNANCE_MODEL.md`. Every approval EBD-002 requires
is still required. Independent gates are an additional control inside an
autonomous run: an independent Codex `PASS` never replaces an EBD-002 approval,
and an EBD-002 approval never counts as a gate verdict. The approvals EBD-002
assigns to the CTO are explicit exit conditions in the loop
(`AUTONOMOUS_LOOP.md` §8). The mapping of seats to run roles is in
`ROLE_MATRIX.md` §1.

## 4. What makes a batch "activated"

A batch is activated only when `ACTIVE_BATCH.md` carries a complete activation
record written from an explicit Founder instruction:

1. Batch ID and the defect(s) or deliverable it covers.
2. Scope — what is in, and what is deliberately out.
3. Acceptance criteria.
4. Baseline HEAD at activation.
5. The Founder's authorization, quoted or precisely referenced, with date.
6. Any exception explicitly granted for this batch (for example a migration).
   An exception not written here does not exist.

Queue position, eligibility, or "next eligible batch" status is **not**
activation.

## 5. Autonomous authority inside an activated batch

Inside an activated batch, and only inside its recorded scope, the team may
proceed without per-step Founder approval on:

- investigation
- architecture work
- review iteration
- implementation
- testing
- debugging
- bounded correction
- commit
- normal fast-forward push to `claude-safe-review`
- remote verification
- closure documentation

Founder approval is **not** required for each routine command.

## 6. Mandatory Founder approval

Regardless of batch state, these always require explicit Founder approval:

- new batch / Slice / Milestone activation
- migrations
- schema changes
- destructive DB operations
- historical evidence deletion or rewrite
- merge to `main`
- production deployment
- force push, including force-with-lease
- any Git history rewrite or lineage replacement — local, unpublished, pushed,
  or shared
- secrets / credentials changes
- major architecture-contract changes
- material scope expansion
- increased autonomous production authority
- unresolved material disagreement between implementation and reviewer

The operational definitions, identifiers and stop procedure are in
`FOUNDER_STOP_CONDITIONS.md`.

## 7. No self-review

Claude Code and Claude Cowork may validate their own work internally. They may
**not** classify an independent gate as PASS. Only the designated independent
reviewer (Codex — see `ROLE_MATRIX.md`, `REVIEW_PROTOCOL.md`) issues an
independent verdict. An internal check is always labelled "internal validation",
never "PASS". A CTO approval under EBD-002 is an approval, not a gate verdict.

## 8. No silent autonomy expansion

Authority never extends by inference.

- "Finish A2" authorizes A2. It does not authorize A3.
- Closing a batch does not activate the next one.
- A finding discovered during a batch is recorded as a deferred finding, not
  absorbed into scope.
- When the loop completes, the team **stops** and waits for the Founder.

Every new engineering batch requires separate Founder activation.

## 9. Git boundaries

- Work happens on `claude-safe-review` only.
- Pushes are normal fast-forward pushes to `origin/claude-safe-review` only.
- Never push to `main`, never force push, never push to any remote other than
  `origin`.
- **History is append-only.** Any Git history rewrite or lineage replacement
  requires explicit Founder authorization, whether the commits are local,
  unpublished, pushed, or shared. That includes at minimum:
  `git commit --amend`; `git rebase`; `git reset` when it changes what commit a
  branch points to; force push and force-with-lease; history filtering or
  rewriting; and replacing or recreating an already reviewed commit under a new
  identity.
- **Forward correction is the default.** If a reviewed commit needs correcting,
  the correction is a new commit on top, sent through the appropriate review
  gates. A reviewed commit is never silently amended, rebased, or reset.
- Every commit contains only the paths the batch scope requires.
- **Claude Code** performs native `stage`, `commit`, and `push`, and only when
  the active Charter and batch authorize them.
- **Claude Cowork** treats Git mutation as read-only by default. It inspects
  Git state and coordinates the workflow; it is not the normal Git mutation
  executor.
- Local HEAD may be ahead of the last remotely verified checkpoint only when
  `CURRENT_AUTONOMOUS_RUN.md` explains it explicitly
  (`SESSION_RECOVERY_PROTOCOL.md` §5). Unexplained divergence is never
  normalized.

## 10. Relationship to `CLAUDE.md` "When to Ask the User"

`CLAUDE.md` tells agents to ask before unclear, architectural, breaking, risky,
or out-of-scope changes. Inside an activated batch that rule resolves as:

- The question is answered by the batch's recorded scope and acceptance
  criteria, and triggers no stop condition → decide, record the decision and
  reasoning in the batch's task document, continue.
- Otherwise → Founder Stop.

All engineering and safety rules in `CLAUDE.md` and `AGENTS.md` stay in force
in full. This Charter changes who is asked and when — never what is safe.

## 11. Resource policy

- **Claude Code** is the primary high-volume engineering executor.
- **Claude Cowork** orchestrates from recorded state and avoids re-reading or
  re-analysing the whole repository.
- **Codex** is conserved for the designated independent gates.
- **ChatGPT Work** is used only when its specialised capabilities materially
  improve the task.
- The same analysis is not duplicated across agents without a stated reason.

## 12. Document set

| Document | Answers |
|---|---|
| `NAWA_AUTONOMOUS_DEVELOPMENT_CHARTER.md` | What authority exists, and where it ends |
| `ROLE_MATRIX.md` | Who does what, and who may not |
| `ACTIVE_BATCH.md` | What is authorized right now |
| `CURRENT_AUTONOMOUS_RUN.md` | Where the run stands, and the next exact action |
| `AUTONOMOUS_LOOP.md` | The sequence an activated batch follows |
| `REVIEW_PROTOCOL.md` | When and how independent review happens |
| `FOUNDER_STOP_CONDITIONS.md` | When the team must stop for the Founder |
| `SESSION_RECOVERY_PROTOCOL.md` | How a new session resumes safely |
| `FOUNDER_REVIEW_PACKAGE_TEMPLATE.md` | What the Founder receives at the end |

Entry order for any agent: this Charter → `ACTIVE_BATCH.md` →
`CURRENT_AUTONOMOUS_RUN.md`.

## 13. Amendment

Only the Founder amends this Charter. Amendments are versioned in the header.
Any amendment that widens autonomous authority is itself a mandatory Founder
approval (Section 6, "increased autonomous production authority").

## 14. Autonomy level: LIMITED

Codex automation is classified
**`CODEX_INTERFACE_PRESENT_BUT_AUTOMATION_NOT_PROVEN`** (H0.1, 2026-10-05;
evidence in `REVIEW_PROTOCOL.md` §6).

Until a controller or adapter is separately authorized by the Founder and
proven end to end, the harness operates as **LIMITED AUTONOMY**:

- Everything Claude Code and Claude Cowork do between gates runs without the
  Founder.
- **Every independent gate requires a Founder-initiated (manual) Codex
  invocation**, using the fixed gate request in `REVIEW_PROTOCOL.md` §6. There
  are six per batch: `G1`, `G2`, `G3a-E`, `G3b-E`, `G3a-G`, `G3b-G`.
- The three EBD-002 checkpoints (`EBD-A`, `EBD-B`, `EBD-C`) need Cowork, as
  CTO, in session.
- No agent may describe the loop as fully autonomous, and no document in this
  directory may claim an automated Codex handoff, until this section is
  amended on evidence.

Building a controller or adapter is not part of the harness setup. It needs its
own Founder authorization.

## 15. Founder decisions on record (H0.1, 2026-10-05)

1. **Role model.** EBD-002 is not amended and its authority model is
   preserved. Run roles are reconciled to it in `ROLE_MATRIX.md`.
2. **Location.** The harness lives in `docs/execution/autonomy/`. The
   Documentation Standard is not amended to add a new folder.
3. **Stop conditions.** FSC-15 to FSC-19 are accepted and retained.
4. **Correction cycles.** Two unsuccessful bounded correction cycles at the
   same gate trigger a root-cause reassessment, not an automatic Founder stop
   (`REVIEW_PROTOCOL.md` §8).
5. **Gate split.** Post-commit / pre-push verification and remote verification
   are retained as separate checks. (Named per sequence in H0.1-R1 — see
   Section 16.)
6. **Ahead-of-checkpoint rule.** Accepted, on condition that the run file
   states it explicitly (`SESSION_RECOVERY_PROTOCOL.md` §5).
7. **Git authority.** Cowork is read-only on Git mutation by default; Claude
   Code performs native stage, commit, and push when authorized.

## 16. Corrections after independent review (H0.1-R1, 2026-10-06)

The H0.1 independent review returned FAIL with four MAJOR findings and one
MINOR finding. The Founder accepted all five. The corrections:

1. **Engineering and governance closure are distinct sequences.** Six gates
   with fixed ids: `G1`, `G2`, `G3a-E`, `G3b-E`, `G3a-G`, `G3b-G`
   (`REVIEW_PROTOCOL.md` §2, `AUTONOMOUS_LOOP.md` §1).
2. **Exact content equivalence.** A commit passes its post-commit gate
   (`G3a-E` or `G3a-G`) only if it matches the review manifest in path set and
   content identity
   (`REVIEW_PROTOCOL.md` §9).
3. **EBD-002 approvals are loop exit conditions.** Checkpoints `EBD-A`,
   `EBD-B`, `EBD-C` (`AUTONOMOUS_LOOP.md` §8). EBD-002 is not amended.
4. **All history rewrites are Founder-protected**, local and unpublished
   included; forward correction is the default (Section 9, FSC-08, FSC-09).
5. **Run state brought current** (`CURRENT_AUTONOMOUS_RUN.md`).

The H0.1-R1 re-review resolved findings 1 and 4 and returned FAIL on what
remained (Section 17).

## 17. Corrections after re-review (H0.1-R2, 2026-10-06)

The H0.1-R1 independent re-review returned FAIL with two MAJOR findings and one
MINOR finding remaining. The Founder accepted all three. The corrections are
confined to them:

1. **Manifest integrity.** `manifest_id` is the SHA-256 of the complete
   canonical manifest — kind, schema, batch, revision, baseline, ordered path
   set, statuses, modes, and content identities. The `SELF` exception is
   removed: `CURRENT_AUTONOMOUS_RUN.md` is bound by a normalized-content
   identity that excludes only a marked region of mechanically derived
   manifest metadata (`REVIEW_PROTOCOL.md` §9.2, §9.5, §9.7).
2. **One closure order.** Closure documentation, then `EBD-C`, then manifest
   finalization, then the governance commit, then `G3a-G`. The manifest is
   never computed before `EBD-C`; any substantive change after `EBD-C`
   invalidates it (`REVIEW_PROTOCOL.md` §9.6, `AUTONOMOUS_LOOP.md` §8.4).
3. **Run state brought current** (`CURRENT_AUTONOMOUS_RUN.md`).

Unchanged by H0.1-R2: the six-gate split, the history-rewrite protection, the
Freeze-adjacent handling, EBD-002, and every authority boundary.

The H0.1-R2 corrections were followed by an independent PASS and by Founder
ratification (Section 18).

## 18. Founder ratification record

- **Decision:** on 2026-10-08, Founder Mubarak stated: "I approve Founder
  Ratification of the NAWA Autonomous Development Harness v1."
- **Preceding independent verdict (Codex):**
  `PASS — H0.1-R2 HARNESS SAFE FOR FOUNDER RATIFICATION`.
- **Decision Log entry:**
  `docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`.
- **Status:** Founder-ratified on 2026-10-08, and amended the same day by the
  Bootstrap Amendment (Section 19). Not ACTIVE until `G3b-G` PASS on the
  harness governance commit.
- **Not authorized by the ratification:** A2 activation or any engineering
  batch; migration or schema changes; product code or test changes; production
  deployment; secrets changes; destructive data operations; staging, commit,
  or push; history rewrite.

Recording the ratification changed header metadata and governance state only.
No rule in the harness changed.

## 19. Founder decisions after ratification (2026-10-08)

1. **Bootstrap Amendment —
   `docs/decisions/EBD-008-harness-bootstrap-amendment.md`.** For the initial
   governance closure of the harness itself, and only for it, the Governance
   Closure Manifest uses the last remotely verified baseline
   (`9e2463fda8dad102601296f7e5bec33da5d68757`) as `baseline_commit`, with
   `batch: NONE`. The rule is in `REVIEW_PROTOCOL.md` §2.6, §9.2, and §9.7
   (version 1.1). Wherever an engineering commit exists, the `G3b-E`-based
   baseline rule is unchanged.
2. **Conditional governance commit authorization —
   `docs/decisions/EBD-009-harness-governance-commit-authorization.md`.** The
   Founder authorized staging and creating the one governance commit that
   closes the harness, executable only after `EBD-C` is approved and the
   Governance Closure Manifest and its derived metadata are finalized and
   confirmed. It grants no push.

The harness is Founder-ratified as amended. Neither decision activates an
engineering batch, and neither makes the harness ACTIVE: that needs `G3b-G`
PASS on the harness governance commit.
