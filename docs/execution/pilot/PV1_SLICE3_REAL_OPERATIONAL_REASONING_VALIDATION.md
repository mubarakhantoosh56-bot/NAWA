# PV1 Slice 3 — Real Operational Reasoning Validation

**Status:** **ACTIVE — FOUNDER BLOCKER REVIEW.**
**Priority:** P0. Third slice of PV1 — Jannat Al-Firdaws Real-Company Pilot Validation.
**Owner:** AI Engineering Team (Claude Code).
**Ownership layer:** Validation, plus the record of correction batch A1. The validation findings below were produced without modifying any application code. Correction batch A1 (DEFECT-007) has since been implemented, reviewed, committed and pushed under separate Founder authorization — engineering checkpoint `0090d00c0de0c757c9618148c8b354c5bc4e3a0b` — and is recorded in §0.1. No frontend, migration, source-data, Company Brain knowledge, or env/config file was modified by the Slice 3 validation/reconciliation pass, the A1 correction, or this A1 closure-documentation work.
**Repository First Policy compliance:** This document is the required task document for this Slice.

---

## 0. Reconciliation status

This document has been **reconciled** following Founder blocker review of its first pass. The reconciliation re-derived every material claim from code and from durable evidence (saved HTTP responses, saved internal decision-context debug snapshots, and direct read-only database queries), rather than from the first pass's own narrative.

**Three first-pass claims were found to be wrong and are corrected here:**

| First-pass claim | Reconciled finding | Section |
|---|---|---|
| DEFECT-005 is a *filename*-token classification gap | It is a **storage-path** dependency. The filenames are irrelevant; the decisive token came from the repository **directory** name. The same file classifies two different ways depending only on where its bytes happen to sit on disk. | §5 |
| DEFECT-007's inverted Hall 2/Hall 3 fact came from "an earlier, unrelated real session" | **Causally backwards.** Scenario 4 *fabricated* the claim in-turn at 12:50, with zero support anywhere in its prompt, and the system then **wrote it back** as a durable `conf:80` company truth. Database `session_id` provenance proves origin. | §10 |
| DEFECT-006 attempt counts (10/10 Scenario 1, "6/6" department-scoped, "identical-wording repeat failed 2/2") | **Overstated.** The harnesses can only have issued 23 chat attempts in total. Exact artifact-grounded ledger below; the failure *rate* remains severe (82.6%). | §13 |

**Two new defects are raised:** DEFECT-009 (CEO Company-Brain applicability gap) and DEFECT-010 (mortality reasoning guardrail enforcement failure).

**One first-pass conclusion is materially strengthened:** the duplicate-contamination check was performed against the wrong table. Actual duplication **did** occur, in `operational_event_drafts` (§12).

No defect was fixed **during the reconciliation pass that produced this document**. Correction batch A1 (DEFECT-007) was authorized and executed afterwards — see §0.1.

---

## 0.1 Correction batch A1 — DEFECT-007: CLOSED — REMOTE VERIFIED

**Engineering checkpoint:** `0090d00c0de0c757c9618148c8b354c5bc4e3a0b` (parent `d23c90e0bb6d4cb5fc453c3c998bb103597ca7c5`, the pre-correction evidence checkpoint).

**What A1 closed:**

1. Live `/ai/chat` no longer automatically persists AI- or user-derived content into durable `memory_facts`.
2. Live operational reasoning no longer loads legacy `memory_facts` through any of the five verified read paths: direct Institutional Facts prompt injection (P1), Company Brain `INSTITUTIONAL_MEMORY` folding (P2), memory-derived Company Profile (P3), Decision Context memory trends (P4), and the memory-profile fallback (P5).
3. The automatic `_extract_and_upsert_facts` invocation from live chat is disabled; the extractor itself is retained, unmodified, and simply no longer called.
4. Historical contaminated facts remain physically present as negative regression fixtures — 13 `memory_facts`, 9 `memory_fact_history`, 80 `operational_event_drafts`, both Hall fixtures. No deletion, edit, cleanup, or seed rewrite was used to obtain a pass.
5. No migration and no schema change was required.
6. `memory_events` remains a separate channel and was deliberately **not** disabled by A1.
7. Helper and repository semantics remain intact outside the live operational reasoning path.

**Acceptance evidence.** Architecture review PASS; implementation review PASS; M7 test re-specification PASS; final pre-commit review PASS; post-amend review PASS; remote verification PASS. Golden Journey 1 passed; A1 focused suite 7 passed; required regressions 385 passed; full suite 1162 passed, 0 failed; real Scenario 4 regression PASS **for A1 isolation only**.

**What A1 did NOT close.** A1 closure is **not** Slice 3 closure. PV1 Slice 3 remains **ACTIVE — FOUNDER BLOCKER REVIEW**. Scenario 4 is **not** fully PROVEN, and no scenario score in §15 changes. CEO-wide Company Brain applicability is **not** solved — A1 intentionally leaves it reporting `no_evidence` until DEFECT-009 / Batch D is addressed. DEFECT-002/A2, DEFECT-008/A3, DEFECT-006/B1, DEFECT-010/B2 and DEFECT-009/D remain **OPEN — NOT ACTIVATED**; C1 (DEFECT-005 + DEFECT-003), C2 (DEFECT-001) and C3 (DEFECT-004) remain **NOT ACTIVATED**; PV1 Slice 4 remains **NOT ACTIVATED**.

**Next eligible correction batch: A2 / DEFECT-002 — A2 ARCHITECTURE GATE REQUIRED BEFORE ACTIVATION.** Race-safe exact-content deduplication across duplicate-sensitive durable writes remains architecture-unproven (see §12.4 and Correction Plan v2.1 §5). **NO MIGRATION IS CURRENTLY AUTHORIZED.** A2 is not activated by this document.

---

## 1. Baseline and governance

Branch `claude-safe-review`. Verified before and after all work: local HEAD = tracking origin = live origin = `a461adda91083dd7131f09ab64e7882914da4944`, divergence 0/0.

- M9: **CLOSED**
- PV1: **ACTIVE**
- PV1 Slice 1: **CLOSED — REMOTE CHECKPOINT VERIFIED**
- PV1 Slice 2: **CLOSED — REMOTE CHECKPOINT VERIFIED**, checkpoint `a461adda91083dd7131f09ab64e7882914da4944`
- PV1 Slice 3: **ACTIVE — FOUNDER BLOCKER REVIEW**
- PV1 Slice 4: **PROPOSED — NOT ACTIVATED**
- PV1 Slice 5: **PROPOSED — NOT ACTIVATED**
- Post-M9 engineering feature expansion: **NOT ACTIVATED**

## 2. Founder activation

The Founder activated PV1 Slice 3 — Real Operational Reasoning Scenarios: validation of NAWA's closed-M9 reasoning architecture against real Jannat Al-Firdaws operational evidence, real Company Brain content, and the real, currently-live reasoning path. Not feature expansion, not ingestion hardening, not defect remediation, not Decision → Action → Outcome validation (that is Slice 4).

## 3. Actual product reasoning path

Discovery was performed by reading the current code, not by inferring from prior docs.

| Stage | Real code | Notes |
|---|---|---|
| API endpoint | `POST /ai/chat` → `app/api/chat.py:chat_endpoint` | Validates `request.company_id == auth_context.company_id` (403 on mismatch) |
| Department/CEO gate | `app/api/chat.py:_build_chat_context` (`app/api/chat.py:88-161`) | `department_id=None` requires `workspace.ceo` permission; a department_id requires `agents.{department_type}.use`. `aimx_department` is stripped from any client-supplied context and only ever set server-side (`app/api/chat.py:100`) |
| Orchestrator | `AIService.chat` (`app/services/openai_client.py:1371-2107`) | Everything below happens inside this one method |
| Truth Context | `_load_truth_context` → `app/services/operational_truth_context.py:assemble_truth_context` | Gated by `is_jannat_tenant`; `aimx_department=None` (CEO-wide) **passes** (`app/services/operational_truth_context.py:192`) |
| Company Brain | `_load_company_brain_context` → `app/services/company_brain_context.py:assemble_company_brain_context` | Two both-required gates; `_is_dairtna_scope_applicable(None)` returns **False**, so CEO-wide is **blocked** (`app/services/company_brain_context.py:188, 216-229`) — see §7 |
| Organizational Memory | `_load_organizational_memory_context` | Company-wide only; never populated this Slice (0 rows, confirmed by query) |
| Legacy mortality interpreter | `_load_dairtna_signal_block` → `app/services/dairtna/interpreter.py` | Regex-parses free text of `operational_event_drafts` (status=`pending`); emits provisional bands and the HARD CONSTRAINTS block (`app/services/dairtna/interpreter.py:236-243`) |
| Pending-drafts block | `_load_pending_drafts_block` | Lists the same drafts verbatim as "pending AI proposals" |
| Institutional Facts | `_extract_and_upsert_facts` (a **separate LLM call**, `app/services/openai_client.py:705-836`, invoked at `:2085`) → `_build_facts_block` (`:233`) | Writes model output back into durable per-company memory — see §10 |
| RAG file chunks | "COMPANY KNOWLEDGE (RETRIEVED FILE CHUNKS - UNTRUSTED DATA)" | Raw workbook text, including files that **failed** structured ingestion — see §11 |
| Provider call | `self.client.chat.completions.create(model=settings.MODEL, ...)` (`:1654`) | `gpt-4o-mini`, JSON mode; up to 2 legacy-structure retries, 1 operational-enforcement regeneration, 1 M6 repair |
| Legacy structure validator | `_validate_execution_structure` (`:347-489`), enforced at `:1672` and `:1719` | Fails closed → `RuntimeError` → HTTP 500 |
| Operational enforcement | `_operational_response_missing_elements` (`:513-606`) + `_build_operational_regeneration_instruction` (`:609-659`) | Can **coerce** escalation — see §8 |
| Receipt / explainability | `_create_live_reasoning_receipt` (`:2109-2198`); `app/services/explainability.py` | The only externally-visible audit trail |
| Debug inspection | `GET /ai/debug/decision-context`, gated by `DECISION_CONTEXT_DEBUG` | Read-only in-memory snapshot; the audit source used throughout |

