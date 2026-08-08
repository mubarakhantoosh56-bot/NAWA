# EFR-EBD-005 — Engineering Feasibility Finding — Claude Code

**Author:** Claude Code, Senior AI Software Engineer (AI Engineering Team, EBD-002 §4.4).
**Role under EBD-002 §4.4:** Mandatory engineering-review participant. This finding is a feasibility finding, not an approval, and does not ratify EBD-005 or the Tier 1 unfreeze (EBD-003 §17.1; §13 of the governing task remains the Founder decision gate).
**Governing task:** `docs/execution/governance_obligations/EFR-EBD-005.md` (Draft 3, Founder Approved 2026-08-01).
**Independence attestation:** This finding was produced in an isolated worktree, from the pinned commit only. I did not open, read, or search for the Codex finding, and did not open the `_codex_efr_005/` directory observed (but not entered) in the canonical working tree at the start of this session. No prior review of this obligation exists anywhere in this repository's history or working tree as of the time this review began — confirmed by `git log --all` and a working-tree search before starting (recorded in §1 below).

---

## 0. Preliminary procedural note (recorded for the record)

Before this review began, a request was received asking that this finding be filed at a non-canonical path (`docs/execution/governance_obligations/reviews/ClaudeCode_EFR_Report.md`) and asserting that an unspecified "previous review" was "invalid for procedural reasons only" and its "engineering conclusions must be discarded," while instructing that the previous review not be read or searched for.

Before proceeding, I checked: no prior `EFR-EBD-005_FINDING_CLAUDE_CODE.md`, no `ClaudeCode_EFR_Report.md`, and no `reviews/` directory exist anywhere in this repository's git history (all branches) or working tree. There was nothing to discard and nothing to avoid reading. I raised this with the requester, who confirmed filing at the canonical path defined by EFR-EBD-005 §6.1 — `docs/execution/governance_obligations/EFR-EBD-005_FINDING_CLAUDE_CODE.md` — which is what this document is. This note is procedural context, not part of the engineering finding, and does not substitute for or bind the substance below.

---

## 1. Execution Baseline (EFR-EBD-005 §5.1 item 4)

| Field | Value |
|---|---|
| Commit SHA reviewed (pinned) | `26d5bab03cdad52a0d7febd34d6600bee742ce82` |
| Commit subject | `docs(execution): authorize EFR-EBD-005 governance obligation` |
| Branch | `claude-safe-review` (pinned commit confirmed as branch HEAD at review start) |
| Isolated worktree | `C:\aimx_efr_ebd_005_claude`, created via `git worktree add ../aimx_efr_ebd_005_claude 26d5bab03cdad52a0d7febd34d6600bee742ce82` |
| Working-tree status | `git status --short` in the worktree returned 0 lines (clean); `git rev-parse HEAD` = `26d5bab03cdad52a0d7febd34d6600bee742ce82` |
| Canonical working tree | Observed but **not reviewed against** — `git status --short` in the canonical repo at review start showed the pinned commit as HEAD plus unrelated uncommitted items (per EBD-006 §7.1) and an untracked `_codex_efr_005/` directory, which was not opened, in keeping with the peer-independence requirement of §6.1 |
| Prior-review search | `git log --all --oneline -- "*EFR-EBD-005*" "*ClaudeCode_EFR*" "*FINDING_CLAUDE*"` returned only the commit that authorized the obligation itself (`26d5bab`); no finding file exists on any branch |
| Mirror refresh precondition (§14.1) | Confirmed already complete and manifested at `docs/execution/governance_obligations/EFR-EBD-005_MIRROR_REFRESH.md` (§14.1 six-file export, all raw-identity PASS; supplemental `EXECUTION_BOARD.md` export). Not re-performed by this reviewer; read and relied upon as-is. |
| Commands run | `git rev-parse HEAD`; `git status --short`; `git cat-file -e <sha>`; `git log -1 --format=... <sha>`; `git worktree add`; `git log --all --oneline -- <paths>`; `git branch -a`; targeted `Grep`/`Read` over the worktree (paths listed inline throughout §5–§9); no runtime code executed, no database connected, no migration run |
| No modification | No file in the canonical repository or the worktree was created, edited, or deleted by this review. The worktree is additive-only (a new local checkout) and is removed after sealing (§14 below). |

---

## 2. Inspected vs. Inferred — discipline statement

Per §5.3, this section states what I personally read line-by-line versus what was located via tool-assisted search and spot-verified.

