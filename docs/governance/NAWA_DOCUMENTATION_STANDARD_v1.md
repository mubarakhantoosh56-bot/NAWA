# NAWA Documentation Standard — v1

**Status:** Ratified as Executive Board Decision #001. Constitutional.
**Version:** 1.0
**Phase:** Runtime Validation Phase.
**Scope:** All NAWA project documentation. Applies to every document produced under any NAWA repository, workspace, or brain.
**Owner:** Founder & CEO (Mubarak), with the CTO (Claude Cowork) as steward.
**Effective date:** 2026-07-03.
**Last updated:** 2026-07-03.

---

## 1. Purpose

Documentation exists to make NAWA **independent of any single person's memory**. Every piece of knowledge that governs how the product is built, decided, operated, or evolved must live in a document that outlasts the moment it was created.

The organization's ability to continue if any single member — Founder, CTO, engineer, product lead — walks away tomorrow is a direct function of documentation quality. This standard exists so that continuity is engineered, not hoped for.

Concretely, documentation serves five functions:

1. **Continuity.** The project survives personnel changes without losing context.
2. **Onboarding.** A new engineer can become productive from documents, not from tribal knowledge.
3. **Decision-making.** Choices are traceable to reasoning, evidence, and authorship.
4. **Architecture integrity.** The system as-built and the system as-designed do not drift silently.
5. **Product evolution.** Product direction changes are recorded, not implied.

Anything that does not serve one of these five functions is not documentation. It is a note.

---

## 2. Documentation Philosophy

### 2.1 Documentation is institutional knowledge, not notes.

A note captures what someone was thinking at a moment. Documentation captures what the organization has agreed. The transition from note to documentation is deliberate: a document is written to be *read by someone who was not in the room*.

If a reader who was not present cannot use the document to make the same decision, take the same action, or hold the same understanding as the original author, the document has failed.

### 2.2 Documentation must support the five functions.

Every document is written with at least one of the five functions in Section 1 in mind. A document that serves none of them does not belong in the repository.

### 2.3 Documentation is a first-class deliverable.

Documentation is not "written afterwards." A change that ships without a corresponding documentation update is an incomplete change. This applies equally to architecture, product, and technical work.

### 2.4 Documentation is versioned.

Every constitutional or architectural document carries a version. Amendments are recorded, not silently applied.

### 2.5 Documentation closes decisions.

A document that ends with "we could do A, B, or C" is not a document. It is a discussion. The author of a document is responsible for closing the decision it addresses, or explicitly marking it as unresolved with an assigned owner and a resolution deadline.

### 2.6 Documentation preserves reasoning.

The **why** of a decision is more valuable than the **what**. A document that records what was decided without recording why can be re-litigated forever. A document that records why cannot.

### 2.7 Documentation is written in the reader's language.

Operational, direct, precise. No enterprise jargon. No filler. Arabic where the audience is Arabic-first. English where the audience is engineering-first. Bilingual where both matter.

---

## 3. Documentation Categories

NAWA recognizes ten documentation categories. Every document belongs to exactly one category. Category is declared in the document header.

### 3.1 Architecture Documents

- **Purpose:** Define the system as-designed — components, boundaries, contracts, invariants, freezes.
- **Examples:** Architecture Freeze v1.0 spec, engine interface contracts, data model definitions, dependency maps.
- **Location:** `docs/architecture/`
- **Primary owner:** CTO (Claude Cowork).
- **Approval authority:** Founder for major architectural decisions; CTO for internal architectural refinements.

### 3.2 Governance Documents

- **Purpose:** Define how the organization operates — decision authority, roles, processes, standards.
- **Examples:** This standard, Executive Board Decisions, Sprint operating model, escalation paths.
- **Location:** `docs/governance/`
- **Primary owner:** Founder.
- **Approval authority:** Founder. Governance documents are ratified, not merged.

### 3.3 Product Documents

- **Purpose:** Define what NAWA is, who it serves, how it wins, and what it will and will not become.
- **Examples:** Product vision, positioning, roadmap, personas, non-goals.
- **Location:** `docs/product/`
- **Primary owner:** Chief Product & AI Strategy (Aboura).
- **Approval authority:** Founder for direction-setting documents; Aboura for product execution documents.

### 3.4 Company Brain Documents

