# EFR-EBD-005 — Engineering Feasibility Review for EBD-005 (CONFLICT-01 / Tier 1 Unfreeze)

**Status:** ✅ **Founder Approved — Authorized for Canonical Application.**
**Review status:** **Not Executed.**
**Approval date:** 2026-08-01.
**Approved by:** Mubarak, Founder and CEO of NAWA.
**Nature of approval:** Founder approval of an execution obligation. **This is not ratification of an Executive Board Decision.**
**Approval gate:** ✅ **Satisfied.** Governance-mirror refresh (§14.1) completed and COWORK revalidation checks R1–R8 (§14.2) passed, 2026-08-01.
**Task ID:** EFR-EBD-005
**Classification:** Standalone Governance Obligation
**Container:** `docs/execution/governance_obligations/`
**Formal conformance scope:** NAWA Reasoning Constitution v1.0 **Article V.2** / **CONFLICT-01**.
**Authority:** EBD-003 §17.1 (Tier 1 unfreeze); EBD-002 §12.4 (unfreeze process); EBD-002 §4.4 (AI Engineering Team review authority); Constitution Article V.2; proposed EBD-005.
**Authorized and scheduled:** 2026-08-01 (Founder).
**Target completion:** 2026-08-05.
**Escalation date:** 2026-08-08.
**Drafted by:** COWORK (CTO / Chief of Staff) — drafting and procedural custody only.
**Approval authority:** Founder & CEO (Mubarak).
**Revision:** Draft 3 — incorporates Founder final controls of 2026-08-01.
**Last updated:** 2026-08-01.

---

## 0. Approval Provenance and Drafting Neutrality

### 0.1 Approval provenance

| Item | Source | Status |
|---|---|---|
| §4 — the twelve Engineering Feasibility Review questions | Prior Founder governance record, external to this repository | ✅ Approved by Founder, 2026-08-01. Reproduced verbatim. |
| §3.2 — D1 / D2 / D3 analytical framework | Founder final control 1, 2026-08-01 | ✅ Approved and retained as the required analytical framework. |
| §7.1 — "Already conformant" evidence threshold | Founder final control 4, 2026-08-01 | ✅ Approved. |
| §5.1 — execution baseline for independent reviews | Founder final control 5, 2026-08-01 | ✅ Approved. |
| §9 — ENG-CONF-001 | Founder decision, 2026-08-01; retained per final control 7 | ✅ Approved as a recommendation-only conditional proposed task. |
| §14.1 — governance-mirror refresh | Founder decision, 2026-08-01; method fixed by final control 6 | ✅ Assigned to Claude Code. Blocking. |
| §6 / §11 — independent review model | Founder decision, 2026-08-01 | ✅ Approved, with a post-seal reconciliation round. |
| **This document as a whole — Draft 3** | Founder decision, 2026-08-01 | ✅ **Founder Approved as the final authoritative task specification; authorized for canonical application.** Approved by Mubarak, Founder and CEO of NAWA. Approval of an execution obligation, not ratification of an EBD. Review status: Not Executed. |

### 0.2 Drafting neutrality — binding

**This task contains no prediction of its own outcome.**

Per Founder final control 2, all predictive wording has been removed. This document does not state, imply, or rank which conformance classification is likely, which divergence is likely to be satisfied, which mechanism is likely to be found, or what the reviewers are likely to conclude.

Binding on all parties:

- Neither reviewer may be given, and neither may seek, any expectation of the outcome before evidence is gathered.
- Illustrative examples in §7.2 and §7.3 are **definitional boundaries**, not likelihood statements, and carry no frequency, precedence, or probability claim.
- COWORK, in its procedural custody role, must not communicate an anticipated outcome to either reviewer at any point before both findings are sealed.
- Any predictive statement introduced into this task in a later revision is a defect and must be removed.

---

## 1. Purpose and Governance Authority

### 1.1 Purpose

Establish whether the change contemplated by EBD-005 — resolution of **CONFLICT-01** by Tier 1 unfreeze of `EBD-003 §12.3 — Company Brain Never Overrides Facts` — is **implementable**, and at what cost, risk, and blast radius.

This obligation produces a **feasibility finding**, not an approval. Under EBD-002 §4.4 Limits, the AI Engineering Team *cannot unfreeze architecture*. The finding informs gates 4–6; it does not satisfy them.

### 1.2 Governing authority

| Source | Clause | Effect on this obligation |
|---|---|---|
| EBD-003 §17.1 | *"Engineering Team review of implementation feasibility (per EBD-002 §4.4 authority)"* | Establishes this review as a mandatory gate in the Tier 1 unfreeze chain |
| EBD-002 §12.4 step 4 | *"Engineering review. AI Engineering Team reviews for implementation feasibility."* | Fixes the review's position between Product review and Founder ratification |
| EBD-002 §4.4 | *"mandatory engineering review, without which decisions affecting implementation are not ratified"* | Makes EBD-005 non-ratifiable while this obligation is open |
| EBD-002 §4.4 | *"The CTO is explicitly excluded from performing engineering peer review"* | Bars COWORK from authoring or substituting for the finding |
| Constitution Article V.2 | *Memory, Current Evidence, and Conflict Resolution* | **The formal conformance scope of this review** |
| Executive Board Directive #001 | *"No engineering task may be executed unless it exists inside `docs/execution/`"* | Requires this file to exist and be applied before execution begins |

