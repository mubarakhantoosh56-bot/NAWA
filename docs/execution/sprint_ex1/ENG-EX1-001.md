# ENG-EX1-001 — Executive Intelligence Analysis

**Priority:** P0. Runs after ENG-EX1-000.
**Owner:** AI Engineering Team (Claude Code / Codex).
**Ownership layer:** Analysis-only (Structure discovery).

---

## Objective

Understand the current Executive Intelligence implementation so the eight-section restructure (Executive Brief v2 Foundation) and every downstream engineering task can be planned against real code paths — not against assumptions.

## Scope

- Read-only analysis of the current Executive Intelligence output layer.
- Identify where the brief is generated, which functions produce it, which data flows feed it.
- Identify the presentation seam where the eight-section restructure will land.
- Identify any refactor pre-work needed under the Improvement over Replacement principle.

**Out of scope:**
- Any modification of Executive Intelligence code.
- Runtime, reasoning pipeline, and upstream Runtime Components (CompanyInput, Classifier, NCO Lite, KAE, OIE, OCE, NCE Lite, OME Foundation).
- Formal Runtime Documents. Per Executive Operating Rule 1, no documentation work required during MVP unless Founder requests it.

## Expected Deliverable

**Internal Engineering Analysis** — a short technical note held internally by the AI Engineering Team. Not a Runtime Document. Rule 1 upheld.

Contents:
- Where the brief is generated in the current implementation.
- Current output structure.
- Presentation seam for the eight-section restructure.
- Improvement paths identified (not rewrite paths — Improvement over Replacement).
- Any refactor pre-work identified with clear Founder-visible flag if the refactor would cross the runtime boundary.

## Dependencies

- ENG-EX1-000 complete. Baseline captured before analysis touches anything.

## Blockers

- If analysis reveals that Executive Brief v2 Foundation would require modifying upstream components (NCE Lite, OCE, KAE, OIE, other runtime components) to work, this is an immediate escalation to Founder and Aboura per Founder Activation Decision #5. **Never silently solved by modifying runtime or reasoning pipeline.**

## Acceptance Criteria

- Current output structure documented internally within the AI Engineering Team.
- Presentation seam identified for the eight-section restructure.
- Improvement paths identified. Improvement over Replacement principle applied.
- Any refactor pre-work identified. Any refactor that would cross the runtime boundary is flagged to Founder and Aboura before any implementation begins.
- No modification of Executive Intelligence code during analysis.
- No modification of any upstream Runtime Component.

---

## Execution Result

**Status:** Approved
**Started:** 2026-07-10
**Completed:** 2026-07-10
**Commit(s):** —
**Reviewer:** Founder
**Validation:** Read-only analysis. All 5 Product Foundation documents read first (`PDS-001_EXECUTIVE_DECISION_BRIEF.md`, `EXECUTIVE_BRIEF_EXPERIENCE_v1.md`, `BUSINESS_IMPACT_FRAMEWORK_v1.md`, `EXECUTIVE_ACTIONS_TAXONOMY_v1.md`, `EXECUTIVE_BRIEF_DESIGN_PRINCIPLES_v1.md`) and treated as authoritative for Executive Brief behavior. Full brief-generation chain traced end to end (entry → Executive Intelligence step → exit) against the ENG-EX1-000 baseline. No code modified; no upstream Runtime Component touched.
**Follow-up:** ENG-EX1-002 awaits explicit Founder activation before implementation begins — not started.
**Notes:**

**Founder decisions on approval (2026-07-10):**

1. PDS-001 is the single source of truth for Executive Decision Brief structure. Any conflicting Sprint or Product document defers to PDS-001. **Open issue:** PDS-001 §4 "Executive Decision Brief Structure" and §5 "Section Definitions" are still marked "(To be defined)" as of this analysis (re-checked at approval time) — this decision sets precedence but does not yet resolve the structure conflict from Finding 3, since PDS-001 has no structure content to defer to yet. ENG-EX1-002 cannot be scoped against a concrete section list until PDS-001 §4/§5 are actually filled in.
2. Executive Actions and Recommended Company Inputs must be completely separated — never in the same collection. Confirms Finding 4/§4 of the analysis note as a required fix, not just an observation.
3. Engineering is authorized to modify `_apply_evidence_policy_to_brief()` in `app/nco/pipeline.py`, Binding/Presentation changes only. Explicitly NOT authorized: Runtime Logic, Evidence Policy, Reasoning, NCO behavior changes. Resolves the boundary question in Finding 6/§6 — scoped narrowly to that one function's binding logic.
4. Executive Thinking (Executive Assessment) is a mandatory section — must not be omitted from ENG-EX1-002.



- Full internal engineering analysis: [analysis/ENG-EX1-001_executive_intelligence_analysis.md](analysis/ENG-EX1-001_executive_intelligence_analysis.md).
- **Structure conflict (Founder/Aboura-visible, needs resolution before ENG-EX1-002):** the Sprint charter's 8-section structure, `EXECUTIVE_BRIEF_EXPERIENCE_v1.md`'s 5-item Reading Order, and `PDS-001` §4/§5 (the doc nominally authoritative on structure) all disagree or are undefined — PDS-001 §4 "Executive Decision Brief Structure" and §5 "Section Definitions" are both still marked "(To be defined)." Engineering has not guessed at a resolution.
- **Concrete Taxonomy v1 violation found in current code, evidenced by the ENG-EX1-000 baseline capture:** `_apply_evidence_policy_to_brief()` in `app/nco/pipeline.py` appends `"Add Company Input: …"` strings into the same `recommended_next_actions` list used for real Executive Actions, directly contradicting `EXECUTIVE_ACTIONS_TAXONOMY_v1.md`'s rule that Executive Actions and Recommended Company Inputs "must never be mixed."
- **Boundary question flagged, not resolved:** fixing the violation above touches `app/nco/pipeline.py`, which is inside the Sprint's named-out-of-scope "NCO Lite" package, even though the specific function is binding/wiring rather than reasoning logic. Recommend Founder/Aboura explicitly authorize engineering to touch that one function.
- Presentation seam identified (model → service → API reshape → frontend view-model → UI render), all four layers owned by Engineering, all outside upstream Runtime Components. Full list of files in the analysis note §5.
- Architectural observation: KAE/OIE-equivalent code and Executive Intelligence (`ceo_brief_service.py`) all live inside the same `app/oip/` package with no directory-level separation — the Runtime Component boundary is not a package boundary. No action needed now; flagged so future edits stay scoped correctly.
- Improvement paths identified (additive, no rewrite) — see analysis note §8. No refactor pre-work was performed; only identified.
