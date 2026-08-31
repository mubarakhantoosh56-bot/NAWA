# EXECUTION INDEX — Project NAWA

**Read this first.** This is the top-level entry point for every AI Engineering Team member and every Executive Board contributor working execution.

For depth, follow the links below. For live team status, see `EXECUTION_BOARD.md`. For cross-Sprint institutional memory, see `SPRINT_HISTORY.md`.

---

## Retrospective Reconciliation Notice (2026-08-28; milestone status updated 2026-08-31)

M1–M8 engineering (plus a Post-M8 hardening commit) executed outside this tracker between 2026-08-09 and 2026-08-28. It is now reconciled: M1–M8 CLOSED, Post-M8 ReasoningReceipt hardening CLOSED, M1–M8 documentation reconciliation CLOSED (commit `71772e95`), Sprint EX-1 PAUSED pending explicit Founder reactivation, remote push checkpoint **COMPLETED and CLOSED as of commit `4e1650e957f8c6d337ec43adef014aa9411aed17`** (verified identical between local `claude-safe-review` and live `origin/claude-safe-review`, divergence 0/0 — this checkpoint includes the Deferred Architecture Pack v1.3 and the M9 Architecture Contract through its v1.3 Founder-acceptance amendment). Next engineering milestone: **M9 — Decision Execution Foundation — ACTIVE.** M9 Architecture Contract v1.3 is **FOUNDER ACCEPTED** at the closed remote checkpoint above; a v1.4 status-only amendment (Slice 1 activation status) exists on disk, uncommitted. **M9 Slice 1 — Action Persistence Foundation is ACTIVE** (migration 015 + domain models implemented and corrected on disk, under independent review, pending commit; no repository, service, API, or frontend yet — see task document [`m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md`](m9/M9_SLICE1_ACTION_PERSISTENCE_FOUNDATION.md)). Slices 2–4 remain **PROPOSED — NOT ACTIVATED**. See [`M8_OME_RECONCILIATION.md`](M8_OME_RECONCILIATION.md) for the M1–M8 record and `docs/architecture/NAWA_M9_DECISION_EXECUTION_FOUNDATION_ARCHITECTURE_CONTRACT_v1.md` for the M9 contract.

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
