# EXECUTION INDEX — Project NAWA

**Read this first.** This is the top-level entry point for every AI Engineering Team member and every Executive Board contributor working execution.

For depth, follow the links below. For live team status, see `EXECUTION_BOARD.md`. For cross-Sprint institutional memory, see `SPRINT_HISTORY.md`.

---

## Retrospective Reconciliation Notice (2026-08-28; milestone status updated 2026-09-03)

M1–M8 engineering (plus a Post-M8 hardening commit) executed outside this tracker between 2026-08-09 and 2026-08-28. It is now reconciled: M1–M8 CLOSED, Post-M8 ReasoningReceipt hardening CLOSED, M1–M8 documentation reconciliation CLOSED (commit `71772e95`), Sprint EX-1 PAUSED pending explicit Founder reactivation. **M9 — Decision Execution Foundation is CLOSED.** Final governance closure commit `acebd7720b1aa6294dffc549185e0d9d7cac1715` (parent: the final M9 engineering checkpoint `4a0c578e75b0d91890cbcb264326765045ff069a`), both remotely verified identical between local `claude-safe-review` and live `origin/claude-safe-review`. M9 Architecture Contract v1.7 is **FOUNDER ACCEPTED**. **M9 Slice 1 — Action Persistence Foundation is CLOSED** — migration 015 + domain models (checksum `aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a`); no repository, service, API, or frontend, per the contract's own Slice 1 scope — see task document [`m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md`](m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md). **M9 Slice 2 — Backend Service / API is CLOSED — REMOTE CHECKPOINT VERIFIED**: `ActionRepository`, `ActionService`, and the five `/actions` endpoints — see task document [`m9/M9_SLICE2_BACKEND_SERVICE_API.md`](m9/M9_SLICE2_BACKEND_SERVICE_API.md). **M9 Slice 3 — Frontend Golden Path is CLOSED — REMOTE CHECKPOINT VERIFIED**: the frontend Golden Path UI anchored to `ChatPanel.tsx` (no standalone Actions surface) plus the Founder-approved bounded read-only `GET /company/members` member source — see task document [`m9/M9_SLICE3_FRONTEND_GOLDEN_PATH.md`](m9/M9_SLICE3_FRONTEND_GOLDEN_PATH.md). **M9 Slice 4 — Golden Path E2E & Hardening is CLOSED — REMOTE CHECKPOINT VERIFIED**: a real-browser Playwright acceptance of the full Decision → Action → Assignment → Status → History loop (`frontend/e2e/m9-slice4-golden-path.spec.ts`), plus one E2E-infrastructure-only hardening correction to `frontend/playwright.config.ts` (`workers: 1`, fixing a real cross-file concurrency defect the new spec exposed against the existing M7 Golden A spec — no product/domain file touched) — see task document [`m9/M9_SLICE4_GOLDEN_PATH_E2E_HARDENING.md`](m9/M9_SLICE4_GOLDEN_PATH_E2E_HARDENING.md). M9 final acceptance (criteria A–AH) is `ALL PROVEN`. M9's closure does not activate Track A, Track B, or any post-M9 milestone — **post-M9 engineering feature expansion remains NOT ACTIVATED**; each would require its own separate, explicit future Founder decision and task document. Live ahead/behind divergence beyond the current checkpoint is verified directly from Git at review time (`git rev-list --left-right --count HEAD...origin/claude-safe-review`), not persisted here as a numeric count. See [`M8_OME_RECONCILIATION.md`](M8_OME_RECONCILIATION.md) for the M1–M8 record and `docs/architecture/NAWA_M9_DECISION_EXECUTION_FOUNDATION_ARCHITECTURE_CONTRACT_v1.md` for the M9 contract.