### 1.3 Gate position

| # | Gate | Owner | Status |
|---|---|---|---|
| 0 | EBD-006 applied, verified, committed, pushed | Claude Code | ✅ `6d5d042`, V1–V11 passed, 2026-08-01 |
| 1 | EBD-005 drafted | CTO / Board | ⚪ Not confirmed |
| 2 | CTO impact review | COWORK | ⚪ Not confirmed |
| 3 | **Engineering Feasibility Review — this obligation** | Claude Code + Codex | 🟠 Authorized 2026-08-01; not executed |
| 4 | Product review (user-facing impact) | Aboura | ⛔ Blocked by gate 3 |
| 5 | Founder ratification | Mubarak | ⛔ Blocked by gates 3–4 |
| 6 | Immediate refreeze → Architecture Freeze v1.1 | CTO | ⛔ Blocked |

## 2. Explicit Non-Sprint Classification

**EFR-EBD-005 is a Standalone Governance Obligation. It is not part of Sprint EX-1 and not part of Sprint EX-2.**

Binding consequences:

- It does **not** appear in the Sprint EX-1 Active Tasks table and does **not** count against the Sprint EX-1 goal, capacity plan, or exit gate.
- It does **not** activate, pre-stage, or imply activation of Sprint EX-2. Sprint EX-2 remains inactive.
- It does **not** consume Aboura's Sprint EX-1 design front-load allocation.
- It satisfies the Repository First Policy through the `governance_obligations/` container, which is a first-class execution container alongside `sprint_exN/` and `backlog/`.
- Sprint EX-1 reporting obligations (EBD-002 §16 six KPIs) are unaffected by this obligation.

Rationale: the obligation is a governance gate on a Tier 1 architectural freeze, not product execution work. Attaching it to a Sprint would misattribute its cost, contaminate that Sprint's goal integrity, and make a governance blocker dependent on Sprint scheduling.

## 3. Constitutional Conflict Being Assessed (CONFLICT-01)

### 3.1 The two positions

**Frozen text — `EBD-003 §12.3`, Tier 1 frozen runtime philosophy (EBD-003 §12.4, §14):**

> Institutional memory (OME Foundation) may inform reasoning but may never contradict a validated Company Input. When memory and current input disagree, the current input is treated as the current truth; memory is updated to reflect the discrepancy, not the other way around.

**Supreme text — `NAWA Reasoning Constitution v1.0, Article V.2 — Memory, Current Evidence, and Conflict Resolution`:**

> Institutional memory informs reasoning. Where institutional memory and current evidence conflict, neither prevails solely because it is older or newer. NAWA investigates the conflict, preserves it rather than silently resolving it, and reasons to the best-supported current understanding.
>
> The resolution — including which sources were weighed, on what basis, and what uncertainty remains — is recorded with its provenance. Prior records are preserved; the resolution is appended, not substituted.

Article VIII.1 establishes Constitutional supremacy. Article V.2 therefore governs, and §12.3 is the text that must move.

### 3.2 Required analytical framework — D1 / D2 / D3

*Founder final control 1, 2026-08-01. Binding. Every finding must address all three axes separately.*

| Axis | Divergence |
|---|---|
| **D1** | **Automatic chronological deference** versus **investigation toward the best-supported current understanding.** |
| **D2** | **Silent resolution** versus **conflict detection and preservation.** |
| **D3** | **Substitution or overwrite** versus **append-with-provenance and preservation of prior records.** |

D1, D2, and D3 are assessed independently. A finding that treats them as a single verdict is procedurally incomplete and will be returned. Each axis carries its own evidence, its own conclusion, and its own contribution to the classification at §7.

### 3.3 Formal scope boundary

*Founder final control 3, 2026-08-01. Binding.*

**The formal conformance scope of EFR-EBD-005 is Constitution Article V.2 / CONFLICT-01. Nothing else.**

**Article VII.5 — Historical Memory Preservation** may be cited as **supporting Constitutional context for D3**. It is context, not scope. It does not extend the assessment, does not add a conformance axis, and does not enlarge EBD-005.

**Adjacent-finding rule:** if a reviewer discovers a VII.5 implementation gap **beyond CONFLICT-01** — that is, a preservation, supersession, or historical-record defect not reachable through the memory-versus-current-evidence conflict path — the reviewer:

1. Records it in a clearly separated **Adjacent Findings** section of their finding.
2. States plainly why it falls outside CONFLICT-01.
3. Does **not** fold it into the D1/D2/D3 assessment or the §7 classification.
4. Does **not** treat it as ENG-CONF-001 scope.

Adjacent findings are routed to the Founder for **separate governance classification**. **EBD-005 scope does not automatically expand to absorb them.** The same rule applies to any other Constitutional article a reviewer believes is implicated.

### 3.4 Related Constitutional articles — context only

- **Article III.7** — five epistemic categories (Fact, Company Policy, Assumption, NAWA Inference, Recommendation). Directly relevant to approved Question 8: an `evidence_conflict` state must not become a sixth category.
- **Article III.6** — Epistemic Uncertainty. Residual uncertainty arising from a conflict must be carried explicitly rather than concealed.
- **Article VII.5** — Historical Memory Preservation. Supporting context for D3 only, subject to §3.3.

