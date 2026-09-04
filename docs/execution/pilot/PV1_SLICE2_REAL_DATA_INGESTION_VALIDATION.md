# PV1 Slice 2 — Real Data Ingestion Validation

**Priority:** P0. Second slice of PV1 — Jannat Al-Firdaws Real-Company Pilot Validation.
**Owner:** AI Engineering Team (Claude Code).
**Ownership layer:** Validation only. No code, test, or migration change authorized or made.
**Repository First Policy compliance:** This document is the required task document for this Slice.

---

## Reconciliation Amendment (2026-09-04) — Upload-Routing + Evidence Precision

The Founder identified, after the first pass of this document, that **direct parser success is not the same evidence as real user upload-routing success**. The first pass proved `OperationalPipelineService` can parse every real file directly; it did not prove the actual production upload-routing function (`app.api.files._run_nco_lite_after_upload_if_applicable`, and the `NCOLitePipeline`/`CompanyInputClassifier` stages downstream of it) actually selects the structured pipeline for those same real files when uploaded through the real product path. This amendment adds that missing evidence and corrects two claims that the first pass overstated. Nothing below was fixed — all findings are recorded, not corrected in code. The sections below are updated in place; where a number or classification changed, the corrected value is what now appears in §6, §9, §10, §14, §19, §21, §22 — the original (superseded) figures are not left standing elsewhere in this document.

**Summary of what changed:**
1. **New evidence gathered:** a real upload-routing matrix (all 6 real poultry files + the real feed-mill file, through the actual `_run_nco_lite_after_upload_if_applicable` production function via the existing safe in-memory FakeDB test infrastructure, using real file bytes and real original filenames — never renamed).
2. **New defect found:** DEFECT-003 — one real, structurally-valid poultry file is silently skipped by the live upload route's filename-marker gate, despite parsing correctly.
3. **Corrected overclaim:** DEFECT-001's real scope is **3 of 6 files**, not "5 of 6" as originally stated — verified by a full-file (not sample-only) header-presence check.
4. **Corrected overclaim:** DEFECT-002 (duplicate upload) was originally proven only against a synthetic workbook; it is now also proven against a real Jannat workbook.
5. **Strengthened, not weakened:** Gate B (provenance) is now proven via the real upload router against real files, not simulated stamping.
6. **Corrected scope precision:** Gate G was scored PROVEN generically; it is now scored PARTIAL, since only OIP context semantics were exercised — the older persisted `operational_events` table subsystem was not.
7. **New evidence:** a deterministic, counted source-to-parsed field comparison (Validation D) replaces the earlier prose-only "everything matched" claim.
8. **New evidence:** the real generic RAG extractor was actually invoked read-only against the 7 real warehouse/sales/finance files, replacing the earlier extension-allowlist-only inference.

## 1. Founder activation

The Founder explicitly activated PV1 Slice 2 — Real Data Ingestion Validation, immediately after PV1 Slice 1 closed. This Slice is validation-first: not general feature development, not authorization to fix every defect discovered, not authorization for new translators, migrations, schema expansion, reasoning features, or any post-M9 feature milestone.

## 2. Baseline checkpoint

Branch `claude-safe-review`. Verified before any action: local HEAD = tracking origin = live origin = `12b4f0d55436e0018455582db673c236924879fb`, divergence 0/0, working tree clean, index clean. M9 CLOSED. PV1 ACTIVE. PV1 Slice 1 CLOSED — REMOTE CHECKPOINT VERIFIED.

## 3. Validation environment

**Target:** the developer's existing local PostgreSQL instance (`nawa-postgres` Docker container, `localhost:5433/aimx`), the same instance used throughout this project's own backend test suite all session. `DATABASE_URL` in `.env` confirmed to point there (credential redacted, host/port/db confirmed non-production). `ENVIRONMENT` is unset, defaulting to `"development"`; `Settings.is_production` requires `"production"`/`"staging"` and is therefore `False`. **No production or shared staging environment was touched.** No credentials, connection strings, or secrets were printed at any point in this Slice.

**Real Jannat company already present locally:** a real "Jannat Al-Firdaws" company row already existed in this local database (`id=b4a0f97a-1615-4427-9936-4dd6fd8c0552`, pre-existing from earlier project work this session, not created by this Slice), with a real `dairtna-poultry` department (`id=ac165787-43e1-49ff-a435-6f24d765a642`). This row was used **read-only** for entitlement/scope evaluation (`is_jannat_tenant`, `is_poultry_department_scope`) in Groups A, H. No row in this company's data was created, modified, or deleted by this Slice, except the one explicitly bounded, disposable, in-memory (never-persisted-to-Postgres) duplicate-upload check in Group F, which used its own throwaway synthetic company id and an in-memory fake database — see §13.

**Static source isolation (Founder Pilot Rule 1):** enforced via a process-local Python environment variable (`os.environ["NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED"] = "false"`) set before any `app.*` module import in the validation harness, for the lifetime of that one process only. No application code was edited. No `.env`/`.env.example` file was edited. This override does not persist beyond the process. Proven excluded in practice — see §14.

## 4. Real-file inventory re-verification

Re-verified directly from the filesystem (not merely re-read from the Slice 1 document), matching Slice 1 exactly:

| Category | Count |
|---|---|
| Real files (non-`.gitkeep`) | 14 |
| `.gitkeep` placeholders | 5 |
| Total entries | 19 |
| `poultry_operations/` | 6 xlsx |
| `warehouse/` | 1 xlsx |
| `sales/` | 1 xlsx |
| `feed_mill/` | 1 xlsx |
| `finance/` | 5 pdf |

## 5. Supported-shape re-confirmation

Confirmed directly against the live `ARABIC_COLUMN_MAP` (`app/oip/translators/poultry_report_translator.py`) and `feed_mill_inventory_translator.py`:

- **Poultry daily technical report** — two shapes, header-co-occurrence detected (never filename-based): `poultry_daily_technical_hall` (anchored on `التاريخ` + `رصيد الطيور`), `poultry_daily_technical_aggregate` (anchored on `التاريخ` + `إجمالي أعداد الطيور للحقول`).
- **Feed-mill raw-material balance block** — the bounded `رصيد الجاروشة` block only, column-aligned, gap-bounded label matching (`الصنف` header → nearest `رصيد الجاروشة` row → nearest `الكمية تكفي/يوم` row).
- **Confirmed unsupported/unconfirmed:** warehouse report, sales workbook, finance PDFs, and the feed-mill workbook's other six sheets (`تسجيل الوارد`, `الوارد AUTO`, `يومي العلف`, `تركيبة علف`, `أسعار المواد`, `Sheet1`) — none of these has a confirmed structured-ingestion entrypoint in the current codebase. No translator was built for any of them in this Slice.

## 6. Poultry workbook results (Group A) — all 6 real files

Executed via `OperationalPipelineService.run_poultry_daily_report(path)` — the exact real production entrypoint also used by `operational_truth_context.py`'s live-upload branch. **All 6 real files parsed and validated successfully — zero validation failures.**