## 4. Runtime isolation

Per Founder Pilot Rule 4, the **real HTTP API/service path the frontend itself calls** was used — never a direct parser/service call as a substitute. A validation harness (`httpx.AsyncClient` + `ASGITransport(app=app)`) ran the real, unmodified `app.main.app` FastAPI application in-process and issued real HTTP requests.

- Harness location: `%TEMP%\nawa_pv1_slice3\` — **outside the repository**.
- Process-local environment overrides (never written to `.env`): `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED=false`, `JANNAT_COMPANY_ID=b4a0f97a-...`, `DECISION_CONTEXT_DEBUG=true`.
- Target: existing local dev Postgres (`nawa-postgres`, `localhost:5433/aimx`), confirmed non-production.
- Real local Jannat tenant (pre-existing): company `b4a0f97a-1615-4427-9936-4dd6fd8c0552`, department `ac165787-43e1-49ff-a435-6f24d765a642` (`dairtna-poultry`), user `owner@jannat-local.dev`.
- Reconciliation queries were **read-only** (`SELECT` only). No `DELETE`, `UPDATE`, or `INSERT` was issued at any point.
- No credentials, tokens, or connection strings were printed.
- Cross-tenant evidence observed: **none.**

---

## 5. Reconciliation A — DEFECT-005 upload classification storage-path dependency

### 5.1 What was reproduced

For the **same real workbook**, with the **same real original Arabic filename**, through the **same unchanged classifier code**, only the `source_path` differing:

| File | `source_path` = repo path | `source_path` = opaque OS temp path (the real HTTP upload path) |
|---|---|---|
| `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` | `excel_poultry_report` 0.90 | `excel_poultry_report` 0.90 |
| `تقرير_القاعة_2_الأبيض.xlsx` | `excel_poultry_report` 0.90 | **`spreadsheet_intake` 0.62** |
| `تقرير_القاعة_2_الأحمر.xlsx` | `excel_poultry_report` 0.90 | **`spreadsheet_intake` 0.62** |
| `تقرير_القاعة_3_الأبيض.xlsx` | `excel_poultry_report` 0.90 | **`spreadsheet_intake` 0.62** |
| `تقرير_إجمالي_الأبيض_والأحمر.xlsx` | `excel_poultry_report` 0.90 | **`spreadsheet_intake` 0.62** |
| `إجمالي_حقول_ديرتنا_الإنتاج.xlsx` | `excel_poultry_report` 0.78 | `excel_poultry_report` 0.78 |

`requires_human_confirmation` flips `false` to `true`, and `probable_department` collapses from `"dairtna_poultry"` to `null`, for the four divergent files.

This matches the **real authenticated `POST /files/upload`** results exactly (saved in `results/uploads.json`): all four uploaded hall/aggregate-colour files returned `nco_status: "waiting_for_input_confirmation"`, `classification.confidence: 0.62`, `probable_department: null`, `record_count: 0`.

### 5.2 Exact root cause, isolated by ablation

`_metadata_text()` (`app/company_input/services/company_input_classifier.py:264-278`) concatenates **`company_input.raw_storage_path`** (line 272) into the classification feature text, then normalizes it: `.lower().replace("_", " ").replace("-", " ")` (line 278).

An ablation over the single divergent variable, `تقرير_القاعة_2_الأبيض.xlsx`:

| `source_path` variant | Result |
|---|---|
| `data_sources/jannat_al_firdaws/2026_06/poultry_operations/<file>` | `excel_poultry_report` 0.90 |
| same, with the `poultry_operations/` directory removed | **`spreadsheet_intake` 0.62** |
| `poultry_operations/<file>` alone | `excel_poultry_report` 0.90 |
| `poultry/<file>` | `excel_poultry_report` 0.90 |
| `uploads/2026_06/<file>` | **`spreadsheet_intake` 0.62** |
| opaque `AppData\Local\Temp\tmpXXXX.xlsx` (real HTTP) | **`spreadsheet_intake` 0.62** |
| empty string | **`spreadsheet_intake` 0.62** |

**The decisive signal is the literal substring `poultry`, contributed by the repository directory name `poultry_operations`** — normalized to `poultry operations` by line 278, then matched by `_has_any(text, ("poultry", "dairtna", "deirtna", "ديرتنا"))` at line 86. Confidence then reaches 0.90 because `_has_any(text, ("daily", "report", "technical", "تقرير", "يومي"))` (line 87) matches `تقرير` from the **real filename**.

The real HTTP route can never supply that token: `app/api/files.py:109-110` streams the upload into `tempfile.NamedTemporaryFile(delete=False, suffix=upload_suffix)` and passes that opaque path onward (`app/api/files.py:120, 137, 314`), where `map_excel_upload_to_company_input` stores it as `raw_storage_path` (`app/company_input/services/excel_upload_mapper.py:44`). 0.62 is below `CONFIRMATION_THRESHOLD` (0.70), so `NCOLiteOrchestrator.run_company_input` returns `waiting_for_input_confirmation` and **KAE never runs** (`app/nco/orchestrator.py:87-94`).

Only `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` and `إجمالي_حقول_ديرتنا_الإنتاج.xlsx` survive, because they carry `ديرتنا` **in the filename itself**, independent of path.

### 5.3 DEFECT-005 — final wording

> **DEFECT-005 — UPLOAD CLASSIFICATION STORAGE-PATH DEPENDENCY**
>
> **Symptom:** The same poultry workbook receives a different routing classification depending on whether its `source_path` contains repository/domain words or is an opaque temporary upload path.
>
> **Effect:** 4 of the 5 previously expected hall/report files fail structured poultry routing through the full authenticated HTTP upload path (`spreadsheet_intake` at 0.62, `requires_human_confirmation=true`, 0 records persisted).
>
> **Root cause:** The classifier's feature text includes source/storage-path text (`_metadata_text`, `company_input_classifier.py:272`), and underscore normalization (line 278) turns the repository directory `poultry_operations` into the matchable token `poultry` (line 86). Repository-path validation therefore leaks a domain hint that a normal HTTP upload — which always presents an opaque `tempfile` path — does not have.
>
> **Classification:** INGESTION / ROUTING CLASSIFICATION DEFECT.
>
> **Pilot status:** **PILOT BLOCKING** for unrestricted real user upload.
>
> **Smallest likely correction surface:** exclude `raw_storage_path` from classification features (the `original_filename` is the user-meaningful signal and is already present), or move to content-shape detection, which already works correctly once reached.

### 5.4 DEFECT-005 is distinct from DEFECT-003

They fire at **different stages**, on **different inputs**:

- **DEFECT-003** — `_has_daily_report_filename_marker(filename)` (`app/api/files.py:307, 442-447`) takes **only the filename**, and runs **before** classification. It blocks `إجمالي_حقول_ديرتنا_الإنتاج.xlsx`. It is structurally immune to the storage-path issue.
- **DEFECT-005** — `CompanyInputClassifier._classify_excel` via `_metadata_text`, which reads `raw_storage_path`, and runs **after** the marker gate. It blocks the four hall/aggregate-colour files.

Confirmed by the ablation: `إجمالي_حقول_ديرتنا_الإنتاج.xlsx` classifies at 0.78 in **both** path cases — it would pass DEFECT-005 and is stopped solely by DEFECT-003. **They are kept as separate defects.**

## 6. SLICE 2 EVIDENCE CLARIFICATION REQUIRED

**The historical PV1 Slice 2 checkpoint remains valid** as the record of what was known and reviewed at that time, and is **not reopened or rewritten**. This section records the clarification in Slice 3 only.

PV1 Slice 2 section 6.1 states its matrix was executed by passing each real workbook through the actual `_run_nco_lite_after_upload_if_applicable` function. **That is true and is preserved**: Slice 2 did invoke the real downstream production NCO/upload helper. It was not a mock and not a substitute reasoning implementation.

The clarification is narrower and specific: **Slice 2's validation supplied the real repository file path directly as `source_path`.** That repository path contains domain/context text (`poultry_operations`) that is absent from the opaque OS temporary path created by the real HTTP upload flow. Because the classifier consumes storage/source-path metadata, the Slice-2 validation environment unintentionally supplied classification signal that a normal user upload does not have.

**Therefore: the prior 5/6 live upload routing claim was materially overstated with respect to the complete user-facing HTTP upload path.** The real figure through `POST /files/upload` is **1 of 6**.

### 6.1 Which Slice 2 acceptance claims are affected

| Slice 2 claim | Status after reconciliation |
|---|---|
| **Gate A — real source file accepted** (scored PARTIAL on DEFECT-003/004 grounds, "live upload route only successfully ingests 5/6") | **PARTIAL — materially narrowed.** The live-route figure is **1/6**, not 5/6. The gate's tier does not change, but its evidentiary basis is much weaker than recorded. |
| Any scenario/product-path readiness conclusion resting on the 5/6 routing claim | **WITHDRAWN as product-path evidence.** It remains valid as *downstream-helper* evidence only. |
| Direct parser correctness | **NOT INVALIDATED.** Independent of `source_path`; unaffected. |
| Source parsing accuracy (counted field-by-field comparison) | **NOT INVALIDATED.** |
| Semantic field mapping evidence | **NOT INVALIDATED.** |
| Provenance mechanism | **NOT INVALIDATED.** |
| Static-source isolation (gate AH) | **NOT INVALIDATED** for the static-scan channel it actually tested — but see section 11: that guarantee is much narrower than it reads. |

**The distinction to carry forward:** *technical downstream helper proof* (Slice 2 has this) is not *complete user-facing product-path proof* (Slice 2 does not have this, and Slice 3 shows it fails).

## 7. Reconciliation B — CEO Company Brain applicability

### 7.1 Observed behaviour

- **CEO/company-wide chat** (`department_id = null`): Truth Context **available** (13 items, T1–T13); Dairtna Company Brain **NOT included**. Every CEO-wide run this Slice returned `dairtna_knowledge_included=false` and `company_brain_policy_available=false`.
- **Department-scoped chat** (`department_id = ac165787-43e1-49ff-a435-6f24d765a642`): loads the real Dairtna Company Brain and exposes authoritative items including **Quality vs Profit**, **Production Reduction**, **Crisis Management**, and the qualitative management priorities.

### 7.2 The gate, and the asymmetry it creates

Both gates were read directly:

- `assemble_truth_context` (`app/services/operational_truth_context.py:192`): `if aimx_department is not None and not is_poultry_department_scope(aimx_department): return NOT_APPLICABLE`. A `None` department (CEO-wide) **passes**. Dairtna *operational evidence* flows to the CEO workspace.
- `assemble_company_brain_context` (`app/services/company_brain_context.py:188`) requires `_is_dairtna_scope_applicable(aimx_department)`, which returns `False` for `None` (`:226-227`). Dairtna *policy* does **not** flow to the CEO workspace.

**The CEO workspace therefore receives one division's raw operational facts while being denied that same division's interpretive policy for those exact facts.** The data with cross-division sensitivity flows; the governance that would constrain reasoning about it does not.

### 7.3 Evaluation against NAWA product intent

The behaviour is deliberate and documented (`_is_dairtna_scope_applicable` docstring). Per the Founder instruction, intentional code behaviour is **not** treated as automatically valid product behaviour, and is evaluated on merits:

| Dimension | Assessment |
|---|---|
| **Security** | No deficiency in the gate itself. It is non-spoofable, server-authoritative, and derived from an RBAC-verified department row, never from user message text. |
| **CEO company-wide authorization** | `department_id=None` is reachable **only** with the `workspace.ceo` permission (`app/api/chat.py:117-122`). This scope is by construction the company-wide, all-divisions authority. The CEO is entitled to Dairtna policy. Withholding it is not an authorization decision — the authorization already passed. |
| **Cross-division leakage risk** | The stated rationale — never present one division's policy "as if it were universal company policy" — is legitimate. But the correct remedy for *mis-attribution* is **attribution** ("per Dairtna Poultry policy…"), not **suppression**. Company Brain items already carry `authority` and source document/heading provenance capable of expressing this. |
| **Department applicability** | Sound in principle. The defect is that applicability is evaluated as a binary on the *chat scope* rather than on the *subject matter of the question*. A CEO asking a plainly Dairtna-specific operational question is, in substance, in Dairtna scope. |
| **Multi-division behaviour** | Today only Dairtna has a Company Brain. The current rule does not scale to the intended end state: with several division brains, the correct company-wide behaviour is to load each **applicable** division's policy with division attribution — not to load none. The present rule degrades as divisions are added. |
| **Reasoning correctness** | **This is where it fails.** Empirically confirmed this Slice: in the CEO-wide runs, `company_brain_alignment` was `"not supported by current evidence"` and `company_basis: []` in every response — not because policy was absent from the company, but because it was withheld from the reasoning call. Scenario 1 (Quality vs Profit) and Scenario 3 (Production Reduction) exist specifically to test policy-grounded reasoning, and both were framed CEO-wide. The department-scoped Scenario 3 run — the only one with the Company Brain loaded — produced the single best-reasoned output of the Slice (section 9). |

**Conclusion: current behaviour prevents legitimate CEO reasoning.** DEFECT-009 is raised.

### 7.4 DEFECT-009 — CEO COMPANY-BRAIN APPLICABILITY GAP

> **Symptom:** A CEO in the company-wide workspace who asks a clearly Dairtna-specific operational question receives Dairtna operational Truth Context but **no** Dairtna Company Brain policy, so the response cannot be grounded in, checked against, or constrained by the company's own decision rules.
>
> **Effect:** `company_brain_policy_available=false` and `company_basis: []` in every CEO-wide run this Slice. The two scenarios designed to test policy-grounded reasoning (Quality vs Profit; Production Reduction) cannot be satisfied from the CEO workspace at all. Directly degrades acceptance gates K, L, AB.
>
> **Root cause:** `_is_dairtna_scope_applicable` (`app/services/company_brain_context.py:216-229`) treats an unresolved/company-wide scope as not applicable by default, while `assemble_truth_context` (`app/services/operational_truth_context.py:192`) treats the same scope as applicable. The two layers disagree about what a CEO-wide scope means.
>
> **Classification:** REASONING SCOPE / POLICY APPLICABILITY DEFECT.
>
> **Pilot status:** **PILOT BLOCKING for the CEO workspace**, which is the primary described usage in the Slice 1 CEO Usability Gate.
>
> **Not implemented.** Recorded only. A correction would need an explicit Founder decision on whether company-wide scope loads applicable division policy **with division attribution**, since that is a product-intent question, not a code question.

## 8. Reconciliation C — mortality reasoning guardrail audit

### 8.1 What the prompt contained

`app/services/dairtna/interpreter.py:236-243` injected, verbatim:

```
HARD CONSTRAINTS for CEO response:
  1. Do NOT escalate any metric beyond its stated signal_level.
  2. If signal_level is 'normal', do NOT frame the metric as a bottleneck, crisis, production delay, or sales risk.
  3. If signal_level is 'unknown', state that baseline data is missing. Do not infer.
  4. Do NOT connect mortality to sales, distribution, or finance unless cross_dept_flag is true
     AND a human-confirmed operational event supports it.
  5. Cite the computed_rate alongside the raw count when referencing mortality.