These are cited for interpretive support. None of them extends the formal scope at §3.3.

### 3.5 Status of the conflict

- The Constitution was ratified 2026-07-31 and is in force.
- **EBD-006** (applied, `6d5d042`) declared Constitutional supremacy across EBD-001 through EBD-004 but **deliberately did not touch §12.3** — verification check V8 exists specifically to confirm EBD-006 did not stray into EBD-005 scope.
- CONFLICT-01 is therefore **live, explicit, and documented**: a recorded contradiction between the stack's supreme authority and an active Tier 1 frozen element, with the Architecture Freeze held at v1.0.

### 3.6 What this review does and does not decide

**In scope:** whether the runtime *as built* satisfies Article V.2 across D1, D2, and D3, and what implementing the Constitutional position would require.

**Out of scope:** the substance of CONFLICT-01, the replacement wording for §12.3, and whether the unfreeze should be granted. **This review must not propose replacement text for §12.3.**

## 4. The Twelve Engineering Feasibility Review Questions

*Founder-approved, reproduced verbatim from the prior Founder governance record. Each reviewer answers all twelve independently.*

**1.** Where in the code is a conflict between institutional memory and current evidence detected or resolved today? Identify files, functions, and Runtime Components.

**2.** Is automatic chronological precedence implemented in deterministic code, partially implemented, present only as prompt instruction text, or documented-only?

**3.** Which Runtime Components read from OME Foundation at runtime?

**4.** What would conflict detection require if it is not already present? Is the comparison surface available today?

**5.** What would recording the resolution — sources weighed, basis, residual uncertainty, and provenance — require? Data-model change, new OME record type, or schema migration?

**6.** Does OME currently overwrite records or append? What would append-not-substitute semantics require?

**7.** Where should this behavior live: NCE Lite, OME Foundation, NCO Lite, or as a distributed responsibility?

**8.** How should an `evidence_conflict` state be represented without creating a sixth epistemic category?

**9.** Which existing tests would change, and what new tests are required?

**10.** What is the implementation effort: hours, days, or Sprint-scale?

**11.** Does the work conflict with, depend on, or block Sprint EX-2? Specifically, does it require an OME data-model change, and does Sprint EX-2 use the same surfaces?

**12.** What breaks if the change is implemented now, and what breaks if it is deferred?

### 4.1 Binding constraint on Question 2 — Founder direction, 2026-08-01

**Question 2 must not prejudge the conformance result.**

A finding of prompt-only implementation is an important finding and must be reported plainly. It does **not**, by itself, determine the classification at §7. The final classification must depend on **evidenced runtime behavior, coverage, tests, provenance, and compliance with Constitution Article V.2** — assessed together across D1, D2, and D3.

Binding on reviewers:

- **Prompt-only does not automatically mean non-conformant.**
- **Deterministic code does not automatically mean conformant.**
- **Behavioral correctness and Constitutional correctness must both be evidenced.** They are independent axes and must be reported separately.
- Reasoning from mechanism directly to verdict is an invalid inference and will be returned.
- Absence of any mechanism is a finding of substance, not an absence of evidence.

### 4.2 Question mapping to D1 / D2 / D3

Provided as an aid to completeness, not as a constraint on how a reviewer answers. A question may bear on more than one axis.

| Axis | Principally served by |
|---|---|
| D1 — chronological deference vs. investigation | Questions 1, 2, 7, 12 |
| D2 — silent resolution vs. detection and preservation | Questions 1, 4, 7, 8 |
| D3 — substitution vs. append-with-provenance | Questions 5, 6, 8 |
| Cross-cutting (effort, risk, tests, Sprint impact) | Questions 3, 9, 10, 11 |

## 5. Execution Baseline and Required Evidence

### 5.1 Execution baseline — binding

*Founder final control 5, 2026-08-01.*

1. **Same pinned canonical commit.** Both Claude Code and Codex review **the identical pinned commit** on `claude-safe-review`. The commit is fixed before either review begins and is not changed mid-review.
2. **Separate isolated checkouts.** Each reviewer works in a **separate clean Git worktree or equivalent isolated checkout**. Reviewers do not share a checkout.
3. **No review against the uncommitted working tree.** Neither reviewer may review against the existing canonical working tree. The canonical repository is known to contain unrelated uncommitted work (EBD-006 §7.1), and that work is not part of the reviewed baseline.
4. **Recorded baseline metadata.** Each report records:

   | Field | Requirement |
   |---|---|
   | Commit SHA | The pinned commit reviewed |
   | Branch | `claude-safe-review` |
   | Working-tree status | Output demonstrating a clean isolated checkout |
   | Inspected files and functions | Paths with line ranges; functions by name |
   | Commands and tests run | Verbatim, with output or a pointer to captured output |
   | Evidence | Per §5.3, mapped to the evidence classes at §5.2 |

5. **Timestamp and hash before peer access.** Each final report is **timestamped and SHA-256 hashed, and the hash recorded, before the other reviewer is permitted to read it.** The hash is the seal.
6. **Reconciliation begins only after both reports are sealed.** No cross-reading, no comparison, no discussion of findings before both seals exist.