| File | Detected shape | Entity (type, ref) | Records | Metrics | Signals | Situations | **Live upload route** |
|---|---|---|---|---|---|---|---|
| `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` | `poultry_daily_technical_hall` | `(None, None)` | 9 | 117 | 10 | 1 (`poultry_production_drop`, ref=null) | **SUCCEEDED** |
| `تقرير_القاعة_2_الأبيض.xlsx` | `poultry_daily_technical_hall` | `(production_hall, "2")` | 9 | 117 | 18 | 0 | **SUCCEEDED** |
| `تقرير_القاعة_2_الأحمر.xlsx` | `poultry_daily_technical_hall` | `(production_hall, "2")` | 8 | 104 | 19 | 3 (`poultry_production_drop`, ref="2") | **SUCCEEDED** |
| `تقرير_القاعة_3_الأبيض.xlsx` | `poultry_daily_technical_hall` | `(production_hall, "3")` | 9 | 117 | 22 | 4 (`poultry_production_drop`, ref="3") | **SUCCEEDED** |
| `تقرير_إجمالي_الأبيض_والأحمر.xlsx` | `poultry_daily_technical_hall` | `(production_hall, "2")` | 8 | 104 | 9 | 0 | **SUCCEEDED** |
| `إجمالي_حقول_ديرتنا_الإنتاج.xlsx` | `poultry_daily_technical_aggregate` | `(company_aggregate, None)` | 7 | 91 | 15 | 0 | **SKIPPED — see DEFECT-003** |
| **Total** | | | **50** | **650** | **93** | **8** | **5/6 routed live** |

**Entity resolution finding:** `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` resolved to `(None, None)` — re-inspected the raw sheet directly: row 0 is a free-text title ("شركة حقول ديرتنا للإنتاج الحيواني - التقرير الفني اليومي"), row 1 blank, row 2 is the header row directly — **no structural `رقم القاعة`/`اسم الحقل` label exists anywhere in this file.** This is a real, confirmed **DATA GAP** in that specific source file, not a code defect — the translator correctly refuses to guess entity identity from free text, per its own documented design law.

### 6.1 Real upload-routing matrix (Reconciliation Amendment)

The table above's "Records/Metrics/Signals/Situations" columns prove **direct parser capability** — `OperationalPipelineService` invoked directly. That is a distinct claim from **live upload-route capability** — the real user path: `POST /files/upload` → `app.api.files._run_nco_lite_after_upload_if_applicable` → tenant/department/filename gates → `NCOLitePipeline`/`CompanyInputClassifier` → KAE/OIE/OCE → `_persist_structured_ingestion_result`.

