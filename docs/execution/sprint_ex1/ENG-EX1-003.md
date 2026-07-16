# ENG-EX1-003 — Statement Traceability Instrumentation

**Priority:** P1. Runs after ENG-EX1-000. Can run in parallel with ENG-EX1-002.
**Owner:** AI Engineering Team (Claude Code / Codex).
**Ownership layer:** Binding.

---

## Objective

Instrument Executive Intelligence output so every statement carries a source reference at output time. Enforcement (auto-flagging or removing untraced statements) is deferred to a later engineering task package once instrumentation is complete and stable.

## Scope

- Every statement generated for the Executive Brief carries a source-reference field.
- Source references: Truth Layer fact (from KAE) / OIE signal / OCE context / NCE Lite hypothesis / synthesis-of-N.
- Instrumentation only. Enforcement comes later.

**Out of scope:**
- Any modification of NCE Lite, OCE, KAE, OIE, NCO Lite, Company Input Classifier, CompanyInput, or OME Foundation.
- Runtime and reasoning pipeline changes.
- Enforcement logic (auto-flagging or removing untraced statements) — later task package.

## Expected Deliverable

Statement-level trace instrumentation at Executive Intelligence. Every statement in Executive Brief v2 carries a source-reference field. Enforcement layer built in a later engineering task package once instrumentation and analysis are complete.

## Dependencies

- ENG-EX1-000 baseline captured.
- ENG-EX1-001 analysis has identified statement generation points at Executive Intelligence.

## Blockers

- If instrumentation reveals that upstream components (NCE Lite, OCE, KAE, or others) are not passing sufficient trace metadata for every statement Executive Intelligence generates, this is an immediate escalation to Founder and Aboura per Founder Activation Decision #5.
- **Never silently modify runtime, reasoning pipeline, or any upstream Runtime Component to make the trace work.**

## Acceptance Criteria

- Every statement in Executive Brief v2 output carries a source-reference field at output time.
- Instrumentation does not modify any upstream Runtime Component.
- Instrumentation surfaces (not fixes) any upstream trace gaps as blocker escalations to Founder and Aboura.
- Enforcement layer explicitly deferred to a later engineering task package.

---

## Execution Result

**Status:** Completed (Founder-accepted)
**Started:** 2026-07-16
**Completed:** 2026-07-16
**Founder acceptance:** 2026-07-16
**Commit(s):** — (see next commit, ENG-EX1-003 only)
**Reviewer:** Founder
**Validation:** See Notes below. Verified end-to-end against real Jannat data via the live `POST /files/upload` endpoint (real Postgres, real auth, real `NCOLiteOrchestrator` run) — not a static/offline check.
**Follow-up:** Row/file-level lineage (`source_file`/`source_row_number`, currently dropped by `PoultrySituationService._evidence()` before reaching Executive Intelligence) remains deferred to Backlog per Founder decision #2 — no upstream component was touched to attempt closing that gap.
**Notes:**

**Founder decisions applied (this activation):**
1. Category-level statement traceability accepted as sufficient for Sprint EX-1. Accepted `source_type` vocabulary: `oie_signal` / `oce_context` / `synthesis`. Accepted `trace_status` vocabulary: `traced` / `coarse` / `pending`.
2. Row/file-level lineage deferred to Backlog. No modification made to `PoultrySituationService`, OIE, OCE, KAE, NCE Lite, or any upstream Runtime Component.
3. `statement_trace` added additively to `CEOBrief`. No existing field changed, renamed, or removed.
4. Template-derived statements (`why_it_matters`, the fixed 5-item action checklist, `headline`, `business_impact.operational`/`.financial`, `executive_attention`) are labeled `source_type: synthesis`, `trace_status: coarse` — never represented as fully evidence-traced, since their content is invariant to the specific evidence present (keyed only on `situation_type`).
5. `pending_executive_language` sections (`executive_priority`, `executive_assessment`, `business_impact.strategic`, and each `executive_actions[i]`'s priority/reason/expected_outcome) carry `trace_status: pending` with `source_ref: None` (or, for the grouped action sub-fields, a `pending_fields` list — never a fabricated source).
6. No frontend files touched. Instrumentation exists in backend/API output only.
7. Implemented in exactly the 4 authorized files: `app/oip/models/ceo_brief.py`, `app/oip/services/ceo_brief_service.py` (`_statement_trace()` + wiring), `app/nco/pipeline.py` (only `_apply_evidence_policy_to_brief()`), `app/api/files.py` (only `_summarize_nco_result()`).

**Classification logic:** `traced` = statement content is directly derived from the specific evidence instance(s) present in this brief (e.g. `what_happened`'s narrative quotes the actual trend-signal message and count; `facts`/`evidence_summary`/`what_changed` items are 1:1 with a specific `OperationalSignal`; `confidence`/`confidence_explanation`/`missing_evidence`/`recommended_company_inputs` are keyed to the specific evidence type(s) actually missing in this run). `coarse` = statement content is a fixed template invariant to the specific evidence present, keyed only on `situation_type` (would read identically regardless of what the evidence said). `pending` = no real statement exists yet (Aboura's language not yet authored); source is never invented.

**Verification performed against real Jannat data** (`data_sources/jannat_al_firdaws/2026_06/poultry_operations/التقرير_الفني_اليومي_حقول_ديرتنا.xlsx`), via the live, authenticated `POST /files/upload` endpoint (real `nawa-postgres` container, real `owner@jannat-local.dev` JWT login, real DB-persisted `files` row):
- `statement_trace` present on the captured brief: 39 entries.
- All entries use only the approved vocabulary: `source_type ⊆ {oie_signal, oce_context, synthesis}` (confirmed: all 3 present), `trace_status ⊆ {traced, coarse, pending}` (confirmed: all 3 present).
- `why_it_matters` and all 5 `recommended_next_actions[i]` / `executive_actions[i].action` entries confirmed `synthesis` + `coarse`, per Founder decision #4.
- `executive_priority`, `executive_assessment`, `business_impact.strategic`, and all 5 `executive_actions[i].priority_reason_outcome` entries confirmed `trace_status: pending` with no fabricated `source_ref` (`None` or an explicit `pending_fields` list only).
- `oce_context` entries for `confidence`, `confidence_explanation`, both `missing_evidence[i]`, and both `recommended_company_inputs[i]` confirmed present and correctly correlated (`evidence_type` matches the corresponding missing-evidence item).
- Re-confirmed the ENG-EX1-002 taxonomy fix still holds: zero `"Add Company Input:"` strings in `executive_actions` or `recommended_actions` in this same run.
- All 39 `field` values confirmed unique (no collisions/overwrites).
- `ast.parse` syntax check clean on all 4 changed files.
