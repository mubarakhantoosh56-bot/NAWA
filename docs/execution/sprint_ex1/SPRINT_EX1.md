# SPRINT EX-1 — Executive Decision Support

**Status:** Active. Founder-activated 2026-07-08.
**Duration:** 2 working weeks per EBD-002 §9.1.
**Sprint Type:** Executive Intelligence quality Sprint. Runtime preserved.
**Reviewed and refined by:** Aboura (CPO).

---

## Goal

> Transform NAWA's Executive Brief into a true Executive Decision Support document.

## Scope

Improve Executive Brief quality along Executive Decision Support dimensions: Executive Brief Experience, Executive Assessment (Executive Thinking), three-dimensional Business Impact (Operational / Financial / Strategic), Executive Actions quality with priority, Statement Traceability, Confidence Explanation.

**Poultry is the validation ground; the language is the deliverable.**

This Sprint establishes the Executive Decision Support language of the NAWA platform. The Executive Brief structure, Business Impact Framework, Executive Actions Taxonomy, and Executive Brief Design Principles produced this Sprint become reusable across Finance, Sales, HR, Manufacturing, Warehousing, and every future operational domain.

## Success Criteria

- Executive Brief operates on the eight-section structure: Executive Summary → Findings → Executive Assessment → Business Impact → Executive Actions → Confidence → Missing Evidence → Recommended Company Inputs.
- Every brief carries an **Executive Assessment** answering the executive's first question: *"What should the CEO care about first, and why?"* Executive prioritization, not AI reasoning.
- Every finding carries **Business Impact** across three dimensions: Operational, Financial (Unknown when unavailable), Strategic.
- Every **Executive Action** is specific, actionable, time-oriented where applicable, connected to supporting evidence, connected to expected business outcome, and carries a priority (🔴 Critical / 🟠 High / 🟡 Medium / 🔵 Low).
- Confidence carries a plain-language explanation referencing the specific evidence gaps captured by the MVP Evidence Policy.
- The Business Impact Framework v1 and Executive Actions Taxonomy v1 are documented at platform-level abstraction — Dairtna is the first instantiation, not the target definition.
- **A CEO can understand the Executive Brief in under 60 seconds.**
- One worked side-by-side: a real Jannat Al-Firdaws brief re-generated under the new experience alongside the pre-Sprint version.

## Exit Criteria

Sprint exits successfully when, in order:

1. All P0 tasks complete and reviewed against their success criterion.
2. All five Sprint Deliverables produced.
3. At least one end-to-end brief produced under the new experience on real Jannat data.
4. Executive Report filed with the six KPIs plus Documentation Debt supporting metric per EBD-002 §16.
5. **Founder Acceptance Test passed.** Founder is presented with the new brief on real data and formally confirms it meets the Sprint Goal on Executive Decision Support. Failing the Founder Acceptance Test means the Sprint does not exit and the retro identifies the specific gap for Sprint EX-2 remediation.

## Tasks

| # | Task | Priority | Owner Lead | Why | Benefit | Risk |
|---|---|---|---|---|---|---|
| 1 | Executive Brief Experience — design the complete experience: reading flow, information hierarchy, section ordering, executive readability, decision support experience | P0 | Aboura | Objective is a decision-support experience, not a template | Foundation for all other tasks | Requires Aboura judgment on executive reading behavior |
| 2 | Implement eight-section structure at Executive Intelligence — Executive Brief v2 Foundation | P0 | Engineering (structure/rendering/binding) + Aboura (language/logic) | Section-level restructuring delivers the surface Aboura's experience targets | Trust surface — executive sees decision-support structure | Some existing content may not fit cleanly into new sections |
| 3 | Executive Thinking → Executive Assessment section — answer "What should the CEO care about first, and why?" as executive prioritization | P0 | Aboura | Executive prioritization is the first thing an executive needs | Elevates brief from data-reporting to executive orientation | Requires Aboura judgment on "care about first" for Dairtna |
| 4 | Three-dimensional Business Impact attribution — Operational, Financial (Unknown if unavailable), Strategic (executive context, not prediction) | P0 | Aboura | Executive decides based on impact across dimensions | Executive compares items on rich impact axis; framework reusable across domains | Financial often Unknown at Dairtna scope; Strategic risks speculation |
| 5 | Executive Actions Taxonomy and Quality — specific, actionable, time-oriented, connected to evidence and outcome, priority (🔴/🟠/🟡/🔵) | P0 | Aboura | Actions must support execution, not description | Executive receives directly actionable output with execution order pre-computed | Distinction between action, recommendation, and data-request must stay clean |
| 6 | Statement Traceability Discipline at Executive Intelligence | P1 | Engineering | EI contract already prohibits statements without evidence trace | Delivers on "remove unsupported statements" directive | Traceability check may reveal upstream trace gaps — Founder-escalated blocker |
| 7 | Confidence Explanation Upgrade | P1 | Aboura + Engineering | Current confidence is a level; users need to know why | Confidence becomes actionable | Writing quality problem; consumes Aboura time |