[Signal 1] metric: mortality_rate | observed_fact: 158 bird deaths recorded on 13/05/2026
  signal_level: unknown
  signal_basis: baseline_missing — flock size not found in uploaded file
  cross_dept_flag: false
[Signal 2] ... 157 bird deaths on 12/05/2026 ... signal_level: unknown ... cross_dept_flag: false
```

### 8.2 What the CEO saw

> "The root operational bottleneck is the **high mortality rates** in the poultry halls, with 158 daily mortalities recorded on 13/05/2026 and 157 on 12/05/2026. This situation necessitates immediate investigation… as it directly **impacts production capacity and revenue generation**. **Affected departments** include Production, Veterinary, and Operations… The **operational impact** includes potential further losses in flock health and production capacity, leading to an **inability to meet sales commitments**."

With `reasoning_state: "aligned"`, `confidence: 80`, `trust_score: 80`, and `operational_assessment: "High mortality rates are confirmed with specific counts from operational events."`

### 8.3 Determinations

| Question | Answer | Evidence |
|---|---|---|
| **Severity upgrade occurred?** | **YES** | `signal_level: unknown` was rendered as "high mortality rates" and as "the root operational bottleneck". Violates constraints 1 and 3. |
| **Unsupported cross-department linkage occurred?** | **YES** | `cross_dept_flag: false`, yet mortality was linked to production capacity, revenue generation, and sales commitments. Violates constraint 4. |
| **Human-confirmed supporting event existed?** | **NO** | Direct query: `operational_event_drafts` has exactly **5** rows with `status='confirmed'` (all confirmed 2026-05-22). The 158/157 figures appear only in rows with `status='pending'`, which the prompt itself labels "NOT confirmed events. Do not treat them as facts." |
| **Required mortality rate citation preserved?** | **NO** | No rate was cited. Violates constraint 5. |

**4 of the 5 hard constraints were violated in a single response.**

### 8.4 Root cause — the product coerced the violation

The model's **first** response did not contain the violations:

> "The current mortality readings indicate a significant issue, with 158 daily mortalities recorded on 13/05/2026 and 157 on 12/05/2026. Immediate action is required to assign an owner to investigate and address the underlying causes within 24 hours."

No "high" framing, no bottleneck claim, **no cross-department linkage at all**.

`_operational_response_missing_elements` then rejected it, demanding exactly: `["root operational bottleneck", "affected departments", "operational impact"]` (`operational_regeneration.missing_elements`, from the saved debug snapshot). The regeneration was `accepted: true` with `remaining_missing_elements: []`.

**Every violation in the final text maps one-to-one to a demanded element.** The escalation, the department linkage, and the revenue/sales impact were all *introduced by the regeneration*, not by the model's own initial judgment.

Two code-level causes:

1. **`_operational_response_missing_elements` (`app/services/openai_client.py:534-539`)** — its protective escape hatch, `all_signals_normal`, requires the literal `"signal_level: normal"` to appear in the signal block. `signal_level: unknown` — the exact state the interpreter emits when baseline data is missing — is **not covered**, so the bottleneck/capacity/impact requirements were enforced against a signal the interpreter had explicitly refused to classify.
2. **`_build_operational_regeneration_instruction` (`app/services/openai_client.py:609-659`)** — has a protective branch for `signal_level: normal` and another for a model-declared `insufficient_evidence`, but `unknown` with a declared `aligned` state falls through to the coercive default: *"Start the executive_summary with the concrete root operational bottleneck."* It then unconditionally appends, for **all** branches, *"Then explain the cause/effect chain, affected departments, operational impact, business impact, and one priority executive action"* — which directly commands the cross-department linkage that hard constraint 4 forbids.

The second protective branch depends on the model volunteering `reasoning_state=insufficient_evidence` — the very humility the enforcement layer is otherwise about to punish. The protection is circular.

**No runtime validator anywhere checks whether the HARD CONSTRAINTS were honoured.** They exist only as prompt text (confirmed by search: the only occurrences of the constraint strings and of `cross_dept_flag` in `app/` are inside `app/services/dairtna/interpreter.py`).

### 8.5 A further, independent contradiction the response did not surface

Direct query of the same tenant, for **13/05/2026**:

| Real source file | Daily mortality | Status |
|---|---|---|
| `التقرير_الفني_اليومي_حقول_ديرتنا.xlsx` | **12**, out of **77,005** birds | **HUMAN-CONFIRMED** |
| `تقرير_إجمالي_الأبيض_والأحمر.xlsx` | 158 | pending |
| `إجمالي_حقول_ديرتنا_الإنتاج.xlsx` | 198 | pending |
| `تقرير_القاعة_2_الأبيض.xlsx` | 98 | pending |
| `تقرير_القاعة_2_الأحمر.xlsx` | 60 | pending |
| `تقرير_القاعة_3_الأبيض.xlsx` | 28 | pending |

These are plausibly **different measurement scopes** (company aggregate vs per-hall vs colour sub-aggregate), and this document does not assert that any figure is factually wrong. The finding is that **the scope relationship between them is unresolved, unlabelled, and invisible to the model, the receipt, and the CEO.**

Two consequences follow, both material:

- The only **human-confirmed** mortality evidence in the system for that date is **12 out of 77,005 birds = 0.016%**, which is below the interpreter's own `normal` band (`<0.05%`). That figure was literally present in the Scenario 1 and Scenario 3 prompts as an institutional fact. The model escalated to crisis framing on the **highest unconfirmed** figure while confirmed evidence pointing the other way sat in the same prompt.
- `truth_validation.contradictions` was `[]` in every run, despite the prompt rule *"If retrieved knowledge conflicts with institutional facts or the user's message, flag it in truth_validation.contradictions."*

Separately, `signal_basis: baseline_missing — flock size not found in uploaded file` is an artifact of the interpreter regex reading only that one draft's free text. Flock-size baselines **were** present elsewhere in the same prompt: `77,005` (confirmed draft and institutional facts), `80,000` and `72,529` (RAG excerpts). The interpreter declared the baseline missing while three other channels in the same prompt carried it.

### 8.6 DEFECT-010 — MORTALITY REASONING GUARDRAIL ENFORCEMENT FAILURE

> **Symptom:** Explicit, prompt-level HARD CONSTRAINTS governing mortality reasoning are violated in the CEO-visible response — severity escalated beyond a declared `unknown` signal, and mortality linked to production, revenue, and sales commitments with `cross_dept_flag: false` and no human-confirmed supporting event.
>
> **Effect:** A CEO reading Scenario 2 is told that high mortality is the root operational bottleneck threatening sales commitments, on the basis of unconfirmed draft rows, while the only human-confirmed figure for the same date implies a rate inside the normal band. `reasoning_state` was reported as `aligned` at confidence 80.
>
> **Root cause:** The guardrails are prompt-only and unenforced, and a *second* enforcement layer actively coerces their violation. `_operational_response_missing_elements` (`openai_client.py:534-539`) exempts only `signal_level: normal`, not `unknown`; `_build_operational_regeneration_instruction` (`:609-659`) then falls through to a default that commands a "concrete root operational bottleneck" and unconditionally demands "affected departments, operational impact, business impact". The model's compliant first response was rejected and regenerated into a non-compliant one.
>
> **Classification:** REASONING GUARDRAIL ENFORCEMENT DEFECT — independent of, and compounding, the provenance failure in DEFECT-007.
>
> **Pilot status:** **PILOT BLOCKING.** This is the failure mode Founder Pilot Rule 2 and Stop Rules 2 and 6 exist to prevent.
>
> **Not implemented.** Recorded only.

## 9. Reconciliation D — Scenario 3 complete claim audit

Both successful Scenario 3 responses are audited. The later, cleaner department-scoped response does **not** erase the earlier CEO-wide product-path behaviour.

### 9.1 First successful response — CEO-wide scope (`pv1-slice3-s3-production`, HTTP 200, first attempt)

Company Brain: **not loaded** (DEFECT-009). `company_basis: []`, `company_brain_alignment: "not supported by current evidence"`.

| Statement | Classification |
|---|---|
| Production decline observed (T3 `production_trend`, derived; T1/T2 `bird_balance` 76942, `daily_production_rate` 91.3, both `observed`, both cited) | **SUPPORTED FACT** (the T1/T2 values) plus **SUPPORTED HEURISTIC INTERPRETATION** (the derived trend) |
| "This decline **may be linked to** increased mortality rates" | **AI INFERENCE WITH DISCLOSED UNCERTAINTY** — hedged, not asserted as proven causation. Acceptable. |
| "…indicating **potential** health issues" / possible flock-health issue | **AI INFERENCE WITH DISCLOSED UNCERTAINTY** — hedged. Acceptable. |
| Potential revenue loss / inability to meet sales commitments | **UNSUPPORTED CLAIM.** No finance evidence exists in the tenant (confirmed: finance PDFs remain non-ingestible). Traced in section 10 to a persisted institutional "fact" (`[metric] revenue`, conf **15**) originating from an earlier `frontend-ceo-session`, and re-demanded by the regeneration instruction's unconditional "business impact" requirement. |
| Did **not** claim the Production Reduction policy trigger was satisfied | **CORRECT ANTI-OVERREACH** — but by absence of the policy rather than by reasoning about it, since the rule was never retrieved in this scope. |
| Priority action: investigate flock health and environmental conditions within 7 days | **AI INFERENCE**, reasonable, but not carried in any structured recommendation field (see section 13.4 — `solution_generator` and `execution_engine` are entirely empty). |

### 9.2 Second successful response — department-scoped (`pv1-slice3-dept-s3-production-a2`, HTTP 200, second attempt)

Company Brain: **loaded** — all 8 sections and all 8 decision rules, including the Production Reduction rule.

| Statement | Classification |
|---|---|
| "A decline in egg production has been observed in some poultry halls, necessitating further investigation **before considering any production reduction**." | **SUPPORTED FACT** (the decline) plus **SUPPORTED COMPANY BRAIN INTERPRETATION in substance** — this is precisely the anti-overreach behaviour Scenario 3 exists to test. |
| Company Brain citation for the above | **NOT MADE.** `company_basis: []` despite the directly on-topic Production Reduction rule being present in the prompt as an authoritative item. The right conclusion was reached without citing the policy that justifies it. |
| Explicit statement that the rule's financial precondition is unevaluable | **NOT MADE.** The response never says the profitability/cost-increase condition cannot be assessed because no finance evidence exists. |

### 9.3 Final Scenario 3 determination

Scenario 3 is the strongest scenario of the Slice: it is the only one to succeed under both scopes, it never asserted a policy trigger that was not satisfied, and the department-scoped run reached exactly the correct operational conclusion.

It nonetheless carries: an unsupported revenue/sales-commitment claim in the CEO-wide run; zero Company Brain citation in the one run where the Company Brain was available; no explicit naming of the missing financial precondition; empty structured recommendation fields in both runs; and a 3-of-4 failure rate across its own real attempts.

**Scenario 3 score: PARTIAL.**

## 10. Reconciliation E — DEFECT-007 corrected root cause

### 10.1 The first pass had the causality backwards

The first pass recorded that the claim *"Hall 2 has specific metrics for feed consumption, while Hall 3 lacks this data"* was carried into Scenario 4 from an earlier, unrelated real session. **That is wrong.** The full evidence path was traced stage by stage.

**Source.** Searched Scenario 4's complete 103,958-character prompt: the string `lacks` appears **0 times**. All four occurrences of `Hall 2` / `Hall 3` are the **CEO's own question text** echoed back. Scenario 4's `INSTITUTIONAL FACTS (COMPANY TRUTHS)` block contained 8 facts, **none** referring to feed or water by hall. The claim had **no source anywhere in the prompt**.

**Extraction / persistence.** After the response, `_extract_and_upsert_facts` (`app/services/openai_client.py:2085`) passed the model's own `executive_summary` and `raw_decision` to a second LLM call, which split the fabricated sentence into two durable facts. Direct query of `memory_facts` — the `session_id` column is an authoritative provenance stamp:

```
created=2026-09-09 12:50:02  [metric] water_consumption    conf=80  sid=pv1-slice3-s4-halls
created=2026-09-09 12:50:02  [metric] feed_consumption     conf=80  sid=pv1-slice3-s4-halls
created=2026-09-09 12:50:02  [risk]   data_incompleteness  conf=80  sid=pv1-slice3-s4-halls
created=2026-09-09 12:50:02  [goal]   data_collection      conf=80  sid=pv1-slice3-s4-halls
created=2026-09-09 12:50:02  [metric] daily_mortalities    conf=80  sid=pv1-slice3-s4-halls
```

**Retrieval.** The facts block, ordered by run time, proves the write-back:

| Run (chronological) | Facts in prompt | Hall 2 / Hall 3 facts present? |
|---|---|---|
| Scenario 1 (12:48) | 8 | **No** |
| Scenario 3 (12:49) | 8 | **No** |
| Scenario 3 rerun (12:49) | 8 | **No** |
| **Scenario 4 (12:50)** | 8 | **No** — this is the run that produced the claim |
| Scenario 2 retry (12:54) | **13** | **Yes** |
| Department Scenario 3 (13:01) | **13** | **Yes** |

**Prompt / reference-catalog treatment.** From 12:54 onward the fabrication was presented to the model under the header `INSTITUTIONAL FACTS (COMPANY TRUTHS)` with the instruction *"Use them for continuity, consistency, and decision accuracy"* — carrying **no** epistemic-origin marker, **no** source-time status, and **no** T#/CB#/OM# reference id, so it is structurally outside the runtime citation validator that governs `recommendation_basis`.

**Receipt and public explainability.** In Scenario 4 itself: `recommendation_basis` was `{evidence_basis: [], company_basis: [], missing_evidence: [], organizational_memory_basis: []}` — every list empty. `explainability.cited_evidence: []`. Yet `explainability.operational_assessment` reproduces the fabricated sentence **verbatim**, alongside `confidence: {value: 80, band: "high", drivers: ["conflicted_company_basis"]}` — a high-confidence band on a response whose own `reasoning_state` was `insufficient_evidence` and whose citations were all empty. **The audit surface carries the fabrication.**

**Human-confirmed?** **No.** Never confirmed by anyone; written automatically at `conf:80`, a value derived from the model's own self-reported `reasoning_assessment.confidence` in the same insufficient-evidence response.

**Historical status visible to the model and the CEO?** **No.** The facts block shows no timestamps, no session origin, and no distinction between a fact from May 2026 and one written four minutes earlier by the model itself.

### 10.2 A second, genuinely historical contamination path also exists

Not every fact was self-created this Slice. Four were carried forward from earlier real sessions, and they explain recurring language across the Slice:

| Fact | Confidence | Origin session | Where it surfaced |
|---|---|---|---|
| `[metric] revenue` = "فقدان الإيرادات بسبب عدم القدرة على تلبية الطلبات" (revenue loss from inability to meet orders) | **15** | `frontend-ceo-session` (May 2026) | The recurring "inability to meet sales commitments" / "potential revenue loss" claims in Scenarios 2, 3 and 4 |
| `[process] goal` = "تعيين مالك مسؤول لتحديد نقاط الاختناق في الإنتاج خلال 24 ساعة" (assign a responsible owner within 24 hours) | **35** | `frontend-ceo-session` | The recurring "assign a responsible owner… within 24 hours" action in Scenarios 2, 3 and 4 |
| `[constraint] constraint` = "تأخيرات الإنتاج الناتجة عن عدم توفر الأعلاف والأدوية" (production delays from feed and medicine unavailability) | **5** | `frontend-ceo-session` | Scenario 2's "ensure adequate feed and medicine availability" |
| `[metric] product_name` = "الطيور" (the birds); `[metric] primary_market` = "قسم المبيعات" (the sales department) | 5 | `interp-test-003/004` — an engineering test session | Degenerate extractions retained as company truths |

All are presented to the model as COMPANY TRUTHS despite confidences of 5, 15 and 35.

### 10.3 Fact-key collision silently replaced a correct fact with a contested one

`upsert_fact` (`app/services/memory/repository.py:155-215`) resolves same-key/different-value collisions by replacing when `new confidence >= existing confidence`. Because the extractor emits degenerate keys (`metric`, `goal`, `revenue`, `constraint`), unrelated facts collide on one key.

Observed directly: the `[metric] metric` key held **"12 حالة وفاة من أصل 77,005 طائر بمعدل وفيات 0.016%"** (12 deaths of 77,005 birds, rate 0.016%) — consistent with the human-confirmed record and inside the interpreter's normal band — in the Scenario 1 and Scenario 3 prompts. At 12:49:29 it was replaced, under session `pv1-slice3-s3-production`, by **"158 deaths recorded on 13/05/2026 and 157 on 12/05/2026"** at conf 0. From that point the correct, confirmation-consistent rate was gone from the facts channel.

**Fairly noted:** the conflict *was* recorded. `memory_fact_history` holds 9 rows for this company, each capturing both sides in `sources_weighed` — the ENG-CONF-001 conflict ledger works as designed. It records the conflict; it does not prevent the weaker value winning, and nothing surfaces it to the CEO or into explainability.

The loop closed again at 12:54:04, when Scenario 2's forced cross-department claim overwrote `[metric] revenue` with "Potential revenue loss due to inability to meet sales commitments."

### 10.4 DEFECT-007 — refined

> **DEFECT-007 — INSTITUTIONAL FACTS WRITE-BACK LOOP INJECTS UNCITED, UNVERIFIED AI CLAIMS AS DURABLE COMPANY TRUTH**
>
> **Symptom:** Model output is extracted by a second LLM call and persisted as durable per-company "facts", then re-injected into every later chat call under the header INSTITUTIONAL FACTS (COMPANY TRUTHS) with no epistemic-origin marker, no source-time status, and no T#/CB#/OM# reference id — outside the citation validator entirely.
>
> **Effect, directly observed:** Scenario 4 fabricated a specific, confident, comparative claim about which hall has feed and water data, with zero support in its prompt. The system wrote it back as two `conf:80` company truths, and every subsequent turn received it as authoritative. The fabrication is reproduced verbatim in the public `explainability.operational_assessment` with `cited_evidence: []` and a `"high"` confidence band. Separately, prior sessions' AI prose (`revenue` conf 15, `goal` conf 35, `constraint` conf 5) recurs as apparent operational reasoning across all scenarios, and a degenerate fact-key collision replaced a confirmation-consistent 0.016% mortality-rate fact with the contested 158/157 figure.
>
> **Root cause:** `_extract_and_upsert_facts` (`openai_client.py:705-836`, called at `:2085`) persists model output with a model-self-reported confidence and no grounding check; `_build_facts_block` (`:233`) re-presents it as company truth without provenance; degenerate `fact_key` values collide in `upsert_fact` (`memory/repository.py:155-215`).
>
> **Classification:** MEMORY PROVENANCE / FABRICATION-PERSISTENCE DEFECT.
>
> **Pilot status:** **PILOT BLOCKING.** This is the closest the Slice came to Stop Rule 2 ("AI silently treats missing evidence as fact") and Stop Rule 6, and it is self-reinforcing rather than self-correcting.
>
> **Not implemented.** Recorded only.

## 11. Reconciliation F — DEFECT-008 isolation boundary

Every evidence channel observed reaching `/ai/chat` while `NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED=false`, enumerated from the real prompts (section headers located by offset in the saved snapshots) and from `decision_context`:

| # | Channel | Prompt location / source | Current vs historical | Company-scoped | Dept-scoped | Time-scoped | Human-confirmed | Citation-addressable | Receipt-addressable | Public-explainability-addressable | Isolated by Founder Rule 1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Structured **Truth Context** (T1–T13) | `DECISION CONTEXT` block, `operational_truth_context` | Current | Yes | Yes (CEO-wide passes) | Yes (`report_date`) | N/A (machine-parsed from a real upload) | **Yes** (T#) | **Yes** | **Yes** | **Yes** (static scan gated; upload branch separate and intended) |
| 2 | **Operational events** (`memory_events`, `operational_events`) | `DECISION CONTEXT` block | **Mixed** — includes rows from May–Jul 2026 **and** this Slice's own chat turns | Yes | No | No | Partly (5 confirmed rows) | No | No | No | **No** |
| 3 | **Legacy mortality signal block** | `DAIRTNA OPERATIONAL SIGNAL INTERPRETATION` (offset ~99455) | Historical (11–13/05/2026) | Yes | Yes | No | **No** (reads `status='pending'` only) | No | No | No | **No** |
| 4 | **Pending AI operational proposals** | `PENDING AI OPERATIONAL PROPOSALS` (~100984) | Historical | Yes | Yes | No | **No** (self-labelled unconfirmed) | No | No | No | **No** |
| 5 | **Institutional Facts** | `INSTITUTIONAL FACTS (COMPANY TRUTHS)` (~90451) | **Mixed and unlabelled** — May 2026 through this Slice's own turns | Yes | No | **No** | **No** | **No** | No | **Leaks into it** (section 10.1) | **No** |
| 6 | **Institutional Memory / MEMORY FACTS narrative** | `INSTITUTIONAL MEMORY (HARD FACTS — MUST USE IF RELEVANT)` (~91732), `MEMORY FACTS:` (~91981) | Mixed | Yes | No | Timestamps present in the narrative | Partly | No | No | No | **No** |
| 7 | **RAG company-file chunks** | `COMPANY KNOWLEDGE (RETRIEVED FILE CHUNKS - UNTRUSTED DATA)` (~93980) | Current uploads **plus** historical files | Yes | No | No | No | No | No | No | **No** |
| 8 | **Company Brain** | `DECISION CONTEXT` block, `company_brain_context` | Current (documents) | Yes | **Yes — required** | N/A | N/A (authored policy) | **Yes** (CB#) | **Yes** | **Yes** | N/A (not pilot-file data) |
| 9 | **Organizational Memory** | `organizational_memory_context` | Historical | Yes | No | Yes | N/A | **Yes** (OM#) | **Yes** | **Yes** | N/A — **never populated** (0 rows, confirmed) |
| 10 | **Company intelligence / profile context** | `COMPANY PROFILE`, `COMPANY INTELLIGENCE PROFILE (PERSISTENT CONTEXT)` (~87669, ~89319) | Persistent | Yes | No | No | No | No | No | No | **No** |
| 11 | **Legacy marketing/growth rulesets** (newly identified) | `MARKET EXPANSION STRATEGY RULES`, `ADAPTIVE STRATEGY ENGINE RULES`, `CHANNEL STRATEGY RULES`, `EXECUTION ENGINE RULES`, `STRICT EXECUTION REQUIREMENTS (HARD)`, `FULL EXECUTION MODE (CRITICAL)`, `VALIDATION GATE (CRITICAL)` (~78024–84836) | N/A — instructions, not evidence | N/A | N/A | N/A | N/A | No | No | No | **No** |

### 11.1 Newly discovered: rejected files are not inert

The four hall/aggregate files that **failed** structured classification (DEFECT-005, 0 structured records) still entered reasoning through **two** ungoverned channels:

- **RAG chunks** — each upload returned `chunk_count: 1, embedding_count: 1, embedding_status: "ready"`. Their raw sheet text, including hall identity, flock sizes (`عدد الدجاج 80000`), daily mortality columns and weekly rates, appears verbatim in the prompt as `[3] Excerpt:` under an UNTRUSTED DATA header.
- **`operational_event_drafts`** — direct query confirms the four rejected files created **20 new pending drafts** at 12:48:20–12:48:22, which then feed channels 3 and 4.

So a file the product declared unroutable and requiring human confirmation nonetheless contributed its numbers to CEO-facing reasoning through two paths that carry no T# citation discipline, no receipt entry, and no explainability entry.

### 11.2 Determination

**Clean pilot evidence isolation is NOT achieved.** Founder Pilot Rule 1's flag correctly gates exactly one channel of eleven (the static `.xlsx` directory scan — gate AH remains PROVEN for that channel specifically). Channels 2–7 and 10 are ungated, and channels 3, 4, 5, 6 and 7 were empirically confirmed carrying real historical data from unrelated prior sessions into every scenario run this Slice.

**DEFECT-008 is confirmed and widened** from three uncovered channels to **eight**, and now includes the RAG chunk channel and the operational-event-draft creation path for files that failed classification. Severity is raised from moderate-to-high to **high**: the leaking data is real rather than invented, but the Rule 1 boundary the Founder relies on does not exist in practice, and DEFECT-007's write-back loop means the boundary is also being crossed *outward* — this Slice's own runs permanently altered the tenant's durable memory.

## 12. Reconciliation G — duplicate contamination

### 12.1 The accidental artifact, identified precisely

An initial connectivity-check run of the harness crashed on a Windows console Unicode bug (a harness bug, not a product issue) **after** its first real upload had already been accepted and persisted. A `DELETE` was attempted to remove it and was blocked by the session's destructive-action safeguard. **No deletion occurred, and none was attempted again.**

The artifact is exactly one row:

```
structured_record_drafts
  id         = 7ee71602-b156-4b24-a3e0-7cc99f78af21
  created_at = 2026-09-09 12:46:27 UTC
  status     = draft
  records    = 9
  source     = التقرير_الفني_اليومي_حقول_ديرتنا.xlsx
