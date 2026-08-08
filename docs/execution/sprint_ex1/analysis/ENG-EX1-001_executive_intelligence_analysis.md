# ENG-EX1-001 — Executive Intelligence Analysis (Internal Engineering Note)

Internal Engineering Analysis per Executive Operating Rule 1. Not a Runtime Document. Read-only analysis; no code was modified while producing this note.

Product Foundation documents read before this analysis: `docs/product/PDS-001_EXECUTIVE_DECISION_BRIEF.md`, `docs/product/EXECUTIVE_BRIEF_EXPERIENCE_v1.md`, `docs/product/BUSINESS_IMPACT_FRAMEWORK_v1.md`, `docs/product/EXECUTIVE_ACTIONS_TAXONOMY_v1.md`, `docs/product/EXECUTIVE_BRIEF_DESIGN_PRINCIPLES_v1.md`.

---

## 1. Where the brief is generated (current implementation)

Confirmed against ENG-EX1-000's baseline capture. Chain, entry to exit:

1. **Entry:** live upload-completed handler in [app/api/files.py](../../../../app/api/files.py) → `NCOLiteOrchestrator.run_upload_completed()` → `_run_excel_poultry_report()` ([app/nco/orchestrator.py](../../../../app/nco/orchestrator.py)).
2. KAE → OIE → OCE → MVP evidence policy → NCE Lite gate (all upstream Runtime Components, out of scope, unchanged).
3. **Executive Intelligence step:** `NCOLitePipeline.run_executive_intelligence()` ([app/nco/pipeline.py:289](../../../../app/nco/pipeline.py)) calls `CEOBriefService.generate_briefs()` ([app/oip/services/ceo_brief_service.py](../../../../app/oip/services/ceo_brief_service.py)), which builds one `CEOBrief` ([app/oip/models/ceo_brief.py](../../../../app/oip/models/ceo_brief.py)) per operational situation.
4. **Evidence-policy binding:** `NCOLitePipeline._apply_evidence_policy_to_brief()` ([app/nco/pipeline.py:346](../../../../app/nco/pipeline.py)) — post-processes the `CEOBrief`, downgrading confidence and appending `"Add Company Input: …"` strings into the same `recommended_next_actions` list used for real actions.
5. **API rendering seam:** `_summarize_nco_result()` ([app/api/files.py:358](../../../../app/api/files.py)) reshapes the `CEOBrief` dict into a `briefs[]` array with renamed keys (`what_happened → summary`, `why_it_matters → business_impact`, `recommended_next_actions → recommended_actions`).
6. **Frontend rendering seam:** `resultFromFile()` / `firstCEOBrief()` in [frontend/src/components/operations/CompanyInputsPanel.tsx:386,554](../../../../frontend/src/components/operations/CompanyInputsPanel.tsx) map the API response into a `CEOBriefPresentation` view-model (first brief only), rendered by `CEOBriefPanel` / `BriefSection` (same file, lines 310–373) as a static 2-column grid.

## 2. Current output structure

`CEOBrief` is a flat, 7-field dataclass: `headline`, `severity`, `what_happened`, `why_it_matters`, `evidence_summary` (list of per-signal citation dicts), `recommended_next_actions` (list of plain strings), `confidence` (plain string: `"initial"` or `"reduced"`).

What the live UI currently renders (`CEOBriefPanel`), in order: Executive Summary (`what_happened`), Business Impact (`why_it_matters`, single string), Recommended Executive Actions (`recommended_next_actions`, unstructured strings — see Finding 4), Confidence Level (plain string + percentage), Missing Evidence, Recommended Company Inputs (the latter two computed independently on the frontend from raw `missing_evidence`, not from the brief).

There is no concept today of: Findings (as distinct from the narrative summary), Executive Assessment/prioritization, three-dimensional Business Impact, Executive Action priority or category, or a structured confidence explanation attached to the brief itself.

## 3. Structure conflict — Founder/Aboura-visible, not silently resolved

Three sources define "the structure" and they do not agree. This blocks precise scoping of ENG-EX1-002 until reconciled:

| Source | Structure |
|---|---|
| `SPRINT_EX1.md` (Sprint charter, §Success Criteria) | 8 sections: Executive Summary → Findings → Executive Assessment → Business Impact → Executive Actions → Confidence → Missing Evidence → Recommended Company Inputs |
| `EXECUTIVE_BRIEF_EXPERIENCE_v1.md` (Reading Order) | 5 sections: Executive Priority → Executive Summary → What Changed? → Executive Assessment → Executive Actions ("everything else supports these five") |
| `PDS-001_EXECUTIVE_DECISION_BRIEF.md` §4 "Executive Decision Brief Structure" and §5 "Section Definitions" | Both marked **"(To be defined)"** — the document nominally positioned as authoritative on structure has no structure in it yet |

None of the three name "Executive Priority" or "What Changed?" the same way, and PDS-001 — the doc titled to be the structural source of truth — is still a stub. Recommend this go back to Aboura/Founder before ENG-EX1-002 picks a concrete section list to build against; engineering should not infer or invent the missing structure.

A secondary, lower-stakes open question: `BUSINESS_IMPACT_FRAMEWORK_v1.md` lists six Impact Categories (Operational, Financial, Strategic, Customer, Compliance, Reputation) while `SPRINT_EX1.md` Task 4 scopes Sprint EX-1 to three (Operational, Financial, Strategic). Worth a one-line confirmation from Aboura that the other three are future-scope, not missed for EX-1.

## 4. Concrete taxonomy violation found in current code

`EXECUTIVE_ACTIONS_TAXONOMY_v1.md` states plainly: *"Executive Actions … Recommended Company Inputs … These two concepts must never be mixed."*

The current implementation mixes them. `_apply_evidence_policy_to_brief()` ([app/nco/pipeline.py:346-370](../../../../app/nco/pipeline.py)) appends `"Add Company Input: <name>"` strings directly into `recommended_next_actions` — the same list the frontend renders under "Recommended Executive Actions." Confirmed in the ENG-EX1-000 baseline capture: the captured brief's `recommended_next_actions` includes both real actions ("review feed consumption", …) and `"Add Company Input: Veterinary report for the affected poultry hall and date range"` in one undifferentiated list. This is a direct, evidenced violation of the adopted taxonomy, not a hypothetical — it should be near the top of ENG-EX1-002's fix list.

## 5. Presentation seam for the eight-section (or whatever-is-confirmed) restructure

Layers that render/shape the brief, in order, all owned by Engineering per the Sprint's Structure/Rendering/Binding rule:

- `app/oip/models/ceo_brief.py` — model shape.
- `app/oip/services/ceo_brief_service.py` — generation logic (where Findings / Executive Assessment / structured Business Impact / structured Actions would be produced).
- `app/nco/pipeline.py::_apply_evidence_policy_to_brief` — evidence-policy binding onto the brief (see §6 — boundary question).
- `app/api/files.py::_summarize_nco_result` — API-layer field reshaping.
- `frontend/.../CompanyInputsPanel.tsx` (`CEOBriefPresentation` type, `firstCEOBrief()`, `CEOBriefPanel`, `BriefSection`) — UI view-model and rendering.
- `frontend/src/lib/i18n/dictionaries/{en,ar}.ts` — section labels/copy.

This is a clean, four-layer seam (model → service → API → UI) that ENG-EX1-002 can restructure without touching KAE/OIE/OCE/NCE Lite logic — with one caveat below.

## 6. Boundary question to flag before ENG-EX1-002 (per Blockers clause, Founder Activation Decision #5)

`app/nco/pipeline.py` is physically inside the `app/nco/` package — named in the Sprint's Out of Scope list as "NCO Lite." Its `_apply_evidence_policy_to_brief()` function currently owns part of the confidence-explanation logic (it is the only place that attaches the evidence-policy reason to the brief and adjusts confidence). If Business Impact / Executive Actions / Confidence Explanation restructuring requires changing this function's contract (e.g., because actions become structured objects instead of strings, or company-input asks move out of `recommended_next_actions` into their own field), that is a change to a file inside the officially out-of-scope NCO Lite package.

