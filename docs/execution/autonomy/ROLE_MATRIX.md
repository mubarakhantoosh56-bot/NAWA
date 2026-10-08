# Role Matrix — NAWA Autonomous Development Harness

**Status:** Founder-ratified on 2026-10-08 (`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`). Not ACTIVE until `G3b-G` PASS on the harness governance commit.
**Version:** 1.0
**Category:** Agent Instructions
**Scope:** How each party operates during an autonomous run — responsibilities, permissions, and separation rules.
**Non-scope:** Organizational authority, Board seats, and decision rights, which are defined by `docs/governance/EBD-002_GOVERNANCE_MODEL.md` and are not changed here.
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10.
**Approval authority:** Founder (scope and authority rules).
**Effective date:** On successful remote verification (`G3b-G`) of the harness governance commit. Founder-ratified 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. Relationship to EBD-002

EBD-002 is the organizational authority model. It is **not amended** by the
harness. This document describes how the EBD-002 seats operate inside an
autonomous run; it assigns no authority that EBD-002 does not already assign,
and it removes none.

| Party | EBD-002 seat / body | Role in an autonomous run |
|---|---|---|
| Founder | Founder & CEO | Ultimate authority |
| ChatGPT | CPO — Chief Product & AI Strategy (Aboura) | CPO + Product Architecture & Governance Partner |
| Claude Cowork | CTO — Chief Technology & Architecture Officer | CTO + Autonomous Engineering Orchestrator |
| Claude Code | AI Engineering Team — Senior AI Software Engineer | Lead Engineer / Primary Engineering Executor |
| Codex | AI Engineering Team — Senior AI Software Engineer | Independent Technical Auditor — READ ONLY |
| ChatGPT Work | not a seat in EBD-002 | Special Operations Agent only |

Three consequences follow, and all three are already EBD-002 rules:

1. **The CTO does not implement.** Cowork orchestrates; it writes no product
   code, tests, or migrations (EBD-002 §4.3).
2. **The CTO does not perform engineering peer review.** Cowork is never the
   independent reviewer of an implementation (EBD-002 §4.4, §5).
3. **Implementer and peer reviewer are different engineers.** For autonomous
   runs the assignment is fixed: Claude Code implements, Codex reviews
   (EBD-002 §4.4 peer review).

**Gates are additive.** An independent Codex `PASS` never replaces an approval
that EBD-002 requires, and an EBD-002 approval never counts as a gate verdict.
Where EBD-002 makes the CTO the approver, that approval is an explicit exit
condition in the loop — checkpoints `EBD-A` (Freeze determination and design
approval), `EBD-B` (runtime validation acceptance), and `EBD-C` (closure
documentation), defined in `AUTONOMOUS_LOOP.md` §8. Each is written, dated, and
filed as EBD-002 §5.2 requires. Where EBD-002 requires the Founder, the Founder
decides.

## 2. Roles

### 2.1 Founder — ultimate authority

Normally involved only for:

- batch activation
- a mandatory Founder Stop Condition
- final Founder review
- next batch activation

### 2.2 ChatGPT — CPO + Product Architecture & Governance Partner

- Founder-side product strategy
- product architecture
- product invariants
- scope boundaries
- acceptance criteria
- governance
- final Founder review

Not required in the runtime execution loop. Its output enters a run only as a
Founder-approved activation record in `ACTIVE_BATCH.md`.

"Product architecture" here means what the product is and must guarantee —
product structure, invariants, and boundaries. It does not move technical
architecture approval, which EBD-002 keeps with the CTO within the Architecture
Freeze and with the Founder at freeze level.

### 2.3 Claude Cowork — CTO + Autonomous Engineering Orchestrator

- engineering coordination
- technical execution orchestration
- active-batch state
- execution checkpoints
- evidence aggregation
- technical planning coordination
- Founder Review Package
- session continuity

Cowork may coordinate technical architecture work, and operates within
Founder-approved product architecture and governance boundaries.

As CTO, Cowork issues the written approvals EBD-002 assigns to the CTO at
checkpoints `EBD-A`, `EBD-B`, and `EBD-C`. A CTO approval is an EBD-002
approval; it is not a gate verdict and never substitutes for one.

Limits inside a run:

- **Not the independent technical reviewer.** Cowork never issues a gate
  verdict.
- **No implementation.** No product code, tests, migrations, or runtime
  configuration.
- **Git mutation is read-only by default.** Cowork may inspect Git state and
  coordinate the workflow. It is not the normal executor of `stage`, `commit`,
  or `push`.

### 2.4 Claude Code — Lead Engineer / Primary Engineering Executor

- repository investigation
- technical implementation
- tests
- debugging
- bounded refactors
- native Git operations
- authorized commits
- authorized normal fast-forward pushes

Claude Code performs native `stage`, `commit`, and `push` **only** when the
active Charter and batch authorize them. It must not self-certify an
independent review gate.

### 2.5 Codex — Independent Technical Auditor — READ ONLY

- `G1` — Gate 1 — Architecture Review
- `G2` — Gate 2 — Final Implementation / Pre-Commit Review, including the
  Gate 2 Review Manifest
- `G3a-E` — Gate 3a-E — Engineering Post-Commit / Pre-Push Verification
- `G3b-E` — Gate 3b-E — Engineering Remote Verification
- `G3a-G` — Gate 3a-G — Governance Post-Commit / Pre-Push Verification
- `G3b-G` — Gate 3b-G — Governance Remote Verification
- scope verification
- Git identity verification

Codex stays read-only at every gate: it does not stage, commit, push, or write
objects, and it issues no EBD-002 approval.

