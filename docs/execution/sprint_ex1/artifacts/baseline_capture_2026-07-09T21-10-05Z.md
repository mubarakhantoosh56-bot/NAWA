# Executive Intelligence Baseline Capture — 2026-07-09T21:10:05Z

Captured for ENG-EX1-000, before any Sprint EX-1 change lands.

## Source data

Real Jannat Al-Firdaws data: `data_sources/jannat_al_firdaws/2026_06/poultry_operations/التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` (the default daily technical poultry report path used by `OperationalPipelineService`).

## Files in this capture

- `baseline_executive_brief_nco_lite_2026-07-09T21-10-05Z.json` — **primary artifact.** Full `NCOExecutionResult` JSON produced by running `NCOLiteOrchestrator.run_upload_completed()` (`app/nco/orchestrator.py`) against the real report, with `company_id=None` and `store_memory=False`. This is the same code path the live upload-completed flow in `app/api/files.py` drives, including the KAE → OIE → OCE → MVP evidence policy → NCE Lite gate → Executive Intelligence (CEO Brief) → OME steps. The Executive Brief itself is under `executive.ceo_briefs`; the evidence-policy adjustments applied to it (confidence downgrade, added "Add Company Input" actions) are under `evidence_policy`.
- `baseline_oip_cli_capture_2026-07-09T21-10-05Z.txt` — secondary artifact. Output of `python -m app.oip.services.operational_pipeline_service --limit 0`, the lower-level OIP CLI. This calls `CEOBriefService.generate_briefs()` directly, **without** the MVP evidence policy pass, so its CEO Brief shows `confidence: "initial"` instead of `"reduced"` and lacks the "Add Company Input" actions. Kept for reference because it shows OIP's raw records/metrics/events/signals/situations/operational-context output in one place.

## Result summary (from the primary artifact)

- 9 parsed records, 90 metrics, 9 events, 10 signals, 1 situation, 1 operational context, 1 CEO Brief.
- Situation: `poultry_production_drop`, warning severity, 2026-05-11 → 2026-05-13.
- Missing evidence: `vet_reports`, `temperature_ventilation` (both MVP-optional) → evidence policy allows continuation with confidence `reduced`.
- `context_ready_for_reasoning`: `false` (blocked only on optional evidence under current MVP policy, so the pipeline still proceeds through NCE Lite and Executive Intelligence).

## How this was produced

No runtime file was modified. Two read-only invocations of existing code:

```
.venv/Scripts/python.exe -m app.oip.services.operational_pipeline_service --limit 0
.venv/Scripts/python.exe <scratchpad script calling NCOLiteOrchestrator.run_upload_completed(...)>
```

`store_memory=False` and no `MemoryRepository` was wired, so no event was written to the memory/OME store during capture.
