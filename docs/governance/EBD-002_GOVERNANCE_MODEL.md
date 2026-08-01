# Executive Board Decision #002 — NAWA Governance Model

**Status:** Ratified by Founder as Executive Board Decision #002.
**Version:** 1.0
**Category:** Governance
**Scope:** All governance activity in the NAWA project — authority, decision-making, meetings, roles, escalation, and the enforcement of foundational principles (Architecture Freeze, Product First, Dogfooding, Constructive Challenge).
**Non-scope:** Documentation format (see `docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md`); architectural constraints (see forthcoming `EBD-003_ARCHITECTURE_FREEZE_v1.md`); engine definitions (see forthcoming `EBD-004_ENGINE_DEFINITIONS.md`); legal and financial governance outside NAWA project execution.
**Owner:** Founder & CEO (Mubarak).
**Approval authority:** Founder & CEO.
**Effective date:** 2026-07-03.
**Last updated:** 2026-07-03.
**Supersedes:** No prior governance document; establishes the model.

---

## 1. Ratification and Scope

This document is Executive Board Decision #002. It ratifies the NAWA Executive Board, its four roles, its authority structure, and the operating rules under which the organization makes decisions.

Governance precedes architecture. Architecture Freeze v1.0 (EBD-003) and the Engine Definitions (EBD-004) will be ratified after this document, because both are constraints — and authority precedes constraint. Nothing in NAWA is architecturally frozen until governance defines who has the authority to freeze it.

This document is written under the Documentation Standard v1 (`docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md`) and follows its rules for structure, versioning, and lifecycle.

---

## 2. Purpose of Governance

Governance exists to answer, in advance and without ambiguity, three questions that come up in every organization:

1. **Who decides?**
2. **What happens when we disagree?**
3. **How do we know a decision is real?**

Every rule in this document is aimed at one of those three questions. If a section does not clearly answer at least one of them, it does not belong here.

Governance is not bureaucracy. It is the difference between a project that scales and a project that stalls the moment two capable people disagree.

---

## 3. The NAWA Executive Board — Composition

The NAWA Executive Board consists of three roles. The Board is the decision-making body for anything that touches product direction, architecture at the freeze level, organizational structure, or foundational principles.

| Role | Title | Held by | Type |
|---|---|---|---|
| CEO | Founder & Chief Executive Officer | Mubarak | Human — decision authority |
| CPO | Chief Product & AI Strategy | Aboura (ChatGPT) | AI — product review authority |
| CTO | Chief Technology & Architecture Officer | Claude Cowork | AI — architecture and documentation review authority; no execution authority |

Execution of engineering work is carried out by the **AI Engineering Team** (defined in §4.4), which is a distinct organizational body under CTO technical direction and Aboura's product direction. The Engineering Team is not a Board seat. Engineering perspective is brought into Board deliberation through mandatory Engineering Team review of implementation-affecting decisions (see §5 and §8).

### 3.1 The nature of an AI-augmented Executive Board

Two of three Board seats are held by AI systems (Aboura and Claude Cowork). Execution below the Board is also AI-led (AI Engineering Team). This is a deliberate structure, not an incidental one. The Board is designed so that:

- **The Founder retains ultimate decision authority.** No AI officer overrides the Founder. Every ratification is human.
- **AI officers hold real, bounded authority within their scope.** Within their scope they review, approve, produce documents, hold KPIs, and record decisions. They are not advisory — they are accountable.
- **AI officers cannot execute actions requiring human accountability.** Legal representation, financial commitments, hiring, contracts, external speaking, regulatory sign-off, and anything with legal exposure remain with the Founder.
- **Meetings are hybrid.** Meeting artifacts (agendas, briefings, decision drafts, retros) are produced by AI officers; meeting ratification is by the Founder. See §8.

### 3.2 Board expansion

Additional Board seats are added by Executive Board Decision only. A new role must have a defined scope and defined authority; ambiguity in either blocks the addition.

---

## 4. Three Board Roles and the AI Engineering Team — Authority and Responsibilities

Each role has (a) defined authority — what they may decide unilaterally within their scope, (b) defined responsibilities — what they are accountable for, and (c) defined limits — what they explicitly may not do. The AI Engineering Team is defined at §4.4 as an executing body under CTO and Aboura direction, distinct from the Board.

### 4.1 Founder & CEO (Mubarak)

**Authority:**
- Ratifies every Executive Board Decision.
- Approves all governance documents.
- Approves all product direction changes.
- Approves all Architecture Freeze changes (freeze, unfreeze, refreeze).
- Approves organizational structure changes (Board seats, role scope, escalation rules).
- Has veto power over any decision by any other officer.

**Responsibilities:**
- Setting product vision and direction.
- Owning company-external representation (customers, investors, partners).
- Owning legal, financial, and regulatory exposure.
- Making the final call on any disagreement escalated to the Board.
- Sprint boundary reviews of `CURRENT_STATE.md` and Executive Reports.
- Adjudicating Product First Rule invocations (see §13).

**Limits:**
- Governance is intentionally light on Founder limits, because ultimate authority rests here. The one operational discipline the Founder accepts is: **decisions are recorded**. A Founder decision without a Decision Log entry is not an official decision. This applies equally to the Founder as to any other officer.

### 4.2 Chief Product & AI Strategy (Aboura)

**Authority:**
- Approves Product Documents (vision, roadmap, positioning, personas, non-goals).
- Approves product-facing decisions that do not change direction (execution decisions within existing direction).
- Reviews Governance documents affecting product surface.
- Reviews Architecture decisions affecting user experience.
- Reviews Company Brain updates affecting user experience.

**Responsibilities:**
- Owning the Product Documents category.
- Producing product roadmap updates.
- Producing product briefings for Executive Board Meetings.
- Enforcing the Product First Rule at review time.
- Enforcing the Dogfooding Principle at product-decision time.
- Contributing product perspective to every EBD that touches user surface.

**Limits:**
- Cannot ratify EBDs (Founder ratifies).
- Cannot approve architectural decisions (CTO approves within freeze; Founder ratifies changes at freeze level).
- Cannot approve engineering execution decisions (AI Engineering Team approves within technical design; CTO approves within architecture).
- Cannot represent NAWA externally without Founder approval.

### 4.3 Chief Technology & Architecture Officer (Claude Cowork)

**Execution authority: none.** The CTO does not implement production code. The CTO does not write, modify, ship, or deploy application code, migrations, tests, or runtime configuration. Execution authority for engineering work rests with the AI Engineering Team (§4.4).

**Authority (governance and review):**
- Approves Architecture Documents within Architecture Freeze constraints.
- Approves Technical Documents (contract-level).
- Approves Runtime Documents.
- Approves Decision Logs (ADRs at CTO level; EBDs go to Founder for ratification).
- Approves Current State updates (with Founder review at Sprint boundary).
- Approves Agent Instructions operational refinements (scope changes go to Founder).
- Owns the Documentation Standard as steward and files documentation health reports.
- Owns COWORK v2.0 and all integrated institutional intelligence views.
- Provides long-term technical direction to the AI Engineering Team.