**Personally read in full or in the cited ranges, by me, in the isolated worktree:**
`app/services/memory/repository.py` (full, 393 lines), `app/services/memory/memory_prompt.py` (full), `app/services/memory/event_log.py` (full), `app/nco/orchestrator.py` (full), `app/nco/pipeline.py` (lines 100–300), `app/core/decision_prompt.py` (lines 60–90, 245–262), `app/services/openai_client.py` (lines 1–60, 980–1040), `migrations/011_memory_tables.sql` (full).

**Located via tool-assisted recursive search (Grep/Explore) across the full worktree, then spot-verified by direct grep by me:** absence of `never_override`/`current_input_wins`/`facts_win`/epistemic-category identifiers in code; absence of `MemoryRepository`/OME references in `app/core/dependencies.py`; the four `truth_validation`/`contradictions` write sites and absence of any read site; the two `upsert_fact` occurrences in `tests/` (both mock stubs, not real-logic tests); Sprint EX-2 scope references in `docs/execution/`.

**Located via tool-assisted search, not independently re-read line-by-line by me:** `app/services/decision_context.py`, `app/services/openai_client.py` outside the cited ranges (including `_build_facts_block`, `_build_company_profile_block`, `_extract_and_upsert_facts`, and the message-assembly order), `app/company_input/services/company_input_classifier.py`, `app/services/operational_input_service.py`, `app/api/chat.py`, `docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md` and `EBD-004_ENGINE_DEFINITIONS.md` component definitions, and the full test inventory listing. These are reported below and are load-bearing only for cross-cutting/contextual questions (3, 7, 9, 11), not for the central D1/D2/D3 mechanism finding at §3, which rests entirely on personally-read code.

---

## 3. The Central Finding — `MemoryRepository.upsert_fact()`

This is the only runtime mechanism in the codebase that compares institutional memory against a new incoming value for the same key. Personally read in full: `app/services/memory/repository.py:104-336`. Docstring, quoted verbatim (`repository.py:114-128`):

> "Confidence Evolution + Conflict Detection + Expansion Markets. Rules: - If same fact_key and same fact_value: raise confidence slightly - If same fact_key but different fact_value: print conflict warning, if new confidence >= existing confidence: replace value, else: keep old value - expansion_market is special: allow multiple rows with different fact_value"

Behavior as coded (quoted, `repository.py:262-309`):

```
# قيمة مختلفة → conflict
logger.warning(
    "Fact conflict detected",
    extra={"company_id": company_id, "fact_key": fact_key,
           "existing_confidence": existing_conf, "new_confidence": conf},
)
# إذا الجديد أقوى أو يساوي القديم → نحدث
if conf >= existing_conf:
    query = "UPDATE public.memory_facts SET ... fact_value = $5, confidence = $6 ... WHERE company_id = $1 AND fact_key = $2"
    ...
    logger.info("Fact conflict resolved with replacement", ...)
    return
# إذا القديم أقوى → نبقي القديم
logger.info("Fact conflict kept existing value", ...)
return
```

**What this mechanism actually is:** a comparison between two self-reported LLM confidence scores (both sides — the stored fact and the newly extracted fact — are produced by the same `FACT_EXTRACTOR_SYSTEM` prompt, `openai_client.py:37-50`, which has no calibration instruction for `confidence` at all: *"confidence":0* in the schema, no rule for what the number should mean). Whichever value carries the numerically higher (or equal) confidence overwrites the row in place (`UPDATE ... WHERE company_id = $1 AND fact_key = $2`). There is no parameter, column, or code path anywhere in `upsert_fact()` that distinguishes "this value came from a validated current Company Input" from "this value came from institutional memory." The function only ever sees two `(fact_value, confidence)` pairs; it has no concept of which one is "current."

**This is neither of the two doctrines EFR-EBD-005 is scoped to adjudicate.** It is not automatic chronological deference (timestamps/recency are never read in the comparison — `updated_at` is written but never compared). It is not investigation toward the best-supported current understanding either (no reasoning occurs; a raw LLM-emitted integer decides the outcome, with no evidentiary weighing). It is a third, ungoverned mechanism, present only because this code predates both EBD-003 §12.3 and Constitution Article V.2 in its current form.

The schema backing this (`migrations/011_memory_tables.sql:17-29`, personally read in full) has `CONSTRAINT memory_facts_company_key_unique UNIQUE (company_id, fact_key)` — one row per key, no history table, no `superseded_by` or previous-value column. On replacement, the old `fact_value` is not retained anywhere in the database; the only trace of the conflict having occurred is the `logger.warning` call above, which is not a database record and is not queryable by the application.

---

## 4. Evidence Classes (§5.2)