```

### 12.2 Was it used by subsequent reasoning?

**Yes — by all of them.** It is the sole source of T1 (`bird_balance` 76942) and T2 (`daily_production_rate` 91.3), the only two `observed` numeric Truth Context values cited in any successful run. It is the entire structured evidence base of this Slice.

The evidence itself is valid: real file, real bytes, real authenticated HTTP route, real classifier pass. The only irregularity is that the harness process crashed after the call succeeded.

### 12.3 Was the same underlying file uploaded again, producing duplicate Truth?

**No.** Direct query: `structured_record_drafts` with `record_type='poultry_daily_technical_report'` for this company returns **exactly 1 row**. The corrected harness deliberately excluded that file from its upload list, and `results/uploads.json` confirms only four files were submitted. **No duplicate structured Truth was created, and no double counting occurred in Truth Context.**

### 12.4 But duplication did occur — in a different channel

The first pass checked only `structured_record_drafts` and concluded no duplication. That check was correct for that table and **insufficient**.

`تقرير_إجمالي_الأبيض_والأحمر.xlsx` had already been uploaded on 2026-05-23. This Slice uploaded it again, and DEFECT-002 (no cross-upload deduplication) fired:

```
2026-05-23 18:15  pending  On 12/05/2026, there were 157 daily mortalities recorded among the poultry.
2026-05-23 18:15  pending  On 13/05/2026, there were 158 daily mortalities recorded among the poultry.
2026-09-09 12:48  pending  On 12/05/2026, there were 157 daily mortalities recorded among the poultry.   <-- duplicate
2026-09-09 12:48  pending  On 13/05/2026, there were 158 daily mortalities recorded among the poultry.   <-- duplicate
```

Slice-wide: pending `operational_event_drafts` went from **55** before this Slice to **75** after — 20 new rows, all from the four re-uploaded files, several exact duplicates of existing rows.

**Exact impact.** The duplicated rows are the direct upstream source of the 158/157 figures that anchor Scenario 2 (section 8) — the very claim that drove the guardrail violation. The prompt blocks are bounded (2 signals, 5 proposals), so the duplication did not produce arithmetic double counting in the visible numbers; it does mean the durable draft store now holds redundant unconfirmed operational claims, and that **which** duplicates surface into a given prompt depends on an unstated ordering rather than on evidence quality. DEFECT-002 is therefore no longer only a documented risk — it is a realised one, observed on a real Jannat workbook through the real upload route.

## 13. Reconciliation H — DEFECT-006 reliability, exact counts

### 13.1 Method

The first-pass summary was **not** relied on. The ledger below is reconstructed from (a) the three harness scripts' control flow and (b) the surviving result artifacts, and is corroborated by file modification times.

Control flow that makes the reconstruction exact:

- `run_scenarios.py` — CEO-wide, **1 attempt per scenario**, writes the response body **unconditionally** (success or failure), keyed by scenario.
- `retry_failed.py` — CEO-wide, up to **3 attempts**, writes **only on HTTP 200**, then breaks.
- `run_dept_scoped.py` — department-scoped, up to **3 attempts**, writes **only on HTTP 200**, then returns. Attempt 1 uses the bare `session_id`; attempts 2 and 3 append `-a2` / `-a3`.

Because the retry harnesses write only on success, an unchanged failure artifact is positive proof that every retry for that scenario also failed. Because successful artifacts embed `meta.session_id`, the winning attempt number is directly readable.

Timeline corroboration (harness mtimes 15:47, 15:52, 15:58; result mtimes 15:48–16:01, in matching order) is consistent with exactly one run of each harness, in sequence.

### 13.2 Exact ledger

**CEO-wide scope**

| Scenario | Attempts | 200 | 500 | Basis |
|---|---|---|---|---|
| 1 — Quality vs profit | **4** | 0 | 4 | Artifact holds `{"detail":"Internal server error"}` and was never overwritten by the 3 retries — PROVEN |
| 2 — Mortality escalation | **2** | 1 | 1 | Winning artifact `meta.session_id = pv1-slice3-s2-mortality-r2-a1` — retry attempt 1 succeeded, PROVEN. The preceding `run_scenarios.py` attempt's outcome is **INFERRED** as 500 (its artifact was overwritten; the harness that re-ran it is named for failed scenarios) |
| 3 — Production decline (original wording) | **1** | 1 | 0 | Artifact `meta.session_id = pv1-slice3-s3-production` — first attempt succeeded, PROVEN |
| 3 — Production decline (reworded rerun) | **4** | 0 | 4 | Artifact holds `{"detail":"Internal server error"}`, never overwritten by the 3 retries — PROVEN |
| 4 — Hall comparison | **1** | 1 | 0 | Artifact `meta.session_id = pv1-slice3-s4-halls` — first attempt succeeded, PROVEN |
| **CEO-wide total** | **12** | **3** | **9** | |

**Department-scoped**

| Scenario | Attempts | 200 | 500 | Basis |
|---|---|---|---|---|
| 1 — Quality vs profit | **3** | 0 | 3 | No artifact written — PROVEN all 3 failed |
| 2 — Mortality escalation | **3** | 0 | 3 | No artifact written — PROVEN all 3 failed |
| 3 — Production decline | **2** | 1 | 1 | Artifact `meta.session_id = ...-a2` — attempt 1 failed, attempt 2 succeeded, PROVEN |
| 4 — Hall comparison | **3** | 0 | 3 | No artifact written — PROVEN all 3 failed |
| **Department total** | **11** | **1** | **10** | |

**Combined: 23 real chat attempts. 4 × HTTP 200 (17.4%). 19 × HTTP 500 (82.6%).**

Per scenario across both scopes: Scenario 1 **0/7**; Scenario 2 **1/5**; Scenario 3 **2/7** (original wording 1/1, reworded 0/4, department 1/2); Scenario 4 **1/4**.

### 13.3 Corrections to the first pass

| First-pass figure | Correct figure |
|---|---|
| Scenario 1: "10/10 failed" | **0 of 7** — still a total failure, but 7 attempts, not 10 |
| "6/6 department-scoped" (each scenario) | **3** attempts maximum per scenario; the department harness never issued 6 |
| Scenario 3: "identical-wording repeat failed 2/2" | **Not supported by any artifact or harness.** No such run exists. Withdrawn. |

The reliability finding is unchanged in substance and remains severe. Only the arithmetic is corrected.

### 13.4 Exact dominant failure stage

**All failures observed are at the legacy execution-structure validator, before any later stage runs.**

The two failed runs that left debug snapshots (`scenario1_quality_vs_profit`, `scenario3_production_decline_rerun`) both show `operational_regeneration.attempted: false`, `m6_reasoning_validation: null`, `m6_reasoning_validation_repair: null`, `final_contract_validation: null` — execution never reached the operational-enforcement stage (`openai_client.py:1742`), the M6 reasoning assessment, or its repair.

The failing path is `openai_client.py:1671-1736`: `max_retries = 2`, so each failed request consumed **3 real model generation calls** (1 initial + 2 retries) before `RuntimeError` and HTTP 500. **19 failures therefore burned at least 57 model generation calls producing zero CEO-visible output, zero receipt, and zero explainability.**

Retry budget assessment: 2 retries is not the binding constraint. The retry instruction (`:1685-1698`) demands every recommendation item carry "1. exact platform, 2. exact audience, 3. exact KPI, 4. exact quantity, 5. exact execution method, 6. exact timeframe, 7. real execution verb", with the worked example *"Send 150 LinkedIn outreach messages to Iraqi retail business owners within 21 days targeting a 12% reply rate."* No additional retry budget would make a poultry flock-health action satisfy that shape.

### 13.5 The binary trap — and why it matters more than the failure rate

`_validate_execution_structure` (`:347-489`) collects every item across `solution_generator.{urgent_30_days, mid_term_90_days, long_term_6_12_months}` and `execution_engine.{priority_order, quick_wins, high_impact_moves}`, and requires each item to **simultaneously** contain a platform keyword, a number, an execution-method keyword, an audience keyword, an execution verb, and a KPI word — all drawn from fixed marketing/growth vocabularies.

But at lines 373-375 it short-circuits:

```python
if not items_to_check:
    # Operational status responses legitimately have no execution items — accept them.
    return True
