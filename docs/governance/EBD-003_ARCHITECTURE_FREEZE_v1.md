# Executive Board Decision #003 — Architecture Freeze v1.0

**Status:** Ratified by Founder as Executive Board Decision #003. Tier 1 active; Tier 2 active per EBD-004.
**Document version:** 1.1
**Architecture Freeze version:** v1.0
**Category:** Governance (architectural constraints applied under authority granted by EBD-002).
**Subordinate to:** NAWA Reasoning Constitution v1.0 (ratified 2026-07-31). Where this decision conflicts with a Constitutional article, the Constitution prevails and this decision is amended.
**Scope:** The NAWA runtime architecture as it exists at the time of ratification — the nine Runtime Components, their order, the runtime philosophy that governs them, and the Company Input Principle they serve. Applies to all NAWA implementation work during the Runtime Validation Phase and until formally unfrozen by subsequent EBD.
**Non-scope:** Contract-level detail of each Runtime Component (deferred to EBD-004 Engine Definitions, which activates Tier 2 of this freeze); documentation format (EBD-001); role authority (EBD-002); product direction; legal/financial governance.
**Owner:** Founder & CEO (Mubarak).
**Approval authority:** Founder & CEO.
**Effective date:** 2026-07-03.
**Last updated:** 2026-08-01.
**Supersedes:** No prior architecture freeze; establishes Freeze v1.0.

---

## 1. Ratification and Scope

This document is Executive Board Decision #003. It ratifies the NAWA Architecture Freeze v1.0 — the boundary that protects Runtime Validation Phase from architectural churn.

Governance (EBD-002) precedes constraints. This freeze is a constraint, executed under the authority defined in EBD-002 §12 (Architecture Freeze Protection) and §4 (role authority). Nothing in this document creates new authority; it applies existing authority to a specific architectural surface.

The freeze is three-tier. Tier 1 activates on ratification of this EBD. Tier 2 activates on ratification of EBD-004 (Engine Definitions). Tier 3 is an explicit non-freeze — it names what remains flexible so that implementation velocity is not confused for architectural drift.

---

## 2. Purpose of the Freeze

The Runtime Validation Phase requires that the architecture stop moving. It does not require that implementation stop moving.

Every hour spent debating whether to add a tenth component, rename a component, or re-order the pipeline is an hour not spent validating the current architecture against real Company Input. The freeze exists so that validation is measured against a stable target.

Concretely, the freeze delivers three benefits:

1. **Convergence.** Runtime Validation results are comparable across Sprints because the thing being validated doesn't change underneath.
2. **Focus.** New engine ideas, however interesting, are deferred until MVP validation completes.
3. **Trust.** Downstream documentation, product decisions, and engineering work can cite the frozen architecture as stable ground.

The freeze is not a signal that the architecture is final. It is a signal that the architecture is *stable enough to validate*.

---

## 3. Contract First Principle

**Architecture freezes contracts, not implementations.**

This is the constitutional principle that governs the freeze. It is added as a load-bearing NAWA principle alongside Product First (EBD-002 §13), Dogfooding (§14), and Constructive Challenge (§15).

### 3.1 What Contract First means

- **Contracts are what components promise to consume and produce, and how they bound with other components.** These are architectural.
- **Implementations are how components fulfill those promises internally.** These are engineering.
- **Freezing contracts protects behavior at the boundary.** Freezing implementations would ossify code and prevent normal engineering hygiene (refactoring, optimization, internal restructuring).
- **A change is architectural if it changes contract**; it is engineering if it does not. This is the tie-breaker for whether the freeze applies.

### 3.2 Corollaries

- Refactoring internal code is not architectural. It is engineering.
- Renaming an internal class is not architectural. Renaming a Runtime Component is.
- Performance improvements that don't change what a component promises are not architectural.
- Adding a new module inside a component is not architectural. Adding a new component with its own boundary is.
- Changing UI representations or internal APIs is not architectural. Changing what leaves a component into the runtime pipeline is.

### 3.3 Enforcement

Every proposed change is triaged against this principle by the CTO. The triage outcome — architectural or engineering — determines which authority applies (CTO+Founder for architectural; AI Engineering Team for engineering, per EBD-002 §5 and §12).

### 3.4 What Contract First is not

- It is not permission to change contracts freely. Contract changes go through the unfreeze process (§17).
- It is not permission to be sloppy about internal design. Engineering quality is enforced by Technical Debt tracking (EBD-002 §16.5) and peer review, not by the freeze.
- It is not an escape hatch. A change dressed as "internal implementation" that actually crosses a component boundary is a freeze breach and is caught in triage.

---

## 4. Runtime Independence Principle

**Every Runtime Component must be independently replaceable as long as its contract remains intact.**

This principle is the operational complement to Contract First (§3). Contract First says the freeze protects contracts, not implementations. Runtime Independence says the architecture must be *built such that* implementations can be replaced without breaking anything upstream or downstream.

### 4.1 What Runtime Independence means

- **Components do not depend on the internals of adjacent components.** A component consumes only what its contract declares it consumes and produces only what its contract declares it produces. Implementation details of neighboring components are opaque.
- **Replacing a component is a legitimate architectural exercise.** Swapping OIE's implementation, migrating NCO Lite to a new model, or rebuilding KAE against a different substrate must all be possible without touching anything outside that component's boundary.
- **A component that requires implementation-level coupling to work is architecturally malformed.** If replacing a component in isolation is impossible, the coupling is a bug in the architecture, not a feature of the implementation.

### 4.2 Corollaries

- Components communicate through their declared contracts only. Private channels, shared internal state, or cross-component knowledge of internals are prohibited.
- Testing a component in isolation must be possible using only its contract. If a test requires standing up an adjacent component's real implementation, the boundary is leaking.
- Provider independence in the AI Engineering Team (EBD-002 §4.4 technology-agnostic principle) has an architectural analogue: implementation independence in Runtime Components. Both principles come from the same discipline — the org and the runtime are both designed to survive replacement of any single element.

### 4.3 Enforcement