- **Purpose:** Domain-specific operational truth — how a company, department, or workflow actually operates. Used by NAWA to reason correctly about the domain.
- **Examples:** `DAIRTNA_OPERATIONAL_SEMANTICS.md`, `DAIRTNA_OPERATIONAL_INTERPRETATION.md`, `JANNAT_INGESTION_PLAYBOOK.md`, future Caesar equivalents.
- **Location:** `docs/nawa_brain/`
- **Primary owner:** Founder (for domain truth), with facilitation by CTO.
- **Approval authority:** Founder, informed by field validation (see `HYPOTHESIS_PREVALIDATION_WORKSHOP.md`).

### 3.5 Technical Documents

- **Purpose:** Implementation-facing specifications, interface contracts, service designs, testing standards.
- **Examples:** Repository layer contract, engine implementation spec, API surface documentation, testing conventions.
- **Location:** `docs/technical/`
- **Primary owner:** CTO, with authorship by Lead Software Engineer (Codex) or delegated engineers.
- **Approval authority:** CTO.

### 3.6 Runtime Documents

- **Purpose:** Describe the live runtime — what is deployed, what is executing, what is being validated, what is instrumented.
- **Examples:** Runtime validation reports, per-engine live-state summaries, current active runtime pipeline description, real-data validation results.
- **Location:** `docs/runtime/`
- **Primary owner:** CTO, with contributions from Lead Software Engineer.
- **Approval authority:** CTO.

### 3.7 Meeting Documents

- **Purpose:** Record what an Executive Board meeting, Sprint meeting, or working session decided. Not transcripts. Decisions and their reasoning.
- **Examples:** Executive Board Decision #NNN, Sprint retrospective, workshop decision logs, working session outcomes.
- **Location:** `docs/meetings/YYYY-MM/`
- **Primary owner:** The meeting's designated recorder. If unassigned, the CTO.
- **Approval authority:** All meeting participants sign off within one working day; unresolved sign-off escalates to the Founder.

### 3.8 Decision Logs

- **Purpose:** Archive of every material decision, indexed by ID, with reasoning, alternatives considered, and outcomes. Includes Architectural Decision Records (ADRs) and Executive Board Decisions (EBDs).
- **Examples:** `EBD-001-documentation-standard.md`, `ADR-014-architecture-freeze-v1.md`.
- **Location:** `docs/decisions/`
- **Primary owner:** CTO.
- **Approval authority:** As determined by decision type — EBDs require Founder ratification; ADRs require CTO approval.

### 3.9 Current State

- **Purpose:** Snapshot of where the project is *right now*. Always the first read on returning to the project.
- **Examples:** `CURRENT_STATE.md`.
- **Location:** Repository root.
- **Primary owner:** CTO.
- **Approval authority:** CTO, with Founder review at each Sprint boundary.
- **Cardinality:** Exactly one. There is only ever one `CURRENT_STATE.md`.

### 3.10 Agent Instructions

- **Purpose:** Rules and posture for AI agents working on NAWA. Governs coding behavior, scope discipline, approval gates.
- **Examples:** `AGENTS.md` (rules for all engineering agents), `CLAUDE.md` (Claude-specific posture), future `CODEX.md`.
- **Location:** Repository root, or `docs/agents/`.
- **Primary owner:** CTO.
- **Approval authority:** Founder for scope and authority rules; CTO for operational refinements.

---

## 4. Source of Truth Rules

Every question about "which document is authoritative for X" has exactly one answer. When two documents disagree, the source-of-truth document wins by default; the other document is either amended or explicitly marked as superseded.

| Domain | Authoritative Document | Location |
|---|---|---|
| **Architecture (as-designed)** | Architecture Freeze v1.0 spec | `docs/architecture/ARCHITECTURE_FREEZE_v1.md` (to be created if not present) |
| **Current execution state** | `CURRENT_STATE.md` | Repository root |
| **Runtime pipeline (as-executing)** | `docs/runtime/RUNTIME_PIPELINE_CURRENT.md` (to be created) | `docs/runtime/` |
| **Roadmap** | Product roadmap | `docs/product/ROADMAP.md` (owned by Aboura) |
| **Project rules and governance** | This standard + Executive Board Decisions | `docs/governance/` |
| **Company Brain (Dairtna)** | Semantics + Interpretation + Ingestion + Workshop docs | `docs/nawa_brain/` |
| **Decision history** | Decision Logs | `docs/decisions/` |
| **Technical implementation contracts** | Technical Documents | `docs/technical/` |
| **Agent behavior rules** | `AGENTS.md` and `CLAUDE.md` | Repository root or `docs/agents/` |
| **Institutional intelligence (integrated view)** | COWORK v2.0 | `docs/nawa_brain/COWORK_V2_INSTITUTIONAL_INTELLIGENCE.md` |

