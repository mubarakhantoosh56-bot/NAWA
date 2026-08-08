# EFR-EBD-005 — Founder Decision

**Document type:** Founder Decision. Terminal decision instrument for Engineering Feasibility Review EFR-EBD-005 (CONFLICT-01 / Tier 1 Unfreeze).
**Decision authority:** Founder, under EFR-EBD-005 §13 (Founder Decision Gate).
**Recorded by:** COWORK (CTO / Chief of Staff), acting as recording officer under §12 procedural custody.
**Decision date:** 2026-08-07.
**Status:** ✅ **EFR-EBD-005 CLOSED.**

**Authoritative source documents — these seven only:**

| # | Document |
|---|---|
| 1 | `EFR-EBD-005.md` — governing task (Draft 3, Founder Approved 2026-08-01) |
| 2 | `EFR-EBD-005_MIRROR_REFRESH.md` — governance mirror refresh manifest |
| 3 | `reviews/EFR-EBD-005_FINDING_CLAUDE_CODE.md` — sealed finding, Engineering Reviewer #1 |
| 4 | `reviews/EFR-EBD-005_FINDING_CLAUDE_CODE_SEAL.md` — post-seal custody addendum |
| 5 | `reviews/EFR-EBD-005_FINDING_CODEX.md` — sealed finding, Engineering Reviewer #2 |
| 6 | `reviews/EFR-EBD-005_FINDING_CODEX_SEAL.md` — post-seal custody addendum |
| 7 | `reviews/EFR-EBD-005_COMPARISON_FINAL.md` — final neutral comparison |

**Superseded and not authoritative:** `reviews/ARCHIVE_EFR_Comparison_Report_PREVIOUS.md.md`, and any earlier comparison artifact. Per Founder ruling of 2026-08-07, archived comparison reports are superseded and carry no authority. They were not read in preparing this decision. Readers are cautioned that the archived report's reviewer attributions are the inverse of the two sealed signature blocks.

> **Recording limits observed.** No runtime code was inspected. No further engineering review was performed. No further comparison was performed. No finding, custody addendum, or comparison was modified. Every engineering statement below is a restatement of, or citation to, one of the two sealed findings, attributed to its author. Every ruling below is the Founder's, recorded as issued.

---

## 1. Founder Decision

The Founder, exercising the decision authority reserved at EFR-EBD-005 §13, decides as follows. These rulings are issued in the Founder's own authority and are not derived from, averaged between, or arbitrated from the two engineering findings.

| # | Matter | Founder ruling | §13 item |
|---|---|---|---|
| **1** | **Final conformance classification** | **Partially Conformant** | §13.3 |
| **2** | **D1 — automatic chronological deference vs. investigation** | **Not Satisfied** | §13.3 |
| **3** | **D2 — silent resolution vs. detection and preservation** | **Partially Satisfied** — detection exists but preservation/provenance remains incomplete | §13.3 |
| **4** | **D3 — substitution/overwrite vs. append-with-provenance** | **Not Satisfied** | §13.3 |
| **5** | **ENG-CONF-001** | **Approved** as the required engineering remediation | §13.4 |
| **6** | **Sprint EX-2** | **Continue.** ENG-CONF-001 shall be completed as an early engineering task before constitutional conformance is considered complete | §13.8 |
| **7** | **Architecture Freeze escalation** | **No Freeze v2.0 escalation approved** | §13.7 |
| **8** | **Runtime Component additions** | **None approved** | §13.7 |
| **9** | **Runtime Component removals** | **None approved** | §13.7 |
| **10** | **Runtime Component renaming** | **None approved** | §13.7 |
| **11** | **Runtime Component reordering** | **None approved** | §13.7 |
| **12** | **Archived comparison reports** | **Superseded. Not authoritative.** | §13.2 |
| **13** | **Disposition of EFR-EBD-005** | **This Founder Decision closes EFR-EBD-005.** | §13.1 |

**Nothing in this decision ratifies the Tier 1 unfreeze.** Per EFR-EBD-005 §13 closing recital, ratification occurs at gate 5 under EBD-003 §17.1, after Product review, and only by the Founder. This decision closes the Engineering Feasibility Review; it does not advance the Freeze.