**Custody note:** COWORK records both seal hashes and timestamps and confirms the ordering. COWORK does not read either finding into the other reviewer's context before both seals exist.

### 5.2 Evidence classes

| # | Class | Requirement | Principal questions | Axis |
|---|---|---|---|---|
| E1 | OME Foundation source | Service, repository, and model definitions — full paths, line ranges | 1, 3, 6 | D3 |
| E2 | Conflict detection and resolution logic | Every code path where memory and current evidence are compared, merged, ranked, or reconciled | 1, 2, 4 | D1, D2 |
| E3 | Prompt and reasoning templates | Any prompt text asserting memory-vs-evidence precedence, quoted verbatim with path | 2 | D1 |
| E4 | Runtime component read paths | Call sites where OME-derived context enters any Runtime Component | 3, 7 | D1, D2 |
| E5 | Schema and migrations | Migration files touching OME tables; current migration head; relevant DDL; overwrite-vs-append semantics at the storage layer | 5, 6 | D3 |
| E6 | Contract mapping | Mapping from each affected code site to the governing EBD-004 component contract clause | 7 | all |
| E7 | Executed behavioural evidence | Test output, trace, or reproduction demonstrating actual conflict behaviour. Code reading alone is insufficient. | 2, 12 | D1, D2 |
| E8 | Test inventory and coverage | Existing tests covering memory-vs-evidence precedence and their coverage, or explicit statement that none exist | 9 | all |
| E9 | Provenance surface | Whether sources weighed, resolution basis, and residual uncertainty are recordable and retrievable today | 5 | D3 |
| E10 | Epistemic category handling | How the five Article III.7 categories are represented today, if at all | 8 | D2 |
| E11 | Conflict retrievability | Whether a preserved conflict can be retrieved and inspected after the fact, and by what interface | 4, 8 | D2 |

E7, E8, E9, and E11 are the evidence base for the §4.1 constraint and the §7.1 threshold — they are what allow a classification to rest on evidenced behavior rather than on mechanism type.

### 5.3 Evidence discipline

- Quote, do not paraphrase, any code or prompt text the finding relies on.
- Absence of a mechanism is a finding and must be stated explicitly.
- Distinguish **inspected** from **inferred** throughout. Inference must be labelled.
- No runtime code may be modified during evidence gathering. **This is a read-only review.**

## 6. Required Named Outputs

### 6.1 Independent findings — both required, produced in isolation

| Output | Author | Path |
|---|---|---|
| Engineering Feasibility Finding — Claude Code | Claude Code, Senior AI Software Engineer | `docs/execution/governance_obligations/EFR-EBD-005_FINDING_CLAUDE_CODE.md` |
| Engineering Feasibility Finding — Codex | Codex, Senior AI Software Engineer | `docs/execution/governance_obligations/EFR-EBD-005_FINDING_CODEX.md` |

Each finding must:

1. Name its author and state the role under EBD-002 §4.4.
2. Record the full execution baseline per §5.1 item 4.
3. Answer **all twelve** approved questions.  No question may be skipped; "cannot determine" is acceptable with a stated reason.
4. Assess **D1, D2, and D3 separately**, each with its own evidence and conclusion.
5. State a proposed conformance classification per §7, satisfying §4.1 and — where "already conformant" is proposed — the §7.1 threshold in full.
6. Record any **Adjacent Findings** per §3.3, clearly separated.
7. List unresolved questions and what would resolve them.
8. Be timestamped and SHA-256 hashed on submission per §5.1 item 5.

**Neither reviewer may read the other's finding before their own is sealed.** A sealed finding is not revised. The sealed originals are preserved as the attributable record.

### 6.2 Reconciliation round — after both findings are sealed

Once both findings are sealed and both hashes recorded, a reconciliation round **may** occur. Its purpose is to compare positions, test reasoning against evidence, and narrow disagreement where the evidence supports narrowing.

Binding limits:

- Reconciliation **does not alter or replace** either sealed finding. Any position change is recorded as a **dated, attributed addendum** in the consolidated record, naming which reviewer moved, on what evidence, and why.
- Reconciliation is **not required to produce consensus**. Preserved disagreement is a legitimate and complete outcome.
- Reconciliation must not be resolved by seniority, filing order, seal order, or CTO input.
- COWORK may schedule and observe the round for procedural custody. COWORK does not participate substantively.

### 6.3 Consolidated record

| Output | Author | Path |
|---|---|---|
| Consolidated Engineering Feasibility Record | Claude Code + Codex jointly, after both findings are sealed | `docs/execution/governance_obligations/EFR-EBD-005_RECORD.md` |

Required content, with **every item attributable to the individual reviewer who holds it**:

- **Execution baselines** — both reviewers' commit SHA, branch, working-tree status, and seal hash with timestamp.
- **Agreement** — questions and axes where both reviewers reached the same conclusion, with the shared answer and both attributions.
- **Disagreement** — where they differ, with both positions stated in full and neither suppressed, each attributed by name.
- **Unresolved questions** — open items, attributed, with what evidence or decision would close them.
- **Evidence basis** — consolidated manifest indicating which reviewer inspected what.
- **Adjacent findings** — per §3.3, flagged for separate governance classification, attributed.
- **Reconciliation addenda** — any post-seal position changes, dated and attributed per §6.2.
- **Resulting conformance classification** per §7. If the reviewers do not converge, the record states both classifications with attribution, and the Founder decides at §13.

