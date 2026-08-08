# EFR-EBD-005 Engineering Feasibility Finding — Codex

**Author:** Codex, Senior AI Software Engineer, AI Engineering Team under EBD-002 §4.4.  
**Reviewer:** Engineering Reviewer #2.  
**Scope:** Engineering Feasibility Review for EBD-005 / CONFLICT-01 only.  
**Timestamp:** 2026-08-05T00:48:32.1067198+03:00.  
**Independence:** Verified. I did not search for, request, open, read, compare against, or infer from any previous engineering review or finding.

## Baseline

| Field | Evidence |
|---|---|
| Commit SHA reviewed | `26d5bab03cdad52a0d7febd34d6600bee742ce82` |
| Commit subject | `docs(execution): authorize EFR-EBD-005 governance obligation` |
| Commit date | `2026-08-01 20:10:50 +0300` |
| Required branch | `claude-safe-review` |
| Checkout state | Detached isolated worktree at pinned commit; `git branch --contains HEAD` showed `* (no branch)` and `+ claude-safe-review`; `git show -s --format='%H%n%D%n%s%n%ci' HEAD` showed `HEAD, origin/claude-safe-review, origin/HEAD, claude-safe-review` |
| Working-tree status | `git status --short --branch` output: `## HEAD (no branch)` |
| Isolated worktree | `C:\AIMX_PROJECTS\_codex_efr005_reviewer2` |

## Governing Evidence

Verified governance text:

- Constitution Article V.2: `docs/governance/NAWA_REASONING_CONSTITUTION_v1.md:204-208` says conflicts between institutional memory and current evidence are investigated, preserved, reasoned to best-supported current understanding, and the resolution with sources, basis, uncertainty, and provenance is appended.
- EBD-003 §12.3: `docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md:340-342` says current input is treated as current truth when memory and current input disagree.
- EBD-004 runtime contracts:
  - OCE consumes history from OME and current state, then emits Organizational Context: `docs/governance/EBD-004_ENGINE_DEFINITIONS.md:159-170`.
  - NCE Lite reasons over Truth Layer, Company Brain, Organizational Context, and NCO context: `docs/governance/EBD-004_ENGINE_DEFINITIONS.md:174-189`.
  - OME Foundation persists memory and exposes a queryable institutional memory surface: `docs/governance/EBD-004_ENGINE_DEFINITIONS.md:210-223`.
  - The cross-component invariant still repeats EBD-003 §12.3: `docs/governance/EBD-004_ENGINE_DEFINITIONS.md:229-234`.

## Inspected Runtime Evidence

E1 / OME source:

- `app/services/memory/repository.py:15-35` inserts `memory_events`.
- `app/services/memory/repository.py:37-75` fetches recent `memory_events`.
- `app/services/memory/repository.py:79-101` fetches one `memory_facts` row by `(company_id, fact_key)`.
- `app/services/memory/repository.py:104-335` upserts facts.
- `app/services/memory/repository.py:338-357` fetches facts.
- `app/services/memory/repository.py:360-389` builds a company profile from facts.
- `migrations/011_memory_tables.sql:3-14` defines append-capable `memory_events`.
- `migrations/011_memory_tables.sql:17-28` defines `memory_facts` with unique `(company_id, fact_key)`.

E2 / Conflict detection and resolution:

- Verified deterministic conflict branch in `MemoryRepository.upsert_fact`: `app/services/memory/repository.py:264` logs `"Fact conflict detected"`.
- Verified deterministic resolution in the same function: `app/services/memory/repository.py:274-299` replaces the stored fact if new confidence is greater than or equal to existing confidence; `app/services/memory/repository.py:306` keeps existing value if old confidence is greater.
- Unknown: no deterministic comparison was found between current CompanyInput Truth Layer and OME memory inside NCE Lite or OCE runtime reasoning.

E3 / Prompt and reasoning templates:

- `app/services/memory/memory_prompt.py:24-26` labels memory as hard facts that must be used if relevant.
- `app/services/memory/memory_prompt.py:55` says: `If memory conflicts with the user’s new info, flag it in truth_validation.contradictions.`
- `app/core/decision_prompt.py:78-85` treats company profile as source of truth and instructs logical resolution of contradictions into `truth_validation`.
- `app/services/openai_client.py:176` similarly instructs retrieved-file conflicts to be flagged in `truth_validation.contradictions`.

E4 / Runtime component read paths:

- Chat runtime loads memory events, facts, and profile through OME repository calls at `app/services/openai_client.py:991-1011`.
- Chat runtime injects decision context, memory facts, and memory events into model messages at `app/services/openai_client.py:1070-1088`.
- Decision Context uses memory inputs in trends and compact events at `app/services/decision_context.py:112-169`, `314-328`, and `383-390`.
- NCO Lite can store into OME through `app/nco/pipeline.py:427-495`; orchestration calls this at `app/nco/orchestrator.py:164-170`.

E5 / Schema and migrations:

- `memory_events` is append-capable and has `logic_json`, `context`, tags, idempotency, and `created_at`: `migrations/011_memory_tables.sql:3-14`.
- `memory_facts` has one row per `(company_id, fact_key)` by unique constraint: `migrations/011_memory_tables.sql:17-28`.
- No migration defines a first-class conflict table, supersession table, resolution record, source-weighing table, residual uncertainty field, or retrievable conflict state.

E6 / Contract mapping:

- OME Foundation owns persisted institutional memory. Storing event history in `memory_events` conforms to the OME storage role, but `memory_facts` replacement semantics conflict with OME's “never overrides current facts” invariant when used as current company truth without preserved conflict provenance.
- OCE is the contractually natural place to assemble current evidence plus memory, but inspected OCE implementation is local operational context and does not compare OME memory to current input.
- NCE Lite is the contractually natural place for reasoning toward best-supported understanding, but current NCO Lite `run_nce_lite` is a placeholder and chat reasoning is implemented in `AIService.chat` prompt assembly rather than a distinct NCE component.
- NCO Lite can enforce routing/rules but should not reason; therefore it should coordinate conflict handling, not own conflict adjudication.

E7 / Executed behavioral evidence:

- Executed an isolated fake-DB reproduction of `MemoryRepository.upsert_fact`.
- Case A: existing `primary_market=Jordan` confidence 40, new `primary_market=Iraq` confidence 80 resulted in final stored fact `Iraq`, execute count 1, with conflict warning.
- Case B: existing `primary_market=Jordan` confidence 90, new `primary_market=Iraq` confidence 50 resulted in final stored fact `Jordan`, execute count 0, with conflict warning.
- This demonstrates confidence precedence and possible replacement/retention, not chronological precedence alone. It also demonstrates absence of append-with-provenance for `memory_facts` conflicts.

E8 / Test inventory and coverage:

- `rg -n "memory|truth_validation|contradictions|conflict|upsert_fact|fetch_facts|fetch_recent_events|OME|Company Brain|institutional" tests app -S` found memory-related tests in `tests/test_decision_context.py` and `tests/test_rag_chat_integration.py`, but no test asserting memory-versus-current-evidence conflict detection, preservation, provenance, or retrievability.
- `tests/test_decision_context.py:45-76` and `tests/test_rag_chat_integration.py:22-34` use fake memory repos, including `upsert_fact`, but do not exercise conflicting fact values.

E9 / Provenance surface:

- `memory_events.logic_json` and `memory_events.context` can store provenance-like payloads, but there is no enforced schema for sources weighed, resolution basis, residual uncertainty, or conflict state.
- `memory_facts.source_event_id` can point to a source event, but `fetch_facts` and `get_fact_by_key` do not return enough source history to reconstruct weighed sources or prior conflicting values.

E10 / Epistemic category handling:

- The output JSON has `truth_validation.contradictions`, but no verified runtime representation of the five Article III.7 categories as typed data.
- No `evidence_conflict` state exists in code or schema. Verified absence by code search.

E11 / Conflict retrievability:

- `memory_events` can be retrieved as recent events, but conflicts are not recorded as first-class events by the fact conflict branch.
- `memory_facts` conflicts are not retrievable after replacement because the previous value is overwritten; when old value wins, the new conflicting value is not persisted.

## Verification Commands

Commands executed:

- `git worktree add --detach _codex_efr005_reviewer2 26d5bab03cdad52a0d7febd34d6600bee742ce82`
- `git rev-parse HEAD` -> `26d5bab03cdad52a0d7febd34d6600bee742ce82`
- `git branch --contains HEAD` -> detached HEAD plus `claude-safe-review`
- `git status --short --branch` -> `## HEAD (no branch)`
- Static searches with `rg` and `Select-String` over `app`, `tests`, `migrations`, and referenced governance files.
- Executed fake-DB behavioral reproduction of `MemoryRepository.upsert_fact`; results recorded in E7.
- `python -m pytest tests/test_decision_context.py tests/test_rag_chat_integration.py -q` -> `11 passed, 6 warnings in 8.58s`.
- `python -m pytest tests/test_decision_context.py tests/test_tenant_isolation.py tests/test_rag_chat_integration.py -q` -> `14 passed, 1 failed, 14 warnings`; failure was `test_valid_jwt_matching_company_id_succeeds`, returning 500 because `_get_company_repository` raised `503: Company service unavailable`. This does not evidence memory conflict behavior.

## Twelve Approved Questions

1. Where is conflict between institutional memory and current evidence detected or resolved today?

Verified: only in `MemoryRepository.upsert_fact` for durable facts, where different `fact_value` under same `(company_id, fact_key)` logs `"Fact conflict detected"` and chooses the stored value by confidence. Prompt-only conflict flagging exists in memory, decision, and RAG prompt blocks. Unknown: no verified deterministic runtime conflict comparison between OME memory and current Truth Layer inside OCE or NCE Lite.

2. Is automatic chronological precedence implemented in deterministic code, partially implemented, prompt-only, or documented-only?

Verified: deterministic fact resolution is confidence-based, not chronological-only. However, `fetch_recent_events` orders memory by `created_at DESC`, `memory_prompt` reverses for chronological readability, and prompts treat memory/profile as hard facts/source of truth. Prompt-only current-vs-memory conflict flagging exists. No deterministic Article V.2 investigation mechanism was found.

3. Which Runtime Components read from OME Foundation at runtime?

Verified implementation: chat `AIService` reads OME repository memory and injects it into reasoning messages. Decision Context consumes memory passed to it. NCO Lite writes OME events but does not normally read them. Contractually, OCE and NCE Lite should consume OME/history, but the inspected OCE service does not read OME directly and NCE Lite in NCO is a placeholder.

4. What would conflict detection require if not already present? Is comparison surface available today?

It would require a canonical comparison surface joining current CompanyInput/Truth Layer facts with OME facts/events by normalized entity, fact key, source, timestamp, confidence, and provenance. Partial surfaces exist: current chat message, unified capture metadata, memory facts, memory events, RAG chunks, and operational context. Missing is a typed, reusable comparison contract and durable conflict object.

5. What would recording the resolution require?

It requires at least a new OME conflict/resolution record type or schema extension that records: memory source IDs, current evidence source IDs, basis for weighting, selected current understanding, residual uncertainty, provenance, and link to prior records. `memory_events.logic_json/context` could host an MVP append-only record without migration, but reliable querying and third-party reproducibility likely require schema work.

6. Does OME currently overwrite records or append? What would append-not-substitute require?

Verified: `memory_events` appends; `memory_facts` overwrites or suppresses conflicting values because of unique `(company_id, fact_key)` and update statements. Append-not-substitute requires preserving prior and conflicting fact assertions as immutable assertions plus an appended resolution/supersession record, rather than mutating the single `fact_value`.

7. Where should this behavior live?

Recommended allocation: OME Foundation owns conflict/resolution persistence and retrievability; OCE assembles memory plus current evidence into the comparison surface; NCE Lite reasons to the best-supported current understanding; NCO Lite coordinates and enforces that required conflict handling occurred before downstream output. This is distributed responsibility within existing components. It does not require adding, removing, renaming, or reordering Runtime Components.

