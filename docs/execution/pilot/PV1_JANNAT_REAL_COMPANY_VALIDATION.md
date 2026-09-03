# PV1 — Jannat Al-Firdaws Real-Company Pilot Validation

**Priority:** P0. First post-M9 phase.
**Owner:** AI Engineering Team (Claude Code).
**Ownership layer:** Discovery, real-data/reasoning validation design, and governance documentation. Not a feature-engineering phase.
**Repository First Policy compliance:** This document is the required task document, filed before any PV1 engineering work begins.

---

## 1. Founder activation

The Founder explicitly activated PV1 — Jannat Al-Firdaws Real-Company Pilot Validation, immediately following M9's closure. This is **not** M10, not a feature-expansion milestone, and not authorization for Voice, Avatar, Automation, workflow engines, external execution, new departments, generic Tasks, or deep integrations. Its purpose is to validate the closed M9 technical MVP against a real company, real operational files, real company knowledge, and realistic executive use.

## 2. Starting checkpoint

Branch `claude-safe-review`. Verified before any edit: local HEAD = tracking origin = live origin = `acebd7720b1aa6294dffc549185e0d9d7cac1715`, divergence 0/0, working tree clean, index clean. M9 is CLOSED (final engineering checkpoint `4a0c578e75b0d91890cbcb264326765045ff069a`; final governance closure commit `acebd7720b1aa6294dffc549185e0d9d7cac1715`; A–AH all proven).

## 3. Phase purpose

The technical MVP is complete. The question this phase asks is not "can we build more?" It is: **can NAWA understand, reason about, and support decisions inside a real operating company using real company data?** M9 proved technical implementation acceptance (the mechanism works, correctly, under test). PV1 must prove real-company operational usefulness — a materially different and harder question, evaluated against a real farm's real reports and a real Company Brain, not synthetic fixtures.

## 4. Non-goals

Not authorized by this activation: M10, an Automation Engine, Voice, Avatar, a workflow scheduler, deep external integrations, new departments beyond the existing Jannat Al-Firdaws structure, a generic Task/project-management abstraction, `due_at`, a `failed` Action state, autonomous execution of any kind, automatic Company Brain mutation, or treating a historical Outcome as causal proof. This document itself is discovery and documentation only — no application code, frontend code, test, or migration was modified to produce it (see §20).

---

## 5. Real pilot architecture — what exists today (Step 2 discovery)

Discovery corrected a stale claim in `CURRENT_STATE.md` ("Only mortality rate implemented in Phase 1... Production percentage, feed consumption, water trend, and egg weight/size distribution are specified in the doctrine doc but not yet wired into the interpreter"). That statement is accurate only for one specific, still-live legacy module in isolation. A separate, substantially more capable structured pipeline was built afterward and is live in parallel. Both are real; neither supersedes the other's actual scope claim about itself. `CURRENT_STATE.md`'s own narrative section was simply never updated when the newer pipeline shipped.