**Deferred to Sprint EX-2:** Executive Brief Quality Rubric v1.

## Deliverables

| # | Deliverable | Owner | Gate |
|---|---|---|---|
| 1 | Executive Brief v2 — the working brief operating on the new eight-section structure, on real Jannat data | Engineering + Aboura | Founder Acceptance Test |
| 2 | Business Impact Framework v1 — three-dimensional attribution model (Operational, Financial, Strategic), documented at platform-agnostic abstraction with Dairtna instantiation as first example | Aboura | CTO review + Founder approval |
| 3 | Executive Actions Taxonomy v1 — specification for what an Executive Action is (form, evidence link, outcome link, priority levels), documented at platform-agnostic abstraction with Dairtna instantiation as first example | Aboura | CTO review + Founder approval |
| 4 | Founder Approved Executive Brief — a real Jannat brief that has passed the Founder Acceptance Test | Engineering + Aboura | Founder Acceptance Test |
| 5 | Executive Brief Design Principles v1 — design philosophy underneath every Executive Brief; principles including Executive First, Evidence First, Business Impact First, Action Oriented, Confidence Transparency. Platform-scale philosophy inheritable across future domains | Aboura | CTO review + Founder approval |

## Risks

- **Sprint capacity — highest priority.** Aboura design front-load Days 1–3 for Tasks 1, 3, 4, 5. If Aboura bandwidth is thin, PMO recommendation: defer Executive Actions Taxonomy (Task 5 / Deliverable 3) to Sprint EX-2 as first drop item.
- **Platform generality vs. MVP specificity.** Deliverables 2, 3, 5 are meant reusable across domains yet validated on Dairtna. Risk of over-generalizing at MVP produces framework that doesn't fit Dairtna; over-specializing produces framework that doesn't extend. Mitigation: v1 documents core structure at platform abstraction with Dairtna as first instantiation and explicit Extension Points.
- **Founder Acceptance Test outcome.** Concentrates schedule risk at exit. Mitigation: mid-Sprint informal draft reviews.
- **Task 6 blocker surface.** Traceability may reveal upstream trace gaps. Escalated immediately per Executive Operating Rule 8. Not absorbed into Sprint.
- **Scope discipline under time pressure.** Named the moment it appears per Executive Operating Rule 9. No silent compression.

## Out of Scope

- Any change to CompanyInput, Company Input Classifier, NCO Lite, KAE, OIE, OCE, NCE Lite, or OME Foundation implementations. Runtime preserved.
- Any change to reasoning outputs — hypotheses, recommendations, or confidence values produced by NCE Lite.
- MVP Evidence Policy semantic changes.
- Architecture Freeze v1.0 amendments (Tier 1 or Tier 2 unfreeze).
- Contract changes to any Runtime Component.
- New Runtime Components (per EBD-003 §13 and Executive Operating Rule 5).
- Executive Brief Quality Rubric — deferred to Sprint EX-2.
- Domain instantiation of Deliverables 2, 3, 5 for departments beyond Dairtna — v1 platform authoring only; future-department instantiation is separate work.
- Executive language / vocabulary polish beyond confidence explanation and taxonomy-required action language — deferred to Sprint EX-2 candidate.
- Filing Decision Log entries for EBD-001 through EBD-004 — Documentation Debt tracked per Executive Operating Rule 2.
- COWORK v2.0 authoring — Documentation Debt.
- CURRENT_STATE.md amendment — Documentation Debt.

## Founder Decisions (Activation)

1. Sprint EX-1 activated as CPO-amended and refined.
2. Sprint started 2026-07-08.
3. Aboura allocated as Product/CPO lead for: Executive Brief Experience, Executive Assessment, Business Impact Framework, Executive Actions Taxonomy, Executive Brief Design Principles.
4. Founder Acceptance Test format: mid-Sprint informal draft review + end-Sprint formal test on real Jannat data.
5. Blocker escalation: any traceability gap or unsupported statement issue → directly to Founder and Aboura. **Do not silently solve by changing runtime or reasoning pipeline.**
6. Executive Actions = actions the executive or management team should take. Recommended Company Inputs = additional data NAWA needs to improve confidence.
7. Platform generality confirmed. Dairtna is validation ground; Executive Decision Support language is platform deliverable.
8. Runtime boundaries confirmed. Do not modify CompanyInput, Classifier, NCO Lite, KAE, OIE, OCE, NCE Lite, or OME Foundation. Do not redesign architecture. Do not add engines. Focus only on Executive Intelligence quality.

## Sprint-Wide Ownership Rule

Engineering owns Structure / Rendering / Binding. Aboura owns Executive language / Section logic / Executive wording / Business framing. **Engineering never defines Executive language.**

## Implementation Principle

**Prefer improvement over replacement.** Never rebuild something that can be improved.