---

## 2. Review Summary

### 2.1 What was reviewed

EFR-EBD-005 assessed CONFLICT-01 — the constitutional conflict between **Constitution Article V.2** (conflicts between institutional memory and current evidence are investigated, preserved, reasoned to the best-supported current understanding, with resolution, sources, basis, uncertainty and provenance appended rather than substituted) and **EBD-003 §12.3** (current input is treated as the current truth when memory and current input disagree).

Two independent Senior AI Software Engineers reviewed the runtime under EBD-002 §4.4, in isolation, against a single pinned commit.

### 2.2 Execution baseline and custody

| Field | Value |
|---|---|
| Pinned commit reviewed, both reviewers | `26d5bab03cdad52a0d7febd34d6600bee742ce82` |
| Commit subject | `docs(execution): authorize EFR-EBD-005 governance obligation` |
| Branch | `claude-safe-review` |
| Claude Code isolated worktree | `C:\aimx_efr_ebd_005_claude` (removed post-seal) |
| Codex isolated worktree | `C:\AIMX_PROJECTS\_codex_efr005_reviewer2` |
| Claude Code finding — authoritative custody hash | `f80a39627a9b2ee2952470bd72b682acc87ed71b8f009811d3403f3682a88f87` |
| Codex finding — authoritative custody hash | `8e46bb4041cb63858e76e8f6f9b562a3c200b21bbc688ec77d3c0fdd82b88576` |
| Mirror refresh precondition (§14.1) | Complete — six-file export, all raw-identity PASS, manifested at `EFR-EBD-005_MIRROR_REFRESH.md`, pinned source commit `6d5d04277d91dda988c81876ca50318297b9e878` |

**Recorded provenance note.** The governance mirror refresh was executed against pinned commit `6d5d042` (`docs(governance): EBD-006 Constitutional Governance Alignment`); the two findings were produced against `26d5bab`, the commit that authorized this obligation. Claude Code's finding §1 records the §14.1 precondition as confirmed complete and relied upon as-is. Both reviewers used the identical review commit. Recorded as custody provenance, not as a defect.

**Custody verification.** Both sealed findings were verified byte-identical to the raw SHA-256 recorded in their companion post-seal custody addenda. Per the Founder ruling of 2026-08-07, a separate post-seal custody addendum is an accepted and authoritative method of satisfying the report-hash requirement, and the SHA-256 is not required to be embedded inside the sealed body.

**Independence.** Neither reviewer read the other's finding before sealing. Claude Code's addendum §2.3 records the Codex finding as "not opened, read, or inspected." Codex's addendum records "Claude Code finding read or inspected: No." Both bodies carry independence attestations.

### 2.3 What the two reviewers found

Both reviewers independently identified the same single deterministic mechanism — `MemoryRepository.upsert_fact()` — as the only site in the codebase where institutional memory and a new incoming value for the same key are compared. Both found that resolution there is decided by confidence magnitude rather than chronology, that the losing value is not preserved, that the schema records no resolution basis, sources weighed, residual uncertainty, or prior value, that all other contradiction handling is prompt-instruction text routed to `truth_validation.contradictions`, and that no test exercises the conflict path.

The comparison record establishes that on the twelve approved questions the reviewers reached the same substantive answer on **eleven of twelve**, and agreed on **D1** and **D3**.

### 2.4 Where the reviewers diverged

| Matter | Claude Code | Codex |
|---|---|---|
| Conformance classification | Non-conformant (§7.3) | Partially conformant (§7.2) |
| D2 axis result | Not satisfied | Partially satisfied at detection only |
| Sprint EX-2 | Non-blocking, provisional caveat | Blocking — sequencing |
| ENG-CONF-001 priority | Activate at elevated priority | Activate after authorization; no priority elevation |
| Executed behavioural evidence (E7) | None produced; static evidence only | Executed fake-DB harness plus `pytest` runs |
| Adjacent findings | One (AF-1) | None |
| Q7 — where the behaviour should live | Declined as out of scope per §3.6 | Answered with a distributed OME/OCE/NCE/NCO allocation |

The comparison record notes that the classification split and the D2 split are the same weighing applied at two levels: whether an isolated detection branch with no preservation counts toward satisfaction of the axis.