- Any proposed component design that requires knowledge of another component's internals to work is rejected by the CTO at architecture review.
- Any implementation change that introduces cross-component coupling below the contract boundary is a Contract First violation (§3) and is caught in triage.
- Independence is verified periodically as part of Architecture Health KPI (EBD-002 §16.4). A component that has not been independently replaceable for multiple Sprints is flagged.

### 4.4 What Runtime Independence is not

- It is not a requirement to actually replace components frequently. It is a requirement that replacement *be possible*.
- It is not permission to change contracts freely under the guise of "independence." Contract changes remain governed by the freeze.
- It is not orthogonality for its own sake. Components are independent because they must be replaceable, not because independence is aesthetically preferred.

---

## 5. Evolution Over Reinvention Principle

**NAWA evolves by improving existing Runtime Components rather than introducing new ones during MVP.**

This principle frames "No New Engines During MVP" (§13) positively. The invariant says what is prohibited; this principle says what is expected.

### 5.1 What Evolution Over Reinvention means

- **The discipline during Runtime Validation Phase is to make the nine Runtime Components better, not to add a tenth.** Improvement of an existing component is unbounded; addition of a new component is prohibited (§13).
- **Perceived need for a new component is treated as a signal that an existing component needs work.** Nine times out of ten, the "new component" is a responsibility that belongs inside an existing component, or a boundary refinement between two existing components. The tenth time is a genuine Freeze v2.0 candidate — but that determination waits until Runtime Validation Phase completes.
- **Reinvention is expensive.** Each new component adds validation surface, contract surface, documentation surface, review surface, and testing surface. Improving an existing component amortizes all of that against work already done.

### 5.2 Corollaries

- Every "we need a new engine" proposal is first reframed as a question: "which existing component's responsibilities does this belong to, and why can't we extend it?"
- A component that has grown too complex to extend is a signal to refactor within its boundary (Tier 3, no freeze process needed), not to split.
- Cross-cutting concerns (logging, observability, tenant isolation) are handled by internal infrastructure, not by new Runtime Components.

### 5.3 Enforcement

- The CTO defaults new-component proposals to rejection during Runtime Validation Phase (§13.2).
- Founder unfreeze default during Runtime Validation Phase is also rejection (§13.3).
- The Sprint retro Architecture Health section (EBD-002 §16.4) counts "reframed-as-improvement" outcomes as a positive signal: a proposal that turned into an improvement of an existing component is a healthier architectural conversation than one that produced a new component.

### 5.4 What Evolution Over Reinvention is not

- It is not permission to bloat existing components indefinitely. Components have coherent scope; work that genuinely does not belong is captured as a Freeze v2.0 candidate for later, not stuffed into an existing component to avoid the freeze.
- It is not an absolute prohibition on new components across NAWA's lifetime. It is a Runtime Validation Phase discipline. Freeze v2.0 may open new-component work formally after validation completes.
- It is not a critique of ambition. New engines are welcome as candidates; they are prohibited as MVP scope.

---

## 6. The Three-Tier Freeze Model

The freeze has three layers. Each layer defines what is frozen, what remains flexible, and when the layer activates.

| Tier | What it covers | Activation | Status |
|---|---|---|---|
| **Tier 1** | Runtime component order, runtime philosophy, Company Input Principle, Runtime Component names, No New Engines During MVP invariant | On ratification of this EBD | Frozen |
| **Tier 2** | Component contracts: responsibilities, inputs, outputs, boundaries, non-responsibilities | On ratification of EBD-004 (Engine Definitions) | Pending |
| **Tier 3** | Implementation details: refactoring, optimization, internal APIs, UI representations, internal classes, performance work | Never — Tier 3 is explicit non-freeze | Flexible |

Tier 1 without Tier 2 is a **naming and structural freeze** — the pipeline shape is protected, but the internal contracts of each component are not yet formalized. Once Tier 2 activates, the freeze becomes a **contract freeze** — the fuller protection the architecture ultimately needs.

Tier 3 is stated as a positive non-freeze so that engineering velocity is preserved and no ambiguity exists about whether normal engineering work requires unfreeze process. It does not.

---

## 7. Tier 1 — Runtime Architecture Freeze (Active)

Tier 1 activates on ratification. The following are frozen:

### 7.1 Runtime component order

The nine Runtime Components execute in a fixed order. Reordering, inserting a new component into the sequence, removing a component, or bypassing a component in the pipeline is a Tier 1 freeze breach.

The order:

```
CompanyInput
    ↓
Company Input Classifier
    ↓
NCO Lite
    ↓
KAE
    ↓
OIE
    ↓
OCE
    ↓
NCE Lite
    ↓
Executive Intelligence
    ↓
OME Foundation
```

### 7.2 Runtime philosophy

The runtime is governed by the Company Input Principle (§11), Truth Before Reasoning, Evidence Before Conclusions, and Company Brain Never Overrides Facts (per NAWA project principles as stated by the Founder). These philosophical positions govern how components are permitted to behave, regardless of their internal implementation. They are frozen.

### 7.3 Company Input Principle

Users interact with Company Inputs only. The runtime consumes Company Inputs; the executive layer produces decisions and memory grounded in those inputs. Users do not interact with intermediate representations, engine outputs, or component internals. The Company Input Principle is the frozen contract between the user and the runtime.

### 7.4 Runtime Component names

Each of the nine components carries a name. Renaming a component is a Tier 1 freeze breach. Names include their variants (e.g., "NCO Lite" as distinct from a future "NCO" — the "Lite" suffix is part of the frozen name).

### 7.5 No New Engines During MVP

No new Runtime Components — engine, classifier, output layer, foundation, or otherwise — may be added to the runtime pipeline during the Runtime Validation Phase. This invariant is Tier 1 frozen and is the most common architectural drift vector, so it receives dedicated enforcement (§13).

### 7.6 Not frozen at Tier 1

The following are explicitly **not frozen** at Tier 1 and remain open until Tier 2:

- Each component's specific responsibilities.
- Each component's inputs and outputs at the interface level.
- Each component's boundaries with adjacent components.
- Each component's explicit non-responsibilities.

Any of the above may be evolved in EBD-004. Once EBD-004 ratifies, they move to Tier 2 frozen.

---

## 8. Tier 2 — Contract Freeze (Pending EBD-004)

