# Executive Board Decision #004 — Engine Definitions (MVP Edition)

**Status:** Ratified by Founder as Executive Board Decision #004 (MVP Edition). Tier 2 of the Architecture Freeze v1.0 activates at MVP scope on this ratification.
**Version:** 1.1-MVP
**Category:** Governance (contracts applied under authority granted by EBD-002 and EBD-003).
**Subordinate to:** NAWA Reasoning Constitution v1.0 (ratified 2026-07-31). Where this decision conflicts with a Constitutional article, the Constitution prevails and this decision is amended.
**Scope:** MVP-scope contracts for the nine Runtime Components — Mission, Inputs, Outputs, Never Does — sufficient to activate Tier 2 of the Architecture Freeze v1.0 for the Runtime Validation Phase.
**Non-scope:** Advanced contract detail (protocols, error handling, retry semantics, orchestration mechanics, schema-level specifications) deferred to post-Runtime-Validation Tier 2 expansion (EBD-004-v2 or successor); implementation (Tier 3 per EBD-003); role authority (EBD-002); documentation format (EBD-001).
**Owner:** Founder & CEO (Mubarak).
**Approval authority:** Founder & CEO.
**Effective date:** 2026-07-03.
**Last updated:** 2026-08-01.
**Supersedes:** No prior engine definitions; establishes MVP Tier 2 contracts.

---

## 1. Ratification and Scope

This document is Executive Board Decision #004, MVP Edition. It defines the minimum set of contracts for each of the nine Runtime Components sufficient to activate Tier 2 of the Architecture Freeze v1.0 during Runtime Validation Phase.

The Founder has explicitly scoped this document to four fields per component: **Mission**, **Inputs**, **Outputs**, **Never Does**. Nothing more. Deeper contract detail — protocols, error semantics, orchestration mechanics, schema specifications, dependency graphs — is deliberately deferred until Runtime Validation Phase reveals what actually matters. Freezing more than the MVP needs would ossify contracts before they have been tested against real Company Input.

This is a Tier 2 contract freeze at the MVP boundary. It is intentionally lean.

---

## 2. Purpose

Runtime Validation Phase needs stable contracts to validate against, but only as many contracts as the validation actually exercises. This EBD delivers exactly that surface — four fields per component — and no more.

The purpose is threefold:

1. **Activate Tier 2.** The Architecture Freeze v1.0 (EBD-003) declared that Tier 2 activates on EBD-004 ratification. This document is what activates it.
2. **Bind boundaries.** Each component's Mission, Inputs, Outputs, and Never Does are the minimum contract required to prevent silent scope drift during MVP validation.
3. **Preserve learning surface.** Everything not in the four fields is intentionally open — validation will teach us what belongs in Tier 2 v2. Locking too early forecloses that learning.

---

## 3. MVP Contract Format

Every Runtime Component's contract is exactly four fields:

- **Mission** — one sentence, active voice, stating what the component is for.
- **Inputs** — what the component consumes at its boundary. Not internal fetches; boundary intake.
- **Outputs** — what the component produces at its boundary. Not internal state; boundary emission.
- **Never Does** — the boundary negation. What the component is explicitly not permitted to do, regardless of implementation.

Nothing else is contract at MVP scope. Not orchestration protocol, not error handling, not schema detail, not sequencing semantics, not retry policy. Those live outside the freeze until Runtime Validation Phase promotes them.

### 3.1 What is bound by ratification

- Each component's four fields are Tier 2 frozen on ratification. Breaking any of them requires Tier 2 unfreeze (EBD-003 §17.2).
- Backward-compatible additions to Inputs and Outputs are permitted without unfreeze per EBD-003 §15.4 and §18.4. Only breaking changes require unfreeze.

### 3.2 What is not bound

- Internal implementation is Tier 3 free (EBD-003 §9).
- Fields not explicitly listed here — protocols, orchestration mechanics, error semantics, telemetry, storage details — are not frozen and evolve through ordinary engineering process until a future EBD promotes them into Tier 2.