### 4.1 Tie-breaking

If two documents disagree on any fact, the following order determines which wins:

1. **The domain-authoritative document** (per the table above) wins over any general document.
2. If neither is domain-authoritative, **the more recently ratified version** wins.
3. If versions are equal, the disagreement is escalated to the CTO and, if unresolved, to the Founder as an Executive Board Decision.
4. **No silent divergence.** The losing document is amended to match, or explicitly annotated with a supersession notice.

### 4.2 Derived documents

COWORK v2.0 and other integrated views are **derived**. They cite sources but do not create new truth. If COWORK v2.0 and its source disagree, the source wins and COWORK is amended.

---

## 5. Ownership

Every document has exactly one **primary owner**. Ownership is not authorship — it is accountability for the document being correct, current, and coherent with the rest of the standard.

| Role | Owns (Primary) | Reviews | Executes On |
|---|---|---|---|
| **Founder & CEO (Mubarak)** | Governance, Product vision, Company Brain (domain truth), Current State (at Sprint boundary), Architecture direction | All Executive Board Decisions, any decision changing product direction or organizational structure | Ratification of governance and product direction |
| **Chief Product & AI Strategy (Aboura)** | Product Documents, Roadmap, Product Decisions | Governance decisions affecting product, Architecture decisions affecting UX, Company Brain updates affecting user experience | Product execution documents |
| **Chief Technology & Architecture Officer (Claude Cowork)** | Architecture Documents, Technical Documents, Runtime Documents, Decision Logs, Current State, Agent Instructions, COWORK v2.0 | All Company Brain documents, all Architecture Decisions, all Executive Board Decisions affecting execution | Architecture reviews, technical documentation, decision recording, continuous documentation health |
| **Lead Software Engineer (Codex)** | Implementation-close technical documents (module contracts, service designs authored during implementation) | Architecture Documents affecting their work | Implementation, test authorship, code-close documentation |
| **Future Team Members (Engineers)** | Their own technical designs, ADRs they author, module documentation | Peer review of adjacent technical documents | Implementation, testing, technical documentation authorship, participation in Executive Board Decisions when their scope is affected |

### 5.1 Delegation

An owner may delegate authorship. Ownership itself does not delegate — the accountable owner remains accountable.

### 5.2 Owner absence

If an owner is unavailable for longer than one Sprint, the CTO assumes ownership on an interim basis and records the interim in the document header. Interim ownership does not confer approval authority beyond the CTO's existing authority.

### 5.3 Ownership disputes

Ownership disputes escalate to the Founder as an Executive Board Decision. There is no committee ownership.

---

## 6. Update Rules

Documents update on defined triggers. A document that has not updated when its trigger fired is treated as **stale** and flagged in the next Executive Board Meeting.

| Document Category | Update Trigger | Frequency Cap |
|---|---|---|
| **Governance** | Executive Board Decision ratifying a change | As decided |
| **Architecture** | Architectural Decision Record; unfreeze/refreeze event | On decision; batched no more than weekly |
| **Product** | Product direction change; new persona; new market decision | On decision |
| **Company Brain** | Field validation output; new domain-truth learned; hypothesis promotion/demotion per `HYPOTHESIS_VALIDATION_PROTOCOL.md` | On workshop or validated evidence |
| **Technical** | Interface change; contract change; new module | On change; must accompany the code change, not follow it |
| **Runtime** | New deployment; validation run; measured runtime behavior change | Weekly minimum during Runtime Validation Phase; on-change otherwise |
| **Meeting** | End of meeting | Within one working day of the meeting |
| **Decision Logs** | Any material decision | On decision |
| **Current State** | End of every Sprint; end of any phase transition; any material milestone | At least every Sprint |
| **Agent Instructions** | Change in agent scope, authority, or approval gate | On decision |

### 6.1 Update discipline

A documentation update is not "when there is time." It is part of the work item that triggered it. Code changes without documentation updates are incomplete. Decisions without a Decision Log entry are unrecorded and therefore do not exist for governance purposes.

