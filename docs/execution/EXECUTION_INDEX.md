# EXECUTION INDEX — Project NAWA

**Read this first.** This is the top-level entry point for every AI Engineering Team member and every Executive Board contributor working execution.

For depth, follow the links below. For live team status, see `EXECUTION_BOARD.md`. For cross-Sprint institutional memory, see `SPRINT_HISTORY.md`.

---

## Retrospective Reconciliation Notice (2026-08-28; milestone status updated 2026-09-02)

M1–M8 engineering (plus a Post-M8 hardening commit) executed outside this tracker between 2026-08-09 and 2026-08-28. It is now reconciled: M1–M8 CLOSED, Post-M8 ReasoningReceipt hardening CLOSED, M1–M8 documentation reconciliation CLOSED (commit `71772e95`), Sprint EX-1 PAUSED pending explicit Founder reactivation, remote push checkpoint **COMPLETED and CLOSED as of commit `de81441089fc97c8403348e5aafbb4206ba3d761`** (verified identical between local `claude-safe-review` and live `origin/claude-safe-review` at that checkpoint — it includes the Deferred Architecture Pack v1.3, the M9 Architecture Contract through v1.6, M9 Slice 1 CLOSED, M9 Slice 2 CLOSED, and M9 Slice 3 CLOSED). Next engineering milestone: **M9 — Decision Execution Foundation — ACTIVE.** M9 Architecture Contract v1.6 is **FOUNDER ACCEPTED** at the closed remote checkpoint above. **M9 Slice 1 — Action Persistence Foundation is CLOSED and pushed** — migration 015 + domain models (checksum `aa427a0d363459b9391b66218967762ce0eddda0604c788c85e25ab7e9bb553a`); no repository, service, API, or frontend, per the contract's own Slice 1 scope — see task document [`m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md`](m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md). **M9 Slice 2 — Backend Service / API is CLOSED — REMOTE CHECKPOINT VERIFIED** at the checkpoint above: `ActionRepository`, `ActionService`, and the five `/actions` endpoints — see task document [`m9/M9_SLICE2_BACKEND_SERVICE_API.md`](m9/M9_SLICE2_BACKEND_SERVICE_API.md). **M9 Slice 3 — Frontend Golden Path is CLOSED — REMOTE CHECKPOINT VERIFIED** at the checkpoint above: the frontend Golden Path UI anchored to `ChatPanel.tsx` (no standalone Actions surface) plus the Founder-approved bounded read-only `GET /company/members` member source — see task document [`m9/M9_SLICE3_FRONTEND_GOLDEN_PATH.md`](m9/M9_SLICE3_FRONTEND_GOLDEN_PATH.md). **M9 Slice 4 — Golden Path E2E & Hardening is ACTIVE**, implemented and focused-tested, under independent review, **not yet committed**: a real-browser Playwright acceptance of the full Decision → Action → Assignment → Status → History loop (`frontend/e2e/m9-slice4-golden-path.spec.ts`), plus one hardening correction to `frontend/playwright.config.ts` (`workers: 1`, fixing a real E2E cross-file concurrency defect the new spec exposed against the existing M7 Golden A spec — no product/domain file touched). Every M9 final-acceptance checklist item is now proven; M9 closure is a candidate recommendation, not yet authorized — see task document [`m9/M9_SLICE4_GOLDEN_PATH_E2E_HARDENING.md`](m9/M9_SLICE4_GOLDEN_PATH_E2E_HARDENING.md). Local `claude-safe-review` HEAD equals the pushed checkpoint above — the Slice 4 work exists only as uncommitted working-tree changes, not yet staged or committed; live ahead/behind divergence is verified directly from Git at review time (`git rev-list --left-right --count HEAD...origin/claude-safe-review`), not persisted here as a numeric count. See [`M8_OME_RECONCILIATION.md`](M8_OME_RECONCILIATION.md) for the M1–M8 record and `docs/architecture/NAWA_M9_DECISION_EXECUTION_FOUNDATION_ARCHITECTURE_CONTRACT_v1.md` for the M9 contract.

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