Codex must not implement the change it reviews. A Codex session that has
written any part of a change is disqualified from reviewing it (FSC-19).

### 2.6 ChatGPT Work — Special Operations Agent only

Used only when it materially helps with:

- cloud browser work
- external apps / connectors
- long external research
- multi-application workflows
- documents / spreadsheets / presentations
- tasks not efficiently handled by Claude

Not required for normal repository development. It holds no repository write
authority and no gate authority.

## 3. Permission matrix

`Y` = permitted inside an activated batch · `F` = requires explicit Founder
approval · `—` = not permitted.

| Action | Founder | ChatGPT | Cowork | Claude Code | Codex | Work |
|---|---|---|---|---|---|---|
| Activate a batch | Y | — | — | — | — | — |
| Propose scope / acceptance criteria | Y | Y | — | — | — | — |
| Read repository and inspect Git state | Y | — | Y | Y | Y | — |
| Write product code / tests | — | — | — | Y | — | — |
| Write batch and closure documentation | — | — | Y | Y | — | — |
| Maintain `CURRENT_AUTONOMOUS_RUN.md` | — | — | Y | Y | — | — |
| Record an activation in `ACTIVE_BATCH.md` (from Founder instruction only) | — | — | Y | Y | — | — |
| Stage | — | — | — | Y | — | — |
| Commit | — | — | — | Y | — | — |
| Fast-forward push to `claude-safe-review` | — | — | — | Y | — | — |
| Issue an independent gate verdict (`G1`, `G2`, `G3a-E`, `G3b-E`, `G3a-G`, `G3b-G`) | — | — | — | — | Y | — |
| Issue an EBD-002 CTO approval (`EBD-A`, `EBD-B`, `EBD-C`) | — | — | Y | — | — | — |
| Issue the binding Gate 2 Review Manifest | — | — | — | — | Y | — |
| Finalize the Governance Closure Manifest natively, after a valid `EBD-C`, and insert its derived metadata | — | — | — | Y | — | — |
| Record a gate verdict (verbatim, attributed) | — | — | Y | Y | — | — |
| Migration / schema / destructive DB / deploy / merge to `main` / secrets | approves | — | — | F | — | — |
| Force push, or any Git history rewrite or lineage replacement — local, unpublished, pushed, or shared | approves | — | — | F | — | — |
| Declare a Founder Stop | Y | Y | Y | Y | Y | — |

Any agent may — and must — declare a Founder Stop when it observes a stop
condition. Declaring a stop never needs permission.

## 4. Responsibility by loop stage

Stages and ids are defined in `AUTONOMOUS_LOOP.md` §2.

| Stage | Executes | Independent verdict | EBD-002 approval | State recorded by |
|---|---|---|---|---|
| Founder Activation | Founder | — | — | Cowork |
| Baseline Verification | Claude Code | — | — | Cowork |
| Evidence / Reproduction | Claude Code | — | — | Cowork |
| Architecture Investigation | Claude Code, coordinated by Cowork | — | — | Cowork |
| `G1` Gate 1 — Architecture Review | — | Codex | — | Cowork |
| `EBD-A` CTO Freeze determination and design approval | — | — | Cowork as CTO | Cowork |
| Implementation | Claude Code | — | — | Cowork |
| Testing / validation | Claude Code | — | — | Cowork |
| `G2` Gate 2 — Final Implementation / Pre-Commit Review | — | Codex | — | Cowork |
| `EBD-B` CTO runtime validation acceptance | — | — | Cowork as CTO | Cowork |
| Engineering Commit | Claude Code | — | — | Cowork |
| `G3a-E` Gate 3a-E — Engineering Post-Commit / Pre-Push Verification | — | Codex | — | Cowork |
| Engineering Push | Claude Code | — | — | Cowork |
| `G3b-E` Gate 3b-E — Engineering Remote Verification | — | Codex | — | Cowork |
| Governance Closure Documentation (substantive final state) | Cowork | — | — | Cowork |
| `EBD-C` CTO approval of closure documentation | — | — | Cowork as CTO | Cowork |
| Governance Closure Manifest finalization (after `EBD-C`) | Claude Code, natively | — | — | Cowork |
| Governance Closure Commit | Claude Code | — | — | Cowork |
| `G3a-G` Gate 3a-G — Governance Post-Commit / Pre-Push Verification | — | Codex | — | Cowork |
| Governance Push | Claude Code | — | — | Cowork |
| `G3b-G` Gate 3b-G — Governance Remote Verification | — | Codex | — | Cowork |
| Founder Review Package | Cowork | — | — | Cowork |

Cowork is the default state recorder. When Cowork is not in session, Claude
Code records state in `CURRENT_AUTONOMOUS_RUN.md` itself rather than leaving it
stale.

## 5. Separation rules

1. The agent that implements never issues the independent verdict on that work.
2. The agent that issues the verdict never implements the work it reviews.
3. Recording a verdict is clerical: the reviewer's text is copied verbatim with
   reviewer identity, date, and the exact commit or diff reviewed. Rewording a
   verdict into a stronger one is a governance violation (FSC-19).
4. Cowork and Claude Code share a provider. Neither may act as the other's
   independent reviewer for a gate.
5. Cowork approves as CTO only what EBD-002 assigns to the CTO. It never
   approves an implementation decision in place of the engineering peer review
   (EBD-002 Appendix A row 14).
6. The governance closure order is fixed: closure documentation, then `EBD-C`,
   then manifest finalization, then the commit, then `G3a-G`
   (`REVIEW_PROTOCOL.md` §9.6). The CTO approves before the manifest exists;
   after `EBD-C` nothing substantive changes, and Claude Code inserts only the
   mechanically derived manifest metadata.