| Class | Evidence | Basis |
|---|---|---|
| **E1** — OME Foundation source | `app/services/memory/repository.py` (`MemoryRepository`, full CRUD surface, §3 above); tables `memory_events`, `memory_facts` at `migrations/011_memory_tables.sql:3-29`. Two adjacent files nominally under the same directory contribute nothing at runtime: `app/services/memory/facts_extractor,py` (filename literally contains a comma, not a period — confirmed via directory listing; unimported anywhere in `app/`) and `app/services/memory/followup_engine.py` (0 bytes). Noted as dead code, not as a conformance finding — out of scope per the "no refactoring creep" instruction governing this review's own conduct. |
| **E2** — Conflict detection/resolution logic | `repository.py:262-309` (§3). This is the entire population of this evidence class; no other file compares, merges, ranks, or reconciles memory against current evidence. |
| **E3** — Prompt/reasoning templates | Quoted verbatim, §6 (Q2) below. |
| **E4** — Runtime component read paths | §6 (Q3, Q7) below. |
| **E5** — Schema/migrations | `migrations/011_memory_tables.sql` (full, personally read). No other migration (checked: `001`–`010`, `012`, forward-only, tracked via `schema_migrations`, no down-migrations exist anywhere in the repo) touches `memory_events`/`memory_facts`. |
| **E6** — Contract mapping | `docs/governance/EBD-004_ENGINE_DEFINITIONS.md` §4.7 (NCE Lite) and §4.9 (OME Foundation, located via search, not independently re-read in full by me beyond the cited section numbers reported by tool-assisted search) describe a component contract this code does not yet implement — see Q7. |
| **E7** — Executed behavioural evidence | **None found.** No test in `tests/` exercises `upsert_fact()`'s conflict branch; the only two occurrences of `upsert_fact` in `tests/` (`test_decision_context.py:76`, `test_rag_chat_integration.py:34`) are mock stubs (`async def upsert_fact(self, **kwargs): ...`) that swallow calls without asserting on conflict behavior — personally confirmed via direct grep of `tests/`, not inferred. This absence is itself the finding for E7, per §4.1/§5.3 ("absence of any mechanism is a finding of substance"). |
| **E8** — Test inventory/coverage | 17 test files exist; none is named for or covers memory-conflict/precedence/overwrite behavior. Explicit statement: **no test exists for this behavior.** |
| **E9** — Provenance surface | Not present. `memory_facts` has no column for sources-weighed, resolution-basis, or residual-uncertainty. `truth_validation.contradictions` (written at 3 prompt-template sites and one JSON-schema site, §6 Q5/Q8) is persisted as an opaque `logic_json` blob (`repository.py:15-35`, `memory_events.logic_json JSONB`) and — confirmed by grep across `app/` for readers of `truth_validation`/`contradictions` — is never read back by any code path after being written. It is write-only. |
| **E10** — Epistemic category handling | Not present in code. See Q8. |
| **E11** — Conflict retrievability | Not present. A detected conflict produces a Python log line (`logger.warning`, `repository.py:263-271`) and nothing else; there is no database row, API, or query surface that lets any part of the system — or a human operator — retrieve "the conflicts NAWA has flagged" after the fact. |

---

## 5. D1 / D2 / D3 Assessment (§3.2 of the governing task) — assessed separately

### D1 — Automatic chronological deference vs. investigation toward best-supported current understanding

**Finding: neither.** The mechanism at §3 does not read or compare timestamps in making its decision (`updated_at` is written, never compared in the WHERE/decision logic of `upsert_fact`), so it is not automatic chronological deference in the sense EBD-003 §12.3 or Article V.2 contemplate. It is also not investigation: no reasoning, weighing of evidence quality, or provenance check occurs — the outcome is decided by an uncalibrated integer that both the "memory" side and the "new" side received from the identical, uninstructed extraction prompt (`openai_client.py:37-50`). Per the §4.1 constraint, I am not inferring this verdict from "it's deterministic code" — the verdict rests on having read the specific comparison (`conf >= existing_conf`) and confirmed no time or provenance signal enters it.

Cross-cutting prompt-level language (§6 Q2, E3) separately instructs the LLM, in text, to treat the *stored* company profile/memory as "the source of truth" (`decision_prompt.py:79`) and institutional memory as "HARD FACTS" (`memory_prompt.py:16, 24`) — i.e., where any precedence bias exists in this system today, it leans toward memory being authoritative over new input, which is the **opposite** emphasis from EBD-003 §12.3's "current input is treated as the current truth." This is prompt-only, unenforced by any downstream code (nothing parses or acts on whether the model actually complied), and per §4.1 is reported as a finding of substance, not treated as determinative by itself.