### 3.3 Provisional acronym expansions

The Runtime Component names in EBD-003 are Tier 1 frozen; their acronym expansions are not. Where an acronym's full expansion has not been declared by the Founder in writing, this document binds only the acronym and the role at the boundary — not any interpretation of the acronym's letters. Founder confirmation of acronym meanings is a prerequisite for the post-Runtime-Validation Tier 2 v2 expansion, but does not block MVP ratification.

---

## 4. The Nine Runtime Component Contracts

Contracts are stated in pipeline order. All nine are bound by every cross-component invariant in §5.

### 4.1 CompanyInput

**Mission:** Represent every piece of information entering the NAWA runtime as a single canonical data object grounded in the Company Input Principle.

**Inputs:** Raw data submitted by users or systems — chat messages, uploaded files (docx, xlsx, pdf, and future formats), structured form submissions, and future integration payloads.

**Outputs:** A structured CompanyInput object carrying content, source, submitter identity, company_id, and submission metadata (timestamp, format, tenant context).

**Never Does:**
- Interpret content.
- Apply domain reasoning.
- Reach conclusions.
- Modify content in transit.
- Cross company_id boundaries.

---

### 4.2 Company Input Classifier

**Mission:** Categorize each incoming CompanyInput so downstream Runtime Components receive only inputs relevant to their scope.

**Inputs:** CompanyInput objects produced by the entry point.

**Outputs:** CompanyInput objects annotated with classification metadata (category, department, type tags, target-component routing).

**Never Does:**
- Reason about operational implications of the input.
- Draw conclusions.
- Modify the original content of the CompanyInput.
- Make executive decisions.
- Skip or reorder downstream Runtime Components.

---

### 4.3 NCO Lite

**Mission:** Coordinate runtime execution and enforce runtime rules. NCO Lite is a runtime coordinator, not a business logic engine.

**Inputs:** Classified CompanyInput from the Company Input Classifier.

**Outputs:** Orchestrated runtime execution context, together with the CompanyInput, passed forward to KAE; runtime-rule enforcement decisions available to every downstream component (block, allow, gate).

**Never Does:**
- Implement business logic.
- Reason about the input's content.
- Make decisions about operational significance.
- Hold persistent memory — that is OME Foundation's role.
- Override the Classifier's routing.
- Maintain cross-input state; each input's flow is coordinated in isolation.

---

### 4.4 KAE

**Mission:** Transform unstructured Company Inputs into validated organizational knowledge through parsing, extraction, normalization, and validation. KAE produces the Truth Layer for the current runtime execution.

**Inputs:** Classified CompanyInput plus orchestration context from NCO Lite.

**Outputs:** Validated organizational knowledge attached to the CompanyInput — parsed structure, extracted facts, normalized entities and quantities, validated references — traceable back to the input content. This output constitutes the Truth Layer for the current input.

**Never Does:**
- Interpret the operational significance of extracted knowledge — that is OIE's role.
- Perform reasoning of any kind — reasoning is exclusively NCE Lite's role (per §4.7 and §5).
- Draw conclusions from extracted knowledge.
- Modify the original CompanyInput content.
- Assume knowledge not present in the input (per Truth Before Reasoning).
- Escalate to downstream components on its own initiative.

---

### 4.5 OIE

**Mission:** Interpret extracted knowledge from a CompanyInput as an operational signal against domain grounding — the runtime discipline first validated at MVP scale through the Jannat Al-Firdaws (Dairtna) work.

**Inputs:** CompanyInput plus extracted knowledge from KAE plus orchestration context from NCO Lite.

**Outputs:** Interpreted operational signal carrying signal level, signal basis, evidence trace, and provisional flag (per the discipline established in `docs/nawa_brain/DAIRTNA_OPERATIONAL_INTERPRETATION.md`).