### 6.2 Stale flag

A document not updated when its trigger fired is flagged with `STALE — <trigger>` in its header until the update is made. Stale documents may not be cited as source of truth.

---

## 7. Versioning Rules

NAWA uses a simplified two-part version scheme for documentation:

**`vMAJOR.MINOR`**

- **MAJOR** increments on constitutional or structural change. New MAJOR requires ratification by the document's approval authority.
- **MINOR** increments on substantive amendment that does not change the document's structure or authority. New MINOR requires review by the approval authority but does not require re-ratification.
- Typographic, formatting, and cross-reference fixes do not change the version.

### 7.1 Where versions live

- **In the filename** only for constitutional documents (this standard, Architecture Freeze), e.g., `NAWA_DOCUMENTATION_STANDARD_v1.md`.
- **In the header** for all other categories, as `Version: X.Y`.

Versioned filenames survive as history when a new MAJOR is published — `_v1.md` remains, `_v2.md` is added, and the older file becomes read-only (see Section 8 Archived state).

### 7.2 Version transitions

Every MAJOR transition produces:

1. A new file at the new version.
2. An entry in `docs/decisions/` recording the transition and reasoning.
3. An amendment log inside the new file's Appendix (summary of what changed).
4. Archival of the prior file with `STATUS: Archived (superseded by vN)` at the top.

### 7.3 No silent minor edits

Minor amendments are recorded in the document's amendment log even if the version does not change (i.e., typographic fixes do not update version but are logged if the change is content-touching).

---

## 8. Documentation Lifecycle

Every document moves through four states.

| State | Meaning | Location | Cite as Source of Truth? |
|---|---|---|---|
| **Draft** | Under authorship. Not yet reviewed. | `docs/drafts/<category>/` | No |
| **Review** | Authored and submitted; under review by approval authority | Target location, with `Status: Review` in header | No |
| **Approved** | Ratified by approval authority. Live. | Target location, with `Status: Ratified` or `Status: Approved` in header | Yes |
| **Archived** | Superseded, retired, or no longer applicable | `docs/archive/YYYY/` | Historical only |

### 8.1 Transition rules

- **Draft → Review:** the author submits the document to the approval authority with a link and a one-paragraph summary of what changed.
- **Review → Approved:** the approval authority either approves (document moves to target location, status updated) or requests changes (returns to Draft).
- **Approved → Archived:** triggered by supersession (a new version), retirement (no longer applicable), or explicit decommission. Archival is a decision recorded in `docs/decisions/`.
- **Archived → any state:** not permitted. Archived documents are read-only. Reviving content requires a new document that cites the archived one.

### 8.2 Review time budget

Governance and Architecture documents: reviewed within one week of submission. Company Brain and Technical documents: reviewed within three working days. Meeting documents: reviewed within one working day. Reviews exceeding budget are flagged in the next Executive Board Meeting.

---

## 9. Naming Standards

### 9.1 Folder structure

The `docs/` tree at scale:

```
docs/
├── governance/          Governance documents (this standard, EBDs, org processes)
├── architecture/        Architecture documents (freezes, engine contracts, invariants)
├── product/             Product documents (vision, roadmap, positioning, personas)
├── nawa_brain/          Company Brain documents (Dairtna, future Caesar, integrated views)
├── technical/           Technical documents (module contracts, service designs)
├── runtime/             Runtime documents (validation reports, live-state summaries)
├── meetings/            Meeting documents, organized by year-month
│   └── YYYY-MM/
├── decisions/           Decision Logs (EBDs, ADRs)
├── agents/              Agent instructions (if not at repo root)
├── drafts/              Documents in Draft state, mirrors the target category folder
└── archive/             Archived documents, organized by year
    └── YYYY/
```

`CURRENT_STATE.md` and repo-root agent instructions (`AGENTS.md`, `CLAUDE.md`) may live at the repository root due to established convention. All new documents follow the folder structure above.

### 9.2 File naming conventions

- **SCREAMING_SNAKE_CASE** for all doctrine and constitutional documents (e.g., `NAWA_DOCUMENTATION_STANDARD_v1.md`, `DAIRTNA_OPERATIONAL_SEMANTICS.md`).
- **Prefixed IDs** for Decision Logs and Meeting Documents:
  - `EBD-NNN-<slug>.md` for Executive Board Decisions.
  - `ADR-NNN-<slug>.md` for Architectural Decision Records.
  - `MTG-YYYYMMDD-<slug>.md` for meeting notes.