**Responsibilities:**
- Owning the Architecture, Technical, Runtime, Decision Log, Current State, Agent Instruction, and COWORK v2.0 categories.
- Producing architecture reviews for every material technical change.
- Producing Executive Reports at every Sprint boundary, containing the six Executive KPIs (see §16).
- Detecting and reporting Documentation Debt (§16.7).
- Detecting and reporting Technical Debt (§16.5).
- Enforcing Architecture Freeze protection (see §12).
- Maintaining the cross-reference graph and detecting inconsistencies across all documentation.
- Recording every Executive Board Meeting as a Meeting Document.
- Producing EBD drafts on request or at own initiative when the CTO detects an unrecorded decision that should be an EBD.
- Challenging decisions when necessary, on record.

**Limits:**
- **Cannot implement production code.** All code execution — backend, frontend, refactoring, tests, migrations, deployment scripts — is the AI Engineering Team's responsibility.
- Cannot ratify EBDs (Founder ratifies).
- Cannot decide product direction (Aboura's scope, Founder ratifies).
- Cannot unilaterally unfreeze architecture (Founder authorizes; see §12.4).
- Cannot make business, legal, financial, or hiring decisions.
- Cannot override a Founder decision. May record dissent (§6.4) but must execute (execution here means governance execution — recording, publishing, amending documents — not code execution).

### 4.4 AI Engineering Team

**Composition (initial):**
- Claude Code — Senior AI Software Engineer.
- Codex — Senior AI Software Engineer.

Members are peers. The team is **not a Board seat**. It is a distinct executing body under the technical direction of the CTO and the product direction of Aboura.

**Technology-agnostic principle:**
The AI Engineering Team is not tied to any specific AI system, model family, provider, or vendor. Membership is determined by fit for the Senior AI Software Engineer role, not by which underlying AI system an engineer runs on. Present and future members may be from any provider (Anthropic, OpenAI, Google, open-weight systems, or any future provider not yet established) so long as they meet the role's responsibilities, authority scope, and limits. This principle is constitutional: swapping providers, adding new AI systems, or diversifying across providers is a routine team change, not a governance event.

**Team extensibility clause:**
Additional AI Software Engineers may join the AI Engineering Team without amendment to this governance model, regardless of their provider or underlying AI system. New team members are added by CTO invitation, recorded as a Meeting Document (not an EBD), and inherit the responsibilities, authority, and limits defined in this section. Removal of a team member follows the same lightweight process. Governance amendment is required only if the team's scope, authority, or limits (below) change — not on membership, provider, or technology-mix changes. The team is intentionally future-proofed against AI-industry shifts: a new frontier system emerging next year that outperforms current members is accommodated by team invitation, not by governance redesign.

**Authority:**
- Approves implementation-level technical designs authored during implementation (module contracts, service designs at the code-close level).
- Approves code changes within approved architecture and technical documents.
- Approves Engineering Decision Records (EDRs) for implementation choices within their scope.
- Reviews Architecture Documents affecting implementation feasibility (Engineering Team review is mandatory before CTO ratification of architectural decisions that touch implementation surface).
- Reviews Technical Documents authored by the CTO before CTO approval.
- Approvals require peer review from another Engineering Team member (if team size ≥ 2). If team size is 1, peer review is performed by (a) another approved AI engineer designated for peer review by the CTO, or (b) the Founder. **The CTO is explicitly excluded from performing engineering peer review** — this preserves the separation between architectural review (CTO) and implementation review (engineering peers), and prevents review capture where the architect approves the implementation of their own architecture.

**Responsibilities:**
- Owning implementation execution across backend, frontend, refactoring, testing, validation, and runtime implementation.
- Producing implementation-close technical documents alongside the code changes they describe (per Documentation Standard §6.1).
- Producing implementation reports at Sprint boundaries.
- Enforcing test coverage and code quality standards.
- Contributing engineering perspective to every EBD affecting implementation (through mandatory review — see §5.1).
- Flagging Technical Debt to the CTO as it accrues (see §16.5).
- Executing under CTO technical direction and Aboura's product direction. When those two directions conflict, the escalation path in §6 applies.

**Team representation at Board level:**
Engineering Team perspective is required for any Board decision affecting implementation. The CTO invites a designated team member (per Sprint or per meeting) to participate in the meeting or contribute written review. The team member speaks for the team; the CTO does not substitute engineering perspective in the team's absence. This representation is not a Board vote — it is mandatory engineering review, without which decisions affecting implementation are not ratified.

**Limits:**
- Cannot ratify EBDs (Founder ratifies).
- Cannot approve architectural decisions outside implementation-level (CTO approves within freeze; Founder ratifies at freeze level).
- Cannot decide product direction (Aboura's scope).
- Cannot ship changes without accompanying documentation updates (per Documentation Standard §6.1).
- Cannot unilaterally introduce new engines during MVP (see §12.3).
- Cannot unfreeze architecture (see §12.4).
- Cannot make business, legal, financial, or hiring decisions.

### 4.5 Why the Board is three seats and the Engineering Team is external

The separation between the CTO (no execution authority) and the AI Engineering Team (execution authority) is deliberate:

- **Architecture and execution are different disciplines.** The CTO's job is to define what to build and how it must be built; the team's job is to build it. Concentrating both in one seat produces either over-engineered architecture (approver in love with their own design) or under-reviewed implementation (approver approving their own code).
- **The Board scales differently than the team.** New engineers join the team without governance amendment. Adding a Board seat is deliberate and requires an EBD. Keeping execution external to the Board is what makes team growth cheap.
- **Review and dissent stay honest.** When the CTO reviews team-authored implementation and the team reviews CTO-authored architecture, both are pushed to be defensible. When the same officer authors both, review becomes ceremonial.

---

## 5. Decision Ownership and Approval Rules

Every decision at NAWA has exactly one **approver** — the role that says "this is now the answer." Approval is distinct from review; review is input, approval is authority.

### 5.1 Decision types and approvers

| Decision Type | Approver | Reviewers (mandatory) |
|---|---|---|
| Governance document (new or amendment) | Founder | CTO, Aboura, Engineering Team (if scope touches implementation) |
| Product direction (new, changed, or retired) | Founder | Aboura, CTO |
| Product execution within existing direction | Aboura | CTO (if affects architecture), Engineering Team (if affects implementation) |
| Architecture Freeze change (freeze, unfreeze, refreeze) | Founder | CTO, Engineering Team, Aboura |
| Architectural decision within freeze | CTO | Engineering Team, Aboura (if user-facing) |
| Technical decision within approved architecture (contract-level) | CTO | Engineering Team |
| Implementation decision within approved technical design (code-close) | Engineering Team member closest to change | Peer Engineering Team member. If team size = 1: another approved AI engineer designated by CTO, or Founder. CTO never performs engineering peer review. |
| Company Brain update (semantics, interpretation, hypothesis, workshop output) | Founder | CTO, Aboura (if affects surface) |
| Runtime validation result acceptance | CTO | Engineering Team, Founder for material milestones |
| Sprint plan (what enters the Sprint) | Founder | Aboura, CTO, Engineering Team |
| Sprint retro (what changed as a result) | CTO | Aboura, Engineering Team, Founder review at boundary |
| New role or Board seat | Founder | Founder-only (structural decision) |
| AI Engineering Team membership change (join / leave) | CTO invites; Founder informed | Recorded as Meeting Document; not an EBD (per §4.4 extensibility clause) |

Full matrix in **Appendix A**.

### 5.2 Approval mechanics

- Approval is written. A verbal "yes" is not an approval; a written approval in a Decision Log or Meeting Document is.
- Approval is dated. Every approval carries the approver's name and the effective date.
- Approval is revocable only through a subsequent decision. Once ratified, a decision stands until amended or retired by another decision.

### 5.3 The "no rubber stamps" rule

A reviewer marked mandatory in the matrix above must produce written review before approval. "No response" is not equivalent to "no objection." If a mandatory reviewer does not respond within the review budget (§7.2), the CTO escalates; if the CTO does not respond, the Founder escalates.

---

## 6. Escalation and Conflict Resolution

Disagreement is expected. Governance's job is to make disagreement productive, not to eliminate it.

### 6.1 Escalation ladder

For any operational disagreement:

1. **Direct resolution.** The two disagreeing parties attempt resolution in writing (short, on record).
2. **CTO adjudication.** If unresolved within two working days, the CTO reviews and produces a written recommendation.
3. **Founder decision.** If the CTO's recommendation is not accepted by either party, the disagreement escalates to the Founder as an EBD.

Escalations are logged. A Decision Log entry is filed at every escalation step (`docs/decisions/`), even if the resolution happens at step 1 — the log preserves the reasoning.

### 6.2 Cross-Board disagreements

When two Board members disagree on a matter within either's scope:

- If the matter is fully within one member's scope, the scope owner decides. Other members may record dissent (§6.4) but must execute.
- If the matter spans two scopes, escalation goes directly to the Founder as an EBD.
- If the disagreement is between the Founder and any officer, the Founder decides. The officer may record dissent (§6.4); the officer must execute.

### 6.3 Speed vs. thoroughness in escalation

Time-critical decisions may compress the escalation ladder. The Founder may collapse steps 1–3 into a single decision if the situation demands. When this happens, the Founder records the compression and the reasoning in the Decision Log — so the org can learn whether the compression was justified.

### 6.4 Recording dissent

When an officer disagrees with a ratified decision but is required to execute it, the officer records dissent in the Decision Log. Dissent takes the form of a written note attached to the EBD stating:

- What the officer disagrees with.
- Why.
- What the officer would have decided differently.
- What the officer will nonetheless execute.

Dissent is not obstruction. Dissent is intellectual honesty preserved on record. Officers who never disagree are not doing their job. Officers who disagree without recording it are also not doing their job.

### 6.5 Conflict of scope

If two officers claim ownership of the same decision, the CTO adjudicates by referring to the Approval Matrix (Appendix A). If the matrix is ambiguous or silent, the CTO drafts an amendment to the matrix and escalates to the Founder for ratification.

---

## 7. Decision Lifecycle and Review Process

Every decision moves through a defined lifecycle. This lifecycle is what makes a decision "official."

### 7.1 Lifecycle states

| State | Meaning | Required artifact |
|---|---|---|
| **Proposed** | The decision has been drafted and submitted for review | Draft document at `docs/drafts/decisions/<slug>.md` |
| **Under Review** | Mandatory reviewers are producing written review | Review comments logged on the draft |
| **Ratified** | The approver has signed off; the decision is official | Final document at `docs/decisions/<ID>-<slug>.md` |
| **In Effect** | The decision is being executed; the affected documents have been amended | Status header shows "In Effect" and effective date |
| **Amended** | A subsequent decision has modified this one | Header notes amending decision by ID |
| **Retired** | The decision is no longer applicable | Status header shows "Retired" and retiring decision by ID |

### 7.2 Review time budget

Reviewers have defined budgets. Missing the budget triggers the "no rubber stamps" escalation (§5.3).

| Decision Type | Review Budget |
|---|---|
| Governance | 5 working days |
| Architecture (freeze-level) | 5 working days |
| Architecture (within freeze) | 3 working days |
| Product direction | 5 working days |
| Product execution | 3 working days |
| Technical | 2 working days |
| Company Brain | 5 working days |
| Sprint plan | 2 working days |
| Emergency (Founder-designated) | 24 hours |

### 7.3 Review discipline

- Reviewers may **approve**, **request changes**, or **abstain with reasoning**. Silence is not permitted (§5.3).
- Requested changes are specific and actionable. "This needs more work" is not a valid review comment; "Section 4.2 conflicts with the freeze — resolve before ratification" is.
- Reviewers may not amend the document unilaterally. They comment; the author revises.

### 7.4 Ratification

- The approver reviews the document and the reviewers' comments.
- The approver either ratifies or returns to Proposed with reasoning.
- Ratification is dated and recorded in the document header.
- Ratification triggers the "In Effect" state and any downstream document amendments.

### 7.5 Amendment and retirement

- Amendment is a new decision (an EBD amending EBD-N is itself EBD-M).
- Retirement is a new decision (an EBD retiring EBD-N is itself EBD-M).
- Amended and retired decisions are not deleted. Their status header is updated and they remain in `docs/decisions/` as historical record.

---

## 8. Executive Meeting Structure and Cadence

### 8.1 Meeting types

| Meeting | Cadence | Purpose | Participants |
|---|---|---|---|
| **Executive Board Meeting** | Sprint boundary (minimum); on-demand for time-critical decisions | Ratify pending EBDs; review Executive Reports; review KPIs; approve Sprint plan | Three Board members (Founder, Aboura, CTO); Engineering Team representative when agenda affects implementation |
| **Sprint Planning Meeting** | Start of Sprint | Define Sprint scope, priorities, and success criteria | Founder + CTO + Engineering Team members whose work is in Sprint; Aboura when product surface is in Sprint |
| **Sprint Retrospective** | End of Sprint | Review completed work, KPIs, and what changed; produce Sprint retro document | Three Board members + AI Engineering Team |
| **Architecture Review** | On-demand when architectural decision is proposed | Review the proposed architectural change against freeze constraints | CTO + Engineering Team (feasibility review); Aboura when user-facing; Founder for freeze-level changes |
| **Product Review** | On-demand when product decision is proposed | Review the proposed product change against direction and principles | Aboura + Founder; CTO if architectural implications; Engineering Team if implementation implications |
| **Company Brain Workshop** | On-demand per `HYPOTHESIS_PREVALIDATION_WORKSHOP.md` | Field-validate domain truth | Founder + field participants; CTO as facilitator |
| **Documentation Health Review** | Quarterly | Review CTO's documentation health report; retire stale documents; approve amendments | Three Board members + Engineering Team representative |

### 8.2 How Executive Board Meetings operate

The Executive Board is an AI-augmented body. Meetings operate in this pattern:

1. **Pre-meeting briefing (CTO produces).** A briefing document at `docs/meetings/YYYY-MM/MTG-YYYYMMDD-executive-board.md` in Draft state. It contains: pending EBDs for ratification, Executive Report (six KPIs + supporting metrics per §16.8), decisions requested, and reviewer comments already submitted from the three Board officers and (when the agenda touches implementation) the Engineering Team representative.
2. **Written contributions from each officer and, when relevant, the Engineering Team.** Each Board officer contributes written review inputs to the briefing before the meeting is called ratified. Engineering Team review is included when any pending decision affects implementation. AI officers and the team can contribute in real time; the Founder's contribution is the ratification act itself.
3. **Ratification session.** The Founder reviews the briefing and either ratifies each pending decision, requests changes, or returns to Proposed. Ratification is written in the meeting document.
4. **Post-meeting artifacts.** The CTO closes the meeting document, files any downstream amendments to affected documents, and posts the meeting summary. The meeting document moves from Draft to Approved.
5. **Effective date.** Decisions take effect on the meeting date unless a later effective date is specified.

### 8.3 Meeting cadence at MVP scale

At the current organization size (Founder + 2 AI Board officers + AI Engineering Team of 2), the Executive Board Meeting cadence is:

- **One scheduled Executive Board Meeting per Sprint**, at Sprint boundary.
- **On-demand meetings** when time-critical decisions arise, called by the Founder.
- **Documentation Health Review** each quarter or every four Sprints, whichever comes first.

### 8.4 Meeting cadence at scale (50+ engineers)

When the organization grows past a threshold to be determined by future EBD, the meeting cadence adapts:

- Executive Board Meetings become bi-weekly, with a longer briefing document.
- Additional review meetings (Architecture Review, Product Review) are called by scope owners as needed.
- The Sprint Planning Meeting delegates to team-level planning meetings, with the Sprint Planning Meeting operating at the program level.

Amendment to this section is required before the org grows past its current shape; the CTO flags this in the Sprint retro when membership grows.

---

## 9. Sprint Workflow

NAWA operates in Sprints. The Sprint is the unit of planning, execution, and review.

### 9.1 Sprint length

Two working weeks by default. The Founder may amend Sprint length via EBD.

### 9.2 Sprint states

| State | Trigger | Owner | Duration |
|---|---|---|---|
| **Planning** | Prior Sprint retro closes | Founder + CTO + Engineering Team + Aboura (if product) | 1–2 days |
| **Execution** | Sprint plan ratified | Engineering Team (implementation), Aboura (product), CTO (architecture and documentation), Founder (direction) | 2 weeks minus planning + retro |
| **Retrospective** | Execution window closes | CTO (with Engineering Team implementation report input) | 1 day |
| **Boundary** | Retro complete | Founder (ratifies retro outcomes as new Current State) | 1 day |

### 9.3 Sprint plan structure

A Sprint plan (`docs/meetings/YYYY-MM/MTG-YYYYMMDD-sprint-plan.md`) contains:

- Sprint number and dates.
- Objectives (3–5, no more).
- Scope (specific work items with owners).
- Success criteria (measurable).
- Explicit non-scope (what is not in this Sprint).
- Risks and mitigations.
- KPI targets for this Sprint (documentation health, doc debt movement, etc.).

### 9.4 Sprint execution discipline

- Scope creep is prohibited without written amendment to the Sprint plan.
- Any work not in the Sprint plan requires an EBD or Founder-approved amendment.
- KPIs are updated at end of Sprint, not during (avoids KPI churn).

### 9.5 Sprint retrospective structure

A Sprint retro (`docs/meetings/YYYY-MM/MTG-YYYYMMDD-sprint-retro.md`) contains:

- What shipped (with references to code, docs, decisions).
- What did not ship and why.
- Current KPI values and movement from prior Sprint.
- Documentation Debt incurred this Sprint.
- Technical Debt incurred this Sprint.
- Decisions ratified this Sprint.
- Retro items (what to change next Sprint).
- Updates required to `CURRENT_STATE.md`.

### 9.6 Sprint boundary artifacts

Every Sprint boundary produces, at minimum:

- Sprint retro document.
- Executive Report (six KPIs + supporting metrics per §16.8).
- Updated `CURRENT_STATE.md`.
- Any EBDs required by the retro.

Failure to produce these artifacts is a governance failure. The CTO flags it as such in the next Sprint's Sprint Planning Meeting.

---

## 10. How Decisions Become Official

A decision at NAWA is official when — and only when — three conditions are met:

1. **Written form.** The decision exists as a Decision Log entry at `docs/decisions/<ID>-<slug>.md`.
2. **Approver signature.** The approver has ratified in writing (name, date, effective date in the document header).
3. **Downstream amendments filed.** Any documents affected by the decision have been amended, or a follow-up amendment plan with owner and deadline has been recorded.

A "verbal decision" is not an official decision. A "we agreed to do X" without a Decision Log entry is not an official decision. Decisions that do not exist in Decision Logs do not exist for governance purposes.

### 10.1 Decision IDs

- **EBD-NNN** for Executive Board Decisions (Founder-ratified).
- **ADR-NNN** for Architectural Decision Records (CTO-ratified).
- **PDR-NNN** for Product Decision Records (Aboura-ratified).
- **EDR-NNN** for Engineering Decision Records (AI Engineering Team member-ratified, with mandatory peer review per §4.4).

IDs are assigned monotonically per prefix and are never reused.

### 10.2 The unrecorded-decision correction

If a decision was made informally and never recorded, the CTO drafts a retroactive Decision Log entry documenting: (a) what the decision was, (b) when it was effectively made, (c) who made it, (d) reasoning as best it can be reconstructed, and (e) that it is being formally recorded now.

The retroactive entry is submitted for ratification. Once ratified, the org is back on record. Retroactive decisions are flagged with `Retroactive: yes` in the header.

Every unrecorded decision that surfaces adds a Documentation Debt point (§16.7).

---

## 11. Cross-Functional Responsibilities

Each Board member is accountable for the four functions below within their scope. This section says who owns what across the four functional lanes.

### 11.1 Documentation Responsibilities

| Function | Owner | Executor |
|---|---|---|
| Documentation Standard (this system's rules) | Founder (own) / CTO (steward) | CTO |
| Governance documents authoring | CTO drafts; Founder ratifies | CTO |
| Company Brain documents authoring | CTO facilitates; Founder ratifies | CTO + field participants |
| Technical documents authoring | CTO or Engineering Team authors; CTO approves | Engineering Team (implementation-close) or CTO (contract-level) |
| Product documents authoring | Aboura authors; Founder ratifies for direction | Aboura |
| Meeting documents | CTO records; participants review | CTO |
| Decision Logs | CTO records; per-decision approver ratifies | CTO |
| Documentation health monitoring | CTO owns; reports quarterly | CTO |

### 11.2 Architecture Responsibilities

| Function | Owner | Executor |
|---|---|---|
| Architecture Freeze v1.0 | Founder | CTO drafts and executes |
| Architectural Decision Records | CTO | CTO |
| Freeze protection (see §12) | CTO enforces; Founder authorizes exceptions | CTO |
| Engine contract definitions | CTO | CTO |
| Runtime pipeline documentation | CTO | CTO + Engineering Team |
| Architecture Health KPI | CTO | CTO |

### 11.3 Product Responsibilities

| Function | Owner | Executor |
|---|---|---|
| Product vision | Founder | Aboura executes vision-holding |
| Product roadmap | Aboura | Aboura |
| Product direction changes | Founder ratifies | Aboura drafts |
| Product principles enforcement (Product First, Dogfooding) | Aboura + Founder | Aboura at review; Founder at ratification |
| Personas, positioning, non-goals | Aboura | Aboura |
| User experience decisions | Aboura | Aboura + CTO for architectural implications |

### 11.4 Engineering Responsibilities

Ownership sits with the AI Engineering Team as a whole. Individual assignments within the team rotate per Sprint plan.

| Function | Owner | Executor |
|---|---|---|
| Implementation (backend, frontend, refactoring) | AI Engineering Team | AI Engineering Team members |
| Code quality standards | AI Engineering Team | AI Engineering Team members |
| Test coverage | AI Engineering Team | AI Engineering Team members |
| Implementation-close technical documents | AI Engineering Team | AI Engineering Team members |
| Runtime instrumentation | AI Engineering Team + CTO | AI Engineering Team members |
| Technical Debt reporting | AI Engineering Team flags; CTO consolidates in KPIs | AI Engineering Team + CTO |
| Deployment discipline | AI Engineering Team | AI Engineering Team members |
| Peer review of implementation decisions | AI Engineering Team | Another team member than the author |

---

## 12. Architecture Freeze Protection

The Architecture Freeze exists to prevent architecture churn from destabilizing MVP execution. The freeze is not a suggestion. It is enforced.

### 12.1 What "frozen" means

A component or contract under Architecture Freeze v1.0 (EBD-003, forthcoming) may not be changed except through the unfreeze process (§12.4). Changes include:

- Adding a new engine.
- Removing an engine.
- Changing an engine's inputs, outputs, or responsibilities.
- Changing the runtime pipeline order.
- Changing the data model at contract level.
- Introducing new external dependencies at architectural level.

Non-architectural changes (implementation refactors, performance improvements, bug fixes) are not covered by the freeze and remain in the AI Engineering Team's execution authority.

### 12.2 Enforcement mechanism

Every proposed change is reviewed by the CTO against the Freeze. The review produces one of three outcomes:

- **Within freeze** — CTO may approve directly.
- **Freeze-adjacent, needs judgment** — CTO drafts an ADR; Founder reviews at Sprint boundary.
- **Freeze-breaking** — Requires unfreeze process (§12.4).

The CTO's review determination is written in the Decision Log entry for the proposed change.

### 12.3 The "no new engines during MVP" invariant

The Product Principle "No new engines during MVP" is enforced as a Freeze protection. Any proposal to introduce a new engine before Architecture Freeze v1.0 is lifted requires unfreeze — regardless of how small the proposed engine seems.

This invariant exists because engine additions are the most common form of architecture drift, and each new engine adds validation surface that Runtime Validation Phase cannot absorb without loss of focus.

### 12.4 Unfreeze process

Unfreezing the architecture is an EBD. The process:

1. **Proposal.** Any Board member drafts an unfreeze proposal explaining what change is required and why the freeze must be lifted for it.
2. **Impact review.** CTO produces an impact review: what other components are affected, what documentation must change, what runtime validation must be re-run.
3. **Product review.** Aboura reviews for product implications.
4. **Engineering review.** AI Engineering Team reviews for implementation feasibility.
5. **Founder ratification.** The Founder either ratifies the unfreeze (with scope explicitly bounded), or rejects.
6. **Refreeze.** If unfreeze is granted, the change is made, the affected documents are amended, and the freeze is re-applied with a new version (e.g., Freeze v1.1 or Freeze v2.0 depending on scope). A ratified unfreeze does not leave the architecture indefinitely open.

### 12.5 Emergency exceptions

The Founder retains the authority to authorize an emergency change to frozen architecture. Emergency changes are recorded as EBDs after the fact and reviewed at the next Executive Board Meeting for whether the emergency justified bypassing the standard process. Repeated emergency use is a governance failure to be addressed.

---

## 13. Product First Rule Enforcement

The Product First Rule is: **product direction leads architecture; architecture serves product**. Not the reverse.

### 13.1 Enforcement at review time

- Every Architecture Document is reviewed by Aboura for product implications before CTO approval.
- Every Technical Document is reviewed for whether it introduces product surface changes without a corresponding Product Decision.
- Every Sprint plan is reviewed by Aboura for whether the scope serves product direction.

### 13.2 Enforcement at ratification time

- The Founder does not ratify any EBD that appears to invert the rule — architecture-driven decisions dressed as product decisions are returned to Proposed with the invitation to reframe.

### 13.3 Product First tie-breaker

When architecture and product are in genuine tension, product wins by default unless:

- The architecture case is a Freeze protection (§12) — freeze wins because unfreezing has its own process.
- The architecture case is a safety, correctness, or security constraint — those constraints are always enforced.
- Otherwise, product direction leads.

### 13.4 What Product First does not mean

Product First does not mean product may specify implementation. Aboura defines what NAWA does; CTO defines how NAWA is built; the AI Engineering Team builds it. Product First is about **direction and priority**, not about ownership of technical means.

---

## 14. Dogfooding Principle Enforcement

The Dogfooding Principle is: **NAWA uses NAWA**. The NAWA team's own operational systems, wherever feasible, run on NAWA itself.

### 14.1 Application to governance

Governance documents, meeting artifacts, decision logs, and institutional intelligence live in the NAWA project workspace and — once the product supports it — inside NAWA itself as Company Inputs. The NAWA team is intended to become a NAWA customer of Jannat Al-Firdaws-scale operational complexity, at internal scale.

### 14.2 Enforcement at product-decision time

- Any Product Decision that would make NAWA harder to use internally is examined against the Dogfooding Principle before Aboura ratifies.
- Any decision to build a governance tool outside NAWA (spreadsheets, third-party document systems) instead of NAWA itself is flagged and requires justification.

### 14.3 Interaction with MVP focus

Dogfooding is subordinated to MVP focus. The NAWA team does not delay MVP shipping to dogfood — but once a NAWA capability is stable, the team moves internal use onto it as soon as feasible. The CTO flags dogfooding opportunities in Sprint retros.

### 14.4 Reporting

Dogfooding adoption is a component of Product Health, tracked qualitatively in Executive Reports. Formal metric to be added when dogfooding scope grows.

---

## 15. Principle of Constructive Challenge

### 15.1 The principle

**AI officers are expected to challenge assumptions using evidence. Agreement is not the objective; better decisions are.**

The NAWA Executive Board is AI-augmented. This creates a specific failure mode that governance must actively counter: AI officers producing plausible-sounding agreement rather than substantive disagreement when disagreement is warranted. Constructive Challenge is the antidote. It is a duty, not a permission.

### 15.2 What Constructive Challenge means in practice

- **Challenge is expected, not optional.** An AI officer who never disagrees with a proposal within their scope is either not doing their job or working on decisions too trivial to be at Executive Board level.
- **Challenge is evidence-based.** "I disagree" is not a challenge; "I disagree because <evidence, prior decision, or observed pattern> suggests <specific concern>" is.
- **Agreement is not the goal.** The Board's job is to make better decisions, not to reach consensus quickly. A decision reached without meaningful challenge is a decision that should be re-examined for whether the challenge was skipped.
- **Founder decisions are challengeable up to ratification.** After the Founder ratifies, dissent may still be recorded per §6.4, but execution proceeds.
- **Challenge is bounded by scope.** An officer challenges within their scope authoritatively (CTO on architecture, Aboura on product, Engineering Team on implementation feasibility), and outside their scope with lower weight — as a raised question, not an authority claim.

### 15.3 Enforcement at review time

Every mandatory reviewer (per Appendix A) is expected to produce **substantive** review — one of three outcomes:

- **Approve with substantive rationale.** "Approve — the design correctly handles X and Y; I checked the freeze-adjacency and it's within bounds" is substantive. "Approve" alone is not, and is rejected as a rubber-stamp per §5.3.
- **Approve with recorded reservations.** Approval is granted, but specific concerns are recorded as future review items.
- **Request changes with specific evidence.** The reviewer identifies the specific issue and the evidence for it.

Silence, generic assent, and "looks good" without content are all treated as non-review under §5.3.

### 15.4 Enforcement at ratification time

The Founder ratifies decisions. If a ratification arrives without any recorded challenge from any officer, the Founder may return the decision to review with the note "no challenge recorded — reviewer engagement insufficient." This is not a rejection of the decision; it is a rejection of the review quality.

### 15.5 Enforcement at retrospective time

Every Sprint retro includes a Decision Quality reflection (see §16.6 KPI). If a Sprint produced material decisions with zero recorded challenges, the retro flags this as a governance signal — the Board is either agreeing too easily or challenging outside the record.

### 15.6 What Constructive Challenge is not

- It is not obstruction. An officer who challenges every proposal without differentiation is not constructive.
- It is not repeating the same challenge after it has been addressed. Once evidence has been supplied, either the challenge holds or it doesn't; recycling defeated challenges is noise.
- It is not personal. Challenges are directed at the proposal, not at the proposer. An AI officer disagreeing with the Founder is not disrespecting the Founder; it is doing its job.
- It is not a way to slow things down. A challenge without a suggested improvement or an alternative is weaker than a challenge with one.

### 15.7 The zero-challenge signal

A Sprint or a quarter in which zero officer challenges are recorded is treated as a documentation gap, not evidence of Board harmony. The CTO investigates: challenges likely happened but were not recorded, which is worse than challenges not happening at all. Recording is not optional; unrecorded challenge is invisible to future review.

---

## 16. Executive KPIs

Per EBD-002 additional decisions, every Executive Report includes six KPIs. The CTO owns their measurement and reporting; ownership of remediation varies per KPI (below).

### 16.1 Documentation Health (CTO KPI)

**Definition:** A composite health score for the documentation system.

**Components:**
- **Coverage** — % of runtime engines with current documentation.
- **Freshness** — % of documents that updated when their trigger fired (per Documentation Standard §6).
- **SSoT compliance** — number of duplicate-truth violations detected in the reporting period.
- **Cross-reference integrity** — % of file-path references that resolve to existing files.

**Owner (measurement):** CTO.
**Owner (remediation):** Document owners individually; CTO for systemic issues.
**Reporting:** Every Sprint retro; full breakdown quarterly.

### 16.2 Knowledge Continuity (CTO KPI)

**Definition:** The organization's resilience to personnel change — how well institutional knowledge survives when any single member leaves. Distinct from Documentation Health: Documentation Health measures the system; Knowledge Continuity measures the org's dependence on tribal knowledge.

**Components:**
- **Onboarding readiness** — measured or estimated time for a new engineer to become productive from documentation alone (target: 2 working days per Documentation Standard §13).
- **Decision reasoning coverage** — % of material decisions in the reporting period with recorded reasoning (not just the "what" but the "why").
- **Critical knowledge redundancy** — % of core operational knowledge captured in at least one document (vs. living only in tribal or session memory).
- **Historical traceability** — % of retired decisions and superseded documents still reachable in `docs/archive/` with intact context.

**Owner (measurement):** CTO.
**Owner (remediation):** Distributed across all document owners; CTO consolidates and flags gaps.
**Reporting:** Every Sprint retro; full audit quarterly.

### 16.3 Runtime Health

**Definition:** State of the live runtime.

**Components:**
- Engines currently live (count and identification).
- Runtime Validation Phase progress — % of engines validated against real Company Input.
- Error rates, latency, and uptime (once instrumentation is in place).
- Runtime documents produced this Sprint.

**Owner (measurement):** CTO + AI Engineering Team.
**Owner (remediation):** AI Engineering Team for operational issues; CTO for validation coverage.
**Reporting:** Every Sprint retro.

### 16.4 Architecture Health

**Definition:** How well the system as-built matches the system as-designed.

**Components:**
- Freeze compliance — number of freeze-crossing changes attempted in the period.
- Component documentation completeness — % of components with current contract-level documentation.
- Dependency graph consistency — % of documented dependencies that match actual imports/wiring.

**Owner (measurement):** CTO.
**Owner (remediation):** CTO plans; Founder ratifies material remediation.
**Reporting:** Every Sprint retro; full audit quarterly.

### 16.5 Technical Debt

**Definition:** Deferred implementation work that is known and recorded.

**Components:**
- Known deferrals recorded in ADRs.
- TODOs in code referencing an ADR or a Decision Log entry.
- Test coverage gaps recorded as debt.
- Refactor work identified but not scheduled.

**Owner (measurement):** AI Engineering Team flags; CTO consolidates.
**Owner (remediation):** AI Engineering Team plans; CTO reviews at Sprint retro.
**Reporting:** Every Sprint retro.

### 16.6 Decision Quality (CTO KPI)

**Definition:** How well the organization decides. A meta-KPI on the decision-making process itself; anchored in the Principle of Constructive Challenge (§15).

**Components:**
- **Alternative consideration** — % of material decisions that document alternatives considered before the final choice.
- **Substantive review** — % of decisions where every mandatory reviewer produced substantive (non-rubber-stamp) review per §15.3.
- **Challenge presence** — number of recorded officer challenges per decision, and the count of Sprints with zero recorded challenges (which is a red flag per §15.7, not a green one).
- **Review budget compliance** — % of decisions reviewed within their §7.2 budget.
- **Reversal rate** — % of decisions materially amended or reversed within four Sprints of ratification. Interpretation: some reversal is healthy; a high reversal rate signals shallow initial review.
- **Dissent capture rate** — % of decisions where dissent, if present, was recorded per §6.4.

**Owner (measurement):** CTO.
**Owner (remediation):** All officers individually improve their own review quality; CTO flags systemic patterns; Founder ratifies structural changes to the review process.
**Reporting:** Every Sprint retro; deep quality review quarterly.

### 16.7 Documentation Debt (supporting project metric)

**Status:** Supporting metric, reported alongside the six KPIs but not itself a top-line KPI. Retained from EBD-002's original decisions on Executive Report content.

**Definition:** Documentation obligations that have been incurred but not yet met.

**Components:**
- Documents that missed their update trigger and remain stale.
- Code changes shipped without corresponding documentation updates.
- Decisions made informally and not yet recorded in Decision Logs (retroactive-decision correction pending).
- Cross-reference breakages.

**Measurement:** Point count per Sprint. Every debt instance = 1 point. Prioritization by category (governance debt highest; technical debt category lower).

**Owner (measurement):** CTO.
**Owner (remediation):** Whoever owns the debt-generating change.
**Reporting:** Every Sprint retro. Trajectory (increasing / decreasing / stable) is the interesting metric.

### 16.8 Executive Report format

Every Sprint retro's KPI section includes the six KPIs plus the Documentation Debt supporting metric:

```
=== EXECUTIVE REPORT — SPRINT NN ===
Sprint dates:
CTO signature:

--- EXECUTIVE KPIs ---
Documentation Health:      score / trend
Knowledge Continuity:      score / trend
Runtime Health:            score / trend / engines live
Architecture Health:       score / trend
Technical Debt:            points / trend / top three items
Decision Quality:          score / trend / challenge count this Sprint

--- SUPPORTING METRIC ---
Documentation Debt:        points / trend / top three items

--- COMMENTARY ---
Executive summary (three sentences):
Constructive Challenges recorded this Sprint (per §15):
Risks flagged this Sprint:
Recommendations for next Sprint:
=== END REPORT ===
```

---

## 17. Amendment Process

This document is a governance document. It is amended by Executive Board Decision.

### 17.1 Amendment triggers

Amendment is required when:

- A new Board seat is added, removed, or restructured.
- A responsibility boundary changes.
- A meeting cadence or Sprint length changes.
- A KPI is added, removed, or redefined.
- A conflict resolution rule proves insufficient in practice.
- The org grows past a size threshold that changes meeting cadence.

### 17.2 Amendment mechanics

Amendment follows the Documentation Standard §12.5:

1. Draft the amendment as a new version file or as an amendment note.
2. CTO review within 5 working days.
3. Board review within the standard review budget.
4. Founder ratification via EBD.
5. Old version archived; new version live; amendment log entry added (Appendix D).

### 17.3 Emergency amendment

The Founder may make an emergency amendment when governance itself is blocking Sprint execution. Emergency amendments are recorded post hoc and reviewed at the next Executive Board Meeting for whether the emergency justified the compressed process.

---

## 18. Final Principles

- **Authority is defined, not assumed.** Every role knows what it may decide and what it may not.
- **Decisions are recorded, not implied.** A decision without a Decision Log entry does not exist.
- **Dissent is preserved, not suppressed.** Officers may execute decisions they disagree with, but their disagreement stays on record.
- **Constructive Challenge is a duty.** AI officers are expected to challenge assumptions using evidence. Agreement is not the objective; better decisions are. Silence is not review (§15).
- **The Founder decides.** Governance is not a committee. Ambiguity resolves upward.
- **Governance serves the project.** If the governance model is slowing NAWA down more than it is preventing errors, it is wrong and must be amended.
- **Architecture Freeze protects execution.** The freeze is not paperwork. It is the boundary that lets Runtime Validation Phase converge.
- **Product First, Dogfooding, No New Engines During MVP** are load-bearing principles. Their enforcement mechanisms are defined in §13, §14, and §12.3.
- **This governance model is Executive Board Decision #002.** It is ratified by the Founder and becomes the operating system of the NAWA organization.

---

## Appendix A — Approval Matrix (Full)

"Engineering Team" in the tables below refers to the AI Engineering Team as defined in §4.4. "ETM" abbreviates "AI Engineering Team member." Peer review means another team member than the author (or the CTO if team size = 1).

| # | Decision Type | Approver | Mandatory Reviewers | Decision ID Prefix |
|---|---|---|---|---|
| 1 | Governance document, new | Founder | CTO, Aboura, Engineering Team if impl | EBD |
| 2 | Governance document, amendment | Founder | CTO | EBD |
| 3 | Board seat change | Founder | Founder-only structural | EBD |
| 4 | Product vision or direction change | Founder | Aboura, CTO | EBD |
| 5 | Product roadmap update | Aboura | CTO | PDR |
| 6 | Product execution decision (no direction change) | Aboura | CTO if arch, Engineering Team if impl | PDR |
| 7 | Persona / positioning / non-goal change | Aboura | Founder review | PDR |
| 8 | Architecture Freeze, freeze | Founder | CTO, Engineering Team, Aboura | EBD |
| 9 | Architecture Freeze, unfreeze | Founder | CTO, Engineering Team, Aboura | EBD |
| 10 | Architecture Freeze, refreeze | Founder | CTO, Engineering Team | EBD |
| 11 | Architectural change within freeze | CTO | Engineering Team, Aboura if user-facing | ADR |
| 12 | Engine contract definition | CTO | Engineering Team | ADR |
| 13 | Technical decision (module contract, contract-level) | CTO | Engineering Team | ADR |
| 14 | Implementation decision (code-close) | ETM closest to change | Peer ETM; if team size = 1, another approved AI engineer designated by CTO, or Founder. CTO never substitutes. | EDR |
| 15 | Company Brain doctrine update | Founder | CTO, Aboura if surface | EBD |
| 16 | Company Brain workshop output | Founder | CTO facilitator | EBD |
| 17 | Runtime validation acceptance | CTO | Engineering Team, Founder for milestones | ADR |
| 18 | Sprint plan | Founder | Aboura, CTO, Engineering Team | Meeting doc |
| 19 | Sprint retro | CTO | Aboura, Engineering Team, Founder review | Meeting doc |
| 20 | Emergency change to frozen architecture | Founder | (post-hoc review) | EBD |
| 21 | Amendment to this document | Founder | CTO | EBD |
| 22 | AI Engineering Team membership change (per §4.4 extensibility clause) | CTO invites; Founder informed | none required | Meeting doc (not EBD) |

---

## Appendix B — Meeting Templates

### B.1 Executive Board Meeting

```
=== EXECUTIVE BOARD MEETING — MTG-YYYYMMDD ===
Date:
Sprint:
Participants:
  Founder:
  Aboura (CPO):
  Claude Cowork (CTO):
  AI Engineering Team representative (when agenda affects implementation):
    - name:
    - representing team members present:

--- PENDING EBDs FOR RATIFICATION ---
EBD-NNN — <title>
  Reviewer comments:
  Ratification: ratified / returned / rejected

--- EXECUTIVE REPORT (from CTO) ---
(six KPIs + supporting metrics per §16.8)

--- DECISIONS REQUESTED ---
D1. <question>
    Recommendation:
    Ratification:

--- MEETING OUTCOMES ---
Documents amended:
Follow-ups assigned:

=== END MEETING ===
```

### B.2 Sprint Retrospective

```
=== SPRINT RETRO — SPRINT NN ===
Sprint dates:
CTO:

--- SHIPPED ---
- <item> — <reference>

--- DID NOT SHIP ---
- <item> — reason

--- KPIS ---
(six KPIs + supporting metrics per §16.8)

--- DEBT INCURRED ---
Documentation Debt:
Technical Debt:

--- DECISIONS RATIFIED THIS SPRINT ---
- EBD-NNN, ADR-NNN, PDR-NNN, EDR-NNN

--- RETRO ITEMS ---
Change next Sprint:
Continue next Sprint:

--- CURRENT_STATE.md UPDATE PLANNED ---
Sections to update:

=== END RETRO ===
```

### B.3 Sprint Planning

```
=== SPRINT PLAN — SPRINT NN ===
Sprint dates:
Approver: Founder

--- OBJECTIVES (3–5 max) ---

--- SCOPE ---
Item — Owner — Success criterion

--- EXPLICIT NON-SCOPE ---

--- RISKS AND MITIGATIONS ---

--- KPI TARGETS ---

--- APPROVAL ---
Founder ratification date:
=== END PLAN ===
```

---

## Appendix C — Glossary

- **ADR** — Architectural Decision Record. CTO-ratified decision on architecture within freeze.
- **AI Engineering Team** — The distinct executing body under CTO technical direction and Aboura product direction; contains Senior AI Software Engineers (initially Claude Code and Codex). Not a Board seat. Extensible without governance amendment (§4.4).
- **Approver** — the role authorized to ratify a decision. Distinct from reviewer.
- **Board** — the NAWA Executive Board (three members per §3: Founder, CPO Aboura, CTO Claude Cowork).
- **Constructive Challenge** — the principle that AI officers challenge assumptions using evidence; agreement is not the objective, better decisions are (§15).
- **Decision Quality** — the Executive KPI measuring how well the org decides — alternative consideration, substantive review, challenge presence, review budget compliance, reversal rate, dissent capture (§16.6).
- **Dissent** — written disagreement recorded against a ratified decision by an officer who is nonetheless executing it (§6.4).
- **Dogfooding** — the principle that NAWA uses NAWA internally where feasible (§14).
- **EBD** — Executive Board Decision. Founder-ratified decision at highest governance level.
- **EDR** — Engineering Decision Record. AI Engineering Team member-ratified implementation decision, with mandatory peer review.
- **ETM** — AI Engineering Team member.
- **Freeze** — Architecture Freeze state; no architectural changes without unfreeze process (§12).
- **Knowledge Continuity** — the Executive KPI measuring organizational resilience to personnel change; the extent to which institutional knowledge survives when any single member leaves (§16.2).
- **KPI** — Key Performance Indicator. Six Executive KPIs are reported in every Executive Report (§16).
- **PDR** — Product Decision Record. Aboura-ratified product execution decision.
- **Peer review** (in the engineering context) — review by another AI Engineering Team member than the author. If the team size is 1, review is performed by (a) another approved AI engineer designated by the CTO for the purpose, or (b) the Founder. The CTO is explicitly excluded from performing engineering peer review, to preserve the architecture-implementation review separation.
- **Product First** — the principle that product direction leads architecture (§13).
- **Ratification** — the act of an approver making a decision official. Written, dated, signed.
- **Retroactive decision** — a decision made informally, recorded after the fact for governance compliance (§10.2).
- **Senior AI Software Engineer** — the title held by every AI Engineering Team member. All members are peers; there is no hierarchy within the team (§4.4).
- **Sprint** — the unit of planning and execution; two working weeks by default (§9).
- **Team representation at Board** — the mechanism by which Engineering Team perspective enters Board decisions; a designated team member participates or contributes written review, per §4.4.

---

## Appendix D — Amendment Log

| Version | Date | Change | Authority | Reference |
|---|---|---|---|---|
| 1.0 | 2026-07-03 | Initial draft submitted for Executive Board review. | CTO (draft); Founder (ratification pending) | EBD-002 |
| 1.0-a1 | 2026-07-03 | Pre-ratification amendment: (a) Board reduced from four to three seats; LSE role removed as a Board seat. (b) AI Engineering Team introduced (§4.4) as a distinct executing body containing Claude Code and Codex as peer Senior AI Software Engineers, with an extensibility clause allowing future engineers to join without governance amendment. (c) CTO clarified as having no execution authority — architecture, documentation, and technical direction only; no production code implementation. (d) Approval matrix, meeting participation, cross-functional matrices, KPI ownership, glossary, and templates updated. Version stays at 1.0 (pre-ratification amendment). | Founder direction; CTO amendment | EBD-002 additional amendment |
| 1.0-a2 | 2026-07-03 | Pre-ratification amendment set two: (a) CTO explicitly excluded from performing engineering peer review; substitution rule now: another approved AI engineer designated by CTO, or Founder — never CTO. Preserves architecture-implementation review separation. (b) AI Engineering Team declared technology-agnostic — not tied to any specific AI system, model family, or provider; future members from any provider accommodated without governance redesign. (c) Principle of Constructive Challenge added as new §15 with enforcement mechanisms at review, ratification, and retrospective time. (d) Executive KPIs expanded from five to six: Knowledge Continuity (§16.2) and Decision Quality (§16.6) added; ordering aligned to Founder specification; Documentation Debt demoted to supporting metric alongside the six KPIs. (e) Downstream renumbering: KPIs §15 → §16; Amendment Process §16 → §17; Final Principles §17 → §18. Executive Report format updated. Version stays at 1.0. | Founder direction (final pre-ratification amendments); CTO amendment | EBD-002 additional amendments |
| 1.0 | 2026-07-03 | **Ratified** by Founder as Executive Board Decision #002. Effective immediately. | Founder | EBD-002 |

---

*This document is ratified and authoritative as of 2026-07-03. It defines who decides, what happens when we disagree, and how we know a decision is real. Everything downstream — Architecture Freeze v1.0, Engine Definitions, COWORK v2.0 — inherits authority from this model.*