**No content in the consolidated record may be anonymous or jointly attributed where the reviewers differ.**

## 7. Conformance Outcomes

Exactly one classification is recorded, unless the reviewers do not converge, in which case both are recorded with attribution.

### 7.0 Basis of classification — binding

Per §4.1, the classification is determined by **evidenced runtime behavior, coverage, tests, provenance, and compliance with Constitution Article V.2**, assessed together across **D1, D2, and D3**. Implementation mechanism is **input to** the classification, never the classification itself.

Each of D1, D2, and D3 is assessed on its own evidence. The classification follows from the three axis results considered together; it is not assigned first and justified afterward.

### 7.1 Already conformant — with mandatory evidence threshold

The runtime **as built** satisfies Article V.2 across D1, D2, and D3.

**Evidence threshold — binding.** *Founder final control 4, 2026-08-01.*

**An "already conformant" verdict may not be based solely on governance text, prompt instructions, or static code inspection.** It requires evidence of **all six** of the following:

| # | Required evidence | Axis |
|---|---|---|
| T1 | **Executed conflict-detection behavior** — demonstrated in execution, not inferred from source | D2 |
| T2 | **Absence of automatic chronological-precedence behavior** — demonstrated, not assumed | D1 |
| T3 | **Preservation and retrievability of the conflict** — the conflict persists and can be retrieved and inspected afterward | D2 |
| T4 | **Recorded resolution basis, residual uncertainty, sources weighed, and provenance** — all four present | D3 |
| T5 | **Append-not-substitute treatment of prior records** — prior records demonstrably preserved | D3 |
| T6 | **Supporting tests or equivalent reproducible evidence** — the behaviour is reproducible by a third party | all |

**If any of T1–T6 is unevidenced, "already conformant" is not available as a classification.** A reviewer proposing it must map each of T1–T6 to specific evidence in their finding. An unmapped threshold item returns the finding.

**Consequence if recorded:** EBD-005 becomes a governance-text correction. No runtime change. Freeze advances to v1.1 on text alone. EBD-004 contract impact is determined by approved Question 7. **ENG-CONF-001 closes without engineering implementation** per §9.

### 7.2 Partially conformant

The runtime satisfies Article V.2 on some but not all of D1, D2, D3 — or satisfies an axis at some sites and not others — or satisfies an axis behaviourally without the coverage, provenance, or reproducibility required at §7.1.

*The preceding sentence is a definitional boundary. It carries no claim about which combination will be found.*

**Consequence:** EBD-005 carries both a text change and a bounded implementation change. **The EFR recommends ENG-CONF-001 activation and defines its evidenced scope** per §9. The recommendation does not authorize execution.

### 7.3 Non-conformant

The runtime contradicts Article V.2 across D1, D2, and D3, or no conflict detection, preservation, or provenance mechanism is evidenced at any site.

*This is a definitional boundary. It carries no claim about likelihood.*

**Consequence:** EBD-005 carries a substantive implementation change. **The EFR recommends ENG-CONF-001 activation at elevated priority and defines its evidenced scope** per §9. If approved Question 7 concludes the behaviour cannot be placed within the existing Runtime Components without adding, removing, reordering, or renaming one, the unfreeze scope escalates from Freeze v1.1 to **v2.0** — a materially larger Founder decision that must be surfaced explicitly at §13.

## 8. Sprint EX-2 Blocking Assessment

Approved Question 11 requires this assessment. Each reviewer states it explicitly in their own finding.

| Assessment | Meaning |
|---|---|
| **Non-blocking** | Sprint EX-2 may be planned and activated independently of EFR-EBD-005 and ENG-CONF-001 |
| **Blocking — sequencing** | Sprint EX-2 may be planned but must not start work touching OME surfaces until refreeze completes |
| **Blocking — scope** | Sprint EX-2 scope cannot be defined until the conformance outcome is known, because remediation would collide with planned work |

Required supporting statements:

1. Whether the work requires an **OME data-model change** (approved Question 11, explicit).
2. Whether **Sprint EX-2 uses the same surfaces** (approved Question 11, explicit).
3. Which components and code paths would be **simultaneously in play**, and whether concurrent modification is safe.

**This assessment is advisory input to the Founder. It does not activate, defer, or scope Sprint EX-2.** Sprint EX-2 remains inactive regardless of the outcome recorded here.

## 9. ENG-CONF-001 — Recommendation Only

**ENG-CONF-001 — Constitutional Conformance Remediation (Memory Precedence).**
**Status: conditional proposed task. Not active. Not scheduled.** *Retained per Founder final control 7.*

### 9.1 Outcome mapping

| Conformance outcome | ENG-CONF-001 disposition |
|---|---|
| **Already conformant** (§7.1) | **Closes without implementation.** |
| **Partially conformant** (§7.2) | **The EFR may recommend activation with an evidenced scope.** |
| **Non-conformant** (§7.3) | **The EFR may recommend activation at elevated priority with an evidenced scope.** |

### 9.2 Binding conditions