Tier 2 activates on ratification of EBD-004 (Engine Definitions). Until then, contracts are described in existing documentation (COWORK v2.0 when ratified; intermediate specs as they emerge) but are not frozen.

### 8.1 What Tier 2 will freeze

Once activated, Tier 2 freezes the following for each Runtime Component:

- **Responsibilities** — what the component does.
- **Inputs** — what the component consumes at its boundary.
- **Outputs** — what the component produces at its boundary.
- **Boundaries** — what the component does not do; the sharp edge between it and the next component.
- **Non-responsibilities** — explicit statements of scope negation, so component roles are not ambiguous.

### 8.2 Why Tier 2 is deferred

Contract-level freeze requires that contracts exist and be reviewed. EBD-004 will define these contracts and route them through review before ratification. Freezing contracts that have not been reviewed would encode error at the architectural level. The two-step model (Tier 1 now, Tier 2 after EBD-004) is deliberate.

### 8.3 Interim behavior

Until Tier 2 activates:

- Component contracts may be refined through architectural review under CTO authority (per EBD-002 §5).
- Refinements should aim toward EBD-004 rather than proliferate specs.
- The CTO is responsible for keeping refinements consistent and preventing pre-EBD-004 divergence from making EBD-004 harder to write.

---

## 9. Tier 3 — Implementation Freedom (Explicit Non-Freeze)

Tier 3 exists to remove all ambiguity about what remains flexible. It is the positive statement of what the freeze does not touch.

### 9.1 What remains flexible

The following are outside the freeze at every tier, provided contracts (Tier 2, once active) remain intact:

- **Refactoring.** Internal code restructuring within a component.
- **Optimization.** Performance improvements that preserve contract behavior.
- **APIs internal to a component.** Function signatures, class methods, module boundaries within a Runtime Component.
- **UI.** Presentation changes, visual design, layout, styling, interaction patterns.
- **Internal classes.** New classes added inside a component; renames of internal classes; changes to internal class hierarchies.
- **Performance improvements.** Latency, memory, throughput improvements that leave contract behavior identical.
- **Testing.** Adding, removing, restructuring tests.
- **Instrumentation.** Logging, metrics, tracing internal to a component.
- **Data storage details.** Schema evolution within a component's owned data, so long as the contract at the boundary is preserved.

### 9.2 The Tier 3 discipline

Tier 3 is not permission to be careless. Implementation quality is governed by:

- Technical Debt tracking (EBD-002 §16.5).
- Peer review (EBD-002 §4.4, amended: CTO does not substitute).
- Test coverage standards.
- Documentation obligations (EBD-001 §6.1: code changes without documentation updates are incomplete).

Tier 3 says these standards apply *without invoking the freeze process*. They are enforced by ordinary engineering governance, not by architectural gatekeeping.

### 9.3 The contract-preservation test

The determining question for any change is: **does this change what a component promises at its boundary?**

- **No** → Tier 3, engineering authority per EBD-002 §5.
- **Yes** → Tier 2 (once active) or Tier 1 (component order/name/philosophy). Freeze process applies.

The CTO performs this triage on request from the AI Engineering Team, or proactively when reviewing proposed changes.

---

## 10. The Nine Runtime Components

The runtime consists of nine Runtime Components in fixed order. This section names them and states their category. Contract-level definition (what each does at the boundary) is deferred to EBD-004.

The term "engine" is reserved for components that transform inputs into structured outputs through domain reasoning. Not every Runtime Component is an engine — some are data models, classifiers, output layers, or memory foundations. The naming "Nine Runtime Components" (not "Nine Engines") reflects this.

| # | Name | Category (provisional; ratified at Tier 2) |
|---|---|---|
| 1 | **CompanyInput** | Data model / entry point — the primary entity that enters the runtime and represents user or system input |
| 2 | **Company Input Classifier** | Classifier / router — categorizes and routes incoming CompanyInput to downstream engines |
| 3 | **NCO Lite** | Engine — MVP-scoped version of the NCO family |
| 4 | **KAE** | Engine |
| 5 | **OIE** | Engine — OIE was first validated through the Jannat Al-Firdaws (Dairtna) MVP; the domain-specific work in `docs/nawa_brain/DAIRTNA_OPERATIONAL_INTERPRETATION.md` is where OIE received its first real-world validation, not its origin |
| 6 | **OCE** | Engine |
| 7 | **NCE Lite** | Engine — MVP-scoped version of the NCE family |
| 8 | **Executive Intelligence** | Output layer — the surface at which decisions become available to the CEO/executive user |
| 9 | **OME Foundation** | Memory foundation — the institutional memory substrate under the runtime; consumes and preserves outputs |

**Note on category provisionals:** The category column is CTO-assigned based on the naming convention and the pipeline position. Where a category is uncertain (KAE, OCE), it is left as "Engine" pending EBD-004 confirmation. If EBD-004 reclassifies a component (e.g., KAE is actually a foundation, not an engine), the reclassification is not a Tier 1 breach — only the name is Tier 1 frozen, not the category label. Categories move to Tier 2 frozen on EBD-004 ratification.

---

## 11. Company Input Principle (Frozen at Tier 1)

The Company Input Principle is one of the frozen elements of Tier 1 and is stated here in full because the freeze depends on it.

### 11.1 Statement

- **Users interact with Company Inputs only.** A user contributes a Company Input into the runtime; a user receives Executive Intelligence back. The internal engines, classifiers, and foundations do not appear in the user-facing surface.
- **The runtime consumes Company Inputs.** All engine reasoning begins from a Company Input. No engine reasons from raw undifferentiated data outside the CompanyInput model.
- **The runtime produces institutional understanding, executive decisions, and institutional memory grounded in Company Inputs.** Outputs of the runtime are traceable to specific inputs.

### 11.2 Enforcement

- Any product design that surfaces intermediate engine outputs, engine names, or component internals to end users violates the Principle. Aboura enforces at product review time (EBD-002 §13 Product First and §5 approval).
- Any engine that reasons outside CompanyInput context violates the Principle. The CTO enforces at architecture review time.
- Any documentation that describes the product to a user in terms of engines rather than Company Inputs violates the Principle. The CTO enforces at documentation review.