### 2.5 Acceptance criteria and procedural check

The Founder accepts the review as procedurally complete under §10 and §12. Both findings were filed, timestamped, hashed, and sealed by their named authors; both answered all twelve approved questions; both assessed D1, D2 and D3 separately; both addressed evidence classes E1–E11; independence held; disagreements were preserved rather than suppressed, averaged, or arbitrated; and the consolidated record is individually attributable throughout. Neither reviewer proposed "already conformant," so the §7.1 T1–T6 threshold is N/A in both findings.

---

## 3. Final Accepted Engineering Position

The Founder accepts the following as the engineering position of record for EFR-EBD-005. It is drawn from the points on which both sealed findings independently agree, and is stated without introducing any conclusion neither reviewer reached.

1. **A single deterministic conflict-detection site exists.** `MemoryRepository.upsert_fact()` logs `"Fact conflict detected"` when the same `(company_id, fact_key)` receives a different `fact_value`. Both reviewers identify this as the only such site in the codebase. *(Claude Code `repository.py:262-309`; Codex `repository.py:264`)*

2. **Resolution at that site is confidence-based, not chronological.** The higher- or equal-confidence value replaces the stored value; the lower-confidence value is discarded after logging. Automatic chronological precedence is not implemented in deterministic code. *(Both reviewers, Q2)*

3. **The losing value is not preserved.** `UNIQUE (company_id, fact_key)` forces one live row per key; the replacement path is an in-place `UPDATE`. No prior value, supersession link, or conflict record survives. *(Both reviewers, D3)*

4. **`memory_events` appends; `memory_facts` substitutes.** The two behaviours coexist on different tables. `memory_events` does not serve as a conflict-provenance record and receives no row when a fact is overwritten. *(Both reviewers, Q6)*

5. **No provenance is recorded.** The schema carries no column for resolution basis, sources weighed, or residual uncertainty. *(Both reviewers, E9/Q5)*

6. **Conflicts are not retrievable.** A detected conflict produces a log line and nothing queryable. *(Both reviewers, E11)*

7. **All other contradiction handling is prompt-instruction text** routed to a `truth_validation.contradictions` output field, unenforced by any deterministic check. *(Both reviewers, E3)*

8. **No test covers the conflict path.** The two existing references use fake or mock memory repositories that do not exercise conflicting values. *(Both reviewers, E8/Q9)*

9. **The five Article III.7 epistemic categories are not represented in code,** and no `evidence_conflict` state exists in code or schema. Any future `evidence_conflict` must be an orthogonal state or status, not a sixth category. *(Both reviewers, Q8)*

10. **Remediation requires an OME data-model change** and is **Sprint-scale**, requiring coordinated write-path and read-path changes. *(Both reviewers, Q5/Q6/Q10/Q11)*

11. **The behaviour fits within the existing nine Runtime Components.** No component addition, removal, rename, or reordering is required. *(Both reviewers — Claude Code §10; Codex Q7 and Feasibility Assessment)*

**Positions not adopted as the engineering position of record.** The following were held by one reviewer only and are recorded as attributed positions, not as accepted findings: Claude Code's characterisation of the mechanism as a third ungoverned doctrine and its finding that live prompt text leans toward memory precedence contrary to EBD-003 §12.3; Claude Code's adjacent finding AF-1; Codex's recommended OME/OCE/NCE/NCO allocation under Q7; Codex's `memory_events.logic_json` no-migration MVP path. Each is carried forward at §10 where follow-up is required.

---

## 4. Final Conformance Classification

> ## **PARTIALLY CONFORMANT (§7.2)**

**Founder ruling.** The final conformance classification of the NAWA runtime against Constitution Article V.2, as evidenced at pinned commit `26d5bab03cdad52a0d7febd34d6600bee742ce82`, is **Partially Conformant**.

**Attribution of the resolved split.** EFR-EBD-005 §7 provides that where the reviewers do not converge, both classifications are recorded with attribution and the Founder decides at §13.3. The two attributed positions were:

- **Claude Code — Non-conformant (§7.3).** "No site in the codebase evidences the combination Article V.2 requires (investigate, preserve, record provenance, append-not-substitute) for any fact conflict."
- **Codex — Partially conformant (§7.2).** "'Non-conformant' is too broad because a deterministic conflict detection branch and appendable memory event substrate do exist."

**The Founder resolves this split in favour of Partially Conformant.** Claude Code's §7.3 position is recorded, preserved, and not adopted. It is not withdrawn, amended, or overruled as an engineering finding — it stands as filed and sealed. The classification of record for governance purposes is Partially Conformant.

**"Already conformant" was not available and was not proposed.** Both reviewers marked the §7.1 T1–T6 evidence threshold N/A; both stated the threshold is not met.

**Consequence under §7.2, as the governing task states it:** "EBD-005 carries both a text change and a bounded implementation change. The EFR recommends ENG-CONF-001 activation and defines its evidenced scope." The Founder's disposition of ENG-CONF-001 is recorded at §7 of this decision.

---

## 5. Final Disposition of D1, D2 and D3

Each axis was assessed separately by both reviewers, as required by §3.2 and §7.0. The Founder's disposition of each is recorded below alongside the two attributed reviewer positions.

### D1 — Automatic chronological deference vs. investigation toward best-supported current understanding

> ### **NOT SATISFIED**

| Source | Position |
|---|---|
| **Claude Code** | **Neither doctrine; not satisfied.** Timestamps are never compared in the decision; no reasoning or evidentiary weighing occurs. |
| **Codex** | **Not satisfied.** "partially present behavior but not conformant to Article V.2 as runtime evidence." |
| **Founder disposition** | **Not Satisfied.** |

**Both reviewers agreed.** The Founder's disposition confirms the converged position. No investigation mechanism in the Article V.2 sense is evidenced in the runtime.

### D2 — Silent resolution vs. conflict detection and preservation

> ### **PARTIALLY SATISFIED** — detection exists but preservation/provenance remains incomplete

| Source | Position |
|---|---|
| **Claude Code** | **Not satisfied.** Detection is momentarily non-silent, but "preservation and retrievability do not exist at all"; `truth_validation.contradictions` is "written-only, never retrieved." |
| **Codex** | **Partially satisfied at detection only.** "conflict detection exists at one storage site and prompt instructions exist, but preservation/retrievability are insufficient." |
| **Founder disposition** | **Partially Satisfied** — detection exists but preservation/provenance remains incomplete. |

**The reviewers diverged on this axis.** The Founder resolves the divergence at Partially Satisfied. Claude Code's "not satisfied" position is recorded, preserved, and not adopted. Both reviewers agree without qualification that **preservation and retrievability are absent**; the Founder's disposition does not disturb that agreed finding, and the incompleteness is expressly carried into ENG-CONF-001 scope at §7.

### D3 — Substitution/overwrite vs. append-with-provenance and preservation of prior records

> ### **NOT SATISFIED**

| Source | Position |
|---|---|
| **Claude Code** | **Not satisfied, unambiguously.** "the prior `fact_value` is not written anywhere else first — it is gone." |
| **Codex** | **Not satisfied.** "no resolution record captures sources weighed, basis, residual uncertainty, and provenance." |
| **Founder disposition** | **Not Satisfied.** |

**Both reviewers agreed.** The Founder's disposition confirms the converged position.

### Axis summary

| Axis | Claude Code | Codex | **Founder disposition** |
|---|---|---|---|
| **D1** | Not satisfied | Not satisfied | **Not Satisfied** |
| **D2** | Not satisfied | Partially satisfied at detection only | **Partially Satisfied** |
| **D3** | Not satisfied | Not satisfied | **Not Satisfied** |

The Partially Conformant classification at §4 rests on these three dispositions considered together, consistent with §7.0's requirement that the classification follow from the axis results rather than being assigned first and justified afterward.

---

## 6. Founder Ruling on Sprint EX-2

> ### **CONTINUE**
> **ENG-CONF-001 shall be completed as an early engineering task before constitutional conformance is considered complete.**

**Founder ruling.** Sprint EX-2 continues. It is not blocked, not deferred, and not held pending completion of ENG-CONF-001. ENG-CONF-001 shall be sequenced as an **early engineering task** within the work ahead, and **constitutional conformance is not considered complete until ENG-CONF-001 is complete.**