1. **Recommendation only.** The EFR recommends; it does not activate. Recommendation does not authorize execution.
2. **Founder authorization and scheduling remain mandatory** before any work begins.
3. **No runtime implementation begins before EBD-005 ratification**, unless the Founder grants an **explicit exception**.
4. **Scope is bounded by the evidenced scope in the consolidated record.** ENG-CONF-001 may not exceed the gaps the reviewers evidenced. Expansion requires a new Founder decision.
5. **Adjacent findings are excluded.** Per §3.3, adjacent findings are not ENG-CONF-001 scope and do not expand EBD-005.
6. **Classification is a Standalone Governance Obligation**, filed in `governance_obligations/` — not Sprint work, unless the Founder later assigns it to a Sprint.
7. **Peer review applies.** ENG-CONF-001 implementation is subject to the same Claude Code / Codex peer requirement under EBD-002 §4.4.
8. **The task file must exist before execution** per Executive Board Directive #001.

### 9.3 Recording non-activation

If §7.1 is recorded, COWORK files a closure note stating that ENG-CONF-001 closed without engineering implementation, and why. **A non-activation is a recorded outcome, not a silent absence.**

## 10. Acceptance Criteria

EFR-EBD-005 is complete when **all** of the following hold:

| # | Criterion |
|---|---|
| A1 | Mirror refresh executed by Claude Code via canonical HEAD export, manifest returned (§14.1) |
| A2 | COWORK verified mirror hashes against the manifest and revalidated this document's references against the refreshed files (§14.2) — and did not represent the refresh as verified before the manifest was available |
| A3 | Execution baseline satisfied per §5.1 — same pinned commit, separate clean worktrees, no review against the uncommitted canonical working tree |
| A4 | Claude Code finding filed, timestamped, hashed, and sealed; all twelve approved questions answered; D1/D2/D3 assessed separately; author named |
| A5 | Codex finding filed, timestamped, hashed, and sealed; all twelve approved questions answered; D1/D2/D3 assessed separately; author named |
| A6 | Independence held — neither reviewer read the other's finding before their own was sealed; seal ordering recorded |
| A7 | Consolidated record filed with all required sections, individually attributable |
| A8 | Evidence classes E1–E11 addressed, or explicit statement of why a class is inapplicable |
| A9 | Classification recorded per §7, satisfying §7.0 and §4.1; if "already conformant", T1–T6 each mapped to specific evidence |
| A10 | Adjacent findings, if any, recorded separately per §3.3 and not folded into scope |
| A11 | Sprint EX-2 blocking assessment recorded per §8, including the two explicit Question 11 statements |
| A12 | ENG-CONF-001 disposition recorded per §9, including non-activation |
| A13 | Both review signatures present per §11 |
| A14 | CTO procedural-completeness check recorded per §12 |
| A15 | No runtime code modified; no governance document modified; EBD-005 unmodified; canonical files unmodified; Sprint EX-1 unchanged; Sprint EX-2 not activated |

**A15 is the boundary guard.** Any breach voids the review and requires it to be re-run.

## 11. Review Signatures

Both signatures required. Neither may be supplied by the CTO.

**Reviewer 1 — Claude Code, Senior AI Software Engineer (AI Engineering Team, EBD-002 §4.4)**

| Field | Value |
|---|---|
| Finding filed, timestamped, hashed, sealed | ☐ |
| Path | |
| Commit SHA reviewed | |
| Branch | |
| Isolated worktree confirmed; working-tree status recorded | ☐ |
| Seal SHA-256 | |
| Seal timestamp | |
| All twelve approved questions answered | ☐ |
| D1, D2, D3 assessed separately | ☐ |
| Independence attested — did not read peer's finding before sealing | ☐ |
| §4.1 constraint observed — Question 2 did not prejudge classification | ☐ |
| §7.1 threshold T1–T6 mapped (only if proposing "already conformant") | ☐ N/A |
| Adjacent findings recorded separately, or none | ☐ |
| Proposed conformance classification | |
| Date | |
| Signature | |

**Reviewer 2 — Codex, Senior AI Software Engineer (AI Engineering Team, EBD-002 §4.4)**

| Field | Value |
|---|---|
| Finding filed, timestamped, hashed, sealed | ☐ |
| Path | |
| Commit SHA reviewed | |
| Branch | |
| Isolated worktree confirmed; working-tree status recorded | ☐ |
| Seal SHA-256 | |
| Seal timestamp | |
| All twelve approved questions answered | ☐ |
| D1, D2, D3 assessed separately | ☐ |
| Independence attested — did not read peer's finding before sealing | ☐ |
| §4.1 constraint observed — Question 2 did not prejudge classification | ☐ |
| §7.1 threshold T1–T6 mapped (only if proposing "already conformant") | ☐ N/A |
| Adjacent findings recorded separately, or none | ☐ |
| Proposed conformance classification | |
| Date | |
| Signature | |

**Baseline identity check**

| Field | Value |
|---|---|
| Both reviewers reviewed the same pinned commit SHA | ☐ |
| Separate isolated checkouts confirmed | ☐ |
| Neither reviewed the uncommitted canonical working tree | ☐ |

**Reconciliation round (optional, post-seal)**

