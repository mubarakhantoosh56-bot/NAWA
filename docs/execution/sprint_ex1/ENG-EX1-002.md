# ENG-EX1-002 — Executive Brief v2 Foundation

**Priority:** P0. Runs after ENG-EX1-000, in parallel with ENG-EX1-001 as feasible.
**Owner (Structure / Rendering / Binding):** AI Engineering Team (Claude Code / Codex).
**Owner (Executive language / Section logic / Executive wording / Business framing):** Aboura (CPO).

---

## Objective

Build the working foundation of Executive Brief v2 — the first usable Executive Brief operating on the eight-section structure — so Aboura's design binds into a running system and mid-Sprint draft reviews see real output on real Jannat data.

The objective is a usable Executive Brief. Not scaffolding. Not placeholders masking as content.

## Scope

- Eight sections wired at Executive Intelligence output: Executive Summary → Findings → Executive Assessment → Business Impact → Executive Actions → Confidence → Missing Evidence → Recommended Company Inputs.
- Engineering owns Structure, Rendering, Binding.
- Aboura owns Executive language, Section logic, Executive wording, Business framing.
- Engineering never defines Executive language.
- Runs end-to-end on real Jannat data.

**Out of scope:**
- Any modification of CompanyInput, Classifier, NCO Lite, KAE, OIE, OCE, NCE Lite, or OME Foundation.
- Runtime, reasoning pipeline changes.
- Executive language, wording, section logic (Aboura owns).

## Expected Deliverable

**Executive Brief v2 Foundation** — structure and rendering for the eight sections running end-to-end on real Jannat data. Aboura's executive language and section logic bind into the foundation as her design lands. First usable Executive Brief v2 output.

## Dependencies

- ENG-EX1-000 baseline captured.
- ENG-EX1-001 analysis complete or in parallel where the analysis has surfaced the presentation seam.
- Aboura design front-load Days 1–3: Executive Brief Experience, Executive Assessment, Business Impact Framework, Executive Actions Taxonomy, Executive Brief Design Principles.
- Improvement over Replacement principle applied — extend the current implementation, do not rewrite.

## Blockers

- If the Foundation reveals that upstream data flows do not carry what a section requires (e.g., Executive Assessment needs an upstream prioritization surface that does not exist), this is an immediate escalation to Founder and Aboura per Founder Activation Decision #5. **Never silently solved by modifying runtime or reasoning pipeline.**
- If Aboura design front-load slips, escalation to PMO for capacity-risk mitigation. PMO recommendation on slip: defer Executive Actions Taxonomy (Sprint Task 5 / Deliverable 3) to Sprint EX-2 as first drop item.

## Acceptance Criteria

- Eight-section structure runs end-to-end on real Jannat data without error.
- Foundation is usable — not scaffolding, not placeholders masking as content. Aboura's language and logic bind progressively.
- Improvement over Replacement principle applied. The current Executive Intelligence implementation is extended, not rewritten.
- Engineering did not define any Executive language.
- No modification of any upstream Runtime Component.
- Mid-Sprint informal Founder draft review sees real end-to-end output.

---

## Execution Result

**Status:** Completed (Founder-accepted)
**Started:** 2026-07-10
**Completed:** 2026-07-10
**Founder acceptance:** 2026-07-16
**Commit(s):** — (see next commit, ENG-EX1-002 only)
**Reviewer:** Founder
**Validation:** See Notes below. Backend verified against real Jannat data (full `NCOLiteOrchestrator` run + direct `_summarize_nco_result` check); frontend verified via clean `tsc --noEmit` and `eslint`. Live-browser/DB end-to-end gap (flagged 2026-07-10) closed on 2026-07-16: `nawa-postgres` Docker container started, real FastAPI backend (`:8000`) and Next.js frontend (`:3000`) run against it, real login as `owner@jannat-local.dev`, real file upload of the Jannat poultry Excel file through the live `POST /files/upload` endpoint, real DB row written to `files` table. Response verified field-for-field against the frontend's `firstCEOBrief()` parser (`CompanyInputsPanel.tsx`) — all 11 PDS-001 section keys present, zero `"Add Company Input:"` strings. `tsc --noEmit` and `eslint` re-confirmed clean.
**Follow-up:** Founder/Aboura review of the "pending executive language" sentinel approach (see Notes) before Aboura's actual language authoring lands, as Aboura's design lands progressively. ENG-EX1-003 not started; awaiting separate Founder activation.
**Notes:**

**Structure used:** PDS-001 §4/§5's 11-section structure (superseding the stale 8-section list still written in this doc's own Scope section above, and the old 5-item Experience Reading Order, per Founder decision #1 on ENG-EX1-001).

**Note on this doc's own Scope section:** the "Eight sections" bullet above is now stale — left as-is (historical record of what was originally scoped) but superseded by PDS-001. The actual implementation targets the 11 PDS-001 sections: Executive Priority, Executive Summary, What Changed?, Facts (Truth Layer), Executive Assessment, Business Impact, Executive Actions, Confidence, Missing Evidence, Recommended Company Inputs, Executive Attention.