### 11.3 Relationship to the freeze

The Company Input Principle is frozen at Tier 1. It cannot be revised through architectural change alone; revision is a governance-level EBD, because the Principle is what defines what NAWA is.

---

## 12. Runtime Philosophy (Frozen at Tier 1)

The runtime is not merely a pipeline of components. It is a pipeline governed by philosophy — commitments about how components must behave regardless of their internal design.

### 12.1 Truth Before Reasoning

Components extract, structure, and validate the truth of a Company Input before any component reasons about it. Reasoning that runs ahead of truth extraction is prohibited at the runtime level. This is the same philosophy that drove the Dairtna interpretation layer's insistence on grounding before escalation (documented in `docs/nawa_brain/DAIRTNA_OPERATIONAL_INTERPRETATION.md`).

### 12.2 Evidence Before Conclusions

A conclusion drawn by a downstream component must be traceable to specific evidence produced by an upstream component. Ungrounded conclusions — those that cannot be tied back to a Company Input via the pipeline — are prohibited.

### 12.3 Company Brain Never Overrides Facts

Institutional memory (OME Foundation) may inform reasoning but may never contradict a validated Company Input. When memory and current input disagree, the current input is treated as the current truth; memory is updated to reflect the discrepancy, not the other way around.

### 12.4 These philosophies are frozen

These are not suggestions. They are Tier 1 frozen. A component that violates any of the three is a freeze breach regardless of what its contract says. A component that requires violation to work is architecturally malformed and must be re-designed.

---

## 13. No New Engines During MVP (Frozen at Tier 1)

The single most common architectural drift vector is the addition of new components disguised as necessary. This invariant exists because that vector is real and the freeze must actively resist it.

### 13.1 The invariant

No new Runtime Components may be added to the runtime pipeline during the Runtime Validation Phase. This applies regardless of:

- How small the proposed component seems.
- How useful it appears.
- Whether it "would have made things easier."
- Whether it duplicates work currently distributed across other components.

### 13.2 Enforcement

- Any proposal to add a Runtime Component is a freeze-breaking change (Tier 1) and requires unfreeze per §17.
- The CTO is required to reject proposals that dress a new component as an "internal helper," a "utility," or "just a small classifier." The category matters less than the presence of a new named component in the runtime pipeline.
- The Founder is the only party who can unfreeze. Aboura's product interest, the Engineering Team's implementation preference, and the CTO's architectural instinct are not sufficient to bypass this rule.

### 13.3 Exceptions during Runtime Validation Phase

There are none. If a legitimate need for a tenth component emerges during Runtime Validation Phase, it is documented as a candidate for Freeze v2.0 (post-Runtime Validation Phase). It does not join the runtime during the current phase.

### 13.4 What is not covered

- Internal modules, classes, and helpers within an existing Runtime Component are not "new engines." They are Tier 3 implementation freedom (see §9).
- Splitting an existing component into two components is a new engine (freeze breach).
- Merging two components into one is a runtime-order change (freeze breach).
- Replacing a component with a differently-named component is a rename (freeze breach on the name).

---

## 14. Stable, Configurable, and Flexible Architectural Elements

Every architectural element in NAWA is classified as **Stable**, **Configurable**, or **Flexible**. This classification is normative — it tells engineers, product, and reviewers whether a proposed change is subject to the freeze, subject to configuration governance, or freely evolvable through ordinary engineering.

The three categories are exhaustive and non-overlapping. Every architectural element belongs to exactly one. Elements whose category is genuinely ambiguous are triaged under §14.4.

### 14.1 Stable elements (subject to the freeze)

| Element | Tier | Rationale |
|---|---|---|
| Runtime component order | Tier 1 | Reordering breaks pipeline semantics |
| Runtime Component names | Tier 1 | Renames break every document that cites the name |
| The nine Runtime Components as a set | Tier 1 | Adding or removing changes the architecture, not the implementation |
| Company Input Principle | Tier 1 | Defines what NAWA is |
| Runtime philosophies (Truth Before Reasoning, etc.) | Tier 1 | Governs component behavior regardless of implementation |
| No New Engines During MVP | Tier 1 | Protects Runtime Validation from drift |
| Component responsibilities | Tier 2 (pending EBD-004) | Cross-component behavior depends on stable responsibility split |
| Component inputs at the boundary | Tier 2 (pending EBD-004) | Contract change breaks upstream components |
| Component outputs at the boundary | Tier 2 (pending EBD-004) | Contract change breaks downstream components |
| Component boundaries | Tier 2 (pending EBD-004) | Boundary change is architectural |
| Component non-responsibilities | Tier 2 (pending EBD-004) | Non-scope preserves separation of concerns |

### 14.2 Configurable elements (tunable within governed policy)

**Configurable elements are architecturally recognized as tunable parameters — not implementation-free, not architecturally locked, but subject to explicit configuration policy.** Changing a configurable element does not require freeze process, but it also is not free-for-all engineering. It is governed by whichever document owns the policy for that element (typically Company Brain docs for domain thresholds, Product Documents for user-facing feature flags, and Runtime Documents for operational parameters).

| Element | Governing policy | Rationale |
|---|---|---|
| Domain thresholds (e.g., Dairtna mortality bands per `DAIRTNA_OPERATIONAL_INTERPRETATION.md` §4) | Company Brain doctrine; tuned via field-validation workshop | Values change per tenant, per season, per breed; the architecture recognizes tunability |
| Provisional-flag status on interpreter output | Company Brain doctrine; flipped on workshop confirmation | Confirmed vs. provisional is a governed transition, not a code change |
| Feature flags per company or per phase | Product Documents; toggled by Aboura or delegated per policy | Tenant differentiation without contract change |
| Tenant-specific behavior overrides | Product Documents + Company Brain per case | Multi-tenancy requires tuning without architecture change |
| Runtime timeouts, retry policies, batch sizes | Runtime Documents; tuned by AI Engineering Team within policy | Operational tuning against real load |
| Environment variables (dev / stage / prod) | Runtime Documents | Environment differentiation |
| Company-specific hypothesis library (per Phase 2A grounding) | Company Brain doctrine | Domain content varies per company |
| Model selection within an engine (which underlying AI system a component uses) | Runtime Documents; per technology-agnostic principle (EBD-002 §4.4) | Provider independence is architecturally required |