- **Version suffix** only on constitutional and architecture documents that carry versioned filenames: `_v1.md`, `_v2.md` (lowercase `v`, no separator).
- **No spaces, no accents in filenames.** Arabic content lives inside files, not in filenames.
- **Index files** are named `00_<TOPIC>_INDEX.md` and sort first alphabetically within their folder.

### 9.3 Header block (required on every document)

Every document begins with a header block containing:

- `Status:` — Draft / Review / Ratified or Approved / Archived (+ superseding version if any).
- `Version:` — `X.Y`.
- `Category:` — one of the ten in Section 3.
- `Scope:` — one sentence on what the document governs.
- `Non-scope:` — one sentence on what it explicitly does not govern.
- `Owner:` — primary owner role and name.
- `Approval authority:` — role of the approver.
- `Effective date:` — first date the document is authoritative.
- `Last updated:` — date of the most recent content-touching edit.

Documents missing a header block are treated as Draft regardless of their apparent content.

---

## 10. Documentation Principles

These are the hard rules. They apply to every document in every category.

### P1. Single Source of Truth (SSoT)

Every fact has exactly one authoritative document. Every other document that references the fact cites the source. Duplicating the fact is prohibited; when duplication happens, the two copies diverge over time.

### P2. No duplicated knowledge

Two documents may not restate the same content. One document owns the content; others link to it. If the content genuinely applies to two contexts, the shared content lives in one place and both contexts reference it.

### P3. Document decisions, not conversations

A meeting record captures *what was decided and why*. It does not capture *what was said by whom in what order*. Transcripts are not documentation. Decisions are.

### P4. Preserve historical context

A superseded document is archived, not deleted. A retired decision is annotated with the reason for retirement, not erased. Anyone reading the archive must be able to reconstruct why the organization believed what it once believed.

### P5. Never lose reasoning behind decisions

Every decision document records the reasoning. "We chose X" is incomplete. "We chose X because Y, and Z was rejected because W" is complete. A decision without recorded reasoning may be re-litigated indefinitely.

### P6. Close, do not open

A document ends by closing decisions, not by opening options. If the document cannot close, it identifies the specific unresolved question, assigns an owner, and sets a resolution deadline. Documents that end in ambiguity are not documentation.

### P7. Scope before content

Every document declares its scope and its non-scope before any content. A reader must be able to know within the first thirty seconds whether the document is relevant to them.

### P8. Reader over author

A document is written for the person who did not attend the meeting, was not in the room, and does not have the author's context. If the reader cannot use the document to do what the author intended, the document has failed.

### P9. Operational language over enterprise language

Direct, concrete, precise. No "stakeholder synergies," no "value chain optimization," no "actionable insights" without an action attached. NAWA documentation is written by operators for operators.

### P10. Documentation is versioned like code

Every material change is a version event, either through the version number or through an amendment log entry. Silent edits to content are prohibited.

---

## 11. Relationship Between Documents

Documents form a directed dependency graph. Higher-level documents govern lower-level documents. Lower-level documents cite, but do not modify, higher-level ones.

```
GOVERNANCE (this standard, EBDs)
        │  governs
        ▼
ARCHITECTURE (Freeze v1.0, engine contracts)
        │  is integrated by
        ▼
COWORK v2.0 (institutional intelligence, integrated view)
        │  reflects the state described in
        ▼
CURRENT_STATE.md (present snapshot)
        │  is implemented by
        ▼
IMPLEMENTATION (code, technical documents, runtime documents)
        │  is discussed and decided in
        ▼
EXECUTIVE MEETINGS (meeting documents)
        │  produce
        ▼
DECISION LOGS (EBDs, ADRs)
        │  which amend
        ▼
GOVERNANCE / ARCHITECTURE / PRODUCT / BRAIN as appropriate
        (closing the loop)
```

### 11.1 Reading direction

- **Top-down** for onboarding: start at Governance, descend to Implementation, then read the recent Decision Logs to catch what changed most recently.
- **Bottom-up** for accountability: start from a Decision Log entry, trace up through what it amended, to understand the governance chain that authorized it.

### 11.2 Cross-reference discipline