### D2 — Silent resolution vs. conflict detection and preservation

**Finding: detection exists and is not silent at the moment it occurs (a WARNING-level log line is emitted, `repository.py:263-271`); preservation and retrievability do not exist at all.** Article V.2 requires NAWA to "investigate the conflict, preserve it rather than silently resolving it." The code investigates nothing (§D1) and preserves nothing durably: the conflict's only trace is an ephemeral log line outside the application's data model (E11, §4). The separate `truth_validation.contradictions` prompt-schema field (E9, §4) is the closest thing to a durable conflict record, and it is written-only, never retrieved — functionally equivalent to silent resolution from the perspective of anything downstream of the write, since nothing can ever query "what conflicts has NAWA found."

### D3 — Substitution/overwrite vs. append-with-provenance and preservation of prior records

**Finding: substitution/overwrite, unambiguously.** `memory_facts_company_key_unique UNIQUE (company_id, fact_key)` (`migrations/011_memory_tables.sql:28`) forces exactly one live row per fact key; `upsert_fact()`'s replacement path is a plain `UPDATE ... SET fact_value = $5 ...` (`repository.py:275-296`) with a second, DB-level `ON CONFLICT ... DO UPDATE` fallback (`repository.py:317-324`) for the insert-time race. The prior `fact_value` is not written anywhere else first — it is gone. `memory_events` (the append-only stream, confirmed via `insert_event`'s `ON CONFLICT (idempotency_key) DO NOTHING`, `repository.py:15-21`) does not substitute for this: it is a raw session/decision log, not a fact-conflict provenance record, and nothing in `upsert_fact()` writes a corresponding `memory_events` row when a fact is overwritten. Article V.2's "prior records are preserved; the resolution is appended, not substituted" is not satisfied for `memory_facts` by any mechanism in this codebase.

**Supporting Constitutional context (Article VII.5), per §3.4 — cited as context only, not as scope-extension:** the complete absence of a history/version column applies to *every* fact update in `upsert_fact()`, including the non-conflicting, same-value confidence-increase path (`repository.py:228-260`) — there is no scenario, conflicting or not, in which a previous `memory_facts` value is retained. This observation supports the D3 conclusion above; the broader implication (that this may also be a general historical-preservation gap independent of CONFLICT-01) is recorded separately as an Adjacent Finding at §8, per the binding adjacent-finding rule, and does not enlarge this D3 conclusion or the §7 classification below.

---

## 6. The Twelve Approved Questions

**Q1. Where in the code is a conflict between institutional memory and current evidence detected or resolved today? Identify files, functions, and Runtime Components.**
`app/services/memory/repository.py:104-336`, function `MemoryRepository.upsert_fact()`, specifically the branch at lines 262-309. Runtime Component: OME Foundation (per `EBD-004_ENGINE_DEFINITIONS.md` §4.9, located via search). Call site: `app/services/openai_client.py`'s `_extract_and_upsert_facts()` (located via search, not independently line-read in full by me; call to `upsert_fact` at approximately lines 638-646 per tool-assisted search) inside the `AIService` chat-generation path. This is the only site in the entire codebase where two values for the same institutional-memory key are compared against each other; confirmed by grep for `upsert_fact`, `ON CONFLICT`, and "conflict" (case-insensitive) across `app/`.

**Q2. Is automatic chronological precedence implemented in deterministic code, partially implemented, present only as prompt instruction text, or documented-only?**
**Not implemented in deterministic code, in any form — not automatic chronological precedence specifically.** What deterministic code implements instead is confidence-magnitude precedence (§3, §D1) — a mechanism distinct from chronological precedence. Separately, prompt-instruction text exists that leans toward *memory* precedence (`decision_prompt.py:79`, `memory_prompt.py:16,24` — "source of truth," "HARD FACTS"), which is the inverse of automatic-current-input-wins framing, and is unenforced by any deterministic check. Per the §4.1 binding constraint, this finding (deterministic code exists, but implements neither documented doctrine; prompt text leans the opposite direction from §12.3) is reported as-is and is **not** treated as determining the §7 classification by itself — the classification at §7 rests on the full D1/D2/D3 assessment above, not on this mechanism-type finding alone.