**PV1 — Jannat Al-Firdaws Real-Company Pilot Validation is ACTIVE.** Founder-activated immediately following M9's closure — this is the first post-M9 phase, validating the closed M9 technical MVP against a real company, real operational files, and real Company Brain content. It is explicitly **not** M10 and not a feature-expansion milestone. **PV1 Slice 1 — Pilot Baseline + Acceptance Contract: CLOSED — REMOTE CHECKPOINT VERIFIED** (commit `12b4f0d55436e0018455582db673c236924879fb`) — real-architecture discovery, real pilot-data inventory (re-verified directly against the filesystem at 14 real files), Company Brain coverage with two Founder pilot rules recorded (static pilot source isolation; numeric threshold discipline), an acceptance model/gate matrix (A–AK), and a proposed PV1 Slice 2–5 sequence — see task document [`pilot/PV1_JANNAT_REAL_COMPANY_VALIDATION.md`](pilot/PV1_JANNAT_REAL_COMPANY_VALIDATION.md). **PV1 Slice 2 — Real Data Ingestion Validation: CLOSED — REMOTE CHECKPOINT VERIFIED** (checkpoint `a461adda91083dd7131f09ab64e7882914da4944`). Real ingestion evidence gathered against all 6 real poultry files and the real feed-mill file (zero validation failures, zero source alteration, static-source isolation proven, provenance traced end-to-end, real upload-routing evidence gathered alongside direct-parser evidence); four real, non-pilot-blocking defects documented and explicitly not fixed — a short-header feed-field semantic mapping gap affecting 3 of 6 real files, a cross-upload non-deduplication gap (proven against a real Jannat workbook), and two live-upload-routing gaps (the real company-aggregate poultry file and the real feed-mill file are both silently skipped by the live upload route today) — see task document [`pilot/PV1_SLICE2_REAL_DATA_INGESTION_VALIDATION.md`](pilot/PV1_SLICE2_REAL_DATA_INGESTION_VALIDATION.md). **PV1 Slice 3 — Real Operational Reasoning Validation: ACTIVE — FOUNDER BLOCKER REVIEW** (not complete, not closed). All four scenarios were run as real chat conversations through the real, unmodified `POST /ai/chat` HTTP route against the real Jannat tenant (in-process ASGI over the real FastAPI app, real OpenAI calls, real local Postgres) — never a direct parser/service substitute. A Founder-directed blocker reconciliation has since re-derived every material claim from code, saved response and debug artifacts, and direct read-only database queries; it corrected three first-pass claims and raised two further defects. **Six real, reproducible defects, none fixed:** **DEFECT-005** — upload classification depends on the file's *storage path*, not its filename (the repository directory `poultry_operations` supplies the decisive `poultry` token that an opaque OS temporary upload path cannot), so 4 of 5 real hall/report files fail structured routing at 0.62 through the real HTTP upload path; **DEFECT-006** — a legacy marketing-shaped execution-structure validator failed closed on 19 of 23 real chat attempts (82.6%, HTTP 500 with no CEO-visible output, receipt or explainability) and passes only responses containing **no** structured recommendations — all four successful runs returned entirely empty `solution_generator` and `execution_engine`; **DEFECT-007** — an Institutional Facts write-back loop persisted a claim fabricated in Scenario 4 as two `conf:80` company truths and reproduced it verbatim in public explainability with zero citations at a "high" confidence band; **DEFECT-008** — Founder Pilot Rule 1's isolation flag gates 1 of 11 real evidence channels, 8 ungated and 5 confirmed leaking; **DEFECT-009** — the CEO company-wide workspace receives Dairtna operational Truth Context but is denied Dairtna Company Brain policy; **DEFECT-010** — the Dairtna mortality guardrails are prompt-only and unenforced, and the product's own enforcement layer coerced their violation. No scenario scored PROVEN (Scenario 1 BLOCKED BY PRODUCT DEFECT at 0 of 7 attempts; Scenarios 2 and 4 NOT PROVEN; Scenario 3 PARTIAL). A **SLICE 2 EVIDENCE CLARIFICATION** is recorded in Slice 3: Slice 2 did invoke the real downstream production upload helper, but supplied the repository path as `source_path`, so its 5/6 live-routing claim was materially overstated for the complete user-facing HTTP path, where the real figure is 1/6 — the closed Slice 2 checkpoint is not reopened or rewritten. See task document [`pilot/PV1_SLICE3_REAL_OPERATIONAL_REASONING_VALIDATION.md`](pilot/PV1_SLICE3_REAL_OPERATIONAL_REASONING_VALIDATION.md). **PV1 Slices 4–5 remain PROPOSED — NOT ACTIVATED**, each requiring its own separate, explicit Founder activation; Slice 4 is assessed **NOT READY** and must not be activated before Founder review of DEFECT-005 through DEFECT-010 — its input precondition does not currently exist, since no successful response this Slice contained a single machine-readable action.

