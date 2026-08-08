# EFR-EBD-005 — Final Neutral Comparison

**Document type:** Neutral comparison of two sealed independent engineering findings. Not an engineering review.
**Prepared by:** COWORK, acting as comparator under EFR-EBD-005 §12 procedural custody.
**Prepared:** 2026-08-07.
**Governing task:** `docs/execution/governance_obligations/EFR-EBD-005.md` (Draft 3, Founder Approved 2026-08-01).

**Sources used — these three only:**

| Designation | Reviewer | Sealed finding | Custody addendum |
|---|---|---|---|
| Engineering Reviewer #1 | **Claude Code**, Senior AI Software Engineer, AI Engineering Team (EBD-002 §4.4) | `EFR-EBD-005_FINDING_CLAUDE_CODE.md` | `EFR-EBD-005_FINDING_CLAUDE_CODE_SEAL.md` |
| Engineering Reviewer #2 | **Codex**, Senior AI Software Engineer, AI Engineering Team (EBD-002 §4.4) | `EFR-EBD-005_FINDING_CODEX.md` | `EFR-EBD-005_FINDING_CODEX_SEAL.md` |

**Excluded by Founder ruling:** `ARCHIVE_EFR_Comparison_Report_PREVIOUS.md.md` is **superseded**. It was not read, and none of its attributions were used. Readers are cautioned that its reviewer attributions are the inverse of the two sealed signature blocks verified below.

> **Scope limits observed.** No runtime code was inspected. No third engineering review was performed. No new technical conclusion was introduced. Neither finding nor either addendum was modified. No disagreement was resolved by comparator judgment. Every technical statement below is a restatement of, or citation to, one of the two sealed findings, attributed to its author.

---

## 1. Custody and Preflight Result

**Result: ALL CHECKS PASS.** Two items are recorded as custody notes under Founder ruling point 5; neither is a failure.

### 1.1 Authoritative hash verification (Founder ruling points 1 and 5)

The raw whole-file SHA-256 recorded in each companion addendum is the authoritative file-identity hash. Computed independently against the mirror copies:

| Report | Computed raw SHA-256 | Addendum-recorded value | Match |
|---|---|---|---|
| `…FINDING_CLAUDE_CODE.md` | `f80a39627a9b2ee2952470bd72b682acc87ed71b8f009811d3403f3682a88f87` | `f80a39627a9b2ee2952470bd72b682acc87ed71b8f009811d3403f3682a88f87` | ✅ **exact** |
| `…FINDING_CODEX.md` | `8e46bb4041cb63858e76e8f6f9b562a3c200b21bbc688ec77d3c0fdd82b88576` | `8E46BB4041CB63858E76E8F6F9B562A3C200B21BBC688EC77D3C0FDD82B88576` | ✅ **exact** (case-insensitive hex) |

Both sealed findings are byte-identical to the documents their reviewers hashed at custody time.

### 1.2 Identity, baseline, and independence

| Check | Claude Code | Codex |
|---|---|---|
| File exists and is readable | ✅ | ✅ |
| `SEALED` declaration present | ✅ §13, line 259 | ✅ line 257 |
| Reviewer identity present | ✅ Claude Code, Sr. AI SWE (EBD-002 §4.4); Engineering Reviewer #1 | ✅ Codex, Sr. AI SWE (EBD-002 §4.4); Engineering Reviewer #2 |
| Reviewed commit recorded in body | ✅ `26d5bab0…2ce82` (§1, §12) | ✅ `26d5bab0…2ce82` (Baseline, Signature) |
| Reviewed commit recorded in addendum | ✅ `26d5bab0…2ce82` | ✅ `26d5bab0…2ce82` |
| Byte size — addendum vs. actual | 39,554 / 39,554 ✅ | 21,938 / 21,938 ✅ |
| Line count — addendum vs. actual | 265 / 265 ✅ | 175 / 265 — see **CN-1** |
| Seal timestamp | `2026-08-04T21:36:29Z` (body §13) | `2026-08-04T22:51:55.3623810Z` (addendum) |
| Independence declaration | ✅ body §0/§1/§12; addendum §3 | ✅ body line 7, Signature; addendum |
| Peer finding read before sealing | **No** — addendum §2.3: Codex finding "not opened, read, or inspected" | **No** — addendum: "Claude Code finding read or inspected: No" |
| Isolated worktree | `C:\aimx_efr_ebd_005_claude` (removed post-seal) | `C:\AIMX_PROJECTS\_codex_efr005_reviewer2` |

### 1.3 Pinned commit confirmation (Founder ruling point 3)

**Both reports reviewed `26d5bab03cdad52a0d7febd34d6600bee742ce82`.** ✅ Confirmed in four independent places: each report body and each companion addendum. Both record commit subject `docs(execution): authorize EFR-EBD-005 governance obligation` and branch `claude-safe-review`.

### 1.4 Custody notes (recorded, not adjudicated)

**CN-1 — Codex line count reconciles to a counting convention.** The Codex addendum records 175 lines; `wc -l` returns 265. 175 is exactly the count of **non-blank** lines in the file (`grep -cve '^[[:space:]]*$'` = 175). The discrepancy is a metric-definition difference, not a content difference. The authoritative raw hash matches exactly, which establishes byte-identity independently of any line-counting convention. Recorded for completeness.

**CN-2 — Claude Code's internal pre-image hash is not reproducible, by design.** The report body §13 records `8a748e11…83f5e9b2`. Recomputation attempts: raw file `f80a3962…`; both hash-bearing lines removed `583623b2…`. Neither reproduces the internal value. The Claude Code addendum §3 states this is expected and by construction — the internal hash is a pre-image digest of an intermediate editing state that excludes its own output, and "is not a hash of any file that has ever existed in finished form." Per Founder ruling point 5, the raw addendum hash supersedes it for custody purposes. Recorded as an unreconciled historical internal hash; **no determination of tampering is made or implied.**

**CN-3 — Mirror path treated as custody-copy location (Founder ruling point 4).** Both signature blocks record the filing path as `docs/execution/governance_obligations/EFR-EBD-005_FINDING_<REVIEWER>.md`; both files currently reside in the `reviews/` subdirectory. The proviso in ruling point 4 is satisfied — raw hashes match the addenda — so the path difference is treated as a custody-copy location, not a filing-path defect.

**CN-4 — Anomaly reported by Claude Code's addendum, outside this mirror.** Addendum §2.2 records a non-matching file in the canonical repository at `docs/execution/governance_obligations/ARCHIVE_EFR-EBD-005_FINDING_CLAUDE_CODE.md` (hash `90f3e80c…`, 30,833 bytes, 270 lines, internal seal timestamp `2026-08-04T20:25:05Z`, internal seal hash `871b40a7…`). Claude Code states: "I am not treating this file as the sealed finding, a valid copy of it, or my work product." That file is **not present in this Cowork mirror** and was not read. Carried forward verbatim as a Founder-attention item (see F9).