**Attribution of the resolved split.** The two attributed reviewer positions were:

- **Claude Code — Non-blocking**, as currently scoped, with an explicit provisional caveat that this rests on the absence of any Sprint EX-2 scope document rather than on a confirmed absence of overlap.
- **Codex — Blocking — sequencing**, for work touching OME memory schema/repository, OCE context, NCE reasoning prompts/runtime, or NCO orchestration.

**Both reviewers independently established the same underlying fact:** Sprint EX-2 has no canonical scope definition at the pinned commit. The Founder's ruling does not adopt either reviewer's §8 label verbatim. It is issued in the Founder's own authority under §13.8, which reserves the Sprint EX-2 relationship as a separate decision not implied by acceptance of the findings.

**Both explicit Question 11 statements, as recorded by each reviewer:**

| Statement | Claude Code | Codex |
|---|---|---|
| Requires an OME data-model change? | **Yes** | **Yes** — "unless governance accepts a weaker `memory_events.logic_json` convention" |
| Does Sprint EX-2 use the same surfaces? | **Cannot be determined from the pinned commit** — no EX-2 scope document exists; `EXECUTION_BOARD.md:77` does not name OME or memory surfaces | **"Appears likely"** to use the same OME/OCE/NCO surfaces; exact scope "inactive and not fully evidenced," collision details "partly Unknown" |

**Surfaces flagged by both reviewers as simultaneously in play.** Whoever scopes Sprint EX-2 is directed to check it against these before activation of any overlapping work:

- `app/services/memory/repository.py` and the `memory_facts` / `memory_events` tables
- `migrations/` — a new migration file
- Every reader of `memory_facts`: `openai_client.py`, `decision_context.py`, and `pipeline.py`'s `store_ome_foundation()`
- OCE context assembly, NCE reasoning prompts/runtime, and NCO orchestration

**Standing constraint.** Because ENG-CONF-001 requires an OME data-model change on which both reviewers agree, Sprint EX-2 work touching the surfaces listed above must be coordinated with ENG-CONF-001 sequencing. Continuation of Sprint EX-2 is not authorization to modify those surfaces independently of ENG-CONF-001.

---

## 7. Founder Ruling on ENG-CONF-001

> ### **APPROVED** — as the required engineering remediation

**Founder ruling.** ENG-CONF-001 — Constitutional Conformance Remediation (Memory Precedence) — is **approved and authorized** as the required engineering remediation for CONFLICT-01. This satisfies §13.4 and converts the conditional proposed task of §9 into an authorized task.

Consistent with the Sprint EX-2 ruling at §6, ENG-CONF-001 is to be **sequenced as an early engineering task**, and constitutional conformance is not considered complete until it is complete.

### 7.1 Approved scope

Scope is bounded by the gaps both sealed findings evidenced, per §9.2 condition 4. The following elements appear in both reviewers' evidenced scopes and are approved:

| # | Approved scope element | Claude Code | Codex |
|---|---|---|---|
| S1 | **Durable conflict/resolution representation in OME**, with the schema change required to record resolution basis, sources weighed, residual uncertainty and provenance | items 1, 3 (scope) | items 1, 3 |
| S2 | **Append-not-substitute semantics** — prior and conflicting fact assertions preserved rather than overwritten, with an appended resolution/supersession record | item 2 | item 2 |
| S3 | **Retrievability** — conflicts and resolutions queryable after the fact | item 4 | item 4 |
| S4 | **Tests** covering detection, preservation, provenance, residual uncertainty, retrievability, and D1/D2/D3 behaviour | item 5 | item 6 |

**Coordinated read-path update is included within S2,** both reviewers having recorded that append-not-substitute cannot be delivered by write-path change alone. Claude Code names the specific readers requiring update: `get_fact_by_key`, `fetch_facts`, `build_company_profile`.

### 7.2 Scope elements requiring a further Founder scope decision

Two elements appear in one reviewer's evidenced scope only. Per §9.2 condition 4, ENG-CONF-001 may not exceed the evidenced scope, and expansion requires a new Founder decision. **These two are not approved or declined by this decision** and are carried forward at §10:

| Element | Held by | Status |
|---|---|---|
| **Source-provenance signal threaded from call sites to `upsert_fact()`**, so the mechanism can distinguish current validated input from institutional memory. Claude Code states this is "required for any future implementation of EBD-003 §12.3 or Article V.2, whichever the Founder ultimately ratifies, since neither can be implemented without this signal existing at all." | Claude Code only | **Open — scope decision required** |
| **Integrate OCE / NCE / NCO responsibilities** into conflict handling without changing the nine-component architecture. | Codex only | **Open — scope decision required** |

### 7.3 Binding conditions carried forward from §9.2

| # | Condition | Status under this decision |
|---|---|---|
| 1 | Recommendation does not authorize execution | **Superseded** — the Founder has now authorized ENG-CONF-001 at §7 above |
| 2 | Founder authorization and scheduling mandatory before work begins | **Authorization granted.** Scheduling to be set when ENG-CONF-001 is sequenced as an early task |
| 3 | No runtime implementation before EBD-005 ratification, absent explicit Founder exception | **Open — see §10, item R2.** Ratification occurs at gate 5 under EBD-003 §17.1. This decision does not record an explicit exception |
| 4 | Scope bounded by evidenced scope; expansion requires a new Founder decision | **In force.** Approved scope at §7.1; two open elements at §7.2 |
| 5 | Adjacent findings excluded from ENG-CONF-001 scope | **In force.** Claude Code's AF-1 is excluded — see §10, item R4 |
| 6 | Classification is a Standalone Governance Obligation filed in `governance_obligations/`, not Sprint work unless the Founder later assigns it | **In force**, as modified by the §6 ruling that ENG-CONF-001 is sequenced as an early engineering task |
| 7 | Peer review under EBD-002 §4.4 applies to ENG-CONF-001 implementation | **In force** |
| 8 | The task file must exist before execution, per Executive Board Directive #001 | **In force** — see §10, item R1 |

---

## 8. Architecture Freeze — No Escalation Approved

> ### **NO ARCHITECTURE FREEZE ESCALATION IS APPROVED.**

**Founder ruling, stated explicitly.** No escalation of the Architecture Freeze is approved. The unfreeze scope does **not** advance to **Freeze v2.0**. No Freeze escalation of any kind is authorized by this decision.

**Basis in the record.** EFR-EBD-005 §7.3 provides that the unfreeze scope escalates from Freeze v1.1 to v2.0 only "if approved Question 7 concludes the behaviour cannot be placed within the existing Runtime Components without adding, removing, reordering, or renaming one." **Both sealed findings answer Question 7 to the contrary:**

- **Claude Code:** "the recommended work fits inside OME Foundation's existing repository layer and does not require adding, removing, or renaming a Runtime Component."
- **Codex:** "Feasible within the existing nine Runtime Components. No new component, component removal, rename, or pipeline reorder is required." Codex's standalone recommendation 3 adds: "do not escalate to Freeze v2.0 on component-structure grounds based on current evidence."

The §7.3 escalation condition was not triggered on either finding. In any event, the classification of record is §7.2, to which no escalation condition attaches.

**Nothing in this decision ratifies the Tier 1 unfreeze.** Ratification remains reserved to the Founder at gate 5 under EBD-003 §17.1, after Product review. This decision closes the Engineering Feasibility Review only.

---

## 9. Runtime Components — No Structural Change Approved

> ### **NO RUNTIME COMPONENT ADDITIONS ARE APPROVED.**
> ### **NO RUNTIME COMPONENT REMOVALS ARE APPROVED.**
> ### **NO RUNTIME COMPONENT RENAMING IS APPROVED.**
> ### **NO RUNTIME COMPONENT REORDERING IS APPROVED.**

**Founder ruling, stated explicitly and separately for each category.** The nine Runtime Components stand unchanged. ENG-CONF-001 shall be implemented entirely within the existing component set.

| Structural change | Founder ruling |
|---|---|
| Component **additions** | **None approved** |
| Component **removals** | **None approved** |
| Component **renaming** | **None approved** |
| Component **reordering** | **None approved** |