```

**All four successful responses passed through that escape hatch.** Every one of the eight recommendation arrays is empty in all four:

| Successful run | `solution_generator` | `execution_engine` |
|---|---|---|
| Scenario 2 (CEO-wide) | 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |
| Scenario 3 (CEO-wide) | 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |
| Scenario 4 (CEO-wide) | 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |
| Scenario 3 (department) | 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |

So the observed behaviour is a binary trap with no middle path:

- Model emits **any** structured recommendation → it must look like a marketing campaign → it does not → **HTTP 500, nothing returned**.
- Model emits **no** structured recommendation → vacuous pass → **HTTP 200 with an executive narrative and zero machine-readable actions**.

**NAWA currently cannot emit a single structurally-valid operational recommendation for this pilot.** That is a stronger and more consequential finding than the 82.6% failure rate, and it is decisive for Slice 4 (section 17).

### 13.6 Is the required execution schema legacy architecture imposed on ordinary NAWA reasoning?

**Yes.** Beyond the validator itself, roughly 9.7 KB of the ~103 KB prompt (offsets ~78024–84836) is legacy marketing/growth instruction — `MARKET EXPANSION STRATEGY RULES`, `ADAPTIVE STRATEGY ENGINE RULES`, `CHANNEL STRATEGY RULES`, `EXECUTION ENGINE RULES`, `STRICT EXECUTION REQUIREMENTS (HARD)`, `FULL EXECUTION MODE (CRITICAL)`, `VALIDATION GATE (CRITICAL)` — carried into every poultry-operations reasoning call. The same file already knows this distinction elsewhere: `_is_ceo_decision_context` and the `all_signals_normal` branch exist precisely to separate operational-status reasoning from campaign reasoning. That distinction is simply not applied to the legacy structural contract.

**DEFECT-006 stands, severity unchanged (High, pilot-blocking), with corrected counts and an added structural finding (13.5).**

## 14. Reconciliation I — evidence taxonomy

Measured against the six named PV1 evidence-origin categories:

| Channel (section 11) | Fits a named category? |
|---|---|
| Truth Context T1–T13 | **Yes** — CURRENT EXPLICIT PILOT EVIDENCE. The only channel that fully satisfies the taxonomy. |
| Legacy mortality signal block | **Yes** — SYSTEM DETERMINISTIC HEURISTIC (provisional bands, self-declared) |
| Company Brain document items | **Yes** — COMPANY BRAIN POLICY (all qualitative; zero numeric policy exists, matching Founder Pilot Rule 2) |
| Organizational Memory | **Yes** in principle — ORGANIZATIONAL MEMORY HISTORY. Never populated, so never exercised. |
| `reasoning_assessment` prose | **Yes** — AI INFERENCE |
| Pending AI operational proposals | **Partially** — self-labels as unconfirmed AI-derived, which is honest, but is not one of the six named categories |
| **Institutional Facts / INSTITUTIONAL_MEMORY** | **No** — unclassified seventh channel (DEFECT-007) |
| **Institutional Memory narrative / MEMORY FACTS** | **No** — unclassified |
| **RAG company-file chunks** | **No** — unclassified eighth channel; carries real numbers from files that failed structured ingestion |
| **Company intelligence / profile context** | **No** — unclassified |
| **Operational events (mixed current + this Slice's own chat turns)** | **No** — and self-referential: a CEO question is captured as an `operational.production.daily_update` event and replayed to the model as an operational event of record |

**Material reasoning inputs left epistemically unlabelled against the six-category taxonomy: yes — five channels, not one.** Gate AI cannot be scored PROVEN.

## 15. Reconciliation J — final scenario scores

| Scenario | Attempts (200/total) | Score | Basis |
|---|---|---|---|
| **1 — Egg quality vs short-term profit** | 0 / 7 | **BLOCKED BY PRODUCT DEFECT** | No response was ever produced, in either scope. DEFECT-006 (all 7 attempts) compounding DEFECT-005 (the hall files carrying `broken_eggs`/`dirty_eggs` never reached structured ingestion) and DEFECT-009 (the Quality vs Profit rule is unreachable from the CEO workspace). No claims exist to audit. |
| **2 — Mortality escalation** | 1 / 5 | **NOT PROVEN** *(downgraded from PARTIAL)* | The single response violated 4 of 5 explicit hard constraints (section 8), asserted unconfirmed pending-draft figures as confirmed fact, cited T1/T2 which are not the source of those figures, reported `truth_validation.contradictions: []` while the tenant held a human-confirmed figure implying a normal-band rate for the same date, and self-declared `reasoning_state: aligned` at confidence 80. The legacy interpreter itself behaved correctly; the product overrode it. |
| **3 — Production decline** | 2 / 7 | **PARTIAL** | The strongest scenario. Correct anti-overreach conclusion in both successful runs; never claimed the Production Reduction trigger was satisfied. Offset by: no Company Brain citation in the one run where it was available, no explicit naming of the missing financial precondition, an unsupported revenue/sales claim in the CEO-wide run, empty recommendation arrays, and 5 of its own 7 attempts failing. |
| **4 — Hall 2 vs Hall 3 missing-evidence comparison** | 1 / 4 | **NOT PROVEN** | The central comparative claim was fabricated with zero prompt support, is inverted relative to the documented real-file reality, carries `evidence_basis: []`, and was reproduced verbatim into the public explainability surface at a `"high"` confidence band — then persisted as two `conf:80` company truths (section 10). `reasoning_state: insufficient_evidence` was correctly declared at the top level and contradicted by the response's own prose. |

**No scenario scored PROVEN. Two scored NOT PROVEN. One was never executable.**

## 16. Reconciliation K — acceptance gate reassessment

Scored against the gate matrix in `docs/execution/pilot/PV1_JANNAT_REAL_COMPANY_VALIDATION.md` section 12. Only gates materially exercised are scored.

| Gate | Score | Reason |
|---|---|---|
| A — real source file accepted (carried forward) | **PARTIAL — materially narrowed** | Live route ingests **1 of 6** real poultry files, not 5 of 6 (section 6.1) |
| K — Company Brain loaded correctly | **PARTIAL** | Correct and complete when department-scoped; never loaded for CEO-wide scope — now raised as DEFECT-009 rather than accepted as design |
| L — Company Brain provenance available | **PARTIAL** | Resolves correctly when cited; never actually cited in the one run that had it available |
| M — Truth/Company Brain conflicts surfaced | **NOT APPLICABLE** | No genuine Truth-vs-policy contradiction arose in a run that produced output |
| N — OM history cannot silently override current Truth | **NOT APPLICABLE** | OM never retrieved (0 rows) |
| O — AI recommendation grounded in available evidence | **NOT PROVEN** | Scenarios 2 and 4's central claims are not grounded in cited evidence |
| Q — Recommendation citations resolve | **PARTIAL** | The T#/CB# citations made do resolve; the material claims that most needed citation carried none |
| R — No unsupported numerical claim | **NOT PROVEN** | Scenario 2's 158/157 asserted as confirmed fact without Truth Context grounding, against a contradicting human-confirmed figure |
| S — No unsupported operational causal claim | **NOT PROVEN** *(downgraded from PARTIAL)* | Scenario 2's mortality-to-sales-commitments chain is an unsupported causal claim, and was **coerced by the product's own enforcement layer** (section 8.4) |
| T — Uncertainty explicit when data missing | **PARTIAL** | Correct in Scenario 3; contradicted within its own response in Scenario 4 |
| AB — CEO can understand "why" | **NOT PROVEN** | A CEO cannot tell which claims are uncited; Scenario 1 produced no answer at all in 7 attempts |
| AC — Missing data visible rather than hallucinated | **NOT PROVEN** | Scenario 4 converted "we don't know" into a specific, wrong "we do know" |
| AH — static pilot source isolation (carried forward) | **PROVEN for the static-scan channel only — materially narrower than it reads** | 1 of 11 channels is gated; 8 are ungated and 5 were confirmed leaking (section 11) |
| AI — evidence-origin classification | **NOT PROVEN** | Five material channels sit outside the six-category taxonomy (section 14) |
| AJ — heuristic threshold never mislabelled as Company Brain policy | **PROVEN, narrowly** | No run presented a provisional band as Company Brain policy. This narrow proof coexists with the same mortality claim failing O, R and S through a different channel. |
| AK — dual mortality mechanisms remain provenance/meaning-distinct | **NOT PROVEN** | Trigger condition occurred; the legacy signal, the pending drafts, the institutional facts and the RAG excerpts all carried mortality figures into one call, and the CEO-facing prose does not distinguish them. The formal citation (T1/T2) points at neither mortality mechanism. |

## 17. Reconciliation L — Slice 4 readiness

**PV1 Slice 4 — Decision → Action → Outcome validation: NOT READY. Do not activate.**

This is not a marginal judgment. Slice 4's input precondition does not currently exist:

1. **There are no Actions to validate.** Section 13.5: 100% of successful responses returned entirely empty `solution_generator` and `execution_engine`. The only way a response passes the legacy validator is by containing no structured recommendation at all. Decision → Action → Outcome validation on top of zero machine-readable actions is not possible.
2. **Recommendations are frequently unavailable.** 82.6% of real attempts returned HTTP 500 with no output, no receipt and no explainability. Scenario 1 never produced a single response in 7 attempts.
3. **Recommendations that are produced can be ungrounded.** Two of four scenarios asserted material claims with empty `evidence_basis`, one of them fabricated and inverted.
4. **Recommendations are not reliably auditable.** The receipt and public explainability reproduce uncited prose verbatim, including a fabrication carrying a `"high"` confidence band.
5. **The evidence base is not isolated, and this Slice's runs mutated it.** Eight of eleven channels are ungated, and DEFECT-007's write-back loop permanently altered the tenant's durable memory during validation.
6. **The CEO workspace — Slice 4's primary surface — cannot reach Company Brain policy at all** (DEFECT-009).

Per the Founder instruction, Slice 4 must not proceed on top of recommendations that are frequently unavailable, ungrounded, or unauditable. All three conditions hold simultaneously.

**Recommended sequence:** Founder review of DEFECT-005 through DEFECT-010, then an explicit Founder decision on remediation scope, before any Slice 4 activation. Slice 4 should **not** be narrowed to the one scenario that reliably succeeds — that would shrink its scope without an explicit Founder decision, and Scenario 3 also returns empty action arrays.

## 18. Complete defect set

Carried forward from PV1 Slice 2, unchanged and not renumbered:

| ID | Summary | Status this Slice |
|---|---|---|
| **DEFECT-001** | Short-header feed-field semantic mapping gap (3 of 6 real files) | Moot this Slice — the affected files never reached ingestion (DEFECT-005) |
| **DEFECT-002** | No cross-upload deduplication | **Realised, not merely risked** — duplicate 157/158 mortality drafts created on a real Jannat workbook through the real route (section 12.4) |
| **DEFECT-003** | Company-aggregate file skipped by the filename-marker gate | Unchanged; confirmed distinct from DEFECT-005 (section 5.4) |
| **DEFECT-004** | Feed-mill translator has no live route | Not exercised |

Raised in this Slice:

| ID | Summary | Severity | Pilot status |
|---|---|---|---|
| **DEFECT-005** | Upload classification storage-path dependency — 4 of 5 real files fail structured routing through the real HTTP path | High | **PILOT BLOCKING** |
| **DEFECT-006** | Legacy marketing-shaped execution-structure validator fails closed (82.6% of real attempts), and passes only responses containing no recommendations | High | **PILOT BLOCKING** |
| **DEFECT-007** | Institutional Facts write-back loop persists uncited, unverified AI claims — including a fabrication — as durable `conf:80` company truth | High | **CLOSED — REMOTE VERIFIED** (batch A1, checkpoint `0090d00c0de0c757c9618148c8b354c5bc4e3a0b`; see §0.1) |
| **DEFECT-008** | Founder Pilot Rule 1 isolation covers 1 of 11 evidence channels; 8 ungated, 5 confirmed leaking | High *(raised from moderate-to-high)* | **PILOT BLOCKING** |
| **DEFECT-009** | CEO company-brain applicability gap — the CEO workspace receives Dairtna operational evidence but no Dairtna policy | High | **PILOT BLOCKING for the CEO workspace** |
| **DEFECT-010** | Mortality reasoning guardrail enforcement failure — hard constraints are prompt-only, and a second enforcement layer coerces their violation | High | **PILOT BLOCKING** |

**Of these, DEFECT-007 has since been corrected and closed by batch A1 (§0.1). The other nine remain unfixed, and no further product code has been modified.**

## 19. Repo safety

No application code, frontend code, test, script, migration, source data, or Company Brain knowledge file was modified. No `.env` or config file was modified — all overrides were process-local environment variables in a harness process outside the repository. All reconciliation database access was `SELECT`-only; no `DELETE`, `UPDATE` or `INSERT` was issued. Validation harnesses and reconciliation scripts live outside the repository, in `%TEMP%\nawa_pv1_slice3\`.

Exactly four documentation paths were touched:

- `CURRENT_STATE.md`
- `docs/execution/EXECUTION_BOARD.md`
- `docs/execution/EXECUTION_INDEX.md`
- `docs/execution/pilot/PV1_SLICE3_REAL_OPERATIONAL_REASONING_VALIDATION.md`

Nothing staged. Nothing committed. Nothing pushed.

## 20. Governance state

- M9: **CLOSED**
- PV1: **ACTIVE**
- PV1 Slice 1: **CLOSED — REMOTE CHECKPOINT VERIFIED**
- PV1 Slice 2: **CLOSED — REMOTE CHECKPOINT VERIFIED**, checkpoint `a461adda91083dd7131f09ab64e7882914da4944`
- PV1 Slice 3: **ACTIVE — FOUNDER BLOCKER REVIEW** (A1 closure does not close Slice 3)
- Correction batch A1 (DEFECT-007): **CLOSED — REMOTE VERIFIED**, checkpoint `0090d00c0de0c757c9618148c8b354c5bc4e3a0b`
- Correction batch A2 (DEFECT-002): **OPEN — NOT ACTIVATED**; next eligible batch, **A2 ARCHITECTURE GATE REQUIRED BEFORE ACTIVATION**; no migration authorized
- Correction batch A3 (DEFECT-008): **OPEN — NOT ACTIVATED**
- Correction batch B1 (DEFECT-006): **OPEN — NOT ACTIVATED**
- Correction batch B2 (DEFECT-010): **OPEN — NOT ACTIVATED**
- Correction batches C1 (DEFECT-005 + DEFECT-003), C2 (DEFECT-001), C3 (DEFECT-004): **NOT ACTIVATED**
- Correction batch D (DEFECT-009): **OPEN — NOT ACTIVATED**
- PV1 Slice 4: **PROPOSED — NOT ACTIVATED** (not activated by this document; recommended NOT READY)
- PV1 Slice 5: **PROPOSED — NOT ACTIVATED**
- Post-M9 engineering feature expansion: **NOT ACTIVATED**