**Never Does:**
- Make executive or business decisions — that is Executive Intelligence's role.
- Correlate across multiple CompanyInputs — that is NCE Lite's role at MVP.
- Override validated Company Input facts (per Company Brain Never Overrides Facts).
- Escalate beyond what threshold or evidence supports.
- Reason from raw content bypassing the knowledge extracted by KAE.

---

### 4.6 OCE

**Mission:** Build organizational context by combining operational intelligence, evidence, history, and current state. OCE never performs reasoning or recommendations.

**Inputs:** Operational intelligence (from OIE) plus evidence (from KAE's Truth Layer output) plus history (from OME Foundation's institutional memory surface) plus current state (CompanyInput and orchestration context from NCO Lite).

**Outputs:** Organizational Context — a consolidated, decision-ready assembly of the four input dimensions above, made available to NCE Lite for reasoning.

**Never Does:**
- Perform reasoning — reasoning is exclusively NCE Lite's role (per §4.7 and §5).
- Produce recommendations.
- Make executive or business decisions.
- Override upstream signal levels from OIE or facts from KAE's Truth Layer.
- Access institutional memory outside of OME Foundation's declared surface.

---

### 4.7 NCE Lite

**Mission:** Perform cognitive reasoning using the Truth Layer, Company Brain, and Organizational Context to produce hypotheses, recommendations, and confidence. NCE Lite is the **only** Runtime Component responsible for reasoning.

**Inputs:** Truth Layer (validated organizational knowledge from KAE for the current CompanyInput) plus Company Brain (institutional memory surface from OME Foundation) plus Organizational Context (consolidated output from OCE) plus orchestration context from NCO Lite.

**Outputs:** Reasoning output carrying hypotheses, recommendations, and per-item confidence — traceable to specific evidence in the Truth Layer, memory in Company Brain, and context from OCE. Passed to Executive Intelligence.

**Never Does:**
- Reason without the Truth Layer being present (per Truth Before Reasoning).
- Produce hypotheses or recommendations without recorded confidence and evidence trace (per Evidence Before Conclusions).
- Reason across tenants; reasoning is company-scoped.
- Override validated Company Input facts (per Company Brain Never Overrides Facts).
- Fabricate hypotheses or recommendations to satisfy expected patterns.
- Make executive or business decisions on behalf of the user; NCE Lite reasons and recommends, it does not act.
- Delegate reasoning to any other Runtime Component; reasoning stays here.

---

### 4.8 Executive Intelligence

**Mission:** Present the reasoned organizational understanding produced by NCE Lite — hypotheses, recommendations, and confidence — to the executive user as decision-relevant output, grounded in the CompanyInput and traceable to upstream evidence.

**Inputs:** Reasoning output from NCE Lite (hypotheses, recommendations, and confidence) plus CompanyInput plus orchestration context from NCO Lite.

**Outputs:** Decision-relevant executive output presented at the user surface — the executive-facing manifestation of the Company Input Principle.

**Never Does:**
- Introduce information not present in upstream signals or institutional memory.
- Override validated facts.
- Present conclusions without an evidence trace (must be able to say where a conclusion came from).
- Take actions on the user's behalf (AI Actions Layer is post-MVP scope per EBD-002 principles).
- Escalate beyond what upstream signals support (per Truth Before Reasoning).

---

### 4.9 OME Foundation

**Mission:** Provide the institutional memory substrate that persists validated organizational understanding across CompanyInputs so future runtime cycles reason from evidence accumulated over time.

**Inputs:** Validated outputs from the Executive Intelligence layer, plus operational intelligence and reasoning context (hypotheses, recommendations, confidence traces) explicitly marked for preservation.

**Outputs:** A queryable institutional memory surface available to upstream components (NCE Lite at MVP; other components as declared in future contract expansions).

**Never Does:**
- Override current Company Input facts (per Company Brain Never Overrides Facts).
- Store unvalidated conclusions.
- Cross tenant boundaries.
- Grow indefinitely without a lifecycle policy (lifecycle policy is Runtime Document scope, not contract).
- Reason on its own initiative — memory stores and serves; it does not conclude.

