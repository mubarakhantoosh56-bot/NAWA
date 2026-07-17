# ENG-EX1-004 — Executive Language Completion Foundation

**Priority:** P1. Extends ENG-EX1-002's Executive Brief v2 Foundation; touches Sprint Tasks 3 (Executive Assessment), 4 (Business Impact), 5 (Executive Actions Taxonomy) partially.
**Owner:** AI Engineering Team (Claude Code / Codex), implementing Founder-approved deterministic Product decisions against PDS-001 §5.1–§5.4.
**Ownership layer:** Binding / Rendering.

**Note on task ID:** PDS-001 §5.1–§5.4 (real per-section definitions) landed after ENG-EX1-003 closed. This doc was numbered ENG-EX1-004 following the established sequential pattern; no explicit Founder-assigned ID preceded it — flag if a different number was intended.

---

## Objective

Implement the structured PDS-001 §5.1–§5.4 shapes for Executive Priority, Executive Assessment, Business Impact, and Executive Actions at Executive Intelligence — replacing `pending_executive_language` only where an explicit, deterministic Product rule was Founder-approved. Never invent content.

## Scope

- **Executive Priority** (PDS-001 §5.1) restructured from one flat pending blob into its 4 real named elements — Attention Level, Situation, Business Risk, Executive Trigger — each individually `pending_executive_language`. No approved rule maps `situation.severity` to an Attention Level value yet, so all four stay pending rather than guessing a mapping.
- **Executive Assessment** (PDS-001 §5.2) restructured into its 3 real named elements — Executive Interpretation, Business Meaning, Executive Recommendation Context — each individually pending.
- **Business Impact** (PDS-001 §5.3): Financial dimension replaced with the Founder-approved sentence, superseding the bare `"Unknown"` literal. Operational unchanged (already real, evidence-templated). Strategic unchanged (still pending).
- **Executive Actions** (PDS-001 §5.4):
  - **Priority reclassified as Business Logic, not Executive Language** (Founder decision) — value is `null`, never the `pending_executive_language` sentinel, until a priority-assignment rule is approved. Accepted vocabulary defined for future use: Critical / High / Medium / Low.
  - **Owner added** — `"Accountable role not yet assigned."` fallback on every action today, since no accountable-role data source exists anywhere upstream (confirmed: `OperationalSituation`/OIE/OCE carry no role or department-assignment concept). Documented in code: *"Owner may be determined in future versions through Company Brain role mapping."*
- `statement_trace` extended: the old single-entry paths for `executive_priority` and `executive_assessment`, and the grouped `executive_actions[i].priority_reason_outcome`, replaced with granular per-element paths.
- Stale PDS-001 citations fixed: `§5.5` → `§5.2` (Executive Assessment), `§5.6` → `§5.3` (Business Impact Strategic). The unrelated `§5.9` citation (Missing Evidence) is out of scope — that section has no real subsection number yet.
- **UI Hotfix:** `pendingNote()` in `CompanyInputsPanel.tsx` previously only recognized the `{status, note}` object shape. `executive_actions[i].reason` / `.expected_outcome` carry the sentinel as a bare string, which fell through unrecognized — meaning the raw literal `pending_executive_language` could reach the executive-facing screen instead of the intended amber "Pending executive language" badge. Fixed by extending `pendingNote()` to also recognize the bare-string form. Covers all 4 `PendingOrText` call sites in the component.

**Out of scope:**
- Any modification of NCE Lite, OCE, KAE, OIE, NCO Lite, Company Input Classifier, CompanyInput, or OME Foundation — confirmed untouched.
- Actual per-action Priority assignment, Owner-from-role-mapping, Executive Priority/Assessment language authoring, Strategic Impact authoring — all remain genuinely pending, deferred to Aboura / a future Company Brain capability.
- Enforcement of `statement_trace` — still instrumentation only, per ENG-EX1-003.

## Expected Deliverable

Structured PDS-001 §5.1–§5.4 shapes live in backend, API, and frontend, carrying exactly the deterministic content the Founder approved — nothing invented — plus the UI hotfix ensuring the raw sentinel literal can never reach an executive-facing screen.

## Dependencies

- ENG-EX1-002 (Executive Brief v2 Foundation) and ENG-EX1-003 (Statement Traceability Instrumentation) complete.
- PDS-001 §5.1–§5.4 real per-section definitions (landed after ENG-EX1-003).
- Founder decisions: Action priority vocabulary (Critical/High/Medium/Low), Owner fallback text, Financial Impact replacement sentence, `StructuredBriefSection` naming.

## Blockers

None encountered. No upstream Runtime Component needed touching.

## Acceptance Criteria

- Executive Priority and Executive Assessment expose their real PDS-001-named sub-elements, not one flat blob.
- Business Impact Financial carries the approved sentence, not `"Unknown"`.
- Executive Actions carry an Owner field with the approved fallback; Priority is `null`, never the pending-language sentinel.
- `statement_trace` paths updated to match the new structure, using only the ENG-EX1-003 approved vocabulary.
- No executive-facing screen can display the literal string `pending_executive_language`.
- No Runtime Component modified.