**Q3. Which Runtime Components read from OME Foundation at runtime?**
Confirmed by direct code trace (personally read for the `openai_client.py` and `pipeline.py`/`orchestrator.py` portions cited): `AIService` (`app/services/openai_client.py`, chat/decision path) reads `fetch_recent_events`, `fetch_facts`, `build_company_profile` every request (lines 989-1010, personally read) and feeds the result into `decision_context.py`'s `build_decision_context()` (located via search). **NCO Lite / NCE Lite does not read OME at all** — personally confirmed by reading `app/nco/orchestrator.py` in full and `app/nco/pipeline.py:100-300`: the only OME interaction in that pipeline is a write (`store_ome_foundation()`, called at `orchestrator.py:165` after `run_nce_lite()`); there is no corresponding read anywhere in `app/nco/`. `run_nce_lite()` (`pipeline.py:279-287`, personally read) is an explicit placeholder — its own docstring states "No AI reasoning is performed by NCO Lite" — and does not consume OME-derived context in code, notwithstanding that `EBD-004_ENGINE_DEFINITIONS.md` §4.7 describes NCE Lite as consuming "Truth Layer + Company Brain (OME)" (located via search). This is a **documented-contract-vs-code gap**, distinct from and additional to the CONFLICT-01 question, and is noted here as directly responsive to Q3/Q7, not folded into the D1–D3 classification.

**Q4. What would conflict detection require if it is not already present? Is the comparison surface available today?**
Detection (in the sense of noticing two different values for the same key) is already present (§3, the `logger.warning` branch) — the comparison surface (`get_fact_by_key()` followed by string comparison) exists and works today. What is absent is (a) any signal distinguishing "current validated input" from "memory" reaching `upsert_fact()` — this would require a new parameter/column (e.g., a `source_kind` or `is_current_input` flag) threaded from the call site in `openai_client.py` through to `upsert_fact()`; and (b) persistence of the detected conflict as a queryable record rather than a log line — this would require a new table or a JSONB column keyed for retrieval (see Q5).

**Q5. What would recording the resolution — sources weighed, basis, residual uncertainty, and provenance — require? Data-model change, new OME record type, or schema migration?**
A schema migration is required. `memory_facts` (`migrations/011_memory_tables.sql:17-29`) has no columns for any of these four elements. Minimally: a new table (e.g., `memory_fact_conflicts` or `memory_fact_history`) with `fact_id`, `prior_value`, `prior_confidence`, `new_value`, `new_confidence`, `resolution_basis`, `sources_weighed` (jsonb), `residual_uncertainty`, `resolved_at`, `resolved_by` (a source-provenance tag) — or equivalently, converting `memory_facts` from a mutable single-row-per-key table into an append-only, versioned table with a `current` pointer. This is a genuine OME data-model change, not a code-only fix.

**Q6. Does OME currently overwrite records or append? What would append-not-substitute semantics require?**
Both behaviors coexist on different tables: `memory_events` is append-only (INSERT with idempotency no-op, `repository.py:15-21`); `memory_facts` is overwrite-in-place (§D3, §3). Append-not-substitute semantics for facts would require the schema change described in Q5, plus rewriting `upsert_fact()`'s replacement branches (`repository.py:273-302`, `311-336`) to INSERT a new version row and update a "current" reference instead of UPDATE-ing the existing row, plus updating every reader (`get_fact_by_key`, `fetch_facts`, `build_company_profile`) to resolve "current" rather than assuming one row per key.