---

## 2. Agreements

Points where both sealed findings independently reach the same conclusion.

| # | Agreed point | Claude Code citation | Codex citation |
|---|---|---|---|
| A1 | Deterministic conflict detection exists at exactly one site — `MemoryRepository.upsert_fact()`, logging `"Fact conflict detected"` | `repository.py:262-309`, §3, Q1 | `repository.py:264`, E2, Q1 |
| A2 | Resolution at that site is **confidence-based, not chronological** | §3, D1, Q2 | E2, Q2, D1 |
| A3 | `memory_events` is append-only / append-capable | `repository.py:15-21` (`ON CONFLICT (idempotency_key) DO NOTHING`) | `migrations/011_memory_tables.sql:3-14`, D3 |
| A4 | `memory_facts` substitutes in place via `UPDATE` / `ON CONFLICT … DO UPDATE` | `repository.py:275-296`, `317-324` | `repository.py:274-299`, Q6 |
| A5 | `UNIQUE (company_id, fact_key)` structurally forces one live row per key | `migrations/011_memory_tables.sql:28` | `migrations/011_memory_tables.sql:17-28` |
| A6 | The schema records no resolution basis, sources weighed, residual uncertainty, or prior value | E9, Q5 | E5, E9, Q5 |
| A7 | All other contradiction handling is **prompt-instruction text** routed to `truth_validation.contradictions` | E3, Q2, `decision_prompt.py:79`, `memory_prompt.py:16,24` | E3, `memory_prompt.py:55`, `decision_prompt.py:78-85`, `openai_client.py:176` |
| A8 | Conflicts are **not retrievable** after the fact | E11 — "a Python log line and nothing else" | E11 — "not recorded as first-class events" |
| A9 | **No test** exercises memory-vs-evidence conflict behaviour; existing references are fake/mock repos | E7, E8, Q9 — `test_decision_context.py:76`, `test_rag_chat_integration.py:34` | E8, Q9 — same two files, `:45-76` and `:22-34` |
| A10 | The five Article III.7 epistemic categories are **not represented in code** | Q8 — "zero hits outside `docs/governance/`" | E10, Q8 — "no verified runtime representation" |
| A11 | No `evidence_conflict` state exists in code or schema today | Q8 | E10 — "Verified absence by code search" |
| A12 | Q5 — recording the resolution requires an **OME data-model change / schema work** | Q5 — "A schema migration is required" | Q5 — "new OME conflict/resolution record type or schema extension" |
| A13 | Q6 — append-not-substitute requires **both write-path and read-path changes** | Q6 — rewrite branches plus update every reader | Q6 — immutable assertions plus appended resolution record |
| A14 | Q8 — `evidence_conflict` must be an **orthogonal state/status**, not a sixth epistemic category | Q8 — "orthogonal state … not a new value in `fact_type`" | Q8 — "a state or status on evidence assertions/resolution workflow" |
| A15 | Q10 — implementation effort is **Sprint-scale** | Q10 — "low Sprint-scale," rising toward the higher end with full scope | Q10 — "Sprint-scale if implemented correctly" |
| A16 | Q11 statement 1 — the work **requires an OME data-model change: Yes** | Q11, §9 item 1 | Q11 — "durable conformance likely requires an OME data-model change" |
| A17 | **Sprint EX-2 has no canonical scope definition** at the pinned commit | Q11, §9 item 2, §11 item 1 | Q11 — "exact scope at the pinned commit is inactive and not fully evidenced" |
| A18 | No new Runtime Component is required; the work fits the existing nine | §10 — "does not require adding, removing, or renaming a Runtime Component" | Q7, Feasibility — "No new component, component removal, rename, or pipeline reorder is required" |
| A19 | NCE Lite in the NCO pipeline is a **placeholder that performs no reasoning** | Q3, Q7 — `pipeline.py:279-287` | E6, Q3 — "`run_nce_lite` is a placeholder" |
| A20 | Live chat reasoning sits in `AIService` prompt assembly, which reads OME every request | Q3 — `openai_client.py:989-1010` | E4, Q3 — `openai_client.py:991-1011`, `1070-1088` |
| A21 | **"Already conformant" (§7.1) is unavailable**; T1–T6 not all evidenced | §7.1 note — T6 "would independently fail" | Final Classification — "T1-T6 are not all evidenced" |
| A22 | **D1 is not satisfied** | §5 D1 | D1 Conclusion |
| A23 | **D3 is not satisfied** | §5 D3 | D3 Conclusion |
| A24 | Article V.2 is **not satisfied overall** across the three axes | §7 | Constitutional Conformance Assessment |
| A25 | ENG-CONF-001 is **recommendation only** and authorizes nothing | §10, §9.2 recital | ENG-CONF-001 Disposition — "does not authorize execution" |
| A26 | Deferral leaves CONFLICT-01 live, with conflicting values overwritten or dropped | Q12 | Q12 |
| A27 | Both findings were produced independently and sealed without reading the peer | §0, §1, §12; addendum §2.3 | Line 7, Signature; addendum |

**Comparator observation on §7.1.** Neither reviewer proposes "already conformant," and both mark the T1–T6 mapping N/A in their signature blocks. Claude Code adds that T6 would independently fail on E7/E8 evidence; Codex states T1–T6 are not all evidenced. §7.1 is therefore not invoked by either finding.

---

## 3. Disagreements

Stated without preference. Both positions are given in full and attributed. **None is resolved here.**

### D-1 — Final conformance classification *(the principal divergence)*

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | **Non-conformant (§7.3).** "No site in the codebase evidences the combination Article V.2 requires (investigate, preserve, record provenance, append-not-substitute) for any fact conflict. This satisfies §7.3's definitional boundary … read as: no site evidences a *durable, retrievable* mechanism, which is the operative requirement of Article V.2; a transient log line is evidenced but does not meet that bar, and is reported as such rather than silently omitted." |
| **Codex** | **Partially conformant (§7.2).** "some conflict detection exists in deterministic storage code and prompt-level contradiction handling exists, but Article V.2 is not satisfied across D1, D2, and D3. 'Already conformant' is unavailable because T1-T6 are not all evidenced. 'Non-conformant' is too broad because a deterministic conflict detection branch and appendable memory event substrate do exist." |

**Comparator observation:** both reviewers identify the same detection mechanism at the same lines, and both find Article V.2 unsatisfied overall. The divergence is in how the existence of that one detection branch is weighed against the §7.2 / §7.3 boundary text — Claude Code reads §7.3's "no … mechanism is evidenced at any site" as requiring a *durable, retrievable* mechanism; Codex reads the existence of the deterministic branch plus the appendable event substrate as placing the finding inside §7.2. This is a classification-boundary difference, not an evidentiary contradiction. **Not resolved here.**