8. How should an `evidence_conflict` state be represented without creating a sixth epistemic category?

Represent it as a state or status on evidence assertions/resolution workflow, not an epistemic category. The underlying assertions remain Article III.7 categories such as Fact, Assumption, or NAWA Inference; `evidence_conflict` marks that sources disagree and that resolution/provenance is required. Current code only has `truth_validation.contradictions` arrays in output JSON; no durable state exists.

9. Which existing tests would change, and what new tests are required?

Existing tests to extend: `tests/test_decision_context.py`, `tests/test_rag_chat_integration.py`, and memory repository tests that should be added because none currently target `MemoryRepository.upsert_fact` conflict semantics. New tests required: conflict detection between memory facts and current extracted facts; no chronological-only deference; conflict preserved and retrievable; resolution record includes sources, basis, residual uncertainty, provenance; prior records preserved; NCE/NCO behavior when conflict exists; tenant isolation for conflict records.

10. What is implementation effort?

Sprint-scale if implemented correctly with durable schema, repository changes, prompt/runtime integration, tests, and migration. A thin prompt-only or `memory_events`-only MVP could be days, but it would likely not satisfy retrievability and provenance threshold T1-T6.

11. Does the work conflict with, depend on, or block Sprint EX-2? Does it require an OME data-model change, and does Sprint EX-2 use the same surfaces?

Assessment: Blocking — sequencing. Sprint EX-2 may be planned, but work touching OME memory facts/events, OCE context assembly, NCE reasoning, or NCO coordination should not start until refreeze/conformance scope is settled. Verified explicit statement: durable conformance likely requires an OME data-model change unless governance accepts a weaker `memory_events.logic_json` convention. Verified/inferred explicit statement: Sprint EX-2 appears likely to use the same OME/OCE/NCO surfaces, but its exact scope at the pinned commit is inactive and not fully evidenced; therefore specific collision details are partly Unknown.

12. What breaks if implemented now, and what breaks if deferred?

If implemented now: existing company-profile behavior may change because single-value `memory_facts` assumptions become assertion/history based; prompts and tests may need updates; any UI/API assuming one fact per key could break; migration risk exists. If deferred: CONFLICT-01 remains live; facts can be overwritten or conflicting input dropped; conflicts are not reliably retrievable; user-facing reasoning may silently resolve conflicts or rely on prompt-only behavior.

## D1 / D2 / D3 Analysis

D1 — automatic chronological deference versus investigation:

- Verified: fact storage resolution is confidence-based, not strictly chronological.
- Verified: prompt/runtime path does not implement deterministic investigation across memory and current evidence.
- Verified: prompt blocks ask the model to flag contradictions, but the runtime does not evidence source weighing or best-supported adjudication.
- Conclusion: partially present behavior but not conformant to Article V.2 as runtime evidence. D1 is not satisfied.

D2 — silent resolution versus conflict detection and preservation:

- Verified: fact conflicts are detected in deterministic code by same key/different value.
- Verified: the conflict branch logs but does not preserve the losing assertion or append a conflict record.
- Verified: prompt-level `truth_validation.contradictions` exists, but no durable conflict state or retrievability exists.
- Conclusion: conflict detection exists at one storage site and prompt instructions exist, but preservation/retrievability are insufficient. D2 is partially satisfied at detection only.

D3 — substitution or overwrite versus append-with-provenance:

- Verified: `memory_events` is append-only in normal inserts.
- Verified: `memory_facts` substitutes on equal/higher new confidence and suppresses lower-confidence new conflicting values.
- Verified: no resolution record captures sources weighed, basis, residual uncertainty, and provenance.
- Conclusion: D3 is not satisfied for fact memory conflicts.

## Constitutional Conformance Assessment