**Configurable is not Flexible.** A configurable element has a governing policy; changing it requires following that policy (workshop, product review, runtime approval, etc.), but does not require freeze unfreeze. Documentation of every configurable element must include its governing policy — undocumented configurable is Documentation Debt (EBD-002 §16.7).

**Configurable is not Stable.** Configurable elements are expected to change over time. Their values are not architectural; the *fact of tunability* is. Freezing a value would break tenant differentiation; freezing that the value *exists as a tunable* is what Tier 2 will protect.

### 14.3 Flexible elements (outside the freeze)

| Element | Rationale |
|---|---|
| Internal code structure | Refactoring is engineering, not architecture |
| Internal APIs within a component | Below the contract boundary |
| Performance optimizations | Preserve behavior; not architectural |
| UI representations | Presentation layer, not runtime layer |
| Data storage details (schema evolution within a component) | So long as contract at the boundary is preserved |
| Test structure | Testing is engineering, not architecture |
| Instrumentation (logging, metrics, tracing) | Observability is engineering |
| New internal classes or helpers within a component | Below the boundary |

### 14.4 Ambiguous cases

When a change appears to sit on the boundary — an interface refinement that is arguably contract, a helper class that arguably has its own boundary — the CTO triages under the Contract First Principle (§3). The triage is written into a Decision Log entry so that the boundary line becomes clearer over time.

---

## 15. Evolution Without Violation

The freeze is not a stagnation contract. NAWA continues to evolve — component by component, sprint by sprint — without unfreezing anything. This section names the six mechanisms by which evolution proceeds inside the freeze.

The freeze protects against drift. It does not protect against improvement. If a proposed change fits any mechanism in §15.1–§15.6, it is compatible with the freeze and requires no unfreeze process.

### 15.1 Component-internal evolution (Tier 3)

Refactoring, optimization, and internal restructuring within any Runtime Component are always permitted. Per §9 Tier 3. Ordinary engineering process applies (peer review, testing, technical documentation). No CTO gatekeeping beyond ordinary architectural sanity.

### 15.2 Component replacement under contract preservation (Runtime Independence)

Per §4 Runtime Independence, any Runtime Component may be entirely rewritten, re-implemented on a different substrate, or swapped for a different underlying model, so long as its contract remains intact. This is not architecture change; this is architecture doing its job. Component replacement is the strongest form of evolution the freeze protects against — and permits.

### 15.3 Configurable-element tuning (Governed by policy, not by freeze)

Per §14.2, tuning configurable elements — thresholds, feature flags, per-tenant behavior, runtime parameters, model selection within a component — is evolution without violation. Each configurable has a governing policy that must be followed, but that policy is not the freeze.

### 15.4 Backward-compatible contract additions (once Tier 2 is active)

Per §18.4, adding an optional output, an optional input, or a new non-breaking output type to a component's contract is permitted without Tier 2 unfreeze once Tier 2 activates. This is the primary controlled channel for contract evolution. The addition is approved by the CTO as an ADR referencing the affected component in EBD-004. Downstream consumers are not required to consume the addition; they must not break under it.

### 15.5 Component-internal capability expansion (Evolution Over Reinvention)

Per §5 Evolution Over Reinvention, extending an existing component to handle new operational cases, new domains, or new levels of detail is the preferred form of new capability during Runtime Validation Phase. The extension happens inside the component (Tier 3) and, if it affects contract, follows §15.4 (backward-compatible addition). The result: NAWA absorbs new operational reality without adding new Runtime Components.

### 15.6 Runtime Validation itself

Runtime Validation is evolution of the org's understanding of the runtime. It does not change the runtime; it changes what the org knows about it. Every validation cycle is evolution without violation. Validation results are recorded in Runtime Documents (per EBD-002 §11.2) and feed into Architecture Health and Runtime Health KPIs.

### 15.7 What Evolution Without Violation is not

- It is not permission to break contracts under the guise of "evolution." Breaking contract changes require unfreeze (§17).
- It is not permission to add new Runtime Components under the guise of "component evolution." Adding is not evolving; adding is inventing (§13, §5).
- It is not permission to skip governance. Configurable-element tuning follows its policy; contract additions are ADRs; internal changes still have peer review and testing standards. Evolution is disciplined, not casual.

### 15.8 The evolution question

For any proposed change, the CTO asks: **does this fit one of §15.1–§15.6?**

- **Yes** → evolution without violation. Ordinary governance applies (engineering peer review, ADR if contract-touching, policy governance if configurable). No freeze process.
- **No** → the change is architectural in a way the freeze protects. Unfreeze process applies (§17).

This is the operational tie-breaker. It is the positive statement of what the freeze allows, complementing the negative statements (§13 No New Engines, §17 Unfreeze).

---

## 16. Enforcement Mechanism

Freeze enforcement is per EBD-002 §12.2 with tier-specific extensions.

### 16.1 Triage classification

Every proposed change is classified by the CTO:

- **Within Tier 3 (Implementation Freedom)** — engineering authority under EBD-002 §5 applies; no freeze process invoked.
- **Within Tier 1 or Tier 2 but not breaking** — architectural change within the freeze (i.e., internal refinements consistent with what is frozen); CTO approves via ADR.
- **Tier-adjacent, needs judgment** — CTO writes an ADR articulating the boundary case; Founder reviews at Sprint boundary.
- **Freeze-breaking (any tier)** — unfreeze process (§17) required.

Triage outcomes are written into the Decision Log entry for the proposed change, so the classification pattern accumulates and becomes reference.

### 16.2 Runtime Validation Phase discipline

While Runtime Validation Phase is active:

- Freeze-breaking proposals are especially resisted; the Founder should default to rejection and require the proposer to show why validation cannot proceed without the change.
- Emergency exceptions per EBD-002 §12.5 remain available but are logged and reviewed for pattern.
- The CTO reports every freeze breach attempt in the Sprint retro, whether approved or rejected. This feeds the Architecture Health KPI (EBD-002 §16.4).

### 16.3 Freeze-adjacent engineering