### D-2 — D2 axis result

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | **Not satisfied.** "detection exists and is not silent at the moment it occurs … preservation and retrievability do not exist at all." The `truth_validation.contradictions` field is "written-only, never retrieved — functionally equivalent to silent resolution from the perspective of anything downstream of the write." |
| **Codex** | **"D2 is partially satisfied at detection only."** "conflict detection exists at one storage site and prompt instructions exist, but preservation/retrievability are insufficient." |

**Comparator observation:** the underlying evidence is identical and both reviewers find preservation and retrievability absent. They differ in whether detection-without-preservation is recorded as partial satisfaction of the axis or as non-satisfaction of the axis. This axis-level difference is the same weighing that produces D-1. **Not resolved here.**

### D-3 — Sprint EX-2 blocking assessment

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | **Non-blocking, as currently scoped — with an explicit caveat that this is provisional.** Rests on the absence of any Sprint EX-2 scope document at the pinned commit: "Whether Sprint EX-2 touches any of these cannot be assessed without a Sprint EX-2 scope document, which does not yet exist at this commit." |
| **Codex** | **Blocking — sequencing.** "work touching OME memory schema/repository, OCE context, NCE reasoning prompts/runtime, or NCO orchestration should wait for EBD-005/refreeze decisions … where it touches OME/OCE/NCE/NCO, collision risk is real." |

**Comparator observation:** both reviewers record the same evidentiary position — Sprint EX-2 has no canonical scope at the pinned commit (A17) — and both direct attention to the same OME surfaces. They select different labels from the §8 table for that position. **Not resolved here.**

### D-4 — ENG-CONF-001 priority

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | "activate ENG-CONF-001 **at elevated priority**, scoped strictly to the evidenced gaps in this finding" — following §9.1's mapping for a Non-conformant outcome. |
| **Codex** | "activate ENG-CONF-001 **after required Founder authorization and scheduling**, with evidenced scope limited to CONFLICT-01" — no priority elevation stated, consistent with §9.1's mapping for a Partially conformant outcome. |

**Comparator observation:** the priority difference follows mechanically from each reviewer's §7 classification under the §9.1 outcome mapping. It is not an independent disagreement about urgency. **Not resolved here.**

### D-5 — Executed behavioural evidence (E7)

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | **None found — and none produced.** "No test in `tests/` exercises `upsert_fact()`'s conflict branch." §1 records "no runtime code executed, no database connected, no migration run." The finding rests on code-reading and static-schema evidence. |
| **Codex** | **Executed.** Isolated fake-DB reproduction of `upsert_fact`: Case A (existing conf 40 → new conf 80) stored `Iraq`, execute count 1; Case B (existing conf 90 → new conf 50) retained `Jordan`, execute count 0; both with conflict warning. Plus `pytest` runs: 11 passed on two files; a second run of three files returned 14 passed / 1 failed, the failure being `test_valid_jwt_matching_company_id_succeeds` (503 from `_get_company_repository`), which Codex states "does not evidence memory conflict behavior." |

**Comparator observation:** Codex's Case A and Case B outcomes are behaviourally consistent with the mechanism Claude Code describes from source at `repository.py:262-309`. The reviewers differ in whether that behaviour was executed or read. Codex expressly rests its classification partly on E7 ("It rests on executed behavior (E7) …"); Claude Code's classification rests on static evidence. **Recorded, not adjudicated.**

### D-6 — Adjacent findings

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | **One recorded — AF-1.** `upsert_fact()`'s non-conflicting paths (`repository.py:228-260`, `146-191`) also overwrite in place with no history, so "`memory_facts` has no historical record for *any* update, not only contested ones." May implicate Article VII.5 more broadly than CONFLICT-01. Recorded separately, excluded from D1/D2/D3, from the §7 classification, and from ENG-CONF-001 scope; routed to the Founder per §3.3. |
| **Codex** | **None recorded.** "I did not identify a separate Article VII.5 defect outside the memory-versus-current-evidence conflict path." |

### D-7 — Characterisation of the prompt layer's precedence direction

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | The prompt layer leans toward **memory precedence** — `decision_prompt.py:79` ("source of truth"), `memory_prompt.py:16,24` ("HARD FACTS") — "which is the **opposite** emphasis from EBD-003 §12.3's 'current input is treated as the current truth.'" Reported as a finding of substance, prompt-only and unenforced. |
| **Codex** | Records both elements without framing them as a directional contradiction: `memory_prompt.py:24-26` labels memory as hard facts, and `memory_prompt.py:55` instructs "If memory conflicts with the user's new info, flag it in `truth_validation.contradictions`." Concludes "Prompt-only current-vs-memory conflict flagging exists." Does not record a memory-precedence-versus-§12.3 divergence. |

### D-8 — Whether the detection mechanism is characterised as a third, ungoverned doctrine

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | Frames it as **neither doctrine under adjudication**: "It is a third, ungoverned mechanism, present only because this code predates both EBD-003 §12.3 and Constitution Article V.2 in its current form." Adds that both confidence scores come from the same uncalibrated extraction prompt (`openai_client.py:37-50`), which "has no calibration instruction for `confidence` at all." |
| **Codex** | Frames it as **confidence precedence rather than chronological precedence**, without characterising it as a third ungoverned doctrine: "deterministic fact resolution is confidence-based, not chronological-only." Notes `fetch_recent_events` orders by `created_at DESC` and `memory_prompt` reverses for chronological readability. Does not raise confidence-score calibration. |

### D-9 — Where the behaviour should live (Q7 framing)

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | **Expressly declines to decide.** "This review does not decide where it *should* live (out of scope per §3.6 … the review is a feasibility finding, not a design)." Offers a feasibility observation only: today the only code path capable of implementing it is the OME repository layer or a new layer inserted between `AIService`/NCO Lite and `MemoryRepository`. |
| **Codex** | **States a recommended allocation.** "OME Foundation owns conflict/resolution persistence and retrievability; OCE assembles memory plus current evidence into the comparison surface; NCE Lite reasons to the best-supported current understanding; NCO Lite coordinates and enforces … This is distributed responsibility within existing components." |

**Comparator observation:** both reviewers agree no new Runtime Component is required (A18). They differ in whether Q7 is answered as a design allocation or declined as out of scope. **Not resolved here.**

### D-10 — Seal timestamp and hash recording method

| Reviewer | Position as filed |
|---|---|
| **Claude Code** | Seal timestamp and an internal pre-image SHA-256 recorded **inside** the report body (§13), method disclosed; raw custody hash later recorded in the companion addendum. |
| **Codex** | Report body records "SHA-256 recorded after file finalization" with **no hash value in the body**; the raw custody hash and seal timestamp are recorded **only** in the companion addendum. |

Both approaches are accepted under the Founder ruling of 2026-08-07. Recorded for the §12 procedural check (P6, P7). **No comparator determination.**