**Basis in the record.** Both sealed findings independently concluded that the remediation fits within the existing components. Codex states the allocation is "distributed responsibility within existing components. It does not require adding, removing, renaming, or reordering Runtime Components." Claude Code states the work "fits inside OME Foundation's existing repository layer."

**Scope boundary.** Any future proposal that would add, remove, rename, or reorder a Runtime Component is **outside ENG-CONF-001 scope** and requires a new Founder decision. It may not be introduced through ENG-CONF-001 implementation.

**Contract-versus-code gaps are not authorization to restructure.** Both reviewers recorded that NCE Lite in the NCO pipeline is a placeholder performing no reasoning, and that live chat reasoning sits in `AIService` prompt assembly. Claude Code records this as a documented-contract-vs-code gap against EBD-004 §4.7. These observations are recorded, and are **not** approval to add, rename, or reorder any component in response. Disposition is carried to §10, item R6.

---

## 10. Required Engineering Follow-Up

The following items are required or remain open. Items marked **Open** were not decided by this Founder Decision and require a further Founder ruling before the affected work proceeds. Recording them here is a disposition of custody, not a decision on their merits.

| # | Item | Type | Owner | Basis |
|---|---|---|---|---|
| **R1** | **Create the ENG-CONF-001 task file** in `docs/execution/governance_obligations/` before any execution begins, per Executive Board Directive #001 and §9.2 condition 8. The task file must carry the approved scope S1–S4 and record the two open scope elements at §7.2 as excluded pending decision. | Required | Engineering Team | §9.2 cond. 8 |
| **R2** | **Founder to grant or withhold the explicit exception** permitting runtime implementation before EBD-005 ratification, per §9.2 condition 3. ENG-CONF-001 is authorized but this condition is unresolved; ratification occurs at gate 5 under EBD-003 §17.1. Sequencing ENG-CONF-001 as an early task makes this decision time-sensitive. | **Open** | Founder | §9.2 cond. 3; §13.5 |
| **R3** | **Founder to fix the two open scope elements** at §7.2 — Claude Code's source-provenance signal threading, and Codex's OCE/NCE/NCO integration. Neither may be implemented under ENG-CONF-001 until decided, per §9.2 condition 4. | **Open** | Founder | §7.2; §13.4 |
| **R4** | **Classify adjacent finding AF-1** for separate governance handling. Claude Code records that `upsert_fact()`'s non-conflicting paths also overwrite in place with no history, so `memory_facts` retains no historical record for *any* update, potentially implicating Article VII.5 beyond CONFLICT-01. Codex recorded no adjacent findings. AF-1 is excluded from ENG-CONF-001 scope per §9.2 condition 5 and does not expand EBD-005. | **Open** | Founder | §3.3; §13.6 |
| **R5** | **Rule on the interim-MVP question.** Codex records that `memory_events.logic_json` / `context` "could host an MVP append-only record without migration," while noting it "would likely not satisfy retrievability and provenance threshold T1-T6." Claude Code states a schema migration is required and offers no no-migration path. Whether an interim MVP is acceptable ahead of the full schema change requires a ruling before implementation approach is fixed. | **Open** | Founder | Q5, Q10 |
| **R6** | **Determine disposition of the prompt-layer directional finding.** Claude Code records that live prompt text instructs the model to treat memory as "the source of truth" and "HARD FACTS" (`decision_prompt.py:79`; `memory_prompt.py:16,24`), which it states is the opposite emphasis from EBD-003 §12.3, and reports it as a finding of substance independent of Article V.2. Codex records the same prompt text without that framing. Whether this falls in ENG-CONF-001 scope, becomes a separate obligation, or is noted only, is undecided. | **Open** | Founder | §13.4, §13.6 |
| **R7** | **Direct disposition of the non-matching archived finding file.** Claude Code's custody addendum §2.2 reports `docs/execution/governance_obligations/ARCHIVE_EFR-EBD-005_FINDING_CLAUDE_CODE.md` in the canonical repository (hash `90f3e80c…`, 30,833 bytes, 270 lines, internal seal timestamp `2026-08-04T20:25:05Z`, internal seal hash `871b40a7…`), which the reviewer expressly disclaims: "I am not treating this file as the sealed finding, a valid copy of it, or my work product." The file is not present in the COWORK mirror. Disposition is a custody matter, not an engineering one. | **Open** | Founder / COWORK | Comparison CN-4; §13.2 |
| **R8** | **Product review at gate 4** (Aboura). Claude Code refers one question there specifically: whether removing the confidence-race mechanism would break product behaviour implicitly relying on it — naming `expansion_market`'s repeated-value confidence accumulation (`repository.py:146-191`) as "a real, apparently intentional feature" that a naive rewrite "could silently break." Claude Code states this is a product judgment it cannot resolve from code. | Required | Product (Aboura) | Claude Code §11 item 3; §1.3 gate chain |
| **R9** | **Coordinate Sprint EX-2 scope against the OME surfaces** listed at §6 before activating any EX-2 work touching them. Both reviewers recorded that EX-2 has no canonical scope document at the pinned commit, so overlap cannot be assessed until EX-2 is scoped. | Required | Engineering Team | §6; Q11 both reviewers |
| **R10** | **Peer review under EBD-002 §4.4** applies to ENG-CONF-001 implementation, per §9.2 condition 7. | Required | Claude Code / Codex | §9.2 cond. 7 |