Engineering work on components remains permitted during freeze. What is restricted is architectural change. This distinction is the whole point of the Contract First Principle (§3).

---

## 17. Unfreeze Process

Per EBD-002 §12.4, unfreeze is an EBD. The three-tier structure requires tier-specific unfreeze paths.

### 17.1 Tier 1 unfreeze

Reordering the pipeline, renaming a Runtime Component, adding or removing a component, revising the Company Input Principle, revising a runtime philosophy, or exceptioning No New Engines During MVP:

- Requires a Tier 1 unfreeze EBD.
- Impact review by CTO covers: which downstream documents change, what runtime validation must be re-run, whether Tier 2 contracts remain valid.
- Engineering Team review of implementation feasibility (per EBD-002 §4.4 authority).
- Product review by Aboura for user-facing impact.
- Founder ratification.
- Refreeze immediately — no indefinite open state. A ratified Tier 1 unfreeze produces Freeze v1.1 or v2.0 depending on scope.

### 17.2 Tier 2 unfreeze (once Tier 2 is active)

Revising component responsibilities, inputs, outputs, boundaries, or non-responsibilities:

- Requires a Tier 2 unfreeze EBD.
- Impact review focuses on which adjacent components are affected at the boundary.
- Engineering Team review of contract feasibility.
- Aboura review only if the contract change affects user-facing behavior.
- Founder ratification.
- Refreeze with an updated EBD-004 revision.

### 17.3 Tier 3 does not have an unfreeze

Tier 3 is explicit non-freeze. No unfreeze is required for engineering work; no engineering work triggers unfreeze. The absence of an unfreeze process here is the point.

### 17.4 Emergency exceptions

Per EBD-002 §12.5, the Founder may authorize an emergency freeze exception. The exception is recorded as an EBD after the fact and reviewed at the next Executive Board Meeting. Repeated emergency use is a governance failure and prompts a review of whether the freeze is calibrated correctly.

---

## 18. Boundary Cases and Judgment Calls

Not every proposed change falls cleanly into a tier. This section names the common boundary cases and states the CTO's default triage.

### 18.1 "It's just a wrapper"

**Scenario:** A proposal to introduce a wrapper layer between two existing components, framed as internal implementation.

**Triage:** If the wrapper is inside a single Runtime Component, Tier 3. If the wrapper mediates between two components in the pipeline, it is a new component — Tier 1 freeze breach.

### 18.2 "It's the same component, just split"

**Scenario:** Splitting one Runtime Component into two, arguing the pipeline order is preserved.

**Triage:** Tier 1 freeze breach. The number of components in the pipeline is frozen at nine. Splitting is adding.

### 18.3 "The internal API needs to change to fix a bug"

**Scenario:** An engineering change that touches an internal API within a component.

**Triage:** Tier 3, no unfreeze needed. Internal APIs are below the boundary. The CTO does not need to be consulted for this class of change (though the change may be surfaced as part of Technical Debt reporting).

### 18.4 "The contract needs a new optional field"

**Scenario:** Adding an optional field to a component's output at the boundary.

**Triage:** After Tier 2 is active, **backward-compatible contract additions are permitted without unfreeze**. Adding an optional output field, adding an optional input field, or adding a new output type that does not remove or change any existing output does not require Tier 2 unfreeze — provided no downstream component's behavior breaks under the addition. **Only breaking contract changes require unfreeze**: removing an output, removing an input, changing the semantics of an existing field, or changing a type in a way that breaks a downstream consumer. Backward-compatible additions are approved by the CTO as ordinary architectural refinement, with the amendment recorded as an ADR referencing the affected component in EBD-004. Before Tier 2 is active, all such additions are under CTO ADR discretion regardless of backward compatibility. See §15 for the full evolution framework.

### 18.5 "The component now handles a new type of Company Input"

**Scenario:** A component that previously handled one type of input starts handling a second type.

**Triage:** This is a responsibility change (Tier 2 once active). Before Tier 2, it goes through architectural review as an ADR because it affects the Classifier's routing behavior (§5.1).

### 18.6 "It's just a rename for clarity"

**Scenario:** Renaming a Runtime Component for readability.

**Triage:** Tier 1 freeze breach. Names are frozen. Rename requires Tier 1 unfreeze EBD. Every downstream document that cites the name must be updated as part of the refreeze.

### 18.7 "It's a refactor that will improve maintainability"

**Scenario:** A large-scale internal refactor within a component.

**Triage:** Tier 3, no unfreeze needed. Refactor magnitude is not a freeze consideration; freeze is about boundary preservation, not code churn. However, large refactors may qualify for Documentation obligations per EBD-001 §6.1 (technical documentation update accompanying the change).

---

## 19. Relation to Other Documents

This EBD interacts with, and is consistent with, the following documents:

- **`docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md` (EBD-001)** — this document is authored under EBD-001's rules for governance documents, versioning, and lifecycle.
- **`docs/governance/EBD-002_GOVERNANCE_MODEL.md`** — this document exercises the authority granted in EBD-002 §12 (Architecture Freeze Protection). The unfreeze process here (§17) is the tiered extension of EBD-002 §12.4.
- **Forthcoming `docs/governance/EBD-004_ENGINE_DEFINITIONS.md`** — this document activates Tier 2 of this freeze on ratification.
- **Forthcoming `docs/nawa_brain/COWORK_V2_INSTITUTIONAL_INTELLIGENCE.md`** — will reference the frozen architecture as institutional truth.
- **`docs/nawa_brain/DAIRTNA_OPERATIONAL_INTERPRETATION.md`** — the domain-specific interpretation work through which OIE (Runtime Component #5) was **first validated at MVP scale**. The Dairtna doctrine remains authoritative for Dairtna-domain semantics; OIE was not born from Dairtna, but it received its first real-world validation there. Future OIE work extends validation to other domains without changing OIE's runtime identity.
- **`CURRENT_STATE.md`** — needs to be amended after ratification to reflect the frozen architecture as the current state. This is a downstream amendment obligation.

---

## 20. Amendment Process

This document is amended by Executive Board Decision.

### 20.1 Amendment triggers

Amendment is required when:

- Tier 1 elements change (unfreeze per §17.1).
- Tier 2 elements change (unfreeze per §17.2, after Tier 2 is active).
- The Contract First Principle is amended.
- The tier structure itself is amended (adding a Tier 4, removing a tier, etc.).
- Boundary case triage rules in §18 need refinement based on accumulated pattern.

### 20.2 Amendment mechanics

Per EBD-002 §17 (Amendment Process) and this document's §17 (Unfreeze Process). MAJOR amendments produce Freeze v2.0; MINOR amendments produce Freeze v1.1.

### 20.3 Emergency amendment

Per EBD-002 §12.5, Founder-authorized. Recorded post hoc.

---

## 21. Final Principles

- **Contract First.** Architecture freezes contracts, not implementations. The freeze protects boundary behavior; engineering is free below the boundary.
- **Runtime Independence.** Every Runtime Component must be independently replaceable as long as its contract remains intact. The architecture is built for replacement, whether or not replacement is exercised.
- **Evolution Over Reinvention.** During MVP, NAWA evolves by improving existing components, not by adding new ones. The invariant "No New Engines During MVP" is the negative statement; this is the positive one.
- **Evolution Without Violation.** Six defined mechanisms permit evolution inside the freeze (§15). The freeze protects against drift, not against improvement.
- **Freeze what needs to be stable; free what needs to move.** Tier 1 stabilizes structure. Tier 2 stabilizes contracts. Tier 3 explicitly frees implementation.
- **The freeze is not the finish line.** Freeze v1.0 is what Runtime Validation Phase needs. Post-validation, Freeze v2.0 may look different. The freeze scales with the org's maturity, not against it.
- **Stable, Configurable, and Flexible are all named.** No architectural element is ambiguous. Every element is classified §14.
- **Backward-compatible contract additions are permitted** once Tier 2 is active (§15.4, §18.4). Only breaking contract changes require unfreeze.
- **No New Engines During MVP is the invariant.** Every other freeze rule can be argued in an unfreeze. This one is not up for renegotiation during Runtime Validation Phase.
- **The freeze serves validation.** If the freeze is preventing legitimate validation work, the freeze is calibrated wrong and must be amended. The freeze is not sacred; validation is.
- **This document is Executive Board Decision #003.** The corresponding entry is `docs/decisions/EBD-003-architecture-freeze-v1.md` and records ratification and reasoning.

---

## Appendix A — Tier Matrix

Change Type column entries grouped by classification: Stable (Tier 1 or Tier 2), Configurable, Flexible (Tier 3), and Evolution Without Violation channels.

### A.1 Stable — Tier 1 (Structural)

| Change Type | Tier | Authority | Process |
|---|---|---|---|
| Add a Runtime Component | Tier 1 | Founder | Unfreeze EBD (§17.1); refreeze immediately |
| Remove a Runtime Component | Tier 1 | Founder | Unfreeze EBD (§17.1); refreeze immediately |
| Reorder pipeline | Tier 1 | Founder | Unfreeze EBD (§17.1) |
| Rename a Runtime Component | Tier 1 | Founder | Unfreeze EBD (§17.1); update downstream docs |
| Revise Company Input Principle | Tier 1 | Founder | Unfreeze EBD; product review; Aboura input |
| Revise runtime philosophy | Tier 1 | Founder | Unfreeze EBD; requires strong justification |
| Exception to No New Engines | Tier 1 | Founder | Unfreeze EBD (§13.2); default = rejection during Runtime Validation Phase |
| Split one component into two | Tier 1 | Founder | Freeze breach (§18.2); unfreeze EBD |
| Merge two components into one | Tier 1 | Founder | Freeze breach (order change); unfreeze EBD |

### A.2 Stable — Tier 2 (Contract, once EBD-004 activates)

| Change Type | Tier | Authority | Process |
|---|---|---|---|
| Breaking change to component responsibility | Tier 2 | Founder | Unfreeze EBD (§17.2); update EBD-004 |
| Breaking change to component input at boundary (removal, type change, semantics change) | Tier 2 | Founder | Unfreeze EBD (§17.2) |
| Breaking change to component output at boundary (removal, type change, semantics change) | Tier 2 | Founder | Unfreeze EBD (§17.2) |
| Refine component boundary in a breaking way | Tier 2 | Founder | Unfreeze EBD (§17.2) |
| Change component non-responsibility | Tier 2 | Founder | Unfreeze EBD (§17.2) |

### A.3 Configurable — governed by policy, not by freeze

| Change Type | Governing Policy | Authority |
|---|---|---|
| Domain thresholds (Dairtna mortality bands, etc.) | Company Brain doctrine + field workshop | Founder ratifies workshop output |
| Provisional-flag status on interpreter output | Company Brain doctrine | Founder ratifies workshop output |
| Feature flags per company or phase | Product Documents | Aboura |
| Tenant-specific behavior overrides | Product Documents + Company Brain | Aboura + CTO per case |
| Runtime timeouts, retry policies, batch sizes | Runtime Documents | CTO within policy; AI Engineering Team executes |
| Environment variables (dev / stage / prod) | Runtime Documents | AI Engineering Team |
| Company-specific hypothesis library | Company Brain doctrine | Founder ratifies workshop output |
| Model selection within an engine (which AI system a component uses) | Runtime Documents | CTO within policy; AI Engineering Team executes |

### A.4 Flexible — Tier 3 (Implementation)

| Change Type | Tier | Authority | Process |
|---|---|---|---|
| Refactor internal code within a component | Tier 3 | AI Engineering Team | Ordinary engineering process |
| Optimize performance | Tier 3 | AI Engineering Team | Ordinary engineering process |
| Change internal APIs within a component | Tier 3 | AI Engineering Team | Ordinary engineering process |
| Change UI presentation | Tier 3 | Aboura + AI Engineering Team | Product + engineering process |
| Add internal classes or helpers | Tier 3 | AI Engineering Team | Ordinary engineering process |
| Change instrumentation | Tier 3 | AI Engineering Team | Ordinary engineering process |
| Evolve internal data storage (schema within a component) | Tier 3 | AI Engineering Team | Ordinary engineering process |
| Add or remove tests | Tier 3 | AI Engineering Team | Ordinary engineering process |
| Replace a Runtime Component's implementation while preserving contract | Tier 3 (per §4 Runtime Independence) | AI Engineering Team + CTO architectural sanity | Ordinary engineering process; contract preservation verified |

### A.5 Evolution Without Violation — permitted inside the freeze (§15)

| Change Type | Mechanism | Authority | Process |
|---|---|---|---|
| Backward-compatible contract addition (after Tier 2 active) | §15.4 | CTO | ADR referencing affected component in EBD-004; no unfreeze |
| Component-internal capability extension | §15.5 | CTO + AI Engineering Team | Ordinary architectural review + engineering process |
| Configurable-element tuning | §15.3 | Per governing policy | Follow policy; no freeze process |
| Component replacement under contract preservation | §15.2 | AI Engineering Team + CTO architectural sanity | Ordinary engineering process |
| Runtime Validation cycle | §15.6 | CTO + AI Engineering Team | Runtime Documents |

---

## Appendix B — Glossary

- **Backward-compatible contract addition** — A contract change that adds without removing or breaking existing behavior; permitted without unfreeze once Tier 2 is active (§15.4, §18.4).
- **Configurable** — An architectural element intentionally tunable within a governing policy, not subject to the freeze but not implementation-free either. Sits between Stable and Flexible (§14.2).
- **Contract** — What a Runtime Component promises to consume and produce, and its boundary with adjacent components. Contract is architectural.
- **Contract First Principle** — Architecture freezes contracts, not implementations (§3).
- **Engine** — A Runtime Component that transforms inputs into structured outputs through domain reasoning. Not every Runtime Component is an engine (see §10).
- **Evolution Over Reinvention Principle** — NAWA evolves by improving existing Runtime Components rather than introducing new ones during MVP (§5).
- **Evolution Without Violation** — The six mechanisms by which NAWA evolves inside the freeze without triggering unfreeze (§15).
- **Executive Intelligence** — Runtime Component #8; output layer at which decisions become available to the executive user.
- **Flexible** — An architectural element outside the freeze; may change through ordinary engineering process (§14.3).
- **Freeze v1.0** — This freeze, at initial ratification.
- **Nine Runtime Components** — The frozen set of Runtime Components in the runtime pipeline (§10).
- **NCO Lite** — Runtime Component #3; MVP-scoped engine in the NCO family.
- **NCE Lite** — Runtime Component #7; MVP-scoped engine in the NCE family.
- **No New Engines During MVP** — The Tier 1 invariant that prohibits adding Runtime Components during the Runtime Validation Phase (§13).
- **OIE** — Runtime Component #5; engine first validated at MVP scale through the Jannat Al-Firdaws (Dairtna) domain work.
- **OME Foundation** — Runtime Component #9; institutional memory substrate.
- **Runtime Component** — Any of the nine named elements of the runtime pipeline. Supersedes "engine" as the umbrella term for pipeline elements.
- **Runtime Independence Principle** — Every Runtime Component must be independently replaceable as long as its contract remains intact (§4).
- **Runtime Validation Phase** — The current NAWA project phase; the freeze exists to protect it.
- **Stable** — An architectural element subject to the freeze at some tier; may not change through ordinary engineering process (§14.1).
- **Tier 1** — Runtime Architecture Freeze — component order, names, philosophy, Company Input Principle, No New Engines. Active on this EBD.
- **Tier 2** — Contract Freeze — component contracts. Active on EBD-004 ratification.
- **Tier 3** — Implementation Freedom — explicit non-freeze on internal implementation.
- **Unfreeze** — The formal process by which a frozen element is changed; requires EBD (§17).

---

## Appendix C — Amendment Log

| Version | Date | Change | Authority | Reference |
|---|---|---|---|---|
| 1.0 | 2026-07-03 | Initial draft submitted for Executive Board review. Three-tier freeze model (Runtime Architecture, Contract, Implementation Freedom). Contract First Principle added as a NAWA principle. Nine Runtime Components named. Stable/Flexible classification. | CTO (draft); Founder (ratification pending) | EBD-003 |
| 1.0-a1 | 2026-07-03 | Pre-ratification amendment set. (a) Runtime Independence Principle added as new §4 — every Runtime Component must be independently replaceable while contract remains intact. (b) Evolution Over Reinvention Principle added as new §5 — NAWA evolves by improving existing components rather than adding new ones during MVP. (c) Classification extended from Stable/Flexible to Stable/Configurable/Flexible; Configurable defined at §14.2 as tunable within governing policy (thresholds, feature flags, model selection, etc.). (d) Evolution Without Violation section added as new §15 — six mechanisms by which NAWA evolves inside the freeze without triggering unfreeze. (e) §18.4 boundary case updated: backward-compatible contract additions permitted without unfreeze once Tier 2 activates; only breaking contract changes require unfreeze. (f) OIE wording updated at §10 and §19: "OIE was first validated through the Jannat Al-Firdaws (Dairtna) MVP" rather than "originated from Dairtna." (g) Downstream renumbering to accommodate new §4, §5, §15: old §4-§8 → new §6-§10; old §9-§12 → new §11-§14; old §13-§18 → new §16-§21. Cross-references updated. Final Principles and Glossary expanded to include new principles. Appendix A restructured into A.1-A.5 by classification. Version stays at 1.0 (pre-ratification amendment). | Founder direction; CTO amendment | EBD-003 additional amendments |
| 1.0 | 2026-07-03 | **Ratified** by Founder as Executive Board Decision #003. Tier 1 immediately active. Tier 2 pending EBD-004. Tier 3 permanently non-frozen. | Founder | EBD-003 |
| 1.1 | 2026-08-01 | Constitutional Governance Alignment per EBD-006. Added Constitutional supremacy declaration to header block. Version field split into Document version and Architecture Freeze version. Status corrected — Tier 2 active per EBD-004, no longer pending. **Architecture Freeze remains v1.0. No freeze element modified.** | Founder & CEO | EBD-006 |

---

*This document is ratified and authoritative as of 2026-07-03. Tier 1 is active. Tier 2 activates on ratification of EBD-004. Tier 3 is permanently non-frozen. The freeze exists to serve Runtime Validation Phase — not to constrain it beyond what validation requires.*