---

## 4. Evidence Differences

Descriptive only. No ranking of the reviewers is implied or intended.

| Dimension | Claude Code | Codex |
|---|---|---|
| **Executed behavioural evidence (E7)** | None — explicitly declared absent and its materiality to §7.1 flagged | Fake-DB harness (Cases A and B) plus two `pytest` runs |
| **Evidence base of the classification** | Code-reading and static-schema evidence, personally read | Expressly "rests on executed behavior (E7), schema evidence (E5), test coverage gaps (E8), provenance gaps (E9), and retrievability gaps (E11)" |
| **Inspected-vs-inferred discipline** | Dedicated §2 separating personally-read-in-full, tool-located-then-spot-verified, and tool-located-not-re-read; states the D1/D2/D3 finding "rests entirely on personally-read code" | No equivalent section; evidence presented as Verified / Unknown labels per item |
| **Epistemic labelling** | Per-item labels plus explicit §4.1 compliance check at §7 | Per-item `Verified:` / `Unknown:` prefixes; separate "Engineering Recommendations Only" block |
| **Governance sources cited** | Article V.2; EBD-003 §12.3, §17.1; EBD-002 §4.4, §12.4; EBD-004 §4.7, §4.9; Article VII.5; Article III.7 | Article V.2 at `NAWA_REASONING_CONSTITUTION_v1.md:204-208`; EBD-003 §12.3 at `:340-342`; EBD-004 at `:159-170`, `:174-189`, `:210-223`, `:229-234`; Article III.7 |
| **Unique evidence — Claude Code** | Confidence scores on both sides originate from the same uninstructed `FACT_EXTRACTOR_SYSTEM` prompt (`openai_client.py:37-50`), which carries no calibration rule; `truth_validation.contradictions` confirmed **write-only** by grep for readers; dead code in `app/services/memory/` (`facts_extractor,py` with a literal comma; 0-byte `followup_engine.py`); no migration `001`–`012` other than `011` touches the memory tables; no down-migrations exist | — |
| **Unique evidence — Codex** | — | `memory_facts.source_event_id` exists but `fetch_facts` / `get_fact_by_key` "do not return enough source history to reconstruct weighed sources or prior conflicting values"; `fetch_recent_events` orders `created_at DESC` while `memory_prompt` reverses for readability; EBD-004's cross-component invariant repeats §12.3 at `:229-234`; executed Case A / Case B outcomes with execute counts; specific `pytest` failure isolated and excluded as non-probative |
| **Runtime surfaces cited uniquely** | `app/nco/orchestrator.py` (full), `pipeline.py:100-300`, `openai_client.py:37-50`, `repository.py:146-191`, `228-260`, `360-392`, `company_input_classifier.py` | `decision_context.py:112-169`, `314-328`, `383-390`, `openai_client.py:1070-1088`, `pipeline.py:427-495`, `orchestrator.py:164-170`, `memory_prompt.py:55` |
| **Procedural context recorded** | §0 records a pre-review request to file at a non-canonical path asserting a "previous review" was invalid; Claude Code searched all branches, found nothing existed, raised it, and filed at the canonical path | Not applicable — no equivalent event recorded |
| **Mirror-refresh precondition (§14.1)** | Confirmed complete, read and relied upon as-is, not re-performed | Not addressed |
| **Standalone recommendations block** | Not present as a separate section | Present — four numbered engineering recommendations |

---

## 5. D1 / D2 / D3 Comparison

| Axis | Claude Code | Codex | Direction |
|---|---|---|---|
| **D1** — automatic chronological deference vs. investigation toward best-supported current understanding | **Neither. Not satisfied.** Timestamps are never compared in the decision (`updated_at` written, never read in the comparison); no reasoning or evidentiary weighing occurs — "the outcome is decided by an uncalibrated integer." Separately records that prompt text leans toward *memory* precedence, the opposite emphasis from §12.3. | **Not satisfied.** "fact storage resolution is confidence-based, not strictly chronological"; "the runtime does not evidence source weighing or best-supported adjudication." Conclusion: "partially present behavior but not conformant to Article V.2 as runtime evidence. D1 is not satisfied." | **AGREEMENT.** Both find D1 not satisfied. Both find the deterministic rule confidence-based rather than chronological, and neither finds investigation. Claude Code additionally records the prompt-layer directional divergence (D-7). |
| **D2** — silent resolution vs. conflict detection and preservation | **Not satisfied.** Detection "is not silent at the moment it occurs" (a WARNING log line) but "preservation and retrievability do not exist at all"; `truth_validation.contradictions` is "written-only, never retrieved — functionally equivalent to silent resolution." | **Partially satisfied at detection only.** "conflict detection exists at one storage site and prompt instructions exist, but preservation/retrievability are insufficient." | **DISAGREEMENT (D-2).** Identical underlying evidence; both find preservation and retrievability absent. They differ on whether detection-without-preservation registers as partial satisfaction or non-satisfaction of the axis. |
| **D3** — substitution/overwrite vs. append-with-provenance and preservation of prior records | **Not satisfied, unambiguously.** `UNIQUE (company_id, fact_key)` forces one live row; the replacement path is a plain `UPDATE` with an `ON CONFLICT … DO UPDATE` fallback; "the prior `fact_value` is not written anywhere else first — it is gone." `memory_events` does not substitute for this and receives no row when a fact is overwritten. | **Not satisfied.** `memory_events` appends; `memory_facts` "substitutes on equal/higher new confidence and suppresses lower-confidence new conflicting values"; "no resolution record captures sources weighed, basis, residual uncertainty, and provenance." | **AGREEMENT.** Both split events (append) from facts (substitute) and both find D3 not satisfied for fact conflicts. |

**Comparator observation:** the reviewers agree on D1 and D3 and diverge on D2. The D2 divergence and the §7 classification divergence (D-1) are the same weighing applied at two levels: whether an isolated detection branch with no preservation counts toward satisfaction. **Not resolved here.**

---

## 6. Question-by-Question Comparison (Q1–Q12)

All twelve approved questions were answered by both reviewers. No question is unanswered in either finding.

### Q1 — Where is a conflict between institutional memory and current evidence detected or resolved today?

| | |
|---|---|
| **Claude Code** | `MemoryRepository.upsert_fact()`, `repository.py:104-336`, branch at `262-309`. Runtime Component: OME Foundation (EBD-004 §4.9). Call site `_extract_and_upsert_facts()` in `openai_client.py` (~638-646) inside the `AIService` chat path. "the only site in the entire codebase where two values for the same institutional-memory key are compared against each other" — confirmed by grep for `upsert_fact`, `ON CONFLICT`, and "conflict" across `app/`. |
| **Codex** | "only in `MemoryRepository.upsert_fact` for durable facts," where a different `fact_value` under the same `(company_id, fact_key)` logs `"Fact conflict detected"` and chooses by confidence. Prompt-only conflict flagging exists in memory, decision, and RAG prompt blocks. **Unknown:** no verified deterministic runtime conflict comparison between OME memory and current Truth Layer inside OCE or NCE Lite. |
| **Relation** | **AGREEMENT** on the single site and the component. Codex adds an explicit *Unknown* on OCE/NCE Lite; Claude Code reaches the same absence via Q3 rather than as a Q1 label. |