**R2 is the nearest-term item.** ENG-CONF-001 is authorized and is to be sequenced early, but §9.2 condition 3 bars runtime implementation before EBD-005 ratification absent an explicit Founder exception, and this decision does not record one.

---

## 11. Closure Statement

**EFR-EBD-005 — Engineering Feasibility Review for EBD-005 (CONFLICT-01 / Tier 1 Unfreeze) — is CLOSED.**

This Founder Decision is the terminal instrument for EFR-EBD-005. It is issued under the Founder Decision Gate at §13 and closes the obligation.

**Recorded on closure:**

- The final conformance classification is **Partially Conformant (§7.2)**.
- **D1: Not Satisfied. D2: Partially Satisfied** — detection exists, preservation and provenance remain incomplete. **D3: Not Satisfied.**
- **ENG-CONF-001 is approved** as the required engineering remediation, scoped per §7.1, with two scope elements open per §7.2.
- **Sprint EX-2 continues**, with ENG-CONF-001 sequenced as an early engineering task; constitutional conformance is not complete until ENG-CONF-001 is complete.
- **No Architecture Freeze escalation is approved.** No advance to Freeze v2.0.
- **No Runtime Component additions, removals, renames, or reorderings are approved.**
- Both sealed findings **stand as filed, sealed, and unmodified**, with their disagreements preserved and attributed. Where the Founder resolved a split, the non-adopted position is recorded and preserved, not withdrawn or overruled as an engineering finding.
- **Archived comparison reports are superseded and are not authoritative.**
- Ten follow-up items are recorded at §10; **six require a further Founder ruling** and are carried forward beyond this closure.

**What this decision does not do.** It does not ratify EBD-005. It does not ratify the Tier 1 unfreeze — ratification occurs at gate 5 under EBD-003 §17.1, after Product review, and only by the Founder. It does not authorize any runtime change beyond the approved ENG-CONF-001 scope, and does not by itself satisfy §9.2 condition 3. It does not activate or scope Sprint EX-2 beyond the ruling at §6. It does not modify any finding, custody addendum, comparison, governance document, or runtime file.

**Custody of the closed record:**

| Artifact | Authoritative hash |
|---|---|
| `EFR-EBD-005_FINDING_CLAUDE_CODE.md` | `f80a39627a9b2ee2952470bd72b682acc87ed71b8f009811d3403f3682a88f87` |
| `EFR-EBD-005_FINDING_CODEX.md` | `8e46bb4041cb63858e76e8f6f9b562a3c200b21bbc688ec77d3c0fdd82b88576` |
| Pinned commit, both findings | `26d5bab03cdad52a0d7febd34d6600bee742ce82` |

---

**Decision issued by:** Founder.
**Recorded by:** COWORK (CTO / Chief of Staff), §12 procedural custody. COWORK verified procedure only, did not assess, endorse, correct, or overrule any engineering conclusion, and authored no part of either finding.
**Decision date:** 2026-08-07.

---

EFR-EBD-005 CLOSED

No further engineering review is required to close this obligation.

No independent engineering judgment was added by the recording officer.