Article V.2 requires investigation, preservation, best-supported current understanding, recorded resolution basis/sources/uncertainty/provenance, and appended rather than substituted records. The runtime has fragments: prompt instructions for contradiction reporting, a deterministic fact conflict branch, appendable memory events, and model output `truth_validation.contradictions`. The runtime does not provide end-to-end executed evidence for Article V.2, durable conflict preservation, retrievability, or append-with-provenance for facts.

Classification is not based solely on prompt-only status. It rests on executed behavior (E7), schema evidence (E5), test coverage gaps (E8), provenance gaps (E9), and retrievability gaps (E11).

## Engineering Feasibility Assessment

Feasible within the existing nine Runtime Components. No new component, component removal, rename, or pipeline reorder is required. The correct implementation is distributed: OME for storage/retrieval, OCE for assembling conflict inputs, NCE for reasoning/adjudication, and NCO for coordination/enforcement. The largest engineering risk is changing `memory_facts` from mutable single-row profile storage into append-preserving assertion/resolution semantics without breaking existing profile and prompt flows.

## Final Engineering Classification

**Proposed classification: Partially conformant.**

Rationale: some conflict detection exists in deterministic storage code and prompt-level contradiction handling exists, but Article V.2 is not satisfied across D1, D2, and D3. “Already conformant” is unavailable because T1-T6 are not all evidenced. “Non-conformant” is too broad because a deterministic conflict detection branch and appendable memory event substrate do exist.

## Sprint EX-2 Blocking Assessment

**Blocking — sequencing.** Sprint EX-2 remains inactive. It may be planned, but work touching OME memory schema/repository, OCE context, NCE reasoning prompts/runtime, or NCO orchestration should wait for EBD-005/refreeze decisions. Durable conformance likely requires an OME data-model change. Sprint EX-2’s exact surface use is not canonically defined at this pinned commit; where it touches OME/OCE/NCE/NCO, collision risk is real.

## ENG-CONF-001 Disposition

Recommendation only: activate ENG-CONF-001 after required Founder authorization and scheduling, with evidenced scope limited to CONFLICT-01:

- Add durable conflict/resolution representation in OME.
- Preserve prior/current conflicting assertions append-only.
- Record sources weighed, basis, uncertainty, and provenance.
- Make conflicts retrievable.
- Integrate OCE/NCE/NCO responsibilities without changing the nine-component architecture.
- Add tests for D1, D2, and D3 behavior.

This recommendation does not authorize execution.

## Adjacent Findings

None recorded. I did not identify a separate Article VII.5 defect outside the memory-versus-current-evidence conflict path.

## Engineering Recommendations Only

1. Treat `evidence_conflict` as a status on evidence/resolution workflow, not a sixth epistemic category.
2. Avoid using mutable `memory_facts` as the authoritative historical record; convert or supplement it with immutable assertions and appended resolutions.
3. Keep the implementation within existing Runtime Components; do not escalate to Freeze v2.0 on component-structure grounds based on current evidence.
4. Require reproducible tests before claiming conformance.

## Signature

| Field | Value |
|---|---|
| Finding filed, timestamped, hashed, sealed | Filed and timestamped; SHA-256 recorded after file finalization |
| Path | `docs/execution/governance_obligations/EFR-EBD-005_FINDING_CODEX.md` |
| Commit SHA reviewed | `26d5bab03cdad52a0d7febd34d6600bee742ce82` |
| Branch | `claude-safe-review`; isolated checkout detached at pinned SHA |
| Isolated worktree confirmed; working-tree status recorded | Yes |
| All twelve approved questions answered | Yes |
| D1, D2, D3 assessed separately | Yes |
| Independence attested | Yes |
| §4.1 constraint observed | Yes |
| §7.1 threshold T1-T6 mapped | N/A; not proposing already conformant |
| Adjacent findings recorded separately, or none | None |
| Proposed conformance classification | Partially conformant |
| Date | 2026-08-05 |
| Signature | Engineering Reviewer #2 (Codex) |

--------------------------------------------------

SEALED

This report was produced independently.

No previous engineering review was consulted.

Engineering Reviewer #2 (Codex)

--------------------------------------------------