---

## 5. Cross-Component Invariants

These bind every Runtime Component in addition to its per-component contract. They are already frozen at Tier 1 (EBD-003 §7, §11, §12); restating them here formalizes them at the Tier 2 contract boundary.

- **Company Input Principle** (EBD-003 §11) — Every runtime execution begins with a CompanyInput and every user-facing output flows through Executive Intelligence. No component reasons outside the CompanyInput lineage.
- **Truth Before Reasoning** (EBD-003 §12.1) — No component reasons ahead of grounded knowledge. Reasoning that runs ahead of validated content is prohibited at every component.
- **Evidence Before Conclusions** (EBD-003 §12.2) — Every conclusion produced by any component must be traceable to specific evidence produced upstream.
- **Company Brain Never Overrides Facts** (EBD-003 §12.3) — OME Foundation may inform but not contradict a validated CompanyInput. Applies to every component reading from memory.
- **Runtime Independence** (EBD-003 §4) — Every component is independently replaceable so long as its contract remains intact. Cross-component coupling below the contract boundary is prohibited.
- **Company Isolation** — Every input, output, memory access, and correlation is scoped to a single company_id. No component crosses tenant boundaries.

A component that would need to violate any invariant above to fulfill its Mission is architecturally malformed and must be re-designed.

---

## 6. Post-Runtime-Validation Contract Expansion

This document is the **MVP Edition** of Tier 2. It is deliberately lean.

After Runtime Validation Phase completes, a successor EBD-004-v2 (or numbered successor) will expand contracts as evidence justifies. Candidate additions include:

- Response types and structured schemas for Inputs and Outputs.
- Error handling and retry semantics.
- Orchestration protocol between components.
- Latency and throughput expectations at the boundary.
- Instrumentation obligations.
- Cross-component invariant refinements as validation surfaces patterns.

Nothing above is frozen at MVP scope. Each candidate becomes Tier 2 material only after Runtime Validation Phase shows it is load-bearing. Freezing before that would ossify choices made in ignorance.

The Founder ratifies the successor EBD once Runtime Validation Phase completes. Until then, the four fields per component are the entirety of the Tier 2 contract surface.

---

## 7. Enforcement and Change Process

Enforcement is per EBD-003 §16 (Enforcement Mechanism) applied to the four fields defined in §4.

### 7.1 Contract change triage

- **Breaking change to Mission, Inputs, Outputs, or Never Does** — Tier 2 unfreeze required (EBD-003 §17.2). Founder ratifies.
- **Backward-compatible addition to Inputs or Outputs** — Permitted without unfreeze per EBD-003 §15.4. CTO approves as ADR.
- **Addition of a new Never Does entry** — Permitted without unfreeze; strengthening a boundary negation is compatible with existing behavior. CTO approves as ADR.
- **Removal of a Never Does entry** — Requires Tier 2 unfreeze; loosening a boundary negation changes what the component is permitted to do.

### 7.2 Contract change process

Every contract change is filed as an ADR under EBD-002 §5, references the affected component in this document, and is included in the next Sprint retro under Architecture Health (EBD-002 §16.4).

### 7.3 Provisional acronym expansions

Confirming a provisional acronym expansion is a Meeting Document decision by the Founder, not an EBD. Ratifying the meaning of, e.g., "KAE" does not alter the four fields; it only records the acronym's expansion for institutional continuity. Recorded expansions are added to the glossary of this document at the next amendment.

---

## 8. Amendment Process

This document is amended by Executive Board Decision.

### 8.1 Amendment triggers