---

## Active Sprint

**Sprint EX-1 — Executive Decision Support.** (PAUSED — see Retrospective Reconciliation Notice above. Content below is the preserved historical record.)

Goal: Transform NAWA's Executive Brief into a true Executive Decision Support document.

## Sprint Status

🟡 PAUSED (started 2026-07-08; requires explicit Founder reactivation).

## Active Engineering Tasks

| ID | Task | Priority | Status | Doc |
|---|---|---|---|---|
| ENG-EX1-000 | Executive Intelligence Baseline Capture | P0 | ✅ Complete | [ENG-EX1-000.md](sprint_ex1/ENG-EX1-000.md) |
| ENG-EX1-001 | Executive Intelligence Analysis | P0 | ✅ Approved | [ENG-EX1-001.md](sprint_ex1/ENG-EX1-001.md) |
| ENG-EX1-002 | Executive Brief v2 Foundation | P0 | 🟡 Complete, pending Founder/Aboura review | [ENG-EX1-002.md](sprint_ex1/ENG-EX1-002.md) |
| ENG-EX1-003 | Statement Traceability Instrumentation | P1 | ⚪ Upcoming | [ENG-EX1-003.md](sprint_ex1/ENG-EX1-003.md) |

## Completed Tasks

- ENG-EX1-000 — Executive Intelligence Baseline Capture (2026-07-09)
- ENG-EX1-001 — Executive Intelligence Analysis (2026-07-10, Founder-approved)
- ENG-EX1-002 — Executive Brief v2 Foundation (2026-07-10, pending Founder/Aboura review; live-browser/DB verification still open — no local Postgres reachable in dev sandbox)

## Blocked Tasks

None.

## Upcoming Tasks

ENG-EX1-001, ENG-EX1-002, ENG-EX1-003 (in order of expected start; parallelism where feasible per Sprint EX-1 charter).

## Current Milestone

**Days 1–3.** Aboura design front-load: Executive Brief Experience, Executive Assessment, Business Impact Framework, Executive Actions Taxonomy, Executive Brief Design Principles. Engineering runs ENG-EX1-000 (Baseline Capture) then begins ENG-EX1-001 (Analysis) and ENG-EX1-002 (v2 Foundation).

## Next Milestone

**Mid-Sprint (Day 5–6).** Informal Founder draft review on real Jannat Al-Firdaws data. First end-to-end brief under the eight-section structure available for review.

## Sprint Folders

- [Sprint EX-1](sprint_ex1/) — paused (historical record preserved)
- Future Sprint folders will appear here as `sprint_exN/`

## Cross-Cutting Documents

- [EXECUTION_BOARD.md](EXECUTION_BOARD.md) — live team dashboard, ownership rules, risks, blockers, Founder decisions
- [SPRINT_HISTORY.md](SPRINT_HISTORY.md) — cross-Sprint institutional memory
- [backlog/](backlog/) — items outside MVP awaiting Founder promotion
- [M8_OME_RECONCILIATION.md](M8_OME_RECONCILIATION.md) — retrospective execution reconciliation record; type: retrospective execution reconciliation; status: current / closed checkpoint record