### Q2 — Is automatic chronological precedence implemented in deterministic code, partially implemented, prompt-only, or documented-only?

| | |
|---|---|
| **Claude Code** | **"Not implemented in deterministic code, in any form."** What deterministic code implements instead is confidence-magnitude precedence — "a mechanism distinct from chronological precedence." Prompt text leans toward *memory* precedence (`decision_prompt.py:79`; `memory_prompt.py:16,24`), "the inverse of automatic-current-input-wins framing," unenforced by any deterministic check. Expressly invokes §4.1: this finding is "**not** treated as determining the §7 classification by itself." |
| **Codex** | **"deterministic fact resolution is confidence-based, not chronological-only."** Notes `fetch_recent_events` orders `created_at DESC` and `memory_prompt` reverses for chronological readability, and that prompts treat memory/profile as hard facts/source of truth. "Prompt-only current-vs-memory conflict flagging exists. No deterministic Article V.2 investigation mechanism was found." |
| **Relation** | **AGREEMENT** on the substance: chronological precedence is not deterministically implemented; confidence-based resolution is; prompt-only flagging exists. Difference in emphasis — Claude Code frames the prompt layer as pointing the opposite direction from §12.3 (D-7); Codex records the same prompt elements without that framing. |

### Q3 — Which Runtime Components read from OME Foundation at runtime?

| | |
|---|---|
| **Claude Code** | `AIService` (`openai_client.py`) reads `fetch_recent_events`, `fetch_facts`, `build_company_profile` every request (`989-1010`, personally read), feeding `build_decision_context()`. **"NCO Lite / NCE Lite does not read OME at all"** — confirmed by reading `orchestrator.py` in full and `pipeline.py:100-300`; the only OME interaction there is a write (`store_ome_foundation()` at `orchestrator.py:165`). `run_nce_lite()` (`pipeline.py:279-287`) is an explicit placeholder whose docstring states "No AI reasoning is performed by NCO Lite." Flags this as a **documented-contract-vs-code gap** against EBD-004 §4.7. |
| **Codex** | Chat `AIService` reads OME memory and injects it into reasoning messages (`openai_client.py:991-1011`, `1070-1088`). Decision Context consumes memory passed to it (`decision_context.py:112-169`, `314-328`, `383-390`). "NCO Lite writes OME events but does not normally read them" (`pipeline.py:427-495`; `orchestrator.py:164-170`). "Contractually, OCE and NCE Lite should consume OME/history, but the inspected OCE service does not read OME directly and NCE Lite in NCO is a placeholder." |
| **Relation** | **AGREEMENT**, closely aligned including line ranges. Codex additionally names OCE explicitly as not reading OME directly. |

### Q4 — What would conflict detection require if not already present? Is the comparison surface available today?

| | |
|---|---|
| **Claude Code** | Detection "in the sense of noticing two different values for the same key" **already exists**; the comparison surface (`get_fact_by_key()` plus string comparison) "exists and works today." Absent: (a) any signal distinguishing current validated input from memory reaching `upsert_fact()` — requires a new parameter/column (e.g. `source_kind` / `is_current_input`) threaded from `openai_client.py`; (b) persistence of the detected conflict as a queryable record rather than a log line. |
| **Codex** | Requires "a canonical comparison surface joining current CompanyInput/Truth Layer facts with OME facts/events by normalized entity, fact key, source, timestamp, confidence, and provenance." Partial surfaces exist: current chat message, unified capture metadata, memory facts, memory events, RAG chunks, operational context. "Missing is a typed, reusable comparison contract and durable conflict object." |
| **Relation** | **AGREEMENT** that a durable conflict object is missing. Different scoping of the comparison surface — Claude Code says the narrow same-key surface exists today and the missing piece is a provenance signal plus persistence; Codex describes a broader canonical joining surface as not yet existing, with only partial surfaces present. |

### Q5 — What would recording the resolution — sources weighed, basis, residual uncertainty, provenance — require?

| | |
|---|---|
| **Claude Code** | **"A schema migration is required."** `memory_facts` has no columns for any of the four elements. Minimally a new table (`memory_fact_conflicts` / `memory_fact_history`) with `fact_id`, `prior_value`, `prior_confidence`, `new_value`, `new_confidence`, `resolution_basis`, `sources_weighed` (jsonb), `residual_uncertainty`, `resolved_at`, `resolved_by` — or converting `memory_facts` into an append-only versioned table with a `current` pointer. "a genuine OME data-model change, not a code-only fix." |
| **Codex** | Requires "at least a new OME conflict/resolution record type or schema extension" recording memory source IDs, current evidence source IDs, weighting basis, selected current understanding, residual uncertainty, provenance, and link to prior records. Adds: "`memory_events.logic_json/context` could host an **MVP append-only record without migration**, but reliable querying and third-party reproducibility likely require schema work." |
| **Relation** | **AGREEMENT** that durable conformance needs a data-model change (A12). **Difference in whether a no-migration MVP path exists** — Codex names `memory_events.logic_json` as a possible MVP host; Claude Code does not offer a no-migration path and states a migration is required. |

### Q6 — Does OME overwrite or append? What would append-not-substitute require?

| | |
|---|---|
| **Claude Code** | "Both behaviors coexist on different tables": `memory_events` append-only (`repository.py:15-21`); `memory_facts` overwrite-in-place. Append-not-substitute requires the Q5 schema change, **plus** rewriting `upsert_fact()`'s replacement branches (`273-302`, `311-336`) to INSERT a version row and update a "current" reference, **plus** updating every reader (`get_fact_by_key`, `fetch_facts`, `build_company_profile`) to resolve "current" rather than assuming one row per key. |
| **Codex** | "`memory_events` appends; `memory_facts` overwrites or suppresses conflicting values because of unique `(company_id, fact_key)` and update statements." Append-not-substitute "requires preserving prior and conflicting fact assertions as immutable assertions plus an appended resolution/supersession record, rather than mutating the single `fact_value`." |
| **Relation** | **AGREEMENT.** Claude Code enumerates the specific read-path call sites requiring change; Codex states the requirement at the model level. |

### Q7 — Where should this behaviour live: NCE Lite, OME Foundation, NCO Lite, or distributed?

