# ENG-EX1-000 — Executive Intelligence Baseline Capture

**Priority:** P0. First task. Must complete before any other Sprint EX-1 engineering task touches Executive Intelligence output.
**Owner:** AI Engineering Team (Claude Code / Codex).
**Ownership layer:** Rendering (capture-only).

---

## Objective

Capture the current Executive Brief output verbatim, before any Sprint EX-1 change lands, so the Founder Acceptance Test can compare Before Sprint vs After Sprint on real Jannat data.

## Scope

- Capture-only. No modification of Executive Intelligence or any Runtime Component.
- One or more Executive Brief outputs generated on real Jannat Al-Firdaws data.
- Verbatim preservation. No editing. No filtering. No interpretation.
- Timestamped.

## Expected Deliverable

Captured Executive Brief output(s) from real Jannat data, preserved verbatim, timestamped, stored under the Sprint EX-1 artifacts, and reference-able for the end-Sprint Founder Acceptance Test comparison.

## Dependencies

None. This is task zero for Sprint EX-1 engineering.

## Blockers

None currently.

## Acceptance Criteria

- Capture completed before any other Sprint EX-1 engineering task modifies Executive Intelligence output.
- Baseline outputs preserved verbatim. No modification, filtering, or interpretation applied.
- Timestamped and reference-able for the end-Sprint Founder Acceptance Test comparison.
- No changes to any Runtime Component during capture.

---

## Execution Result

**Status:** Complete
**Started:** 2026-07-09
**Completed:** 2026-07-09T21:10:05Z
**Commit(s):** —
**Reviewer:** —
**Validation:** Pipeline entry/exit located and confirmed against live upload flow; baseline captured by running the existing `NCOLiteOrchestrator` (same code path as `app/api/files.py`) end-to-end against the real Jannat Al-Firdaws daily poultry report, with `store_memory=False` and no `MemoryRepository` wired, so no runtime/memory write occurred. A secondary capture via the lower-level OIP CLI (`operational_pipeline_service`) was also preserved for reference. No source file was modified.
**Follow-up:** ENG-EX1-001 (Executive Intelligence Analysis) can proceed using this baseline for before/after comparison.
**Notes:**

- Executive Brief generation entry point (current implementation, "Executive Brief" = `CEOBrief`): `NCOLiteOrchestrator.run_upload_completed()` → `_run_excel_poultry_report()` in [app/nco/orchestrator.py](../../../app/nco/orchestrator.py), driven by the live upload-completed handler in [app/api/files.py](../../../app/api/files.py).
- Pipeline order: KAE (`NCOLitePipeline.run_kae` → `OperationalPipelineService.parse_poultry_daily_report`, loads/translates/validates the Excel report) → OIE (`run_oie`, derives metrics/events/signals, generates situations) → OCE (`run_oce`, builds operational contexts, identifies available/missing evidence) → MVP evidence policy (`evaluate_mvp_evidence_policy`) → NCE Lite gate (`run_nce_lite`, no reasoning) → **Executive Intelligence** (`run_executive_intelligence` in [app/nco/pipeline.py](../../../app/nco/pipeline.py), which calls `CEOBriefService.generate_briefs()` in [app/oip/services/ceo_brief_service.py](../../../app/oip/services/ceo_brief_service.py) then applies the evidence-policy adjustments) → OME (`store_ome_foundation`, persists to memory when configured).
- Pipeline exit: `NCOExecutionResult.executive.ceo_briefs` (a list of `CEOBrief`, [app/oip/models/ceo_brief.py](../../../app/oip/models/ceo_brief.py)), serialized in the API response by `_summarize_nco_result()` in `app/api/files.py`.
- Real Jannat data used: `data_sources/jannat_al_firdaws/2026_06/poultry_operations/التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` (the default source in `OperationalPipelineService`).
- Baseline result: 1 CEO Brief generated (`poultry_production_drop`, warning severity, 2026-05-11 → 2026-05-13), confidence `reduced` due to two MVP-optional missing-evidence types (`vet_reports`, `temperature_ventilation`).
- Artifacts preserved under [docs/execution/sprint_ex1/artifacts/](artifacts/): `baseline_executive_brief_nco_lite_2026-07-09T21-10-05Z.json` (primary — full live-flow output), `baseline_oip_cli_capture_2026-07-09T21-10-05Z.txt` (secondary — raw OIP CLI output), `baseline_capture_2026-07-09T21-10-05Z.md` (capture note explaining both).
- Current output is not yet the eight-section Executive Brief structure defined in the Sprint goal — it is a flat `CEOBrief` (headline, severity, what_happened, why_it_matters, evidence_summary, recommended_next_actions, confidence). This is an observation for ENG-EX1-001, not a change made here.