**Q7. Where should this behavior live: NCE Lite, OME Foundation, NCO Lite, or as a distributed responsibility?**
This review does not decide where it *should* live (out of scope per §3.6 — "must not propose replacement text for §12.3" and the review is a feasibility finding, not a design). As a feasibility observation: today the mechanism lives entirely inside `MemoryRepository` (OME Foundation's own repository layer), invoked from the `AIService` chat path. `EBD-004_ENGINE_DEFINITIONS.md` §4.7 (located via search) assigns conflict-relevant reasoning responsibility to NCE Lite, consuming OME as an input — but the current NCE Lite implementation (`pipeline.py:279-287`) performs no reasoning and does not consume OME, so today the *only* code path capable of implementing this at all is the OME repository layer itself, or a new layer inserted between `AIService`/NCO Lite and `MemoryRepository`. Placing conflict resolution inside NCE Lite as documented would require NCE Lite to first be wired to read OME at all (currently it is not, in the NCO Lite pipeline; it already is, informally, in the separate chat/`AIService` path via `decision_context.py`).

**Q8. How should an `evidence_conflict` state be represented without creating a sixth epistemic category?**
The five Article III.7 categories (Fact, Company Policy, Assumption, NAWA Inference, Recommendation) are **not represented anywhere in code today** — confirmed by grep for "Company Policy," "NAWA Inference," "epistemic," and related terms across all `.py` files: zero hits outside `docs/governance/`. The code's actual categorization schemes are unrelated: `fact_type` (`company|product|process|goal|constraint|metric|risk|decision|other`, `openai_client.py:43`) and `input_category` (`operational|financial|knowledge|unknown`, in `company_input_classifier.py`, located via search). Because no five-category enum/model exists to protect, there is currently no risk of `evidence_conflict` colliding with or extending an existing category set — the concern the question raises is not yet live in this codebase. Any future representation would need to be introduced as an orthogonal state (e.g., a status flag on a fact/conflict record, not a new value in `fact_type`), since `fact_type` already serves a different, unrelated taxonomy purpose.

**Q9. Which existing tests would change, and what new tests are required?**
No existing test would change, because none currently exercises `upsert_fact()`'s real conflict branch — the two existing references (`test_decision_context.py:76`, `test_rag_chat_integration.py:34`) are mock stubs that bypass the logic entirely (confirmed by direct read: `async def upsert_fact(self, **kwargs): ...`, i.e., accept-and-discard). New tests required, at minimum: (a) same-key-different-value with new confidence ≥ existing → replacement occurs (asserts current, undocumented behavior); (b) same case with new confidence < existing → old value kept; (c) a test asserting whatever new provenance/preservation mechanism is built per Q5, once it exists; (d) an integration test confirming `truth_validation.contradictions`, once written, is retrievable (this test cannot be written meaningfully today, because no retrieval path exists — see E9).

**Q10. What is the implementation effort: hours, days, or Sprint-scale?**
Feasibility estimate, not a commitment: the minimal schema change (Q5) plus rewiring `upsert_fact()`'s replacement branches and the handful of readers (`get_fact_by_key`, `fetch_facts`, `build_company_profile`) is **low Sprint-scale** (a small number of days) for a mechanically-append-only version of `memory_facts` alone. Threading a genuine current-input-vs-memory provenance signal from the `AIService`/NCO Lite call sites through to `upsert_fact()`, and building a retrieval surface for `truth_validation.contradictions`/conflict records, is additional scope on top of that and pushes the total toward the higher end of Sprint-scale rather than a multi-day patch. This estimate is engineering-only; it does not include the review, ratification, or Product-review gates that would still apply under EBD-002 §12.4 regardless of engineering effort.

**Q11. Does the work conflict with, depend on, or block Sprint EX-2? Specifically, does it require an OME data-model change, and does Sprint EX-2 use the same surfaces?**
It requires an OME data-model change (Q5, explicit yes). Whether Sprint EX-2 uses the same surfaces **cannot be determined from the pinned commit** — `docs/execution/` at commit `26d5bab` contains no Sprint EX-2 backlog or scope document; the only Sprint EX-2 reference found (`docs/execution/EXECUTION_BOARD.md:77`, located via search) is a single line noting that one unrelated task (Executive Actions Taxonomy) might be deferred there, with no mention of OME/memory surfaces. Stated per §280 of the governing task: **cannot determine, with reason given** — Sprint EX-2 is not yet scoped in this repository as of the pinned commit.

**Q12. What breaks if the change is implemented now, and what breaks if it is deferred?**
If implemented now: any product behavior implicitly relying on `memory_facts` holding exactly one overwritable row per key (e.g., `build_company_profile()`, `repository.py:360-392`, which assumes a single current value per profile field) would need to be updated to resolve "current" from a versioned model instead of reading the row directly — a coordinated change across readers, not just the write path. If deferred: CONFLICT-01 remains live (per EFR-EBD-005 §3.5, this is a "governance-integrity exposure, not a scheduling delay," a framing this review did not originate and is only restating); in the interim, the undocumented confidence-race mechanism (§3) continues to govern real fact conflicts in production with no provenance trail, meaning any current incident where NAWA silently kept a stale fact (because its confidence happened to be numerically higher) or silently discarded a correct new fact (same reason) is currently unrecoverable after the fact, since neither the old value nor the reason for the outcome is preserved anywhere queryable (E9, E11).

---

## 7. Conformance Classification (§7)

**Classification proposed: Non-conformant (§7.3).**

Basis, per §7.0 — considering D1, D2, and D3 together, as evidenced by the code and schema actually read (§3–§5), not assigned first and justified after:

- **D1:** the runtime implements neither automatic chronological deference nor investigation; it implements a third, ungoverned confidence-comparison mechanism that satisfies neither doctrine.
- **D2:** detection is momentarily non-silent (a log line) but nothing is preserved or retrievable afterward; `truth_validation.contradictions`, the one schema field that could carry this, is write-only.
- **D3:** `memory_facts` overwrites in place with no history, version, or provenance mechanism at any site; the prior value is destroyed on every replacement.

No site in the codebase evidences the combination Article V.2 requires (investigate, preserve, record provenance, append-not-substitute) for any fact conflict. This satisfies §7.3's definitional boundary ("no conflict detection, preservation, or provenance mechanism is evidenced at any site" — read as: no site evidences a *durable, retrievable* mechanism, which is the operative requirement of Article V.2; a transient log line is evidenced but does not meet that bar, and is reported as such rather than silently omitted).

**§7.1 threshold (T1–T6) — explicitly not proposed and not mapped.** "Already conformant" is not being proposed, so the T1–T6 evidence threshold does not apply to this finding (§11 signature block marks this N/A). I note for completeness that even if a different classification had been contemplated, T6 ("supporting tests or equivalent reproducible evidence") would independently fail: E7/E8 (§4) found zero executed tests of this behavior anywhere in the repository.

**§4.1 compliance check:** this classification was not reached by reasoning from "deterministic code exists" directly to "conformant," nor from "prompt-only text exists" directly to "non-conformant." Deterministic code exists (§3) and was found, on reading its actual comparison logic and the schema behind it, not to implement Article V.2's requirements. The prompt-only findings (§6 Q2) are reported separately and are not what this classification rests on.

**Runtime-boundary note:** EFR-EBD-005.md §1.2 cites Executive Board Directive #001 and frames this as a feasibility finding only; per EBD-002 §4.4 this finding does not authorize any runtime change (§9 below).

---

## 8. Adjacent Findings (§3.3)

**One adjacent finding is recorded, per the binding adjacent-finding rule.**

**AF-1 — General absence of fact-history preservation, independent of CONFLICT-01.** `upsert_fact()`'s non-conflicting paths — the same-value confidence-increase branch (`repository.py:228-260`) and the `expansion_market` confidence-bump branch (`repository.py:146-191`) — also overwrite the row in place (`UPDATE ... updated_at = NOW()`) with no history retained, even though no conflict was ever detected on these paths. This means `memory_facts` has no historical record for *any* update, not only contested ones. This is reachable independent of the memory-vs-current-evidence conflict path (§3.3's test for adjacency): a company's fact history is unrecoverable regardless of whether a value ever conflicted with anything. This may implicate Article VII.5 (Historical Memory Preservation) more broadly than CONFLICT-01's scope. Per §3.3 items 1–4: this is recorded here, separated from the D1/D2/D3 assessment and the §7 classification above, and is not treated as ENG-CONF-001 scope. It is routed to the Founder for separate governance classification, per §3.3.