| | |
|---|---|
| **Claude Code** | **Declines to decide** — "out of scope per §3.6 … the review is a feasibility finding, not a design." Feasibility observation only: today the mechanism lives entirely in `MemoryRepository`, invoked from `AIService`. EBD-004 §4.7 assigns conflict-relevant reasoning to NCE Lite consuming OME, "but the current NCE Lite implementation performs no reasoning and does not consume OME, so today the *only* code path capable of implementing this at all is the OME repository layer itself, or a new layer inserted between `AIService`/NCO Lite and `MemoryRepository`." |
| **Codex** | **States a recommended allocation.** "OME Foundation owns conflict/resolution persistence and retrievability; OCE assembles memory plus current evidence into the comparison surface; NCE Lite reasons to the best-supported current understanding; NCO Lite coordinates and enforces that required conflict handling occurred before downstream output. This is distributed responsibility within existing components. It does not require adding, removing, renaming, or reordering Runtime Components." |
| **Relation** | **DISAGREEMENT on framing (D-9)**, with **AGREEMENT on the component-set consequence (A18)** — both conclude no Runtime Component need be added, removed, renamed, or reordered, which is the §7.3 escalation test. |

### Q8 — How should an `evidence_conflict` state be represented without creating a sixth epistemic category?

| | |
|---|---|
| **Claude Code** | The five Article III.7 categories are "**not represented anywhere in code today**" — grep for "Company Policy," "NAWA Inference," "epistemic" returns "zero hits outside `docs/governance/`." The actual schemes are unrelated: `fact_type` (`company|product|process|goal|constraint|metric|risk|decision|other`, `openai_client.py:43`) and `input_category` (`operational|financial|knowledge|unknown`). "Because no five-category enum/model exists to protect, there is currently no risk of `evidence_conflict` colliding with … an existing category set — the concern the question raises is not yet live in this codebase." Any future representation must be "an orthogonal state … not a new value in `fact_type`." |
| **Codex** | "Represent it as a state or status on evidence assertions/resolution workflow, not an epistemic category. The underlying assertions remain Article III.7 categories such as Fact, Assumption, or NAWA Inference; `evidence_conflict` marks that sources disagree and that resolution/provenance is required. Current code only has `truth_validation.contradictions` arrays in output JSON; no durable state exists." |
| **Relation** | **AGREEMENT** on the answer — orthogonal state, not a sixth category (A14) — and on the absence of the five categories in code (A10) and of any `evidence_conflict` state (A11). Claude Code adds that the collision concern is not yet live because there is no category model to protect. |

### Q9 — Which existing tests would change, and what new tests are required?

| | |
|---|---|
| **Claude Code** | "**No existing test would change**, because none currently exercises `upsert_fact()`'s real conflict branch" — the two references (`test_decision_context.py:76`, `test_rag_chat_integration.py:34`) are mock stubs (`async def upsert_fact(self, **kwargs): ...`) that "bypass the logic entirely." New tests: (a) new confidence ≥ existing → replacement; (b) new confidence < existing → old kept; (c) a test for whatever provenance/preservation mechanism is built per Q5; (d) an integration test that `truth_validation.contradictions` is retrievable — "this test cannot be written meaningfully today, because no retrieval path exists." |
| **Codex** | "Existing tests to **extend**: `tests/test_decision_context.py`, `tests/test_rag_chat_integration.py`, and memory repository tests that should be added because none currently target `MemoryRepository.upsert_fact` conflict semantics." New tests: conflict detection between memory facts and current extracted facts; no chronological-only deference; conflict preserved and retrievable; resolution record includes sources, basis, residual uncertainty, provenance; prior records preserved; NCE/NCO behaviour when conflict exists; **tenant isolation for conflict records**. |
| **Relation** | **AGREEMENT** on the underlying state — no test covers the conflict path; the same two files hold only fake repos (A9). **Difference in phrasing**: Claude Code says no existing test *would change*; Codex says those two tests should be *extended*. Codex uniquely names tenant isolation for conflict records. |

### Q10 — What is the implementation effort?

| | |
|---|---|
| **Claude Code** | "**low Sprint-scale** (a small number of days)" for a mechanically append-only `memory_facts` alone. Threading a genuine current-input-vs-memory provenance signal from the call sites through to `upsert_fact()`, plus a retrieval surface for conflict records, "pushes the total toward the higher end of Sprint-scale rather than a multi-day patch." Engineering-only; excludes review, ratification, and Product-review gates. |
| **Codex** | "**Sprint-scale** if implemented correctly with durable schema, repository changes, prompt/runtime integration, tests, and migration. A thin prompt-only or `memory_events`-only MVP could be days, but it would likely not satisfy retrievability and provenance threshold T1-T6." |
| **Relation** | **AGREEMENT** on Sprint-scale (A15). Both identify a smaller sub-scope measurable in days and a full scope at Sprint-scale. Codex ties the thin MVP explicitly to failing T1–T6. |

### Q11 — Does the work conflict with, depend on, or block Sprint EX-2? Does it require an OME data-model change, and does Sprint EX-2 use the same surfaces?

| | |
|---|---|
| **Claude Code** | **Requires an OME data-model change: Yes** (explicit). **Does EX-2 use the same surfaces: "cannot be determined from the pinned commit"** — `docs/execution/` at `26d5bab` contains no Sprint EX-2 backlog or scope document; the only reference (`EXECUTION_BOARD.md:77`) notes one unrelated task (Executive Actions Taxonomy) might be deferred there, "with no mention of OME/memory surfaces." Stated as "cannot determine, with reason given." |
| **Codex** | **Assessment: Blocking — sequencing.** "durable conformance likely requires an OME data-model change unless governance accepts a weaker `memory_events.logic_json` convention." On surfaces: "Sprint EX-2 **appears likely** to use the same OME/OCE/NCO surfaces, but its exact scope at the pinned commit is inactive and not fully evidenced; therefore specific collision details are partly **Unknown**." |
| **Relation** | **AGREEMENT** on statement 1 (OME data-model change required — A16) and on the underlying evidentiary fact that EX-2 has no canonical scope at the pinned commit (A17). **DISAGREEMENT (D-3)** on the §8 label. **Difference on statement 2:** Claude Code records "cannot determine"; Codex records "appears likely … partly Unknown." Codex also conditions the data-model requirement on governance not accepting a weaker `logic_json` convention; Claude Code states it unconditionally. |

### Q12 — What breaks if implemented now, and what breaks if deferred?