| Field | Value |
|---|---|
| Both seals recorded before any cross-reading | ☐ |
| Round held | ☐ Yes ☐ No |
| Date | |
| Addenda recorded with attribution | ☐ N/A |
| Sealed findings unaltered | ☐ |

**Joint consolidated record**

| Field | Value |
|---|---|
| Record filed | ☐ |
| All required sections complete and individually attributable | ☐ |
| Final classification (or both, with attribution) | |
| Date | |
| Both signatures | |

## 12. CTO Procedural-Completeness Check

COWORK verifies **procedure only**. COWORK does not assess, endorse, correct, or overrule the engineering conclusions, does not substitute its technical judgment for either finding, and does not author any part of the findings or the record.

| # | Check | Result |
|---|---|---|
| P1 | Claude Code hash manifest received before review began | ☐ |
| P2 | Mirror hashes verified against the manifest; refresh not represented as verified before the manifest existed | ☐ |
| P3 | This document's references revalidated against the refreshed governance files (§14.2) | ☐ |
| P4 | Both reviewers used the same pinned commit SHA | ☐ |
| P5 | Separate isolated checkouts confirmed; no review against the uncommitted canonical working tree | ☐ |
| P6 | Both findings filed, timestamped, hashed, and sealed by their named authors | ☐ |
| P7 | Seal ordering confirms neither reviewer had access to the other before sealing | ☐ |
| P8 | All twelve approved questions answered in both findings | ☐ |
| P9 | D1, D2, D3 assessed separately in both findings | ☐ |
| P10 | Evidence classes E1–E11 addressed | ☐ |
| P11 | Where "already conformant" is proposed, T1–T6 each mapped to specific evidence | ☐ N/A |
| P12 | Adjacent findings, if any, recorded separately and not folded into scope or ENG-CONF-001 | ☐ |
| P13 | Consolidated record contains all required sections | ☐ |
| P14 | Every agreement, disagreement, unresolved question, and evidence basis is attributable to an individual reviewer | ☐ |
| P15 | Disagreements preserved — not suppressed, averaged, or arbitrated by CTO | ☐ |
| P16 | Reconciliation, if held, left sealed findings unaltered and recorded addenda with attribution | ☐ |
| P17 | Classification recorded per §7.0; §4.1 constraint observed | ☐ |
| P18 | Sprint EX-2 assessment recorded, including both explicit Question 11 statements | ☐ |
| P19 | ENG-CONF-001 disposition recorded, including non-activation | ☐ |
| P20 | No predictive statement introduced into the task or communicated to reviewers before sealing (§0.2) | ☐ |
| P21 | A15 boundary guard intact | ☐ |
| P22 | No CTO authorship anywhere in the findings or record | ☐ |

**A failed check returns the obligation to the Engineering Team. It does not permit CTO correction of the finding.**

## 13. Founder Decision Gate

On procedural completeness, COWORK submits the package to the Founder. The Founder decides:

1. **Accept the finding** and proceed to gate 4 (Aboura product review).
2. **Return for additional evidence** on named questions or unmapped §7.1 threshold items.
3. **Resolve a reviewer disagreement** where the record states two attributed positions.
4. **Authorize and schedule ENG-CONF-001**, or decline — recommendation alone does not authorize execution (§9.2).
5. **Grant or withhold an explicit exception** permitting runtime implementation before EBD-005 ratification (§9.2 condition 3).
6. **Classify any adjacent findings** for separate governance handling per §3.3.
7. **Rule on unfreeze scope** — Freeze v1.1 or v2.0 — where approved Question 7 indicates the behaviour cannot be placed within the existing component set.
8. **Rule on the Sprint EX-2 relationship**, which remains a separate decision and is not implied by acceptance of this finding.

**Nothing in this obligation ratifies the unfreeze.** Ratification occurs at gate 5 under EBD-003 §17.1, after Product review, and only by the Founder.

## 14. Precondition, Target Date, Escalation

### 14.1 Blocking precondition — governance-mirror refresh (assigned to Claude Code)

*Founder final control 6, 2026-08-01.*

**The mirror refresh must complete before Draft 3 receives final Founder approval and before this task is applied to the canonical repository.** It is not merely a precondition to executing the review.

**Assignee: Claude Code.** Claude Code holds canonical repository access as the designated executor under EBD-006 §7.1.

**Source:**

- Repository: `C:\AIMX_PROJECTS`
- Branch: `claude-safe-review`
- Canonical governance commit: `6d5d042` — EBD-006 Constitutional Governance Alignment

**Method — binding.** Export the **tracked governance content from the canonical HEAD**, preferably:

```
git show HEAD:<path>
```

rather than copying potentially modified working-tree content. The canonical repository contains unrelated uncommitted work (EBD-006 §7.1); working-tree copies risk importing it.

**Files:**

```
docs/governance/NAWA_REASONING_CONSTITUTION_v1.md
docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md
docs/governance/EBD-002_GOVERNANCE_MODEL.md
docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md
docs/governance/EBD-004_ENGINE_DEFINITIONS.md
docs/governance/EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md
```

**Claude Code must:**

1. Make **no change** to the canonical files. This is an export-out operation only.
2. Export from **canonical HEAD**, not the working tree.
3. Record the **source commit SHA**.
4. Record **source SHA-256** and **mirror SHA-256** for **all six** files.
5. Confirm **source-to-mirror content identity**.
6. Return a **refresh manifest** at `docs/execution/governance_obligations/EFR-EBD-005_MIRROR_REFRESH.md`.