**Files changed (exactly the 6 authorized, confirmed via `git diff --name-only`):**
- `app/oip/models/ceo_brief.py` — `CEOBrief` dataclass extended with 9 additive fields (all with defaults; the original 7 fields unchanged in name/type/order, since `store_ome_foundation()` in `app/nco/pipeline.py` — not authorized to touch — reads them directly).
- `app/oip/services/ceo_brief_service.py` — added builder methods for the 7 situation-derived sections (Executive Priority, What Changed, Facts, Executive Assessment, Business Impact, Executive Actions, Executive Attention), wired into `_brief_for_situation()`. `_why_it_matters()` reused unchanged for Business Impact's operational dimension.
- `app/nco/pipeline.py` — **only** `_apply_evidence_policy_to_brief()` changed, as Binding/Presentation per Founder decision #3. Fixes the confirmed Taxonomy v1 violation from ENG-EX1-001: `"Add Company Input: …"` strings are no longer appended into `recommended_next_actions`. Company inputs now flow into their own `recommended_company_inputs` field; confidence explanation and per-item missing-evidence detail are now first-class fields. No other function in this file touched; no Runtime Logic/Evidence Policy/Reasoning/NCO behavior changed.
- `app/api/files.py` — `_summarize_nco_result()` extended to pass through all 9 new fields under distinct keys (`business_impact_detail`, `missing_evidence_detail`, etc.) alongside the untouched legacy keys.
- `frontend/src/components/operations/CompanyInputsPanel.tsx` — `CEOBriefPresentation` extended; `firstCEOBrief()` maps the new fields (and now prefers the real backend `recommended_company_inputs` over the old frontend-side fabrication helper, falling back to it only if the backend list is empty); `CEOBriefPanel` reordered into PDS-001 §4 order with new `PendingSection`, `BusinessImpactSection`, `ExecutiveActionsSection`, `ExecutiveAttentionSection` renderers reusing the existing generic `BriefSection` where the shape still fit.
- `frontend/src/lib/i18n/dictionaries/{en,ar}.ts` — ~19 new keys under the existing `companyInputs.*` namespace for the 5 net-new section labels and their sub-labels.

**Per-section content-source decisions applied** (full table in the approved execution plan): Executive Summary, What Changed?, Facts, Confidence, and Recommended Company Inputs are populated with real derived data today. Business Impact and Executive Actions are partially populated (operational impact and action text are real; financial impact is the literal, PDS-001-mandated `"Unknown"`; strategic impact and per-action priority/reason/expected-outcome are pending). Executive Priority and Executive Assessment (Executive Thinking) are fully pending — **the section slot is present** (satisfies Founder decision #4's "mandatory, not omitted"), but no upstream data exists to populate it honestly; Engineering did not author any Executive language to fill it. Every pending value uses one consistent, structured, machine-detectable sentinel: `{"status": "pending_executive_language", "note": "..."}`, rendered in the UI as a visible amber "Pending executive language" badge — never a blank field, never invented prose.

**Verification performed against real Jannat data** (`data_sources/jannat_al_firdaws/2026_06/poultry_operations/التقرير_الفني_اليومي_حقول_ديرتنا.xlsx`):
- Full `NCOLiteOrchestrator.run_upload_completed()` run (`store_memory=False`, no DB write) — captured at [artifacts/after_eng_ex1_002_executive_brief_nco_lite_2026-07-09T23-15-01Z.json](artifacts/after_eng_ex1_002_executive_brief_nco_lite_2026-07-09T23-15-01Z.json), diffable against the ENG-EX1-000 baseline at [artifacts/baseline_executive_brief_nco_lite_2026-07-09T21-10-05Z.json](artifacts/baseline_executive_brief_nco_lite_2026-07-09T21-10-05Z.json).
- Confirmed zero `"Add Company Input:"` strings anywhere in `recommended_next_actions` or `executive_actions[*].action`; `recommended_company_inputs` contains exactly the 2 expected strings, in its own field.
- Confirmed all 11 section keys present and non-empty on the captured brief.
- Confirmed `_summarize_nco_result()` (the real API-layer function) passes through all new keys when run directly against the captured pipeline output.
- Frontend: `npx tsc --noEmit` and `npx eslint` both clean on all changed files.
- **Update 2026-07-16:** live authenticated run through the actual `/files/upload` endpoint completed against a real Postgres (`nawa-postgres` container) and real Jannat tenant — real JWT login, real multipart upload, real DB-persisted `files` row, full `NCOLiteOrchestrator` execution. Response payload confirmed field-for-field against the frontend's `firstCEOBrief()` parser. No browser-automation tool was available in this environment, so pixel/DOM-level screenshot capture was not performed; both servers were left running for manual browser confirmation at `localhost:3000`.