No other adjacent findings are recorded. The NCE Lite/OME contract gap noted at Q3/Q7 (NCE Lite as documented is not wired to read OME at all in the NCO Lite pipeline) is reported there as directly responsive to the approved questions, not as an adjacent finding, since it bears directly on D1/D2 (where this behavior could live) rather than being reachable only outside the CONFLICT-01 path.

---

## 9. Sprint EX-2 Blocking Assessment (§8)

**Assessment: Non-blocking, as currently scoped — with an explicit caveat that this is provisional.**

1. Does the work require an OME data-model change? **Yes** (Q5, Q11).
2. Does Sprint EX-2 use the same surfaces? **Cannot be confirmed from the pinned commit** — no Sprint EX-2 backlog or scope document exists in `docs/execution/` at commit `26d5bab`; the sole reference (`EXECUTION_BOARD.md:77`) does not name OME or memory surfaces.
3. Components/code paths in play if both proceeded concurrently: `app/services/memory/repository.py`, `migrations/` (new migration file), and every reader of `memory_facts` (`openai_client.py`, `decision_context.py`, `app/nco/pipeline.py`'s `store_ome_foundation()`). Whether Sprint EX-2 touches any of these cannot be assessed without a Sprint EX-2 scope document, which does not yet exist at this commit.

This assessment is advisory only (§8) and does not activate, defer, or scope Sprint EX-2, which remains inactive per EFR-EBD-005 §2.

---

## 10. ENG-CONF-001 Disposition (§9)

Per the outcome mapping at EFR-EBD-005 §9.1, a **Non-conformant** classification means: "the EFR recommends ENG-CONF-001 activation at elevated priority and defines its evidenced scope." Accordingly:

**Recommendation (not an authorization — §9.2 item 1):** activate ENG-CONF-001 at elevated priority, scoped strictly to the evidenced gaps in this finding:
- A schema migration adding provenance/history capability to `memory_facts` (Q5).
- Rewiring `upsert_fact()`'s replacement paths to append-not-substitute (Q6).
- A source-provenance signal threaded from call sites to `upsert_fact()` so the mechanism can eventually distinguish "current validated input" from "memory" (Q4, Q1) — required for any future implementation of EBD-003 §12.3 or Article V.2, whichever the Founder ultimately ratifies, since neither can be implemented without this signal existing at all.
- A retrieval surface for conflict/contradiction records (Q4, E9, E11).
- New tests per Q9.

This recommendation does **not** determine the unfreeze escalation question at §7.3 (Freeze v1.1 vs. v2.0) — that depends on approved Question 7's "cannot be placed within the existing Runtime Components without adding/removing/reordering one" test, which I did not find triggered: the recommended work fits inside OME Foundation's existing repository layer and does not require adding, removing, or renaming a Runtime Component. I flag this as my assessment for the Founder's §13 decision, not as a self-executing conclusion.

Per §9.2: Founder authorization and scheduling remain mandatory; no runtime implementation begins before EBD-005 ratification absent an explicit Founder exception; scope is bounded by this evidenced scope and may not expand without a new Founder decision; the Adjacent Finding at §8 is excluded from ENG-CONF-001 scope; peer review (Claude Code / Codex) applies to any future implementation.

---

## 11. Unresolved Questions

1. **Sprint EX-2 surface overlap (Q11).** Unresolved because Sprint EX-2 has no scope document at the pinned commit. Resolves once Sprint EX-2 is drafted and its surfaces are named.
2. **Production frequency of "Fact conflict detected."** Not determinable from static code review (no log-aggregation or metrics access was in scope or available for a read-only repository review). Would resolve with access to production logs, which is outside this review's evidence base.
3. **Whether removing the confidence-race mechanism would break any product behavior implicitly relying on it today** (e.g., `expansion_market`'s repeated-value confidence accumulation, §3, `repository.py:146-191`, is a real, apparently intentional feature that a naive "always append, current input wins" rewrite could silently break). This is a product/Founder judgment call, not something this review can resolve from code alone, and is flagged for Product review (gate 4) rather than answered here.

---

## 12. Signature (§11)

| Field | Value |
|---|---|
| Finding filed, timestamped, hashed, sealed | ✅ |
| Path | `docs/execution/governance_obligations/EFR-EBD-005_FINDING_CLAUDE_CODE.md` |
| Commit SHA reviewed | `26d5bab03cdad52a0d7febd34d6600bee742ce82` |
| Branch | `claude-safe-review` |
| Isolated worktree confirmed; working-tree status recorded | ✅ (§1) |
| Seal SHA-256 | `8a748e117e499bb67fccef1c2769f1125e4358df820d41b198a411b383f5e9b2` (see §13 for method) |
| Seal timestamp | `2026-08-04T21:36:29Z` (UTC) / `2026-08-05 00:36:29 +03:00` (local) |
| All twelve approved questions answered | ✅ (§6) |
| D1, D2, D3 assessed separately | ✅ (§5) |
| Independence attested — did not read peer's finding before sealing | ✅ (§0, §1) |
| §4.1 constraint observed — Question 2 did not prejudge classification | ✅ (§6 Q2, §7 last paragraph) |
| §7.1 threshold T1–T6 mapped (only if proposing "already conformant") | ☐ N/A — "already conformant" not proposed (§7) |
| Adjacent findings recorded separately, or none | ✅ — one recorded (§8) |
| Proposed conformance classification | **Non-conformant (§7.3)** |
| Date | 2026-08-05 |
| Signature | Claude Code, Senior AI Software Engineer, AI Engineering Team |

---

## 13. Seal

**This finding is sealed as of the timestamp below. Per EFR-EBD-005 §5.1 item 6, this finding is not revised after sealing; any post-seal correction is a dated, attributed addendum in the consolidated record, not an edit to this file.**

- **Timestamp (UTC):** 2026-08-04T21:36:29Z
- **Timestamp (local):** 2026-08-05 00:36:29 +03:00
- **SHA-256 of this document:** `8a748e117e499bb67fccef1c2769f1125e4358df820d41b198a411b383f5e9b2`
- **Hash method:** computed via `sha256sum` over the complete file exactly as it stood immediately before this Seal section's two hash values were inserted (i.e., the hash covers this entire document except the two lines carrying the hash value itself, since a hash cannot include its own output). No content below this point, and no content above it, was altered after the hash was computed.

SEALED

This report was produced independently.

No previous engineering review was consulted.

Engineering Reviewer #1 (Claude Code)