---

## Execution Result

**Status:** Completed (Founder-accepted)
**Started:** 2026-07-17
**Completed:** 2026-07-18
**Founder acceptance:** 2026-07-18
**Commit(s):** — (see next commit, ENG-EX1-004 only)
**Reviewer:** Founder
**Validation:** See below. Verified end-to-end against real Jannat data via the live `POST /files/upload` endpoint (real Postgres, real auth, real `NCOLiteOrchestrator` run).
**Follow-up:**
- `executive_actions[i].priority`'s `statement_trace` entry keeps `trace_status: "pending"` (closest existing approved category), distinguished only via `source_ref` wording ("no priority-assignment business rule approved yet") rather than a dedicated 4th vocabulary term — flagged for Founder/Aboura in case a distinct status (e.g. `"undetermined"`) is wanted to separate Business-Logic-pending from Language-pending more cleanly. Not changed without further approval.
- Real Priority assignment, real Owner-from-role-mapping (Company Brain), and Aboura's actual language for Executive Priority/Assessment/Strategic Impact/Business Rationale/Expected Outcome all remain open — this task built the structural foundation and applied only the explicitly-approved deterministic content, per instruction.

**Notes:**

**Files changed (exactly the 4 authorized):**
- `app/oip/services/ceo_brief_service.py` — `_executive_priority()` and `_executive_assessment()` restructured into their real named PDS-001 sub-elements via a new `_pending()` helper; `_business_impact()` financial sentence replaced; `_executive_actions()` gains `owner` and reclassifies `priority` to `None`; `_statement_trace()` gains 13 new granular paths (4 Priority + 3 Assessment + owner-per-action) and splits the old grouped action-pending entry into 3 (priority/reason/expected_outcome); 2 stale PDS-001 citations fixed. New module constants `EXECUTIVE_ACTION_PRIORITY_VALUES` and `EXECUTIVE_ACTION_OWNER_NOT_YET_ASSIGNED`.
- `frontend/src/components/operations/CompanyInputsPanel.tsx` — `PendingSection` replaced by `StructuredBriefSection` (per Founder naming decision) plus `executivePriorityFields()`/`executiveAssessmentFields()` builders; new `ExecutivePriorityPresentation`/`ExecutiveAssessmentPresentation` types (replacing `unknown`); `ExecutiveActionPresentation` gains `owner: string` and narrows `priority` to `string | null`; new `PriorityValue` component renders Priority distinctly from `PendingOrText`'s Executive-Language treatment; `ExecutiveActionsSection` gains an Owner line; **hotfix** in `pendingNote()` to recognize the bare-string sentinel.
- `frontend/src/lib/i18n/dictionaries/en.ts` / `ar.ts` — 9 new keys: Attention Level, Situation, Business Risk, Executive Trigger, Executive Interpretation, Business Meaning, Executive Recommendation Context, Owner, "Not yet determined" (with Arabic equivalents).

**Verification performed against real Jannat data** (`data_sources/jannat_al_firdaws/2026_06/poultry_operations/التقرير_الفني_اليومي_حقول_ديرتنا.xlsx`), via the live, authenticated `POST /files/upload` endpoint (real `nawa-postgres` container, real `owner@jannat-local.dev` JWT login, real DB-persisted `files` row):

- `executive_priority` returns 4 named sub-elements (`attention_level`, `situation`, `business_risk`, `executive_trigger`), each a `{"status": "pending_executive_language", "note": "..."}` object citing PDS-001 §5.1 correctly.
- `executive_assessment` returns 3 named sub-elements (`executive_interpretation`, `business_meaning`, `executive_recommendation_context`), each correctly citing PDS-001 §5.2.
- `business_impact_detail.financial` = `"Financial impact cannot currently be quantified because the required cost and revenue inputs are unavailable."` verbatim.
- All 5 `executive_actions[i]`: `priority: null` (confirmed on every action, never the sentinel string), `owner: "Accountable role not yet assigned."` verbatim on every action.
- `statement_trace`: 59 entries (up from 39 pre-task). All `source_type` values within `{oie_signal, oce_context, synthesis}`; all `trace_status` values within `{traced, coarse, pending}`. All 59 `field` paths confirmed unique. New `executive_actions[i].owner` entries correctly `synthesis`/`coarse` (fixed literal, invariant to evidence). New Priority/Assessment sub-element paths correctly `pending`.
- ENG-EX1-002 taxonomy fix reconfirmed: zero `"Add Company Input:"` strings in `executive_actions` or `recommended_actions` in this same run.
- `tsc --noEmit` and `eslint` clean on all 3 changed frontend files, before and after the hotfix.
- Hotfix logic traced against live data: `action.reason` = the bare string `"pending_executive_language"` → `pendingNote()`'s new first check matches it directly → `PendingOrText` renders the amber "Pending executive language" badge, not the raw literal. Confirmed via code trace against the actual captured value (no browser-automation tool available in this environment to capture a rendered screenshot — same limitation noted in the Sprint EX-1 Founder Review).