This looks mechanical (binding/wiring, not reasoning), and Improvement over Replacement favors fixing it in place. But it does technically cross the named boundary, so per the ENG-EX1-001 Blockers clause this is flagged now rather than decided silently: **recommend engineering be allowed to touch `_apply_evidence_policy_to_brief()` specifically as a binding/wiring fix (no change to NCE Lite/OCE/OIE/KAE reasoning or contracts), with Founder/Aboura sign-off**, rather than treating all of `app/nco/pipeline.py` as frozen.

## 7. Architectural observation: package boundary ≠ Runtime Component boundary

The Runtime Component names in the Sprint charter (KAE, OIE, OCE, NCE Lite) don't map onto separate Python packages. `app/oip/` physically contains the KAE-equivalent code (`loaders/`, `translators/`, `validators/` — wrapped by `NCOLitePipeline.run_kae`), the OIE-equivalent code (`poultry_derivation_service.py`, `poultry_situation_service.py` — wrapped by `run_oie`), *and* Executive Intelligence (`ceo_brief_service.py`, `ceo_brief.py`) side by side in one package with no directory-level separation. There is nothing in the file layout that prevents an edit intended for Executive Intelligence from accidentally reaching into KAE/OIE code sitting in the same directory. Not a blocker, but worth keeping in mind during ENG-EX1-002: changes should be scoped to `ceo_brief_service.py` / `ceo_brief.py` specifically, not "the `oip` package" generally.

## 8. Improvement paths (Improvement over Replacement — no rewrite path proposed)

All of these are additive/structural changes to the existing four-layer seam, not replacements:

1. **`CEOBrief` model** — add fields rather than rename existing ones where possible: `findings` (list, currently folded into `what_happened`), `executive_assessment` (str, Aboura-authored logic slot), `business_impact` (structured: operational/financial/strategic, replacing the single `why_it_matters` string — this is a breaking shape change, see §9), `confidence_explanation` (str, promoting `evidence_policy.confidence_reduction_reason` into the brief itself instead of leaving it to be bolted on downstream).
2. **`recommended_next_actions`** — restructure from `list[str]` to `list[ExecutiveAction]` (headline/category/priority/evidence-link/expected-outcome per Taxonomy v1), and add a separate `recommended_company_inputs: list[str]` field on `CEOBrief` so Company Inputs stop being appended into the actions list (fixes Finding 4 at the source).
3. **`evidence_summary`** — currently mixes two row shapes: per-signal citation dicts and (after evidence-policy binding) one evidence-policy-reason dict. Once `confidence_explanation` becomes a first-class field (improvement 1), the evidence-policy dict no longer needs to be smuggled into `evidence_summary`, which becomes a clean, single-shape list again — this is a side effect cleanup, not separate work.
4. **API layer (`_summarize_nco_result`)** — extend the reshape to pass through the new structured fields instead of collapsing them to strings; keep the existing flat fields for backwards compatibility with the current frontend until the frontend restructure lands, per the Sprint's backwards-compatibility expectation.
5. **Frontend** — extend `CEOBriefPresentation` and `CEOBriefPanel` to render the confirmed section list once §3 is resolved; today's `BriefSection` grid component is generic enough (title + body-or-items) to reuse for new sections without a rewrite.
6. **Naming drift (cosmetic, optional)** — model/service/variables/i18n keys are all named `CEOBrief`/`ceoBrief` throughout the stack while product docs now say "Executive Decision Brief." Not required for Sprint EX-1 scope; flagging so a future rename is deliberate rather than partial.

## 9. Refactor pre-work required before ENG-EX1-002 can implement cleanly

- Resolve the structure conflict in §3 (Founder/Aboura) — without it, ENG-EX1-002 cannot know which section list to build the model/API/UI against.
- Confirm the `_apply_evidence_policy_to_brief()` boundary question in §6 (Founder/Aboura) — determines whether that one function in `app/nco/pipeline.py` is fair game.
- Decide whether `business_impact` and `recommended_next_actions` shape changes (str → structured object) are acceptable as breaking changes to the `CEOBrief`/API contract within Sprint EX-1, or need a transition period where both old and new fields are emitted (affects `_summarize_nco_result` and the frontend rollout order).

No other upstream Runtime Component (CompanyInput, Classifier, KAE, OIE, OCE, NCE Lite, OME Foundation) needs to change for the eight-section (or confirmed) restructure — confirmed by the full pipeline trace in §1.