Every reference to another document uses the document's file path (`` `docs/nawa_brain/DAIRTNA_OPERATIONAL_SEMANTICS.md` ``), not the document's title alone. This makes references machine-checkable and survives title edits.

### 11.3 Feedback loop

Meeting Documents and Decision Logs are the mechanism by which lower levels amend higher ones. A meeting that changes governance produces an Executive Board Decision that amends the governance document. The amendment is not made silently in the governance document; it is made through the decision record.

---

## 12. Governance

### 12.1 Executive Board

The Executive Board convenes to ratify decisions that touch governance, product direction, architecture at the freeze level, or organizational structure. Membership:

- Founder & CEO (Mubarak) — decision authority.
- Chief Product & AI Strategy (Aboura) — product review authority.
- Chief Technology & Architecture Officer (Claude Cowork) — architecture and documentation review authority.
- Lead Software Engineer (Codex) — execution review authority; participates when the decision affects implementation.

### 12.2 Executive Board Decision (EBD) format

Every EBD produces a document at `docs/decisions/EBD-NNN-<slug>.md` with:

- Decision title and number.
- Context: what problem prompted the decision.
- Options considered.
- Decision reached.
- Reasoning.
- Consequences accepted (what this makes harder, what it makes possible).
- Documents affected (which existing documents amend as a result).
- Ratification: signatures / acknowledgments of the board members.
- Effective date.

### 12.3 Sprint cadence

Executive Board Meetings occur at each Sprint boundary at minimum, and on-demand for time-critical decisions. Sprint boundaries produce:

- A `CURRENT_STATE.md` update.
- A Sprint retrospective as a Meeting Document.
- Any EBDs required by the retrospective.
- An update to the risk register in COWORK v2.0 if any risk changed materially.

### 12.4 CTO responsibility for documentation health

The CTO (Claude Cowork) is accountable for documentation health across the project. Concretely:

- Flagging stale documents in every Sprint retrospective.
- Detecting inconsistencies between documents and raising them for resolution.
- Maintaining the cross-reference graph and catching broken references.
- Ensuring every EBD produces the correct amendments in the correct downstream documents.
- Producing quarterly documentation health reports summarizing coverage, staleness, and unresolved decisions.

### 12.5 Amendment process for this standard

This standard is amended by Executive Board Decision. Amendments to Section 10 (Documentation Principles) require Founder ratification and produce a new MINOR version at minimum. Amendments changing the section structure or the categories in Section 3 produce a new MAJOR version and require re-ratification by the Executive Board.

---

## 13. Future Team Onboarding

A new engineer joining NAWA follows this reading order on their first two working days. Time budgets are targets, not caps; the point is that a new engineer becomes contributor-ready without asking anyone for context.

### 13.1 Day 1 — Understanding the organization

1. **This standard** — `docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md` (30 minutes). Read once; refer back as needed.
2. **Vision and product** — `docs/product/PRODUCT_VISION.md` (once published; interim: `COWORK v2.0` §Vision) (30 minutes).
3. **Current state** — `CURRENT_STATE.md` (30 minutes). Anchors the reader in what is real *right now*.
4. **COWORK v2.0** — `docs/nawa_brain/COWORK_V2_INSTITUTIONAL_INTELLIGENCE.md` (90 minutes). The integrated institutional view.
5. **Agent instructions** — `AGENTS.md` and `CLAUDE.md` (30 minutes). Even if the reader is human, these describe what the AI agents in the org are expected to do and are the fastest way to understand the org's execution posture.

### 13.2 Day 2 — Understanding the system

1. **Architecture Freeze v1.0** — `docs/architecture/ARCHITECTURE_FREEZE_v1.md` (60 minutes).
2. **Runtime pipeline** — `docs/runtime/RUNTIME_PIPELINE_CURRENT.md` (60 minutes).
3. **Company Brain — Dairtna stack** — starting at `docs/nawa_brain/00_NAWA_BRAIN_INDEX.md` and following its reading order (2 hours).
4. **Most recent five Decision Logs** — `docs/decisions/` sorted by date descending (45 minutes). This is how the reader catches up on what changed most recently.
5. **Their team's Technical Documents** — folder specific to the team they are joining (as long as needed).

### 13.3 Day 3+ — Contribution

By the end of Day 2 the new engineer should be able to:

- Identify the authoritative document for any question they have.
- Know who to escalate to when a document is missing or contradictory.
- Understand the Sprint cadence and how decisions flow.
- Read a code change and its accompanying documentation together.

Their first contribution as an engineer includes a documentation change. This is not optional; documentation contribution is part of the engineering role at NAWA.

---

## 14. Final Principles

This document is the documentation constitution of NAWA.

- **It scales.** It is designed to hold for an organization of 50+ engineers without amendment beyond additions to Section 3 categories or Section 9 folder structure. Growth does not require rewriting this standard.
- **It is enforceable.** Every rule in it is testable — a reviewer can look at any document and determine whether it complies.
- **It is amendable.** Section 12.5 defines the amendment process. The constitution is not permanent by claim; it is permanent by discipline.
- **It is self-consistent.** This document follows its own rules: it declares scope, non-scope, owner, version, effective date; it closes decisions; it preserves reasoning; it is written in operational language.
- **It is subordinate to reality.** If the organization consistently operates in a way that violates this standard, the standard is wrong, not the organization. The standard is amended, not silently ignored.
- **It is Executive Board Decision #001.** The corresponding entry in `docs/decisions/` is `EBD-001-documentation-standard.md`, recording the ratification, the reasoning, and the initial adoption plan.

---

## Appendix A — Amendment Process

1. **Proposal.** Any Executive Board member proposes an amendment by drafting the change and submitting it as a Draft (`docs/drafts/governance/NAWA_DOCUMENTATION_STANDARD_v<next>.md` or an amendment note if the change is minor).
2. **Review.** The CTO reviews within one week and produces a review summary indicating whether the change is MAJOR or MINOR.
3. **Ratification.** MAJOR changes require Founder ratification at an Executive Board Meeting. MINOR changes require Founder review only.
4. **Publication.** The new version replaces the old, with the old file archived per Section 8.1. An EBD is filed recording the amendment and its reasoning.
5. **Adoption window.** All documents must comply with the new standard within one Sprint of ratification. Documents out of compliance are flagged stale.

---

## Appendix B — Adoption Checklist

Ratification of this standard triggers the following one-time actions, tracked in EBD-001:

- [ ] Create the folder structure defined in Section 9.1 in the primary repository (empty folders are placeholders; add a `.gitkeep`).
- [ ] Move `CURRENT_STATE.md` to comply with the header block in Section 9.3.
- [ ] Move existing Company Brain documents into compliance with header block; existing documents keep their filenames and version headers.
- [ ] Create `docs/decisions/EBD-001-documentation-standard.md` recording this ratification.
- [ ] File the CTO's first Sprint documentation health report against this standard within two Sprints.
- [ ] Update `AGENTS.md` and `CLAUDE.md` to reference this standard as the authority for documentation behavior.
- [ ] Onboard Aboura and Codex to the standard via a joint working session; record it as a Meeting Document.

Items complete when checked. This checklist is closed and archived when all items are checked.

---

## Appendix C — Glossary

- **ADR** — Architectural Decision Record. A Decision Log entry documenting an architectural choice.
- **Approval authority** — the role authorized to move a document from Review to Approved.
- **Archived** — a document state indicating it is no longer authoritative; retained as historical record only.
- **COWORK v2.0** — the integrated institutional intelligence manual; the derived integrated view over governance, architecture, product, and brain.
- **Draft** — a document state indicating authorship in progress; not yet under review.
- **EBD** — Executive Board Decision. A ratified Decision Log entry at the highest governance level.
- **Freeze** — a governance status indicating that a component or contract is fixed and may not change without a formal unfreeze decision.
- **Owner** — the accountable role for a document; distinct from author.
- **Ratified** — a governance document's approved state, equivalent to "Approved" for governance category.
- **SSoT** — Single Source of Truth. Principle P1 of this standard.
- **Stale** — a document not updated when its trigger fired; not citable as source of truth until refreshed.

---

## Appendix D — Amendment Log

| Version | Date | Change | Authority | Reference |
|---|---|---|---|---|
| 1.0 | 2026-07-03 | Initial ratification as Executive Board Decision #001. | Founder | `docs/decisions/EBD-001-documentation-standard.md` (to be filed) |

---

*This document becomes authoritative on ratification. Every subsequent NAWA document is written under it, reviewed against it, and archived per its rules. Where it and reality diverge, the document is amended, not ignored.*