| # | Stage | Status | Evidence |
|---|---|---|---|
| A | File upload / source intake | **IMPLEMENTED** | `POST /files/upload` (`app/api/files.py:93-169`). Streams to temp path, runs `FileIngestionService.ingest_file()` for every supported type (txt/md/csv/json/pdf/docx/xlsx). |
| B | Excel / supported operational-source loaders | **IMPLEMENTED** | `app/oip/loaders/excel_loader.py` + two shape-specific translators (`poultry_report_translator.py`, `feed_mill_inventory_translator.py`), both header-co-occurrence-based, never filename-based. |
| C | OIP parsing / translation / validation | **IMPLEMENTED** | `app/oip/translators/*`, `app/oip/validators/poultry_validator.py`. Hard-fails the **whole file** on one bad row (`date is None`, `bird_balance <= 0`, negative mortality, or a rate outside `[0,100]`) — no partial-row salvage in the live upload path. |
| D | Metric creation | **IMPLEMENTED** | `app/oip/services/poultry_derivation_service.py` — 13 typed metrics per record (`bird_balance`, `daily_mortality`, `weekly_mortality_rate`, `daily_tray_production`, `box_production`, `daily_production_rate`, `standard_production_rate`, `broken_eggs`, `dirty_eggs`, `water_consumption`, `feed_received`, `feed_consumed`, `feed_per_bird_average`), emitted even when null so missing-evidence can be detected downstream. |
| E | Operational Event creation | **IMPLEMENTED, but two distinct subsystems** | (1) The **older, general** Phase-1 path — `operational_events` table/API (migration 009), fed by manual structured forms and free-text natural capture, generic across all business types, not Dairtna-semantic-aware. (2) The **newer, Dairtna-specific** OIP/OCE path builds evidence "contexts" directly from Metrics/Signals for reasoning — it does not write a separate persisted "Event" row; the metric/signal *is* the event-equivalent unit at this layer. Treat these as parallel, not identical, concepts. |
| F | Signal creation | **IMPLEMENTED, deterministic, zero AI** | Same file: `production_below_standard` (daily rate < standard), `high_daily_mortality` (>20 daily count — **not** a rate, and not the same threshold family as the legacy interpreter's mortality-rate bands, see §9 finding), `data_quality_warning` (key fields missing), `production_declining_trend` (3 consecutive records, monotonic decline). |
| G | Situation creation / grouping | **IMPLEMENTED, narrow** | `app/oip/services/poultry_situation_service.py` — exactly one situation type, `poultry_production_drop`, requiring a trend signal **plus ≥2** `production_below_standard` signals in-window. Mortality alone never creates an OIP situation. This is a separate, in-memory, per-request `OperationalSituation` dataclass — **not** the older persisted `operational_situations` table (migration 010, rule-based grouping from Phase 1). |
| H | Operational Timeline | **IMPLEMENTED** (older subsystem) | The Phase-1 `operational_events`/`operational_situations` tables and API provide a persisted, chronological, company-scoped timeline. Generic, not Dairtna-semantic-aware. |
| I | Truth/context assembly for reasoning | **IMPLEMENTED** | `app/services/operational_truth_context.py` (`assemble_truth_context`). Re-derives Metrics/Signals/Situations **fresh, in-memory, on every chat call** from persisted `structured_record_drafts` rows (real uploads) plus, by default, a static bundled-file scan (see §9). Not a separately-persisted derived table — single source of truth is the translated record, re-derived on read. |
| J | Company Brain loading / provenance | **IMPLEMENTED** | `app/services/company_brain_context.py` (`assemble_company_brain_context`). Loads `DAIRTNA_COMPANY_BRAIN.md` and `DAIRTNA_DECISION_RULES.md` by H2-section heading, tenant/department-gated (Jannat + Dairtna Poultry only), unrecognized headings skipped rather than guessed. |
| K | Organizational Memory retrieval | **IMPLEMENTED** | `app/ome/services/organizational_memory_retrieval_service.py`, invoked per chat call; provenance resolved via `build_organizational_memory_provenance_refs`. |
| L | AI reasoning / chat | **IMPLEMENTED** | `app/services/openai_client.py` — fuses Truth Context, Company Brain, and OM retrieval into one reasoning call; already proven (M6–M8) to ground citations and refuse unsupported claims in the existing test suite. |
| M | ReasoningReceipt | **IMPLEMENTED** | Created for every authenticated live chat call (M8 Slice 3A); `reasoning_receipt_id` returned to the client, anchors the Decision chain. |
| N | Human Decision recording | **IMPLEMENTED** | `POST /decisions` (M8 Slice 3B); real UI (`RecordDecision.tsx`); no AI prefill. |
| O | Action creation / status / assignment / history | **IMPLEMENTED** | M9, closed this session: full create/status-transition/assign-reassign-unassign/history lifecycle, real named-assignee selector over `GET /company/members`. |
| P | Human Outcome recording | **IMPLEMENTED** | `POST /outcomes` (M8 Slice 3C); real UI (`RecordOutcome.tsx`); distinct vocabulary from Action status, no causal linkage asserted. |
| Q | Organizational-memory persistence | **IMPLEMENTED** | `ome_reasoning_receipts`, `ome_decision_memories`, `ome_outcome_memories`, `ome_actions`, `ome_action_change_events` — all real tables, migrations 014–015, all exercised by the existing 1155-test backend suite. |
| R | Browser Golden Path | **PARTIAL** | Two separate, real, passing browser specs exist (`frontend/e2e/golden-a.spec.ts`: upload → grounded chat citation; `frontend/e2e/m9-slice4-golden-path.spec.ts`: Decision → Action → Assignment → Status → History → Outcome) — but **no single continuous browser run currently proves the full chain from a real Dairtna upload through grounded reasoning through Decision/Action/Outcome in one session.** Each half is proven; the join is not. This directly affects acceptance gate AF (§12). |

---

## 6. Real pilot data inventory summary (Step 3 — full detail in discovery record)

Real files live under `data_sources/jannat_al_firdaws/2026_06/`, five subfolders. **14 real files total** (directly re-verified from the filesystem: `find data_sources/jannat_al_firdaws -type f` → 19 entries = 14 real files + 5 `.gitkeep` placeholders, one per subfolder — corrects an off-by-one in the first discovery pass, which had reported 13), spanning roughly April–June 2026:

| Folder | Files | Format |
|---|---|---|
| `poultry_operations/` | 6 | xlsx (6 hall/aggregate daily technical reports) |
| `warehouse/` | 1 | xlsx (egg warehouse inventory, 7 grade columns) |
| `sales/` | 1 | xlsx, 3 sheets (retail sales + stock reconciliation) |
| `feed_mill/` | 1 | xlsx, 7 sheets (raw-material receipts, daily consumption, mill balance, formula, prices) |
| `finance/` | 5 | PDF (per-hall daily P&L for Halls 1/2/3/Red, plus one store-expense summary) |

One synthetic E2E fixture (`frontend/e2e/fixtures/golden_a_dairtna_poultry_daily_technical_report.xlsx`, self-labeled "Synthetic Test Company") was found and **excluded** from this count — it is test-only and must never be conflated with real pilot data.

**Zero real files exist for:** temperature, ventilation, veterinary/medicine (clinical detail — only a bundled cost figure exists in finance PDFs, not the drug/dose/vet-identity fields `DAIRTNA_OPERATIONAL_SEMANTICS.md` itself says should be recorded), and electricity/power. **Water is only a column inside some poultry files, missing from 2 of 6** (the Hall 2 White/Red hall-level reports omit water and feed columns entirely, unlike the aggregate and Hall 3 reports).

## 7. Company Brain coverage (Step 4 — full detail in discovery record)

Three documents exist exactly where expected, all consistent with each other:

- **`DAIRTNA_COMPANY_BRAIN.md`** — COMPANY POLICY: success/failure definitions, daily/monthly indicator lists, quality/risk/expansion/investment philosophy, a four-item decision-priority ordering (continuity → quality → profitability → liquidity), red lines, 2026–2028 goals.
- **`DAIRTNA_OPERATIONAL_SEMANTICS.md`** — mixed OBSERVED FACT / domain-glossary, plus one section (§9, interpretation/diagnosis rules) flagged as **possibly AI-assisted synthesis, unconfirmed provenance** — worth verifying with the pilot SME before treating as ground truth on the same footing as the other two documents.
- **`DAIRTNA_DECISION_RULES.md`** — COMPANY POLICY: seven qualitative IF/THEN rules (Quality vs Profit, Growth vs Stability, Production Increase/Reduction, Supplier Replacement, New Market Entry, New Product Launch, Crisis Management priority list).

**Material finding:** none of the three documents states a numeric threshold (e.g., "mortality > X% ⇒ escalate"). All triggers are qualitative ("sudden increase," "exceeds reference rates," "continues rising several days"). If pilot acceptance requires a quantified rule, that number does not currently exist in the Company Brain and must be elicited from the operator, not assumed or invented by NAWA or by this discovery pass.

### Founder Pilot Rule 2 — Numeric threshold discipline

**Decision:** do not invent or add numeric Company Brain thresholds before PV1 Slice 2. Current Company Brain documents contain qualitative management rules but no explicit numeric mortality/quality escalation thresholds, and that is acceptable for Slice 2 — Slice 2 is real-data ingestion validation, not policy-threshold authoring.

**The distinction that must be preserved everywhere in PV1:** a **system deterministic heuristic** is not the same thing as **Company Brain policy**. Two concrete examples already exist in this codebase and must never be conflated with each other or presented to a CEO as human-approved Jannat management policy unless that policy is explicitly sourced and added through an authorized Company Brain governance action:

- OIP's `high_daily_mortality` signal — a system heuristic, `daily mortality count > 20`.
- The legacy Dairtna interpreter's mortality-rate bands — a different system heuristic, percentage-based (`<0.05%/<0.10%/<0.20%/≥0.20%`).

Neither is Company Brain policy. Neither was sourced from a Jannat manager. Both are engineering-chosen provisional thresholds (the legacy interpreter says so explicitly in its own module docstring).

**Governing rule for Slices 2–3:** Slice 2 proceeds without adding any new Company Brain numeric threshold. Reasoning must expose missing policy thresholds when material to a scenario, rather than silently filling the gap. If Slice 3 requires a real management threshold for a scenario to be evaluated meaningfully, it must be obtained from the Jannat operator/SME, and its addition to the Company Brain must be treated as its own explicit governance action — not inferred from existing code, not copied from an OIP heuristic, and not merged conceptually with the legacy interpreter's thresholds.

**Required-input coverage:** of the eight decision rules plus the semantics doc's own "what to check when production drops" checklist, the clearest data gaps are: liquidity/cash-flow (no source found), supplier quality/delay history (receipt logs have no supplier identity or quality flag), market-demand/distribution data (sales file only covers direct retail, not market conditions), and — again — temperature, and clinical veterinary detail.

## 8. Data coverage matrix (Step 5)

| Category | Status | Basis |
|---|---|---|
| Poultry production (output, grading) | **AVAILABLE + INGESTIBLE** | Mapped columns, derived metrics, real signal/situation logic |
| Mortality | **AVAILABLE + INGESTIBLE** | `daily_mortality`/`weekly_mortality_rate` mapped and metriced; also cross-checkable against finance PDFs' per-hall mortality-cost line |
| Feed consumption | **PARTIAL** | Mapped and metriced (`feed_received`/`feed_consumed`/`feed_per_bird_average`), but **no feed-specific signal or trend detection exists** — only production has a trend signal |
| Egg production/quality (broken/dirty rate) | **AVAILABLE + INGESTIBLE** | `كسر`/`متسخ` mapped; size-grade columns (S/M/L/XL/…) deliberately unmapped (Founder ruling), remain in `raw_values` only |
| Warehouse | **AVAILABLE + NOT YET INGESTIBLE** | Real file exists (`جرد_مخزن_البيض.xlsx`); no translator found for this shape — only poultry-daily and feed-mill-inventory shapes exist |
| Feed mill | **PARTIAL** | A structured translator exists for the raw-material balance block specifically (`رصيد الجاروشة`); other sheets in the same real workbook (incoming log, daily consumption, formula, prices) have real data but no confirmed translator coverage in this discovery pass |
| Sales | **AVAILABLE + NOT YET INGESTIBLE** | Real file exists, multi-sheet; no translator found |
| Finance | **AVAILABLE + NOT YET INGESTIBLE** | Real PDFs exist (5 files, rich per-hall P&L); no PDF-to-structured-record path found in this discovery pass — PDF ingestion for Dairtna-specific structured finance was not located |
| Water | **PARTIAL** | Mapped as a metric where present; no trend/threshold signal; **missing from 2 of 6 real poultry files** |
| Temperature | **MISSING** | Zero real files or columns found anywhere |
| Ventilation | **MISSING** | Zero real files or columns found anywhere |
| Veterinary / medicine | **MISSING (clinical detail)** | Only a bundled cost figure in finance PDFs; no drug/dose/diagnosis/vet-identity record, despite the semantics doc naming these as required fields |
| Electricity / power | **MISSING** | Zero real files or columns found anywhere |

## 9. Ingestion readiness and no-fake-data findings (Steps 6–7)

**Field mapping (`app/oip/translators/poultry_report_translator.py`, `ARABIC_COLUMN_MAP`, verified against the live file):** 19 Arabic headers map to typed fields including `كسر → broken_eggs`, `متسخ → dirty_eggs`, `الماء المستهلك → water_consumption`, `إجمالي العلف المستلم/المستهلك → feed_received/feed_consumed`. Egg-size grading columns are deliberately unmapped. Unrecognized headers are silently dropped from the typed record (but preserved in `raw_values` for audit — never lost, never guessed).

**Hard assumptions:** dates parse only as `%d/%m/%Y`, `%Y-%m-%d`, `%d-%m-%Y`, or native Excel date cells — anything else fails validation. No unit conversion or checking exists anywhere (a value is trusted as-is once its column is identified). Hall/entity identity is resolved only from a structural label (`رقم القاعة`/`اسم الحقل`) — never guessed from free text or filename; unresolved entity identity is left `None`, never defaulted. Company identity is never read from the file at all — it comes exclusively from the authenticated upload's `company_id`, stamped on at persistence.

**Validation failure mode:** `PoultryValidator` hard-fails the **entire file** on one bad row (missing date, non-positive bird balance, negative mortality, or an out-of-range percentage). The live upload path does **not** currently catch this distinctly from a generic failure — it surfaces only as `nco_status: "failed"` with no partial-row salvage. This is a real usability risk for a pilot operator uploading imperfect real-world spreadsheets.

**Deduplication:** re-uploading the *identical* file (same `file_id`, e.g. a retry) is idempotent. **Uploading the same physical report twice as two separate uploads is NOT deduplicated** — no content-hash or period-based check exists; each becomes a distinct evidence item. This is a genuine gap, not a hypothetical one, and is realistic operator behavior (a farm manager re-sending yesterday's report "just in case").

**Provenance:** confirmed end-to-end. `source_file_id`, `source_filename`, `source_company_id`, `source_department_id` are stamped once at persistence (the one place identity is authoritatively known) and propagate through every derived Metric/Event/Signal into the Truth Context items the reasoning prompt actually receives. Real uploaded evidence is prioritized over static-file evidence when a context-window bound is hit.

**No-fake-data audit:**
- The legacy mortality interpreter and `REFERENCE_SEED_EVENT_SOURCE_TYPE` (test/reference seed events) are both actively excluded from the live reasoning path by name — confirmed **PRODUCTION-PATH SAFE**.
- Frontend demo mode (`demo-mode.ts`/`demo-data.ts`) is genuinely opt-in (an unset-by-default `NEXT_PUBLIC_DEMO_MODE` build flag), only substitutes for a confirmed-empty real result, and is always banner-labeled. Confirmed **DEMO-ONLY**.
- **One finding required a Founder decision, not a code fix — now resolved (Founder Pilot Rule 1):** `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED` defaults to **`true`** in production (not disabled, correcting an assumption in the original activation prompt). This gates whether the same real bundled `data_sources/jannat_al_firdaws/.../poultry_operations/*.xlsx` files are scanned and injected into every Jannat/Dairtna chat call automatically, tenant-gated but **not upload-gated** — a live CEO asking about "today" could be answered using a static June-2026 file with no UI distinction from a fresh upload. This is real historical Jannat data, not fabrication — but automatic inclusion creates a recency/transparency problem PV1 must not tolerate silently.

### Founder Pilot Rule 1 — Static pilot source isolation during real-pilot runs

**Decision:** During real PV1 validation runs, bundled static pilot operational files must **not** silently participate in the live Truth Layer. The PV1 real-pilot runtime policy is `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED=false` for the PV1 validation environment/runs.

**Reasoning preserved exactly:** the bundled files remain real historical Jannat data, not fabricated data, and are **not** deleted, and **may** be deliberately used later when a scenario explicitly calls for them. The rule exists solely to establish one clean evidence boundary for pilot validation: **explicit real pilot input → Truth Layer → reasoning**, without silent static historical enrichment sitting alongside it indistinguishably.

**Scope of this rule, exactly:** this is a pilot-validation *runtime configuration* rule, recorded here for Slice 2 to carry forward. It is **not** authorization in this Slice to edit application code, environment files, or `.env`/`.env.example` defaults, and it is **not** a claim that the static files are fake. No environment file was changed in this documentation pass. **PV1 Slice 2's own activation brief must set `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED=false` in whatever environment its real-pilot ingestion/reasoning runs execute against, before any real-pilot acceptance run begins** — this is now a precondition of Slice 2, not an open question for it.

## 10. Proposed real pilot scenarios (Step 8)

Four scenarios, each grounded in files and rules that actually exist today. None invents data or a "correct answer" beyond what deterministic rules or source truth support.

### Scenario 1 — Egg quality vs. short-term profit (Quality vs Profit rule)
- **Capability boundary (read before running):** current structured ingestion supports poultry quality evidence (`كسر`/`متسخ` broken/dirty counts) directly. Warehouse, sales, and finance evidence — the sources a real profitability signal would need — are **not confirmed structured-ingestible today** (§8: AVAILABLE + NOT YET INGESTIBLE). **This scenario therefore also tests whether NAWA correctly states that profitability evidence is unavailable/not grounded, rather than falsely claiming a proven quality-vs-profit conflict.** Do not treat the conflict as already proven by this scenario's design — that is exactly the failure mode being tested for.
- **Business question:** Is the observed broken/dirty egg rate high enough to warrant action, and does responding to it conflict with short-term sales?
- **Real source(s):** `poultry_operations/*.xlsx` (`كسر`/`متسخ` columns) — structured-ingestible today; `warehouse/جرد_مخزن_البيض.xlsx`, `sales/مبيعات_جنة_الفردوس_وقاعة_البيض.xlsx` — real files exist but are **not yet structured-ingestible** (§8).
- **Relevant metrics:** `broken_eggs`, `dirty_eggs` (per hall/day).
- **Company Brain rule:** `DAIRTNA_DECISION_RULES.md` — Quality vs Profit ("IF quality conflicts with short-term profit THEN prioritize quality").
- **Expected Truth facts:** real broken/dirty counts per hall/day, with provenance to the specific uploaded file.
- **Expected Signal/Event:** none of the current deterministic OIP signals target egg quality directly (`production_below_standard`/`high_daily_mortality`/`data_quality_warning`/`production_declining_trend` — none is quality-specific) — this is itself a finding: quality-rate anomalies are visible as raw metrics but have **no dedicated signal**, unlike production and mortality.
- **Expected Situation:** none (no quality-specific situation type exists).
- **Expected reasoning behavior:** cite the raw counts, decline to assert a "quality crisis" without a defined threshold (none exists in Company Brain — Founder Pilot Rule 2, §7), correctly surface the Quality vs Profit priority rule as *policy context* rather than a numeric trigger, and explicitly state that profitability/sales evidence needed to evaluate the "conflicts with short-term profit" half of the rule is not currently available in structured form.
- **Expected citation/provenance:** must resolve to the real uploaded file, hall, and date.
- **Expected CEO recommendation characteristics:** should note the observed rate, name the applicable policy, explicitly flag that no numeric quality threshold exists in Company Brain, and explicitly flag that the profit side of "Quality vs Profit" is currently ungrounded — not invent either.
- **Human Decision → Action → Outcome:** CEO records a decision (e.g., "investigate hall X's egg handling"); Action created and assigned to a named responsible person; Outcome recorded after follow-up.
- **What would count as WRONG:** NAWA inventing a numeric "acceptable" broken-egg rate; NAWA silently treating the raw rate as already a "crisis" without the human deciding that; NAWA citing a hall/date the data doesn't actually show; **NAWA asserting a quality-vs-profit conflict is already proven when the profit side has no structured evidence backing it.**

### Scenario 2 — Mortality signal escalation (Crisis Management priority rule)
- **Business question:** Given an observed mortality reading, does it warrant escalation, and in what priority order should the response be framed?
- **Real source(s):** `poultry_operations/*.xlsx` (`الهلاكات اليومية`/`نسبة الهلاكات الأسبوعية`), finance `ح*.pdf` (mortality cost line, cross-check).
- **Relevant metrics:** `daily_mortality`, `weekly_mortality_rate`.
- **Company Brain rule:** `DAIRTNA_DECISION_RULES.md` — Crisis Management (bird health → operational continuity → loss reduction → financial stability); `DAIRTNA_OPERATIONAL_SEMANTICS.md` §4 (qualitative mortality alarm conditions).
- **Expected Truth facts:** real daily mortality counts and weekly rate, per hall/day, with provenance.
- **Expected Signal:** `high_daily_mortality` (>20 daily count) — a real, deterministic, already-implemented signal.
- **Expected Situation:** none directly (the only OIP situation type is `poultry_production_drop`; the *legacy* interpreter's own mortality-rate-band classification is a separate code path over free-text drafts, not this structured pipeline — this scenario should surface **which** of the two mortality paths actually produced the signal the CEO sees, since they use different thresholds: the legacy interpreter's `<0.05%/<0.10%/<0.20%/≥0.20%` rate bands vs. OIP's flat `>20` daily count).
- **Expected reasoning behavior:** ground any escalation language in the real numbers, apply the Crisis Management priority ordering as stated, never invent a numeric alarm threshold beyond what Company Brain states qualitatively or what the deterministic signal actually fired on.
- **Human Decision → Action → Outcome:** as Scenario 1.
- **What would count as WRONG:** conflating the two different mortality-detection pathways' thresholds as if they were one; presenting either heuristic's classification as if it were Company Brain policy (see Founder Pilot Rule 2, §7); escalating beyond what either signal actually supports; connecting mortality to sales/finance without the `cross_dept_flag`/explicit human-confirmed link the interpreter's own hard constraints require.

**Mortality dual-path risk — retained and sharpened as an explicit Slice 3 acceptance check.** Two mortality-interpretation mechanisms are live simultaneously: (1) the legacy `app/services/dairtna/interpreter.py`, free-text-draft-derived, percentage-rate-banded; (2) structured OIP derivation's `high_daily_mortality`, a flat daily-count threshold. PV1 must treat these as distinct mechanisms — neither is Company Brain policy, and they are not semantically equivalent to each other. Slice 3 must explicitly determine, for every scenario run where mortality evidence is presented to the CEO: **(a)** which mechanism produced each classification/signal actually shown; **(b)** whether both mechanisms can enter the same reasoning call; **(c)** whether conflicting classifications between the two are possible in that call; **(d)** whether the user-facing reasoning output clearly distinguishes observed fact, deterministic system heuristic, and Company Brain rule for each mortality-related statement (this is gate AJ/AK, §12). If a real reasoning path is found to present contradictory mortality interpretations without distinguishing them, that is classified as a **SEMANTIC MAPPING / REASONING DEFECT candidate** — Slice 3's job is to detect and classify this, not to fix it inline.

### Scenario 3 — Production decline trend (Production Reduction rule)
- **Capability boundary (read before running):** the *production-decline detection* half of this scenario is the strongest-supported case in the whole pilot — `poultry_production_drop` is a real, already-implemented Situation type. The *policy-evaluation* half is not: the Production Reduction rule requires "profitability declines OR operating costs increase significantly," and finance PDFs are **not confirmed structured-ingestible today** (§8). **Observed production decline alone must never be treated as proof that the rule's condition is satisfied** — the expected good behavior is to clearly distinguish the observed production decline (grounded, real) from the missing/unavailable financial evidence needed to evaluate whether the policy rule's trigger condition is actually met (ungrounded, must be stated as such).
- **Business question:** Is a hall's production declining, and if so, should production be reduced or investigated?
- **Real source(s):** `poultry_operations/*.xlsx` (multi-day series per hall) — structured-ingestible today; finance `ح*.pdf` — real files exist but are **not yet structured-ingestible** (§8), so any profit/loss cross-check is currently manual/out-of-band, not something the reasoning layer can grounds itself in.
- **Relevant metrics:** `daily_production_rate`, `standard_production_rate`.
- **Company Brain rule:** `DAIRTNA_DECISION_RULES.md` — Production Reduction ("IF profitability declines OR operating costs increase significantly THEN evaluate production reduction").
- **Expected Signal + Situation:** `production_below_standard` (per record) and, if ≥2 consecutive occurrences plus a trend signal, the real, already-implemented `poultry_production_drop` situation.
- **Expected reasoning behavior:** cite the real situation and underlying records for the production decline itself with full confidence — that part is genuinely grounded. Do **not** connect it to the Production Reduction rule as if the rule's condition were satisfied; instead state that the profitability/cost condition cannot currently be evaluated because that evidence is not structured-ingestible yet.
- **What would count as WRONG:** treating a production dip as automatically warranting the Production Reduction rule without checking the profitability/cost condition the rule actually states; **presenting the rule as already triggered/satisfied when its financial condition is unevaluated**; fabricating a "cause" for the decline the data doesn't show (e.g., asserting a feed or water cause without those columns being present for that hall — see Scenario 4).

### Scenario 4 — Missing-evidence hall comparison (uncertainty gate)
- **Business question:** Comparing Hall 2 (White/Red — no water/feed columns in the source file) against Hall 3 (full column set) for the same period — can NAWA correctly state what it does and does not know?
- **Real source(s):** `تقرير_القاعة_2_الأبيض.xlsx`, `تقرير_القاعة_2_الأحمر.xlsx` (no water/feed columns) vs. `تقرير_القاعة_3_الأبيض.xlsx` (has them).
- **Expected Truth facts:** production/mortality data for both halls; water/feed data **only** for Hall 3.
- **Expected reasoning behavior:** this scenario specifically tests acceptance gates T/AC (§12) — NAWA must state explicitly that water/feed evidence is unavailable for Hall 2 rather than silently omitting the caveat or, worse, inferring a Hall 2 water/feed figure from Hall 3's.
- **What would count as WRONG:** any numeric water/feed claim about Hall 2; silence about the gap rather than an explicit "not available for this hall" statement.

## 11. Pilot acceptance model (Step 9)

Every capability below is scored with exactly one of: **PROVEN** (demonstrated against real pilot data/company context, with evidence), **PARTIAL** (some but not all of the capability is demonstrated), **NOT PROVEN** (capability exists per code but has not yet been exercised against real pilot conditions), **BLOCKED BY DATA** (the capability cannot be demonstrated because the required real data does not exist), **BLOCKED BY PRODUCT DEFECT** (a real defect prevents demonstration), or **NOT APPLICABLE**. No capability may be scored with an informal status ("looks good," "probably works," "ready").

As of this discovery pass, **no gate below has been executed against real pilot data yet** — this Slice is discovery and contract-design only. Every gate in §12 is currently unscored (design-only); scoring begins in the next PV1 slice.

## 12. Pilot acceptance gates (Step 10)

| # | Gate | Design note |
|---|---|---|
| A | Real source file accepted | Covered by §5 row A/B; PoultryValidator's whole-file-fail mode (§9) is a known risk to watch |
| B | Source provenance retained | Confirmed by code (§9); needs a real-pilot-run confirmation |
| C | Real facts parsed correctly | Needs a real upload run per file in §6 |
| D | Units/date/company/hall semantics correct | Date format assumptions (§9) are a specific risk — verify against actual real file date formats |
| E | No fake operational facts | §9's static-file-default finding is the primary watch item |
| F | Metrics correct | Needs real-run verification against manually-computed expected values |
| G | Events correct | Needs clarification of which "Event" concept (§5 row E) is being tested |
| H | Signals evidence-grounded | `high_daily_mortality`/`production_below_standard`/`data_quality_warning`/`production_declining_trend` — verify each against Scenario 1–4 |
| I | Situation grounded in current operational evidence | `poultry_production_drop` — verify against Scenario 3 |
| J | Truth Layer distinguishes fact from inference | `epistemic_origin="observed"` design (§5) supports this; needs a real-run check that the reasoning output preserves the distinction in its own language |
| K | Company Brain loaded correctly | Confirmed by code; verify tenant/department gating with a real Jannat session |
| L | Company Brain provenance available | Verify citations resolve to the actual document/heading |
| M | Truth/Company Brain conflicts surfaced rather than hidden | No current scenario explicitly designs a Truth-vs-policy contradiction; may need a fifth scenario in the next slice if real data supports one |
| N | OM history cannot silently override current Truth | Needs a real-run check once enough Decision/Outcome history exists to test against |
| O | AI recommendation grounded in available evidence | Central test across all four scenarios |
| P | Reasoning receipt created | Already unit/integration-tested; needs a real-pilot-session confirmation |
| Q | Recommendation citations resolve | Central test across all four scenarios |
| R | No unsupported numerical claim | Central test, especially Scenario 4 |
| S | No unsupported operational causal claim | Central test, especially Scenario 3's cost-condition check |
| T | Uncertainty explicit when data missing | Central test, Scenario 4 |
| U | Human Decision remains explicit | Already proven at the technical level (M8/M9); real-pilot-session confirmation only |
| V | Action cannot exist without real DecisionMemory | Already proven technically; real-pilot-session confirmation only |
| W | Named human assignee works | Already proven technically (M9 Slice 3/4); real-pilot-session confirmation only |
| X | Action status lifecycle works | Already proven technically; real-pilot-session confirmation only |
| Y | Action history remains auditable | Already proven technically; real-pilot-session confirmation only |
| Z | Human Outcome remains separate | Already proven technically; real-pilot-session confirmation only |
| AA | Tenant/company isolation preserved | Already proven technically (extensive test suite); real-pilot-session confirmation only |
| AB | CEO can understand "why" | Central to §13's usability gate |
| AC | Missing data is visible rather than hallucinated | Central test, Scenario 4 |
| AD | Failure path is safe | The PoultryValidator whole-file-fail mode (§9) needs a real-run check that the failure message is CEO-safe, not a raw stack trace |
| AE | Repeated run does not corrupt/duplicate truth unexpectedly | **Known gap** (§9 dedup finding) — likely to score BLOCKED BY PRODUCT DEFECT once tested, unless accepted as out-of-scope for PV1 |
| AF | Pilot can be demonstrated end-to-end without manual DB surgery | **Known gap** (§5 row R) — the two existing browser specs don't yet join into one continuous run |
| AG | Pilot result can be reproduced by another operator following documented steps | No such operator runbook exists yet — to be authored in a later slice |
| AH | Static bundled historical pilot data does not enter the PV1 live Truth Context when PV1 isolation mode is enabled | New — Founder Pilot Rule 1 (§9). Related to, but more specific than, gate E (no fake operational facts): the static files are real, not fake, so E alone would not catch this; AH exists precisely because "real but not upload-gated" is a distinct risk from "fabricated." Requires `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED=false` for the run under test, confirmed before scoring, not merely assumed |
| AI | Every operational fact shown in the PV1 reasoning path can be classified as one of: current explicit pilot evidence; deliberate historical evidence; deterministic system heuristic; Company Brain policy; Organizational Memory history; AI inference | New — a granular expansion of gate J (Truth Layer distinguishes fact from inference), which only requires a fact/inference split. AI requires the full six-way classification to be recoverable from the reasoning output itself, not merely true internally |
| AJ | System heuristic thresholds are never mislabeled as Company Brain policy | New — Founder Pilot Rule 2 (§7). Directly targets `high_daily_mortality` (>20 daily count) and the legacy interpreter's mortality-rate bands, neither of which is Jannat management policy |
| AK | If both mortality mechanisms (legacy interpreter, structured OIP) can affect one reasoning call, their provenance/meaning remains distinguishable and non-contradictory to the CEO; otherwise the run fails this gate | New — the explicit Slice 3 acceptance check named in Scenario 2 (§10). A failure here is classified as a SEMANTIC MAPPING / REASONING DEFECT candidate (§14), not fixed inline |

Gate range: **A–AK** (33 base gates plus AH–AK, 37 total). No existing gate fully duplicated AH–AK, so all four were added rather than consolidated; AH and AI each note their relationship to the narrower pre-existing gate they extend.

## 13. CEO usability gate (Step 11)

The pilot must let a CEO answer, without inspecting raw JSON or database IDs:

1. What happened? 2. Why does NAWA believe it happened? 3. What evidence is it using? 4. What does the Company Brain say? 5. Is Truth in conflict with company policy? 6. What does NAWA recommend? 7. What is uncertain or missing? 8. What did the human decide? 9. Who is responsible for execution? 10. What happened afterward?

Items 1–7 are answerable today through the existing chat UI and `ExecutiveReasoningPanel` (proven not to leak raw internal structure — M7/M8 privacy hardening). Items 8–10 are answerable through the existing Decision/Action/Outcome UI (M8/M9). No new UI capability is implied by this gate; it is a **content and framing** gate, not a feature gate — the real test is whether real scenario runs actually produce answers a CEO would find complete and honest, not whether the buttons exist.

## 14. Blocker taxonomy (Step 12)

DATA GAP · INGESTION DEFECT · SEMANTIC MAPPING DEFECT · TRUTH-LAYER DEFECT · REASONING DEFECT · PROVENANCE/EXPLAINABILITY DEFECT · DECISION/ACTION/OUTCOME DEFECT · UI/PILOT-USABILITY DEFECT · TENANT/SECURITY DEFECT · TEST-HARNESS DEFECT · DOCUMENTATION/OPERATING-PROCEDURE GAP · FUTURE FEATURE — NOT PILOT BLOCKING.

Findings from this Slice, pre-classified:

| Finding | Classification |
|---|---|
| Temperature/ventilation/electricity/clinical-veterinary data absent | DATA GAP |
| No numeric Company Brain thresholds | DATA GAP — **governed by Founder Pilot Rule 2 (§7):** requires operator elicitation before any scenario needs one, never engineering inference; not a blocker for Slice 2 |
| Warehouse/sales/feed-mill-detail/finance-PDF translators don't exist yet | INGESTION DEFECT candidate, or FUTURE FEATURE if PV1 scope stays poultry-hall-only |
| Whole-file validation failure with no partial-row salvage | INGESTION DEFECT candidate |
| No duplicate-upload deduplication | INGESTION DEFECT candidate |
| No quality-specific signal type | REASONING/TRUTH-LAYER scope gap — FUTURE FEATURE unless a scenario proves it pilot-blocking |
| Two parallel mortality-detection pathways with different thresholds | SEMANTIC MAPPING DEFECT candidate — sharpened into gate AK / an explicit Slice 3 acceptance check (§10, Scenario 2) |
| Static pilot-file auto-inclusion defaults on in production | PROVENANCE/EXPLAINABILITY finding — **resolved by Founder Pilot Rule 1 (§9):** `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED=false` is now a Slice 2 precondition, not an open decision |
| No unified end-to-end browser demonstration | UI/PILOT-USABILITY DEFECT candidate, ties to gate AF |
| No operator runbook for reproducing a pilot run | DOCUMENTATION/OPERATING-PROCEDURE GAP, ties to gate AG |
| `DAIRTNA_OPERATIONAL_SEMANTICS.md` §9 provenance unconfirmed | DOCUMENTATION/OPERATING-PROCEDURE GAP |

None of these is yet confirmed as an actual pilot blocker — each is a candidate to be scored once a real scenario run is attempted in the next slice.

## 15. Pilot stop rules (Step 13)

The pilot cannot be declared successful if any of the following occurs: a fabricated company fact; wrong company/tenant data; an unsupported numeric recommendation; real source data that cannot be traced to provenance; a materially incorrect field mapping; Company Brain silently overriding contradictory Truth; historical memory silently replacing current Truth; an Action created without an explicit Decision; autonomous execution of any kind; an Outcome created automatically; cross-company assignee/data leakage; or a CEO unable to determine why a recommendation exists.

## 16. What does not block the pilot (Step 14)

Track A, Track B, SituationMemory, full EBD-004 compliance, OME lifecycle/bounded-growth governance, Voice, Avatar, an Automation Engine, a workflow scheduler, deep integrations, `due_at`, a `failed` Action state, and a generic project-management abstraction are **not** automatic pilot blockers and remain exactly as deferred/paused as they were at M9 closure. If real pilot evidence in a later slice makes one of these objectively necessary to conduct the pilot at all, it must be classified and justified in that slice's own document — never implemented preemptively here.

## 17. Proposed PV1 execution slices (Step 15 — not activated)

**PV1 Slice 2 — Real Data Ingestion Validation.** **Precondition (Founder Pilot Rule 1, §9): `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED=false` must be set for whatever environment this Slice's real-pilot ingestion/reasoning runs execute against, verified before any run, before this Slice's acceptance evidence is collected.** Goal: run the four Scenario 1–4 source files (and any others from §6 already ingestible) through the real upload path against the real Jannat tenant, and score gates A–J, R, AD, AE, AH against actual results. Exclusions: no new translator, no schema change, no new Company Brain numeric threshold (Founder Pilot Rule 2, §7). Acceptance evidence: per-file ingestion result plus a filled-in acceptance-gate scorecard. Dependency: none beyond this Slice. Code changes: only if a genuine defect is found and the smallest fix is authorized separately — this slice is validation-first.

**PV1 Slice 3 — Real Operational Reasoning Scenarios.** Goal: run Scenarios 1–4 as real chat conversations against the real Jannat tenant and real ingested data from Slice 2, and score gates K–T, AB, AC, AI, AJ, AK. Includes the explicit dual-mortality-path acceptance check (§10, Scenario 2). Exclusions: no new signal/situation type invented mid-slice — if one is needed, it is classified and deferred, not built inline; no new Company Brain numeric threshold invented from code (Founder Pilot Rule 2) — if a scenario genuinely needs one, it is elicited from the Jannat operator/SME as its own governance action, not authored inline. Acceptance evidence: a transcript + citation-resolution proof per scenario. Dependency: Slice 2.

**PV1 Slice 4 — Decision → Action → Outcome Pilot Validation.** Goal: for each Scenario, complete the human loop (Decision → Action → assignee → status → Outcome) with a real Jannat user, and score gates U–Z, AF (the unified browser demonstration). Exclusions: no new Action state, no automation. Acceptance evidence: a real, reproducible end-to-end session record. Dependency: Slice 3.

**PV1 Slice 5 — Pilot Hardening + Founder Acceptance.** Goal: close whatever real (not hypothetical) defects Slices 2–4 surfaced, author the operator runbook (gate AG), and present the final scored acceptance matrix for Founder review. Exclusions: no feature growth beyond fixing what was actually found broken. Acceptance evidence: the completed matrix from §12, all gates scored, plus the runbook. Dependency: Slices 2–4.

This is the smallest sequence discovery currently supports — no slice is merged further because each depends on the real, scored output of the one before it, and no slice is split further because each has one clear, bounded acceptance artifact. **Only Slice 1 (this document) is activated. Slices 2–5 require their own separate, explicit Founder activation.**

## 18. Explicitly deferred items

Unchanged from M9 closure: Track A `DEFERRED`, Track B `DEFERRED`, SituationMemory `DEFERRED — NOT MVP BLOCKING`, full EBD-004 compliance `NOT ESTABLISHED`, OME lifecycle/bounded-growth governance `DEFERRED`, Sprint EX-1 `PAUSED`. PV1's activation does not resolve, activate, or otherwise touch any of these.

## 19. Current Slice 1 status

**BASELINE + ACCEPTANCE CONTRACT COMPLETE — UNDER INDEPENDENT REVIEW.** Not CLOSED — closure requires review, commit, Founder push authorization, and remote verification under the existing governance model established at M9 closure; this document does not close itself. Complete: architecture discovery (§5), real data inventory re-verified directly against the filesystem at 14 real files / 5 `.gitkeep` / 19 total entries (§6), Company Brain inventory (§7) with Founder Pilot Rule 2 (numeric threshold discipline) recorded, data coverage matrix (§8), ingestion readiness and no-fake-data findings (§9) with Founder Pilot Rule 1 (static pilot source isolation) recorded, four real pilot scenarios with explicit capability-boundary precision and a sharpened dual-mortality-path acceptance check (§10), the acceptance model and gate matrix now spanning A–AK (§11–§12), the CEO usability gate (§13), blocker taxonomy applied to this pass's findings including the two now-resolved Founder-decision items (§14), stop rules (§15), explicitly-preserved deferred items (§16), and a proposed (not activated) four-slice execution sequence carrying both Founder rules forward as explicit preconditions/exclusions (§17). No code, test, or migration was touched. No gate has been executed against real data yet — that begins in PV1 Slice 2.

## 20. Recommendation for next step

This document is ready for independent review. The two findings that previously warranted explicit Founder attention are now resolved as explicit governing rules rather than open questions: **Founder Pilot Rule 1** (§9) sets `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED=false` as a precondition of Slice 2's real-pilot runs; **Founder Pilot Rule 2** (§7) forbids inventing or copying a numeric Company Brain threshold before Slice 2, and requires any threshold a later scenario genuinely needs to be elicited from the Jannat operator/SME as its own governance action. Both rules are carried forward into §17's Slice 2/3 scope as explicit preconditions and exclusions. No other open decision remains in this document. Everything in this document can proceed to Slice 2 on Founder activation without further discovery.