| | |
|---|---|
| **Claude Code** | **If implemented now:** anything relying on `memory_facts` holding exactly one overwritable row per key — e.g. `build_company_profile()` (`repository.py:360-392`) — "would need to be updated to resolve 'current' from a versioned model … a coordinated change across readers, not just the write path." **If deferred:** CONFLICT-01 remains live (restating §3.5's "governance-integrity exposure, not a scheduling delay"); the undocumented confidence-race mechanism "continues to govern real fact conflicts in production with no provenance trail, meaning any current incident where NAWA silently kept a stale fact … or silently discarded a correct new fact … is currently **unrecoverable after the fact**, since neither the old value nor the reason for the outcome is preserved anywhere queryable." |
| **Codex** | **If implemented now:** "existing company-profile behavior may change because single-value `memory_facts` assumptions become assertion/history based; prompts and tests may need updates; any UI/API assuming one fact per key could break; **migration risk exists**." **If deferred:** "CONFLICT-01 remains live; facts can be overwritten or conflicting input dropped; conflicts are not reliably retrievable; user-facing reasoning may silently resolve conflicts or rely on prompt-only behavior." |
| **Relation** | **AGREEMENT** on both directions (A26). **Differences in emphasis:** Claude Code frames irreversibility as the material consequence of deferral; Codex does not frame it as central. Codex uniquely names migration risk and UI/API breakage; Claude Code uniquely names `build_company_profile()` as the concrete coupling. |

### Q1–Q12 summary

| Question | Relation |
|---|---|
| Q1 | Agreement |
| Q2 | Agreement on substance; difference in framing of the prompt layer (D-7) |
| Q3 | Agreement |
| Q4 | Agreement on the missing durable conflict object; difference in scoping the comparison surface |
| Q5 | Agreement that a data-model change is required; difference on whether a no-migration MVP path exists |
| Q6 | Agreement |
| Q7 | Disagreement on framing — declined as out of scope vs. recommended allocation (D-9); agreement that no component change is required |
| Q8 | Agreement |
| Q9 | Agreement on state; difference in phrasing (no change vs. extend) |
| Q10 | Agreement |
| Q11 | Agreement on statement 1; disagreement on the §8 label (D-3); difference on statement 2's wording |
| Q12 | Agreement on both directions; differences in emphasis |

**Comparator observation:** of the twelve questions, the reviewers reach the same substantive answer on eleven. Q7 is the one question where the answers differ in kind rather than in emphasis — and even there, both reach the same conclusion on the component-set test that §7.3 makes decisive for the unfreeze-scope escalation.

---

## 7. Final Conformance Classification — Each Reviewer

| Reviewer | Classification | EFR section | Recorded at |
|---|---|---|---|
| **Claude Code** | **Non-conformant** | §7.3 | §7 and Signature §12 |
| **Codex** | **Partially conformant** | §7.2 | Final Engineering Classification and Signature |

Neither reviewer proposes "already conformant" (§7.1); both mark the T1–T6 mapping N/A in their signature blocks (A21).

Per EFR-EBD-005 §7, where the reviewers do not converge, **both classifications are recorded with attribution** and the Founder decides at §13.3.

**Consequence attaching to each, per the governing task — stated as the task states it, not as a comparator recommendation:**

- §7.2 (Codex): "EBD-005 carries both a text change and a bounded implementation change. The EFR recommends ENG-CONF-001 activation and defines its evidenced scope."
- §7.3 (Claude Code): "EBD-005 carries a substantive implementation change. The EFR recommends ENG-CONF-001 activation at elevated priority … If approved Question 7 concludes the behaviour cannot be placed within the existing Runtime Components without adding, removing, reordering, or renaming one, the unfreeze scope escalates from Freeze v1.1 to v2.0."

**Comparator observation:** the v2.0 escalation condition attached to §7.3 is **not triggered on either finding** — both reviewers answer Q7 that the behaviour fits within the existing nine components (A18).

---

## 8. Sprint EX-2 Assessment — Each Reviewer

| Reviewer | §8 assessment | Q11 stmt 1 — OME data-model change required? | Q11 stmt 2 — does EX-2 use the same surfaces? |
|---|---|---|---|
| **Claude Code** | **Non-blocking**, as currently scoped, with an explicit provisional caveat | **Yes** | **Cannot be determined from the pinned commit** — no EX-2 scope document exists; `EXECUTION_BOARD.md:77` does not name OME or memory surfaces |
| **Codex** | **Blocking — sequencing** | **Yes** — "durable conformance likely requires an OME data-model change unless governance accepts a weaker `memory_events.logic_json` convention" | **"Appears likely"** to use the same OME/OCE/NCO surfaces; exact scope "inactive and not fully evidenced," collision details "partly Unknown" |

**Components and code paths simultaneously in play (§8 required statement 3):**

- **Claude Code:** `app/services/memory/repository.py`; `migrations/` (new migration file); every reader of `memory_facts` — `openai_client.py`, `decision_context.py`, and `pipeline.py`'s `store_ome_foundation()`. Whether EX-2 touches any of these "cannot be assessed without a Sprint EX-2 scope document, which does not yet exist at this commit."
- **Codex:** OME memory schema/repository; OCE context; NCE reasoning prompts/runtime; NCO orchestration. "where it touches OME/OCE/NCE/NCO, collision risk is real."

Both reviewers state the assessment is advisory and does not activate, defer, or scope Sprint EX-2, which remains inactive per EFR-EBD-005 §2.

---

## 9. ENG-CONF-001 Recommendation — Each Reviewer

| Reviewer | Recommendation | Evidenced scope as filed |
|---|---|---|
| **Claude Code** | Activate **at elevated priority**, per §9.1's mapping for a Non-conformant outcome. Scoped "strictly to the evidenced gaps in this finding." | (1) Schema migration adding provenance/history capability to `memory_facts` (Q5); (2) rewiring `upsert_fact()`'s replacement paths to append-not-substitute (Q6); (3) a **source-provenance signal threaded from call sites to `upsert_fact()`** so the mechanism can distinguish current validated input from memory — "required for any future implementation of EBD-003 §12.3 or Article V.2, whichever the Founder ultimately ratifies, since neither can be implemented without this signal existing at all"; (4) a retrieval surface for conflict/contradiction records; (5) new tests per Q9. |
| **Codex** | Activate **after required Founder authorization and scheduling**, with evidenced scope "limited to CONFLICT-01." No priority elevation stated. | (1) Add durable conflict/resolution representation in OME; (2) preserve prior/current conflicting assertions append-only; (3) record sources weighed, basis, uncertainty, and provenance; (4) make conflicts retrievable; (5) **integrate OCE/NCE/NCO responsibilities** without changing the nine-component architecture; (6) add tests for D1, D2, and D3 behaviour. |

Both state the recommendation does not authorize execution (A25). Claude Code additionally recites the §9.2 binding conditions in full and expressly excludes adjacent finding AF-1 from ENG-CONF-001 scope.

**Scope mapping — stated as a mapping, not as a merged scope.** No consolidated scope is proposed here.

| Element | Claude Code | Codex |
|---|---|---|
| Durable conflict/resolution record + schema | item 1 | items 1, 3 |
| Append-not-substitute for prior values | item 2 | item 2 |
| Retrievability of conflicts | item 4 | item 4 |
| Tests | item 5 | item 6 |
| **Source-provenance signal threaded to `upsert_fact()`** | item 3 | **no counterpart** |
| **Integrate OCE / NCE / NCO responsibilities** | **no counterpart** | item 5 |

**Comparator observation:** four of the elements correspond across both lists. Two do not: Claude Code's provenance-signal threading has no counterpart in Codex's scope, and Codex's OCE/NCE/NCO integration has no counterpart in Claude Code's. The second asymmetry follows from the Q7 divergence at D-9. **Not resolved here.**

**Codex standalone engineering recommendations (no Claude Code counterpart section):**

1. Treat `evidence_conflict` as a status on evidence/resolution workflow, not a sixth epistemic category.
2. Avoid using mutable `memory_facts` as the authoritative historical record; convert or supplement it with immutable assertions and appended resolutions.
3. Keep the implementation within existing Runtime Components; do not escalate to Freeze v2.0 on component-structure grounds based on current evidence.
4. Require reproducible tests before claiming conformance.

---

## 10. Exact Founder Decision Points

Derived from the divergences above and the decision gate at EFR-EBD-005 §13. Each is reserved to the Founder. **None is answered here.**

| # | Decision | Source | §13 item |
|---|---|---|---|
| **F1** | **Resolve the classification split** — Claude Code "Non-conformant (§7.3)" vs. Codex "Partially conformant (§7.2)" — or direct a further step. This determines whether EBD-005 carries a bounded or a substantive implementation change, and whether ENG-CONF-001 is recommended at elevated priority. | D-1 | §13.3 |
| **F2** | **Resolve the D2 axis split** — "not satisfied" vs. "partially satisfied at detection only" — or record both. This is the axis-level form of F1 and may be decided with it or separately. | D-2 | §13.3 |
| **F3** | **Rule on the Sprint EX-2 relationship** — "Non-blocking (provisional caveat)" vs. "Blocking — sequencing." Both reviewers agree EX-2 has no canonical scope at the pinned commit; the decision is which §8 label governs in that state of evidence. | D-3 | §13.8 |
| **F4** | **Authorize or decline ENG-CONF-001, and set its priority** — one reviewer recommends elevated priority, the other does not. Recommendation alone does not authorize execution (§9.2). | D-4, §9 | §13.4 |
| **F5** | **Fix the scope of ENG-CONF-001** where the two evidenced scopes do not overlap — specifically whether Claude Code's *source-provenance signal threaded to `upsert_fact()`* and Codex's *OCE/NCE/NCO integration* are in or out. Per §9.2 condition 4, scope may not exceed what the reviewers evidenced, and expansion requires a new Founder decision. | §9 mapping | §13.4 |
| **F6** | **Rule on the Q5 MVP question** — whether an append-only conflict record hosted in `memory_events.logic_json` without a migration (Codex) is an acceptable interim conformance path, or whether a schema migration is required (Claude Code). Codex notes the MVP "would likely not satisfy retrievability and provenance threshold T1-T6." | Q5, Q10 | §13.4 |
| **F7** | **Rule on the E7 asymmetry** — whether a finding resting on static evidence is accepted alongside one resting partly on executed behaviour, or returned for additional evidence under §13.2. | D-5 | §13.2 |
| **F8** | **Classify adjacent finding AF-1** — general absence of fact-history preservation on *all* `memory_facts` updates, potentially implicating Article VII.5 beyond CONFLICT-01 — for separate governance handling. Claude Code records it and excludes it from ENG-CONF-001 scope per §9.2 condition 5; Codex records no adjacent findings. | D-6 | §13.6 |
| **F9** | **Direct disposition of the non-matching `ARCHIVE_EFR-EBD-005_FINDING_CLAUDE_CODE.md`** in the canonical repository (hash `90f3e80c…`, 270 lines, internal seal timestamp `2026-08-04T20:25:05Z`), which Claude Code's custody addendum expressly disclaims as "not … the sealed finding, a valid copy of it, or my work product." | CN-4 | §13.2 |
| **F10** | **Rule on the prompt-layer directional finding** — Claude Code records that live prompt text leans toward *memory* precedence (`decision_prompt.py:79`; `memory_prompt.py:16,24`), the opposite emphasis from EBD-003 §12.3, and reports it as a finding of substance independent of Article V.2. Codex records the same prompt text without that framing. Whether this is in ENG-CONF-001 scope, a separate obligation, or noted only. | D-7 | §13.4, §13.6 |
| **F11** | **Rule on unfreeze scope — Freeze v1.1 or v2.0.** Both reviewers answer Q7 that no Runtime Component need be added, removed, renamed, or reordered (A18), so the §7.3 escalation condition is not triggered on either finding. The ruling is still reserved to the Founder. | A18, Q7 both | §13.7 |
| **F12** | **Grant or withhold an explicit exception** permitting runtime implementation before EBD-005 ratification (§9.2 condition 3). Neither reviewer requested one. | §9.2 | §13.5 |
| **F13** | **Accept the findings and proceed to gate 4** (Aboura product review), or return for additional evidence on named questions. | §1.3 gate chain | §13.1, §13.2 |
| **F14** | **Rule on Claude Code's unresolved question 3** — whether removing the confidence-race mechanism would break product behaviour implicitly relying on it (e.g. `expansion_market` repeated-value confidence accumulation, `repository.py:146-191`, described as "a real, apparently intentional feature"). Claude Code flags this for Product review at gate 4 rather than answering it. | Claude Code §11 item 3 | §13.1 |

---

## Comparator Compliance Statement

- Only the two sealed findings, their two companion custody addenda, and the governing task were read.
- **No runtime code was inspected.** No repository source file was opened.
- **No third engineering review was performed.** No new technical conclusion was introduced. Every technical statement above is a restatement of, or citation to, one of the two sealed findings, attributed to its author.
- **No disagreement was resolved.** Where the reviewers differ, both positions stand with attribution.
- Comparator observations describe the relationship between the two findings only and carry no engineering opinion.
- Neither sealed finding nor either custody addendum was modified. Both remain byte-identical to their addendum-recorded hashes.
- `ARCHIVE_EFR_Comparison_Report_PREVIOUS.md.md` was **not read** and none of its attributions were used.
- This report is a comparison artifact. It does not ratify EBD-005, does not activate ENG-CONF-001, and does not activate or scope Sprint EX-2.

---

**Custody of this comparison**

| Field | Value |
|---|---|
| Claude Code finding — authoritative hash | `f80a39627a9b2ee2952470bd72b682acc87ed71b8f009811d3403f3682a88f87` |
| Codex finding — authoritative hash | `8e46bb4041cb63858e76e8f6f9b562a3c200b21bbc688ec77d3c0fdd82b88576` |
| Pinned commit, both findings | `26d5bab03cdad52a0d7febd34d6600bee742ce82` |
| Comparison prepared | 2026-08-07 |

---

COMPARISON COMPLETE

No independent engineering judgment added.