- Any breaking change to a component's four fields (Tier 2 unfreeze).
- Post-Runtime-Validation Tier 2 expansion (produces EBD-004-v2 or successor).
- Founder confirmation of acronym expansions (Meeting Document; captured in this document's glossary on next amendment).
- Cross-component invariant additions or removals.

### 8.2 Amendment mechanics

Per EBD-002 §17 and EBD-003 §17.2. MAJOR amendments produce a new version file (e.g., `EBD-004-v2_ENGINE_DEFINITIONS.md`) and archive the prior; MINOR amendments produce a new version in the header and an entry in Appendix C.

### 8.3 Emergency amendment

Per EBD-002 §12.5. Founder-authorized, recorded post hoc.

---

## 9. Final Principles

- **MVP contracts are lean by design.** Four fields per component. Nothing more. Freezing more before validation would ossify choices made in ignorance.
- **Boundaries first, protocols later.** Mission, Inputs, Outputs, Never Does bind the surface. Everything else is Tier 3 or Runtime Document scope until Runtime Validation earns its place at Tier 2.
- **Backward-compatible growth is permitted.** Additions to Inputs, Outputs, and Never Does grow the contract without unfreezing it. Only breaking changes require unfreeze.
- **Cross-component invariants bind every component.** The runtime philosophy from EBD-003 is restated here at the contract boundary so it is enforceable per-component.
- **Runtime Independence is a contract, not just a principle.** Every component must be replaceable while its four fields hold. Cross-component coupling below the boundary is a contract violation.
- **Provisional acronyms do not block ratification.** The Founder confirms acronym meanings at a Meeting Document; this document binds behavior at the boundary regardless of what the letters expand to.
- **This document is Executive Board Decision #004, MVP Edition.** On ratification, Tier 2 of the Architecture Freeze v1.0 activates at MVP scope. The corresponding entry is `docs/decisions/EBD-004-engine-definitions-mvp.md` and records ratification and reasoning.

---

## Appendix A — Tier 2 Activation Log

| Event | Date | Reference |
|---|---|---|
| EBD-003 Architecture Freeze v1.0 ratified; Tier 2 pending | 2026-07-03 | EBD-003 |
| EBD-004 MVP Edition drafted; Tier 2 pending ratification | 2026-07-03 | This document |
| **Tier 2 (MVP scope) activated** | **2026-07-03 on Founder ratification** | **This document** |

---

## Appendix B — Glossary

- **Backward-compatible addition** — A contract change that adds without removing or changing existing behavior; permitted without Tier 2 unfreeze (EBD-003 §15.4).
- **Boundary negation** — What a component is explicitly not permitted to do; captured in the Never Does field.
- **Company Brain** — In the runtime context, the institutional memory surface exposed by OME Foundation. NCE Lite reasons over the Company Brain as one of its three canonical inputs (alongside the Truth Layer and Organizational Context). Distinct from the broader Company Brain documents category in EBD-001.
- **Company Input** — Both the data model (Runtime Component #1, `CompanyInput`) and the Principle that the runtime consumes only Company Inputs and produces Executive Intelligence.
- **Company Input Classifier** — Runtime Component #2; classifies and routes CompanyInputs.
- **Cognitive reasoning** — The exclusive responsibility of NCE Lite. Producing hypotheses, recommendations, and confidence over the Truth Layer, Company Brain, and Organizational Context. No other Runtime Component performs cognitive reasoning.
- **Executive Intelligence** — Runtime Component #8; the user-facing output layer.
- **KAE** — Runtime Component #4; transforms unstructured CompanyInputs into validated organizational knowledge (parsing, extraction, normalization, validation); produces the Truth Layer. Acronym expansion provisional; confirmation pending Founder Meeting Document.
- **MVP contract** — The four fields (Mission, Inputs, Outputs, Never Does) that constitute a component's Tier 2 contract during Runtime Validation Phase.
- **NCE Lite** — Runtime Component #7; the only Runtime Component responsible for cognitive reasoning. Consumes Truth Layer + Company Brain + Organizational Context; produces hypotheses, recommendations, and confidence. Acronym expansion provisional.
- **NCO Lite** — Runtime Component #3; runtime coordinator that enforces runtime rules. Not a business logic engine. Acronym expansion provisional.
- **OCE** — Runtime Component #6; builds Organizational Context by combining operational intelligence, evidence, history, and current state. Never reasons or recommends. Acronym expansion provisional.
- **OIE** — Runtime Component #5; produces operational intelligence by interpreting extracted knowledge as an operational signal against domain grounding. First validated at MVP through Jannat Al-Firdaws (Dairtna) work. Acronym expansion provisional.
- **OME Foundation** — Runtime Component #9; institutional memory substrate; exposes the Company Brain surface at runtime. Acronym expansion provisional.
- **Organizational Context** — The consolidated output of OCE, combining operational intelligence, evidence, history, and current state. One of NCE Lite's three canonical inputs.
- **Runtime Component** — Any of the nine named elements of the runtime pipeline per EBD-003 §10.
- **Runtime rules** — The runtime-enforceable constraints derived from the runtime philosophy (Company Input Principle, Truth Before Reasoning, Evidence Before Conclusions, Company Brain Never Overrides Facts, Company Isolation, Runtime Independence). NCO Lite is the runtime coordinator that enforces these rules across every input's traversal.
- **Tier 2 (MVP)** — The contract freeze activated by ratification of this document; binds Mission, Inputs, Outputs, Never Does per component.
- **Tier 2 (v2, post-Runtime-Validation)** — The expanded contract freeze anticipated after Runtime Validation Phase completes; not scope of this document.
- **Truth Layer** — The validated organizational knowledge produced by KAE for the current CompanyInput. Represents the current-input facts that satisfy Truth Before Reasoning. One of NCE Lite's three canonical inputs. Distinct from Company Brain (which is memory across inputs).

---

## Appendix C — Amendment Log

| Version | Date | Change | Authority | Reference |
|---|---|---|---|---|
| 1.0-MVP | 2026-07-03 | Initial draft submitted for Executive Board review. Four fields per component (Mission, Inputs, Outputs, Never Does). MVP-scope only; post-Runtime-Validation expansion deferred. | CTO (draft); Founder (ratification pending) | EBD-004 MVP Edition |
| 1.0-MVP-a1 | 2026-07-03 | Pre-ratification amendment set. Founder-specified missions applied to the four components flagged as uncertain in the CTO briefing: (a) **NCO Lite** — reframed as runtime coordinator that enforces runtime rules; explicitly not a business logic engine. (b) **KAE** — reframed as transformer from unstructured CompanyInputs into validated organizational knowledge; produces the **Truth Layer**. (c) **OCE** — reframed as builder of Organizational Context by combining operational intelligence, evidence, history, and current state; explicitly not a reasoning or recommendation component. (d) **NCE Lite** — reframed as the **only** Runtime Component responsible for cognitive reasoning; consumes Truth Layer + Company Brain + Organizational Context; produces hypotheses, recommendations, and confidence. Consistency edits: Executive Intelligence Mission and Inputs updated to reference NCE Lite's new output surface (hypotheses/recommendations/confidence rather than correlation); OME Foundation Inputs updated to reference reasoning context rather than correlation context. Glossary expanded with **Truth Layer**, **Cognitive reasoning**, **Company Brain (runtime alias)**, **Organizational Context**, **Runtime rules**. Version stays at 1.0-MVP. | Founder direction; CTO amendment | EBD-004 MVP Edition amendments |
| 1.0-MVP | 2026-07-03 | **Ratified** by Founder as Executive Board Decision #004 (MVP Edition). Tier 2 of the Architecture Freeze v1.0 activates at MVP scope. | Founder | EBD-004 MVP Edition |
| 1.1-MVP | 2026-08-01 | Constitutional Governance Alignment per EBD-006. Added Constitutional supremacy declaration to header block. No contract, Mission, Inputs, Outputs, Never Does, or invariant change. | Founder & CEO | EBD-006 |

---

*This document is ratified and authoritative as of 2026-07-03. Tier 2 of the Architecture Freeze v1.0 is active at MVP scope. Deeper contract detail is deferred until Runtime Validation Phase earns its place. The freeze binds boundaries; validation teaches what else belongs behind them.*