This matrix was executed for real: each of the 6 real poultry workbooks was passed, with its real bytes and its real original filename (never renamed), through the actual `_run_nco_lite_after_upload_if_applicable` function, using a disposable synthetic tenant/department identity in the existing safe in-memory `_FakeDB` (`tests/test_m7_slice1_upload_truth_bridge.py`'s established infrastructure — reused, not modified).

| File | Filename-marker gate | Classifier pipeline | Live route result | Draft created | Record count |
|---|---|---|---|---|---|
| `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` | PASS | `excel_poultry_report` (0.90) | **succeeded** | Yes | 9 |
| `تقرير_القاعة_2_الأبيض.xlsx` | PASS | `excel_poultry_report` (0.90) | **succeeded** | Yes | 9 |
| `تقرير_القاعة_2_الأحمر.xlsx` | PASS | `excel_poultry_report` (0.90) | **succeeded** | Yes | 8 |
| `تقرير_القاعة_3_الأبيض.xlsx` | PASS | `excel_poultry_report` (0.90) | **succeeded** | Yes | 9 |
| `تقرير_إجمالي_الأبيض_والأحمر.xlsx` | PASS | `excel_poultry_report` (0.90) | **succeeded** | Yes | 8 |
| `إجمالي_حقول_ديرتنا_الإنتاج.xlsx` | **FAIL** | *(never reached — gate returns before classification)* | **SKIPPED** | No | — |

**Critical question answered:** 5 of the 6 real poultry files that parse directly also reach structured ingestion through the actual upload route. The 6th (`إجمالي_حقول_ديرتنا_الإنتاج.xlsx`, the company-aggregate report) is silently skipped — see **DEFECT-003** (§19).

**Root cause, traced exactly:** `app/api/files.py::_run_nco_lite_after_upload_if_applicable` checks `_has_daily_report_filename_marker(filename)` — a coarse token match against `("daily", "technical", "report", "تقرير", "التقرير", "يومي", "اليومي")` — **before** any content-based classification runs. `إجمالي_حقول_ديرتنا_الإنتاج.xlsx` contains none of these tokens (it does contain `ديرتنا`, which the downstream `CompanyInputClassifier` would have correctly recognized — confirmed by running the classifier directly against this filename in isolation: it returns `excel_poultry_report` at 0.78 confidence, `requires_human_confirmation=False` — but the classifier is never reached, because the filename-marker gate returns `None` first). This is a real, filename-heuristic-caused routing gap, independent of and prior to the (correctly working) content-based shape detection and classification stages.

For the 5 files that did route successfully, `structured_ingestion_status` reported `"succeeded"` and `record_count` in the live-route NCO summary matched the direct-parser record counts in §6's table exactly (9/9/8/9/8) — the same real KAE/OIE/OCE pipeline runs in both paths, as expected, since both ultimately call `OperationalPipelineService`'s translator.

## 7. Source-to-parsed sample comparison

Bounded sample (first/middle/last row) taken for every file; every present, supported field's parsed value was compared against the raw source cell. Example (first row, `إجمالي_حقول_ديرتنا_الإنتاج.xlsx`, row 4):

| Field | Source cell | Parsed value | Match | Normalization | Provenance |
|---|---|---|---|---|---|
| `date` | `2026-05-13` (native Excel date) | `2026-05-13` | Yes | None | via `source_file`/`row_number` |
| `bird_balance` | `225032` | `225032` | Yes | None | Yes |
| `daily_mortality` | `198` | `198` | Yes | None | Yes |
| `weekly_mortality_rate` | `0.63` (source cell already a fraction/percent-like value) | `0.63` | Yes | None | Yes |
| `daily_production_rate` | `76.7` | `76.7` | Yes | None | Yes |
| `standard_production_rate` | *(column absent from this file)* | `null` | N/A — genuine absence | — | — |
| `broken_eggs` | `168` | `168` | Yes | None | Yes |
| `dirty_eggs` | `78` | `78` | Yes | None | Yes |
| `water_consumption` | `66000` | `66000` | Yes | None | Yes |
| `feed_received` | `28000` | `28000.0` | Yes | type only (float) | Yes |
| `feed_consumed` | `23816` | `23816.0` | Yes | type only (float) | Yes |
| `feed_per_bird_average` | `106` | `106.0` | Yes | type only (float) | Yes |

### 7.1 Deterministic counted comparison, all 6 files (Reconciliation Amendment)

The prior pass's claim "everything matched" is replaced here with an actual counted tally. First/middle/last parsed row was taken from each of the 6 real poultry files' full real record set (18 sample rows total), and all 18 canonical fields (`date`, `day_name`, `age_week`, `age_day`, `bird_balance`, `daily_mortality`, `weekly_mortality`, `weekly_mortality_rate`, `daily_tray_production`, `box_production`, `daily_production_rate`, `standard_production_rate`, `broken_eggs`, `dirty_eggs`, `water_consumption`, `feed_received`, `feed_consumed`, `feed_per_bird_average`) were compared per sampled row against the pre-normalization raw source cell (via `resolve_source_label`, reading each record's own `raw_values`), executed programmatically against the real translator output — not eyeballed:

| Filename | Sample rows | Field comparisons | Matches | Expected nulls (column absent) | Mapping gaps (DEFECT-001) | Unexpected mismatches |
|---|---|---|---|---|---|---|
| `إجمالي_حقول_ديرتنا_الإنتاج.xlsx` | 3 | 54 | 45 | 9 | 0 | 0 |
| `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` | 3 | 54 | 45 | 0 | 9 | 0 |
| `تقرير_إجمالي_الأبيض_والأحمر.xlsx` | 3 | 54 | 45 | 0 | 9 | 0 |
| `تقرير_القاعة_2_الأبيض.xlsx` | 3 | 54 | 39 | 15 | 0 | 0 |
| `تقرير_القاعة_2_الأحمر.xlsx` | 3 | 54 | 42 | 12 | 0 | 0 |
| `تقرير_القاعة_3_الأبيض.xlsx` | 3 | 54 | 45 | 0 | 9 | 0 |
| **Total** | **18** | **324** | **261** | **36** | **27** | **0** |

**261 real matches, 0 unexpected mismatches, across 324 field-level comparisons.** The date field required accounting for a display-format difference (raw source cells are DD/MM/YYYY strings; the parsed `date` field is a Python `date` object whose string form is ISO YYYY-MM-DD) — verified as the same real calendar date on every one of the 18 sampled rows, not a value change, consistent with the "type normalization only, never a value change" standard applied throughout this document. The 36 "expected nulls" are genuine source-column absences (verified column-by-column, not assumed). The 27 "mapping gaps" are exactly DEFECT-001 (§19) — 9 gaps × 3 affected files, each gap being one of `feed_received`/`feed_consumed`/`feed_per_bird_average` on one of the 3 sampled rows.

**No unit conversion, no silent value alteration, no forced-zero for a missing column was observed in any of the 324 comparisons.** Missing source columns consistently parsed as `null`, never `0`.

## 8. Raw / unmapped field check

Confirmed directly against real files: egg-size grading columns (`S`, `M`, `L`, `XL`, `خشن XXL`, `صفارين XXXL`, `أشقر`/`الأشقر`) are present with real numeric values in every poultry file and are **never guessed into a canonical field** — verified preserved verbatim in each record's `raw_values` dict. `وزن البيضة (غرام)` (egg weight in grams — real values 56.2/65.3/64.9 g observed) is also present and unmapped, confirming the pre-existing, Founder-acknowledged "egg weight/size distribution" scope gap remains accurate against real data.

**One real, confirmed SEMANTIC MAPPING DEFECT found — see §19, DEFECT-001. Its scope is corrected in this reconciliation pass: the affected files are 3 of the 6 real poultry files, not "5 of 6" as originally (incorrectly) stated.** A full-file check (every record's `raw_values`, not just the sampled rows) confirms: `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx`, `تقرير_إجمالي_الأبيض_والأحمر.xlsx`, and `تقرير_القاعة_3_الأبيض.xlsx` all genuinely contain the short-variant feed headers (`العلف المستلم`/`العلف المستهلك`/`العلف للطير الواحد`) with real unmapped data. `تقرير_القاعة_2_الأبيض.xlsx` and `تقرير_القاعة_2_الأحمر.xlsx` contain **neither** the short nor the long feed-header variant anywhere in their sheets — for these 2 files, the absence of `feed_received`/`feed_consumed`/`feed_per_bird_average` is a genuine **DATA GAP** (the source itself does not report feed data for these halls/dates), not a mapping defect. The original claim conflated these two distinct causes; they are now correctly separated.

## 9. Feed-mill result (Group B)

Executed via `OperationalPipelineService.parse_feed_mill_inventory(path)` against `feed_mill/جرد الجاروشة.xlsx`. **Result: 15/15 materials correctly extracted, including numeric balance and days-coverage — fully working.**

*(Correction recorded in the interest of validation integrity: an initial pass of this validation misread the result as "balance/days-coverage all null" due to the validation script itself querying the wrong attribute names — `FeedMillInventoryRecord`'s real fields are `raw_material_inventory` and `source_reported_days_coverage`, not `balance`/`days_coverage`. Re-run against the correct field names, per real production code, confirms full correct extraction. This is recorded transparently rather than silently corrected, since PV1 exists to produce trustworthy findings, including about its own validation process.)*

Sample (of 15, verified against the raw sheet's row 6/row 8 cells directly):

| Material | `raw_material_inventory` | `source_reported_days_coverage` | Match source? |
|---|---|---|---|
| الذرة (corn) | 216290.2 | 14.397 | Yes |
| الصويا (soybean) | 47828.6 | 8.818 | Yes |
| بريمكس (premix) | 10560.0 | 44.0 | Yes |
| مضاد سموم (toxin binder) | 4887.0 | 101.8125 | Yes |

**One real, non-defect finding:** `report_date_status = "unresolved"` for all 15 records. The raw sheet contains a bare date cell (`2026-06-12`) in the material-header row, not paired with any of the `AUTHORITATIVE_DATE_LABELS` allowlist (`تاريخ التقرير`/`تاريخ الجرد`/`تاريخ الرصيد`). The translator correctly refuses to promote an unlabeled date as authoritative — a real limitation of this specific source file's layout, not a code defect. `report_date` therefore stays `None` for this real file today.

### 9.1 Translator capability vs. live upload-route capability (Reconciliation Amendment — now directly tested)

`parse_feed_mill_inventory` is a real, directly-callable, correct capability, proven above. Whether the live `POST /files/upload` route actually reaches it for the real feed-mill file was directly tested this pass, through the same real `_run_nco_lite_after_upload_if_applicable` function and the same safe in-memory FakeDB infrastructure used in §6.1, against the real `جرد الجاروشة.xlsx` file with its real, unmodified filename.

**Result: TRANSLATOR CAPABILITY = PROVEN. LIVE USER-UPLOAD CAPABILITY = NOT WORKING / NOT ROUTED.**

Two independent, compounding gaps were confirmed, both without editing any code:

1. **Filename-marker gate fails first.** `_has_daily_report_filename_marker("جرد الجاروشة.xlsx")` returns `False` (no token from `("daily", "technical", "report", "تقرير", "التقرير", "يومي", "اليومي")` is present) — `_run_nco_lite_after_upload_if_applicable` returns `None` before any classification or KAE stage runs. Confirmed directly (executed, not inferred): live-route result = **SKIPPED**, no draft created.
2. **Even if the filename gate were bypassed, no feed-mill dispatch exists downstream.** `CompanyInputClassifier._classify_excel` would route `"جرد الجاروشة.xlsx"` to the generic `spreadsheet_intake` pipeline (confidence 0.62, `requires_human_confirmation=True` — below the classifier's own 0.70 threshold, since neither `"poultry"`, `"dairtna"`, `"deirtna"`, nor `"ديرتنا"` appears in this filename), not `excel_poultry_report`. And even that is moot: `NCOLitePipeline.run_kae` (`app/nco/pipeline.py`) unconditionally calls `self.operational_pipeline.translator` — the poultry translator only. There is no feed-mill branch anywhere in `app/nco/pipeline.py`, `app/nco/orchestrator.py`, or `CompanyInputClassifier` (confirmed by direct search — zero matches for any feed-mill reference in any of the three). The NCO-lite upload-completed orchestration path has **no route to `parse_feed_mill_inventory` at all today**, independent of the filename-marker gap.

This is recorded as **DEFECT-004** (§19), kept distinct from DEFECT-003 (the poultry aggregate file's routing gap) because the causes differ materially: DEFECT-003 is fixed by the filename-marker gate alone (the classifier and KAE would both work correctly if reached), while DEFECT-004 would persist even if the filename-marker gate were bypassed, since no feed-mill dispatch exists anywhere downstream in the NCO-lite orchestration path.

## 10. Unsupported real sources (Group C)

### 10.1 Real generic extraction, actually invoked (Reconciliation Amendment)

The first pass of this document inferred "generically ingestible" from extension-allowlist membership alone. Per the Founder's correction, extension support alone is not sufficient real-pilot evidence. The real production extractor, `app.services.rag.extractors.extract_text`, was invoked read-only against every one of the 7 real files in this category (no output persisted, no database write):

| Source | Extension | Extractor invoked? | Success/Failure | Non-empty? | Char count | Classification |
|---|---|---|---|---|---|---|
| `warehouse/جرد_مخزن_البيض.xlsx` | `.xlsx` | Yes | Success | Yes | 1,013 | **AVAILABLE + GENERIC EXTRACTION PROVEN** — readable Arabic sheet text, e.g. `"[Sheet: جرد مخزن البيض] شركة حقول ديرتنا للإنتاج الحيواني - جرد مخزن البيض - 19 مايو 2026 ..."` |
| `sales/مبيعات_جنة_الفردوس_وقاعة_البيض.xlsx` | `.xlsx` | Yes | Success | Yes | 789 | **AVAILABLE + GENERIC EXTRACTION PROVEN** — readable Arabic sheet text, e.g. `"[Sheet: مبيعات جنة الفردوس] مبيعات جنة الفردوس - 19/05/2026 ... أبيض صفارين XXXL ..."` |
| `finance/المخزن.pdf` | `.pdf` | Yes | Success (no exception) | Yes (231 chars) | 231 | **AVAILABLE + GENERIC EXTRACTION PROVEN, with a real quality caveat** (below) |
| `finance/ح 3.pdf` | `.pdf` | Yes | Success (no exception) | Yes (2,376 chars) | 2,376 | same caveat |
| `finance/ح احمر.pdf` | `.pdf` | Yes | Success (no exception) | Yes (1,033 chars) | 1,033 | same caveat |
| `finance/ح1.pdf` | `.pdf` | Yes | Success (no exception) | Yes (2,262 chars) | 2,262 | same caveat |
| `finance/ح2.pdf` | `.pdf` | Yes | Success (no exception) | Yes (2,289 chars) | 2,289 | same caveat |

**Real, new finding — PDF text-quality caveat.** All 5 real finance PDFs extract without error and produce non-empty text, so `extract_text` genuinely succeeds by its own contract (no exception, non-empty output) — **AVAILABLE + GENERIC EXTRACTION PROVEN** is accurate for the mechanical claim. However, the extracted text for all 5 is visibly garbled: character-reordering/encoding artifacts consistent with naive PDF text extraction over right-to-left Arabic tables without BiDi/glyph reordering (e.g. `المخزن.pdf` extracts as `"Ȗǽɑɖ ا 5/1/2026 ǊǦ ɘɖ..."`; the `ح*.pdf` files extract column headers concatenated without reliable word boundaries, e.g. `"ت كمية  اﻻستهﻼكسعر الكليوسعر كمية اﻻستهﻼكالهﻼكسعر الطيرسعر الهﻼكعﻼج ولقاحمصاريفكارتون وطبقالمجموعمبيع اﻹنتاجمﻼححظات..."`). This means: technically the extractor works and returns content; **the extracted content's practical usability for semantic RAG search over these specific real Arabic finance PDFs is questionable and was not further evaluated in this Slice** — the file is not silently dropped or force-fit, but the mechanical "success" should not be read as proof that Company-Brain-quality search would find real facts in it. This is recorded as an honest quality observation, not a new defect (no fabrication, no crash, no silent data loss — the text really was extracted, it is just poor quality for RTL tabular Arabic), and it is out of this Slice's fix authority regardless.

`SUPPORTED_EXTENSIONS = {.txt, .md, .csv, .json, .pdf, .docx, .xlsx}` confirmed directly from `app/services/rag/extractors.py`. Real-time proof that structured shape detection correctly returns "unsupported" for all 7 of these real files (not a guess, not a crash, not a false-positive structured record) while generic extraction independently succeeds for all 7 at the mechanical level — **AVAILABLE + STRUCTURED INGESTION NOT SUPPORTED** for all 7, confirmed by the structured pipeline's own shape-detection returning `None`/0 records for the 2 `.xlsx` files, and by the `.pdf` extension being outside the `.xlsx`-only structured-ingestion gate entirely for the 5 finance files.

## 11. Date / entity / unit semantics (Group D)

- **Dates:** every real date cell parsed correctly (native Excel date objects; `DD/MM/YYYY` string cells in the finance-adjacent raw fixture format also confirmed elsewhere in this codebase's test coverage). No date was altered.
- **Entities:** structural-label-only resolution confirmed (`رقم القاعة`/`اسم الحقل`), never filename-based, never free-text-guessed. One real file (§6) has no resolvable entity — correctly left `None`, not defaulted.
- **Units:** no unit conversion observed anywhere in the real run. Values pass through as raw numbers; the system makes no claim about kg vs. tonnes, liters vs. cubic meters, etc. — **unit semantics remain UNKNOWN/UNVALIDATED**, exactly as Slice 1 predicted, now empirically confirmed rather than merely inferred from code reading.

## 12. Validation failure path (Group E)

**No real file triggered a validation failure.** All 6 poultry files and the 1 feed-mill file passed validation as-is, with no source alteration. This means gate AD ("failure path is safe") has **no real-file evidence either way from this Slice** — the existing project's pytest suite already has synthetic coverage for the whole-file-fail behavior (confirmed present, not re-read in full here), which is referenced as corroborating context only, per this Slice's own instruction that synthetic tests cannot substitute for a real-file finding. **Gate AD: NOT APPLICABLE this Slice (no real failure occurred to observe).**

## 13. Duplicate / idempotency (Group F)

An existing, already-established, safe, in-memory test isolation mechanism was identified and reused: `tests/test_m7_slice1_upload_truth_bridge.py`'s `_FakeDB` (an in-memory stand-in for the database — no real Postgres write occurs), `_seed_tenant`, and `_configure_jannat_company_id`. **No new test infrastructure was built; these exact existing helpers were imported and reused** in one bounded, disposable script (`scratchpad`, never committed, not part of the tracked test suite), calling the real production function `app.api.files._run_nco_lite_after_upload_if_applicable` twice with a synthetic disposable company id and two **distinct** `file_id` values (mirroring exactly what two separate real uploads of the same report would produce).

**First pass (superseded):** the first pass of this check used a synthetic fabricated workbook (`_write_supported_workbook`), not a real Jannat file — technically proving the product behavior but overclaiming when the original wording described it as "real Jannat duplicate upload empirically demonstrated." That wording is corrected below.

**Reconciliation Amendment — repeated against an ACTUAL real Jannat workbook.** The same check was re-run using `poultry_operations/تقرير_القاعة_2_الأبيض.xlsx` — a real file confirmed to route successfully live in §6.1 — with its real bytes and real filename, unmodified, uploaded twice with two distinct disposable `file_id` values through the real production function.

**Result, executed and observed directly against the real file:** `structured_record_drafts` count after 2 distinct uploads of the same real workbook's identical content = **2**. No deduplication occurred.

**Gate AE score: BLOCKED BY PRODUCT DEFECT — empirically confirmed against a real Jannat workbook in safe in-memory production-routing validation** (upgraded from "NOT PROVEN": this is no longer an absence of evidence, it is direct proof that the "no unexpected duplication" capability does not hold today). Classification: **INGESTION DEFECT — DEFECT-002 (§19), now proven with a real workbook, not only a synthetic one.** The real Jannat/pilot dataset itself was never touched; the throwaway company/records existed only in an in-memory fake for the duration of one bounded, disposable script invocation — only the uploaded file's bytes were real.

## 14. Provenance trace (Group G)

One real value traced end-to-end: `bird_balance = 76942`, source `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx`, row 12, date `2026-05-19`.

`PoultryOperationalRecord` → `OperationalMetric` (via `PoultryDerivationService.derive`) → (no signal/situation fired for this specific value) → `assemble_truth_context()`'s output item:

```
source_file_id: 2a165b6f-854a-46df-85e9-88e1e46dadaf   (stamped at persistence-simulation time)
source_filename: التقرير_الفني_اليومي_حقول_ديرتنا.xlsx
source_company_id: b4a0f97a-1615-4427-9936-4dd6fd8c0552
source_department_id: ac165787-43e1-49ff-a435-6f24d765a642
source_row_number: 12
sheet_name: التقرير الفني اليومي
report_shape: poultry_daily_technical_hall
epistemic_origin: observed
canonical_field: bird_balance
normalized_value: 76942
raw_source_value: 76942
```

**Every stage traces back to its real source with no break.** `source_file_id` is stamped only at persistence time (the one authoritative point of identity, by design) — the original pass of this trace used a synthetic stand-in id to simulate that stamping point.

### 14.1 Provenance strength, now via the real upload router (Reconciliation Amendment)

The trace above proves the stamping *mechanism*. Whether a structured draft produced by an **actual real workbook, routed through the actual production upload router**, carries full provenance was directly tested in §6.1's matrix, against all 5 real poultry files that routed successfully. Every one of the 5 resulting `structured_record_drafts` rows carried complete, correct provenance with no break — for example, from `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx`:

```
company_id_on_draft:      ff50a2af-c529-4d8b-83e6-9795284305f0
department_id_on_draft:   83662d3a-4f17-46d8-8f12-05f4ee5eda3f
payload_file_id:          d9e1cdd8-7e90-423c-8a56-31c34ba63c20
payload_filename:         التقرير_الفني_اليومي_حقول_ديرتنا.xlsx
sample_record.source_file_id:       d9e1cdd8-7e90-423c-8a56-31c34ba63c20  (matches payload_file_id)
sample_record.source_filename:      التقرير_الفني_اليومي_حقول_ديرتنا.xlsx
sample_record.source_company_id:    ff50a2af-c529-4d8b-83e6-9795284305f0
```

The same held for all other 4 successfully-routed real files (`تقرير_إجمالي_الأبيض_والأحمر.xlsx`, `تقرير_القاعة_2_الأبيض.xlsx`, `تقرير_القاعة_2_الأحمر.xlsx`, `تقرير_القاعة_3_الأبيض.xlsx`) — each draft's `source_file_id`/`source_filename`/`source_company_id`/`source_department_id` matched its own real upload's identity exactly, no cross-contamination between the 5 disposable synthetic tenants used (each file was routed under its own separate synthetic company/department, confirming per-tenant provenance isolation held even across 5 independent real-file runs).

**Gate B: PROVEN, now with real-file + real-router evidence, not simulated stamping.** No manual stamping was used for this result — this is ACTUAL REAL JANNAT FILE + ACTUAL PRODUCTION UPLOAD ROUTER + the existing safe in-memory persistence model, exactly as required.

## 15. Static source isolation (Group H, gate AH)

**Executed against the real code path, real Jannat company/department, with `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED=false`:**

1. **Isolation on, no explicit upload:** `assemble_truth_context(company=REAL_JANNAT, aimx_department=DAIRTNA_POULTRY, uploaded_records=None)` → `status="no_evidence"`, `evidence_count=0`. **Zero static-scan artifacts entered Truth Context.**
2. **Isolation still on, WITH an explicit (simulated) real upload:** same call with 9 real, freshly-parsed, provenance-stamped records from `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` → `status="ok"`, `evidence_count=13`, all 3 resulting truth items carry `source_file_id` and full provenance.

**Gate AH: PROVEN.** Auto-bundled static source correctly excluded; explicit real pilot evidence correctly included. Both proven in the same real code path, same process, same isolation setting — the clean evidence boundary the Founder rule requires is real and working today.

## 16. Real signals

93 real signals fired across the 6 real poultry files, all deterministic, zero AI/LLM involvement (this Slice made no live reasoning call, per its own scope):

| `signal_type` | Count | Deterministic condition | Sample real trigger |
|---|---|---|---|
| `high_daily_mortality` | 41 | `daily_mortality > 20` | 198 > 20 (aggregate file, 2026-05-13) |
| `production_below_standard` | 35 | `daily_production_rate < standard_production_rate` | present wherever both fields resolve |
| `production_declining_trend` | 10 | 3 consecutive records, monotonic decline | multiple hall files |
| `data_quality_warning` | 7 | required field missing (e.g. `standard_production_rate` absent) | aggregate file (genuine column absence, §6) |

`high_daily_mortality` is a **system deterministic heuristic**, never presented or treated as Company Brain policy anywhere in this validation, per Founder Pilot Rule 2.

## 17. Real situations

8 real `poultry_production_drop` situations fired, requiring a trend signal plus ≥2 `production_below_standard` signals within the implemented window — the exact documented condition, verified against real multi-day series:

- `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` — 1 situation, `entity_reference=null` (this file's own unresolved entity identity, §6, correctly carried through rather than guessed)
- `تقرير_القاعة_2_الأحمر.xlsx` — 3 situations, `entity_reference="2"`
- `تقرير_القاعة_3_الأبيض.xlsx` — 4 situations, `entity_reference="3"`
- The remaining 3 files produced **zero** situations — a valid, unforced result, not adjusted to manufacture a pass.

## 18. Truth-layer epistemic findings

Every real observed source value carries `epistemic_origin: "observed"` through to the Truth Context item (confirmed directly, §14). No inference, no AI-generated value, was inserted anywhere in this Slice's real ingestion path — consistent with this Slice's own scope (no live LLM reasoning call was made; that is Slice 3's job). Derived Metrics/Signals/Situations remain identifiable as system-derived (their own typed objects/fields), never blended into the same representation as an observed fact.

### 18.1 Event/context gate precision (Reconciliation Amendment)

The PV1 Slice 1 contract itself flags Gate G ("Events correct") as needing clarification of which "Event" concept is being tested (§12 of the Slice 1 document, design-note column, verbatim: *"Needs clarification of which 'Event' concept (§5 row E) is being tested"*) — there are two distinct, non-overlapping concepts: (1) the older persisted `operational_events` table (Phase 1 rule-based grouping), and (2) the OIP layer's `OperationalMetric`/`event_count` context-semantics this Slice actually exercised throughout §6–§17.

This Slice's real runs — both the direct-parser runs and the real upload-routing matrix in §6.1 — exercised **only** the second concept: `_run_nco_lite_after_upload_if_applicable` calls `NCOLitePipeline.run_kae`/`run_oie`/`run_oce`, and persists only to `structured_record_drafts` (via `_persist_structured_ingestion_result`) — it never writes to the `operational_events` table. Traced directly through the real code path: no part of the real upload-routing flow this Slice exercised touches `operational_events`.

**Gate G is therefore scored PARTIAL, not PROVEN.** OIP operational-context semantics (Metric/Signal/Situation/event_count) are proven real, grounded, and correctly derived from real files — that half of Gate G's ambiguous scope is fully evidenced. The older persisted `operational_events` table subsystem was not exercised by any real run in this Slice and remains unproven here.

## 19. Defects discovered

**DEFECT-001 — Feed short-header-variant mapping gap (SEMANTIC MAPPING DEFECT, confirmed real). Scope corrected in this reconciliation pass.**
Affected source: **3 of 6 real poultry files** (`التقرير_الفني_اليومي_حقول_ديرتنا.xlsx`, `تقرير_إجمالي_الأبيض_والأحمر.xlsx`, `تقرير_القاعة_3_الأبيض.xlsx`) — corrected from the original, overstated "5 of 6" claim. Verified by a full-file (every record, not just sampled rows) header-presence check: the other 2 hall files (`تقرير_القاعة_2_الأبيض.xlsx`, `تقرير_القاعة_2_الأحمر.xlsx`) contain **neither** the short nor long feed-header variant anywhere in their sheets — a genuine data gap, not this mapping defect.
Expected behavior: `feed_received`, `feed_consumed`, `feed_per_bird_average` should populate from the real, present source columns `العلف المستلم` / `العلف المستهلك` / `العلف للطير الواحد` in these 3 files.
Actual behavior: all three fields are silently `null` for these 3 files. `ARABIC_COLUMN_MAP` (`app/oip/translators/poultry_report_translator.py`) only recognizes the `إجمالي`/`متوسط`-prefixed header variants (`إجمالي العلف المستلم`, `إجمالي العلف المستهلك`, `متوسط العلف للطير الواحد`), used only by the aggregate file. The translator's own `_normalize_header` strips `%` and collapses whitespace, but does not strip prefix words — so the short variants never match. The real numeric data is preserved in `raw_values` (verified, §8) but never reaches a Metric, Signal, or Truth Context item. Directly confirmed with counted evidence in §7.1: exactly 27 of 324 sampled field comparisons are this gap (9 per affected file × 3 files).
Acceptance gate impact: F (Metrics correct) — PARTIAL, not full PASS; downstream feed-related reasoning in Slice 3 will be evidence-blind for these 3 real files, one of which (`تقرير_القاعة_3_الأبيض.xlsx`) is a named Scenario 4 file (§22).
Severity: Moderate. No fabrication risk (the field is correctly absent, never wrongly populated) — this is a coverage gap, not a correctness violation.
Smallest likely correction surface: add 3 dict entries to `ARABIC_COLUMN_MAP` for the short header variants. No schema change, no new migration.
Pilot can continue around it: **Yes.** Feed evidence for the aggregate file and for the 2 genuinely-feed-data-absent hall files remains correctly represented; Scenario 3 (production decline) does not depend on feed fields; Scenario 4 needs the precision note in §22.

**DEFECT-002 — No cross-upload deduplication (INGESTION DEFECT, confirmed real, now against an actual real Jannat workbook).**
Affected source: any real file, if uploaded twice as two separate uploads — proven this pass specifically with `تقرير_القاعة_2_الأبيض.xlsx` (§13), not only a synthetic fixture.
Expected behavior: (no explicit product decision recorded either way — flagging the absence of a decision, not asserting a specific expected behavior).
Actual behavior: two distinct `structured_record_drafts` rows are created, doubling Metric/Signal/Situation evidence for the same underlying real data.
Acceptance gate impact: AE — BLOCKED BY PRODUCT DEFECT (upgraded from "NOT PROVEN": direct real-file runtime evidence now exists, not just an absence of proof).
Severity: Moderate — realistic operator behavior (a farm manager re-sending "just in case"), would double-count evidence in downstream reasoning if it occurs during Slice 3/4.
Smallest likely correction surface: a content-hash or (company, department, record_type, date-range) idempotency check before persisting a new `structured_record_drafts` row.
Pilot can continue around it: **Yes**, provided Slice 3/4 real-run operators are instructed not to re-upload the same report twice, and any accidental duplicate is visually checked for before drawing conclusions from a scenario run.

**DEFECT-003 — Company-aggregate poultry file silently skipped by the live upload route's filename-marker gate (INGESTION INTEGRATION DEFECT, confirmed real via §6.1).**
Affected source: `poultry_operations/إجمالي_حقول_ديرتنا_الإنتاج.xlsx` — the one real poultry file this Slice's Group A confirmed parses and validates correctly (7 records, direct parser), yet never reaches structured ingestion when routed through the actual production upload path.
Expected behavior: a structurally-valid, correctly-shaped real report should reach the same KAE/OIE/OCE pipeline as the other 5 files when uploaded.
Actual behavior: `app.api.files._has_daily_report_filename_marker(filename)` returns `False` for this exact real filename (no token from `("daily", "technical", "report", "تقرير", "التقرير", "يومي", "اليومي")` is present in it), so `_run_nco_lite_after_upload_if_applicable` returns `None` immediately — before content-based classification or shape detection ever run. Confirmed the downstream `CompanyInputClassifier` would have correctly classified this exact file as `excel_poultry_report` (0.78 confidence, no human-confirmation required) had it been reached — the failure is isolated entirely to this one filename-heuristic gate, prior to and independent of the classifier/KAE stages, both of which work correctly for this file's actual content.
Acceptance gate impact: A (real source file accepted) — PARTIAL, not fully PROVEN, since one real, structurally-supported file's live upload route is blocked while its direct parse succeeds.
Severity: Moderate. No fabrication or cross-tenant risk — the failure mode is silent non-ingestion (the raw file itself still uploads successfully at HTTP 201; only structured Truth ingestion is skipped, with no distinct error surfaced to the uploader).
Smallest likely correction surface: broaden `_has_daily_report_filename_marker`'s token list, or reconsider whether a filename-heuristic pre-gate is still needed at all now that content-based classification and shape detection both work correctly without it.
Pilot can continue around it: **Yes.** None of the 4 defined PV1 scenarios (Slice 1 §10) requires this specific aggregate file — all four use hall-level files, all of which route successfully (§6.1).

**DEFECT-004 — Feed-mill workbook has no live upload route at all (INGESTION INTEGRATION DEFECT, confirmed real via §9.1). Kept distinct from DEFECT-003.**
Affected source: `feed_mill/جرد الجاروشة.xlsx` — the one real feed-mill file this Slice's Group B confirmed the translator parses correctly (15/15 materials), yet which has no path to structured ingestion through the real upload route today, for two independently-confirmed, compounding reasons.
Expected behavior: uploading this real file should reach `OperationalPipelineService.parse_feed_mill_inventory`, the translator already proven correct in §9.
Actual behavior: (1) the same filename-marker gate as DEFECT-003 returns `False` for this filename, blocking it before classification; (2) even bypassing that gate, `NCOLitePipeline.run_kae` (`app/nco/pipeline.py`) unconditionally calls only the poultry translator — there is no feed-mill branch anywhere in `app/nco/pipeline.py`, `app/nco/orchestrator.py`, or `CompanyInputClassifier` (confirmed by direct search of all three, zero matches). The NCO-lite upload-completed path has no route to the feed-mill translator today, independent of the filename gate.
Acceptance gate impact: A (real source file accepted) — PARTIAL for the same reason as DEFECT-003, compounded by the deeper architectural gap in (2).
Severity: Moderate-to-notable. No fabrication risk. Unlike DEFECT-003, fixing only the filename-marker gate would **not** resolve this defect — a real dispatch path to the feed-mill translator does not exist in the NCO-lite orchestrator today.
Smallest likely correction surface: this is a real architectural gap, not a one-line heuristic fix — a feed-mill branch would need to be added to the NCO-lite upload-completed flow (classification routing + a KAE-equivalent step calling `parse_feed_mill_inventory`). Sizing that correction is out of this Slice's validation-only scope.
Pilot can continue around it: **Yes for the 4 defined PV1 scenarios** (none references feed-mill data) — but this defect should be flagged explicitly if any future scenario is designed around feed-mill evidence, since the translator's correctness (§9) does not currently translate into any live-upload capability at all.

**No other product defect was found.** Every other observation in §6–§18 is either a genuine data gap (source doesn't have the field) or a correctly-conservative non-guess (entity identity, report date), not a code defect.

## 20. Data gaps (not defects — informational)

Temperature, ventilation, electricity, clinical veterinary detail — confirmed still absent (unchanged from Slice 1, no new source appeared). Egg-size grading and egg-weight columns — confirmed present in real data, confirmed deliberately/structurally unmapped. Company-aggregate file has no `standard_production_rate` column at all. One poultry file has no resolvable hall entity. Feed-mill's real report date is not promoted (unlabeled date cell in this specific file's layout).

## 21. Acceptance scorecard

Re-scored this reconciliation pass wherever upload-routing evidence bears on the gate — evidence wins over the prior pass's claim in every case it changed.

| Gate | Score | Evidence |
|---|---|---|
| A — real source file accepted | **PARTIAL** *(changed from PROVEN)* | 5/6 poultry files + the feed-mill file's translator all parse and validate directly with zero failures, but the live upload route only successfully ingests 5/6 real poultry files — DEFECT-003 and DEFECT-004 (§6.1, §9.1, §19) |
| B — source provenance retained | **PROVEN** *(strengthened)* | §14.1: full provenance confirmed via the real upload router against 5 real files, not simulated stamping |
| C — real facts parsed correctly | **PROVEN** | §7/§7.1: 261 real matches, 0 unexpected mismatches across 324 counted field comparisons |
| D — units/date/company/hall semantics correct | **PARTIAL** | Dates/entities correct and never guessed (§11); units remain genuinely UNKNOWN/UNVALIDATED by design, not a failure but an open scope boundary |
| E — no fake operational facts | **PROVEN** | Static-source auto-inclusion excluded (§15); no forced-zero, no fabricated hall/entity (§6, §7) |
| F — Metrics correct | **PARTIAL** | Correct for every field that maps; DEFECT-001 (corrected scope: 3/6 files, §19) leaves 3 fields blind on those 3 files |
| G — Events/context semantics correct | **PARTIAL** *(changed from PROVEN)* | §18.1: OIP context semantics (Metric/Signal/Situation) proven real and grounded; the older persisted `operational_events` table subsystem was not exercised by any real run this Slice — the gate's own ambiguous scope (flagged in the Slice 1 contract itself) is only half-evidenced |
| H — Signals evidence-grounded | **PROVEN** | 93 real signals, every one traced to a real deterministic condition on real source values (§16) |
| I — Situation grounded in current operational evidence | **PROVEN** | 8 real situations, each traceable to real trend + threshold signals (§17); 3 files correctly produced none |
| J — Truth Layer distinguishes fact from inference | **PROVEN** | `epistemic_origin="observed"` preserved end-to-end (§18); no AI inference in this Slice's scope |
| R — no unsupported numerical claim at ingestion/Truth level | **PROVEN** | Every numeric value traced to a real source cell (§7, §14); no computed/inferred number was presented as observed |
| AD — failure path is safe | **NOT APPLICABLE** | No real file failed (§12); no real-file evidence available this Slice |
| AE — repeated run does not corrupt/duplicate Truth unexpectedly | **BLOCKED BY PRODUCT DEFECT** *(upgraded from NOT PROVEN)* | §13, empirically demonstrated duplication against a real Jannat workbook (DEFECT-002) — direct proof, not absence of evidence |
| AH — static bundled historical pilot data excluded in PV1 isolation mode | **PROVEN** | §15, clean isolation + clean explicit-evidence inclusion, same real code path |

No other A–AK gate is directly evidenced by this Slice's own work (Slice 3/4 own the reasoning-, Decision-, Action-, Outcome-, and CEO-usability-scoped gates).

## 22. Slice 3 readiness

**READY**, with three carried-forward caveats operators/reasoning-scenario designers must account for (one more than the prior pass, reflecting the newly-discovered upload-routing gaps):

1. Feed evidence (received/consumed/per-bird-average) reaches Truth only from the aggregate file and is genuinely absent (not a mapping gap) for `تقرير_القاعة_2_الأبيض.xlsx`/`تقرير_القاعة_2_الأحمر.xlsx`; it is present-but-unmapped (DEFECT-001, corrected scope: 3 files) for `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx`, `تقرير_إجمالي_الأبيض_والأحمر.xlsx`, and `تقرير_القاعة_3_الأبيض.xlsx` — until DEFECT-001 is corrected (Founder decision pending — not authorized in this Slice).
2. Re-uploading the same real report twice will double Truth Context evidence (DEFECT-002, now proven against a real workbook) — Slice 3/4 real-run operators should avoid duplicate uploads or explicitly check for them before drawing scenario conclusions.
3. **New this pass:** the real company-aggregate poultry file and the real feed-mill file are both silently skipped by the live upload route today (DEFECT-003, DEFECT-004) — a real user attempting to upload either through the actual product would get no structured Truth evidence and no distinguishing error message. Any Slice 3/4 scenario work involving these two specific files must go through direct developer invocation, not the live product path, until these are addressed — and must say so explicitly rather than imply live-upload parity.

**None of the four defects meets a PV1 Stop Rule** (no fabricated fact, no cross-tenant data, no unsupported numeric claim was produced by NAWA in any of them — all four are coverage/routing gaps or omissions, not correctness violations).

**Scenario-by-scenario, through the actual product upload path (not direct developer invocation):**
- **Scenario 1 (egg quality)** — uses `broken_eggs`/`dirty_eggs` from any hall file; all hall files used for this scenario route live successfully. **Executable through the real product path.**
- **Scenario 2 (mortality)** — uses `daily_mortality`/`weekly_mortality_rate` from any hall file; same as Scenario 1. **Executable through the real product path.**
- **Scenario 3 (production decline)** — the Slice 1 document names `poultry_operations/*.xlsx` generically; the real `poultry_production_drop` situations in this Slice (§17) came from `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx`, `تقرير_القاعة_2_الأحمر.xlsx`, `تقرير_القاعة_3_الأبيض.xlsx` — all three route live successfully. **Executable through the real product path.**
- **Scenario 4 (missing-evidence hall comparison)** — explicitly names `تقرير_القاعة_2_الأبيض.xlsx`/`تقرير_القاعة_2_الأحمر.xlsx` (no water/feed columns) vs. `تقرير_القاعة_3_الأبيض.xlsx` (has them). All three route live successfully — **executable through the real product path** — **but with a real precision nuance this reconciliation surfaced**: `تقرير_القاعة_3_الأبيض.xlsx`'s water column is genuinely present and mapped, but its feed columns, while genuinely present in the raw source, are currently blocked from reaching canonical Metrics by DEFECT-001. This means the scenario's premise ("water/feed data only for Hall 3") is only true for water at the canonical-evidence level today — feed evidence is *also* unavailable for Hall 3 in practice, though for a different reason (a mapping gap, not source absence) than for Hall 2 (genuine source absence). Slice 3 should test whether NAWA's reasoning output correctly states feed unavailability for Hall 3 too, without needing to know or explain *why* — and this nuance should not be misread as the scenario failing; it is the scenario correctly exercising an uncertainty case the original design did not anticipate.

None of the 4 defined scenarios requires `إجمالي_حقول_ديرتنا_الإنتاج.xlsx` or the feed-mill file (DEFECT-003/DEFECT-004's affected files), so neither newly-discovered routing gap blocks Slice 3 as currently scoped.

---

## Execution Result

**Status:** Real-data ingestion validation complete against all 6 real poultry files, the real feed-mill file, and the 7 real unsupported-source files — including, in this reconciliation pass, real **upload-routing** evidence (not only direct-parser evidence) for all 7 real `.xlsx`/relevant files. Four real, bounded product defects found and documented, not fixed, per this Slice's own validation-first scope. **Under review — not closed, not committed.**
**Started / completed:** 2026-09-04. Reconciliation amendment (upload-routing + evidence precision): 2026-09-04.
**Validation method:** direct invocation of real production code (`OperationalPipelineService`, `assemble_truth_context`, `app.api.files._run_nco_lite_after_upload_if_applicable`, `CompanyInputClassifier`, `app.services.rag.extractors.extract_text`, existing safe in-memory test helpers) against real Jannat pilot files and both a real local Jannat entitlement (direct-parser runs) and disposable synthetic entitlements in the existing safe `_FakeDB` (upload-routing runs) — no HTTP layer, no mocking of the ingestion/Truth pipeline itself, no real file ever renamed or edited.
**Defects found:** 4 — DEFECT-001 (semantic mapping gap, corrected scope: 3 of 6 files, not 5), DEFECT-002 (duplicate-upload gap, now proven against a real Jannat workbook), DEFECT-003 (real company-aggregate poultry file silently skipped by the live upload route's filename-marker gate), DEFECT-004 (real feed-mill file has no live upload route at all — filename gate plus a deeper missing-dispatch architectural gap). None fixed in this pass, per explicit "no bug fixes" instruction. None meets a PV1 Stop Rule.
**Gate scores this Slice:** B, C, E, H, I, J, R, AH = PROVEN; A, D, F, G = PARTIAL; AD = NOT APPLICABLE; AE = BLOCKED BY PRODUCT DEFECT. (Changed this pass: A PROVEN→PARTIAL, G PROVEN→PARTIAL, AE NOT PROVEN→BLOCKED BY PRODUCT DEFECT; B strengthened from simulated to real-router evidence.)
**Recommendation:** PV1 Slice 3 readiness = READY, with three carried-forward caveats (§22) — none of the four defects blocks any of the 4 defined PV1 scenarios, all of which remain executable through the actual real product upload path.
**Notes:** No code, test, or migration file was modified. No `.env`/config file was modified. No production/shared database was touched. All upload-routing checks used existing, already-established, safe in-memory `_FakeDB` test infrastructure with disposable synthetic tenant identities; the uploaded file bytes and filenames were always the real, unmodified Jannat source files.