**COWORK constraint — binding:** COWORK may verify the mirror hashes against that manifest, but **must not represent the refresh as verified before the manifest is available.** Until the manifest exists, the mirror's state is unverified, this task may not receive final approval, and the review may not begin.

### 14.2 COWORK revalidation after refresh

On receipt of the manifest, COWORK revalidates **this document's references** against the refreshed governance files, and records the result:

| # | Revalidation | Basis |
|---|---|---|
| R1 | Source commit SHA in the manifest matches the declared canonical governance baseline | §14.1 |
| R2 | All six files: source SHA-256 equals mirror SHA-256 | §14.1 item 4 |
| R3 | Article V.2 text quoted at §3.1 is byte-accurate against the refreshed Constitution | §3.1 |
| R4 | EBD-003 §12.3 text quoted at §3.1 is byte-accurate, and V8 holds — §12.3 unmodified, in its pre-EBD-005 state | EBD-006 V8 |
| R5 | EBD-002 §4.4 and §12.4 citations resolve correctly in the refreshed text | §1.2 |
| R6 | EBD-003 §17.1 citation resolves correctly in the refreshed text | §1.2 |
| R7 | Article III.6, III.7, VII.5, VIII.1 citations resolve correctly | §3.3, §3.4 |
| R8 | Post-EBD-006 header state confirmed: EBD-001 v1.1, EBD-002 v1.1, EBD-003 Document v1.1 / Freeze v1.0, EBD-004 v1.1-MVP; `Subordinate to:` present in all four; all dated 2026-08-01 | EBD-006 V1–V3 |

**Any revalidation failure returns this task to draft for correction before Founder approval.** A citation that no longer resolves is a defect in the task, not in the refreshed document.

### 14.3 Schedule

| Milestone | Date |
|---|---|
| Authorized and scheduled by Founder | 2026-08-01 |
| Mirror refresh complete, manifest returned | before final approval |
| COWORK revalidation complete (§14.2) | before final approval |
| Final Founder approval and canonical application | after §14.1 and §14.2 |
| Target completion | **2026-08-05** |
| Escalation if incomplete or unscheduled | **2026-08-08** |

### 14.4 Escalation rule

If the obligation is incomplete or unscheduled at 2026-08-08, COWORK escalates to the Founder as a formal blocker on the Execution Board, recording days open and the specific gate that stalled.

**Standing risk while open:** CONFLICT-01 remains a live, documented contradiction between Constitution Article V.2 and an active Tier 1 frozen element, with the Architecture Freeze held at v1.0. This is a governance-integrity exposure, not a scheduling delay.

---

## Appendix A — Change Log

| Date | Event | By |
|---|---|---|
| 2026-08-01 | Founder authorized EFR-EBD-005 as a Standalone Governance Obligation; container `docs/execution/governance_obligations/` established; schedule and review requirements set. | Mubarak, Founder & CEO |
| 2026-08-01 | Draft 1 prepared and returned for Founder review. Twelve EFR questions and ENG-CONF-001 activation rule flagged as CTO-authored, pending approval. Not applied to canonical. | COWORK (CTO / Chief of Staff) |
| 2026-08-01 | Draft 2. Founder decisions incorporated: §4 replaced with the twelve approved questions verbatim; Question 2 non-prejudgment constraint added; ENG-CONF-001 revised to recommendation-only; mirror refresh assigned to Claude Code; post-seal reconciliation round added; individual attributability made binding. Remains Draft, mirror only. | COWORK (CTO / Chief of Staff) |
| 2026-08-01 | **Draft 3.** Founder final controls incorporated: D1/D2/D3 retained as the required analytical framework in Founder wording (§3.2); all predictive language removed and a standing neutrality rule added (§0.2, P20); Article VII.5 confined to supporting context with an adjacent-finding rule (§3.3); mandatory T1–T6 evidence threshold added for "already conformant" (§7.1); execution baseline added — same pinned commit, isolated worktrees, no uncommitted working tree, recorded metadata, seal-before-peer-access (§5.1); mirror refresh made blocking on final approval and canonical application, with `git show HEAD:<path>` export method and source commit SHA in the manifest (§14.1); COWORK revalidation checks R1–R8 added (§14.2); ENG-CONF-001 recommendation-only status retained and tightened (§9). Remains Draft, mirror only. Not applied to canonical. | COWORK (CTO / Chief of Staff) |
| 2026-08-01 | Governance-mirror refresh completed from pinned canonical commit `6d5d042`; six governance files plus `EXECUTION_BOARD.md` verified identical. COWORK revalidation checks R1–R8 passed; all quotation, version, authority, section, and cross-reference checks clear. | COWORK (CTO / Chief of Staff) |
| 2026-08-01 | **Founder Approved.** Draft 3 approved as the final authoritative task specification and authorized for canonical application. Approval of an execution obligation, not ratification of an Executive Board Decision. Version unchanged. Review status: Not Executed. Approval metadata applied to the mirror copy only; no analytical or procedural text altered. | Mubarak, Founder and CEO of NAWA |