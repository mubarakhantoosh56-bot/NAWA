# Executive Board Decision #006 — Constitutional Governance Alignment

**Status:** Ratified. In force.
**Version:** 1.0
**Category:** Governance
**Subordinate to:** NAWA Reasoning Constitution v1.0 (ratified 2026-07-31). Where this decision conflicts with a Constitutional article, the Constitution prevails and this decision is amended.
**Scope:** Align EBD-001 through EBD-004 with the ratified NAWA Reasoning Constitution v1.0 by declaring Constitutional supremacy in each document, recording the Constitution as supreme authority in the EBD-001 Source of Truth Rules, and correcting stale Codex-specific engineering-role references in EBD-001 (DEBT-01).
**Non-scope:** CONFLICT-01 and the Tier 1 unfreeze (EBD-005). All Constitution-to-EBD gaps (GAP-01 through GAP-07b). Addition of a Constitutional Documents category to EBD-001 §3 (deferred — triggers MAJOR transition per EBD-001 §12.5). Any Architecture Freeze change. Any runtime, contract, or product change.
**Owner:** Founder & CEO (Mubarak).
**Approval authority:** Founder & CEO.
**Effective date:** 2026-08-01.
**Last updated:** 2026-08-01.
**Precedence:** Precedes EBD-005. Must be applied and verified before EBD-005 is applied.

---

## 1. Purpose and Authority

The NAWA Reasoning Constitution v1.0 was ratified 2026-07-31 and is in force. Article VIII.1 establishes Constitutional supremacy over all downstream governance. Article VIII.4 requires downstream governance to operationalize the Constitution without contradicting it.

EBD-001 through EBD-004 were all ratified before the Constitution existed. None declares subordination to it. This decision closes that gap.

This decision also corrects DEBT-01: EBD-001 continues to reference a Codex-specific engineering role superseded by the AI Engineering Team in EBD-002. The correction is included here because EBD-001 is already being amended, avoiding a second amendment cycle on the same document.

## 2. Path B Scope Decision

EBD-001 §12.5 provides that amendments changing the categories in Section 3 produce a new MAJOR version and require Executive Board re-ratification. Adding a Constitutional Documents category would therefore force EBD-001 to v2.0, a new file, archival of v1, and Board re-ratification.

The Constitution does not require a Constitutional Documents category in EBD-001. Article VIII.4 requires downstream governance to operationalize the Constitution without contradicting it; the supremacy declaration and the Source of Truth row achieve that.

**Path B is adopted.** The category addition is deferred and queued for whenever EBD-001 next requires a MAJOR revision on independent grounds.

## 3. Amendments

**Thirteen amendments are applied across four existing documents. One amendment, AMEND-10, is explicitly deferred and is not applied.**

| Target | Applied amendments | Count |
|---|---|---|
| EBD-001 | AMEND-08, 09, 14, 15, 16, 17, 18 | 7 |
| EBD-002 | AMEND-11, 19 | 2 |
| EBD-003 | AMEND-12, 20 | 2 |
| EBD-004 | AMEND-13, 21 | 2 |
| **Total applied** | | **13** |
| **Deferred (not applied)** | AMEND-10 — Constitutional Documents category, EBD-001 §3 | **1** |

Full amendment text at Appendix A.

## 4. Version Effects

| Document | Doc version | Freeze version | Effect |
|---|---|---|---|
| EBD-001 | v1.0 → **v1.1** | n/a | MINOR — substantive, no structural or category change |
| EBD-002 | v1.0 → **v1.1** | n/a | MINOR — header declaration only |
| EBD-003 | v1.0 → **v1.1** | **v1.0 — unchanged** | MINOR — header declaration only. No freeze element touched. |
| EBD-004 | v1.0-MVP → **v1.1-MVP** | n/a | MINOR — header declaration only. No contract touched. |

No document reaches MAJOR. No file is archived. No filename changes. No Executive Board re-ratification is required.

## 5. Relationship to EBD-005

EBD-006 precedes EBD-005. EBD-005 subsequently advances EBD-003 to document v1.2 with Architecture Freeze v1.1, and EBD-004 to v1.2-MVP. The two decisions are independent in substance and sequential in application.

EBD-006 touches no Tier 1 or Tier 2 frozen element and therefore requires no unfreeze process, no Engineering feasibility review, and no Product review.

## 6. Ratification Metadata Operation

On the Founder's formal ratification signal, the following metadata operation is applied to this document. Until that signal, this document remains Draft.

| Field | Value on ratification |
|---|---|
| **Status** | `Ratified. In force.` |
| **Effective date** | `2026-08-01` |
| **Last updated** | `2026-08-01` |
| **Founder ratification record** | Mubarak, Founder and CEO of NAWA, 2026-08-01 |

The ratification event is recorded in Appendix B of this document. No Constitutional principle, article, amendment text, or verification requirement changes as part of the ratification metadata operation.

## 7. Application and Verification Plan

### 7.1 Executor and Boundaries

**Application is executed by Claude Code in the canonical repository:**

- **Repository:** `C:\AIMX_PROJECTS`
- **Branch:** `claude-safe-review`

**Cowork (CTO / Chief of Staff) remains responsible for the exact governance text and for verification review.** Cowork does not write to the canonical repository.

**Staging constraint — binding:** Claude Code stages and commits **only** the five governance files listed in §7.2. **`git add .` must not be used.** Each path is staged explicitly. The repository contains unrelated uncommitted work that must not enter this commit.

### 7.2 Files Affected

```
docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md
docs/governance/EBD-002_GOVERNANCE_MODEL.md
docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md
docs/governance/EBD-004_ENGINE_DEFINITIONS.md
docs/governance/EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md   (new)
```

Four existing files amended. One new file created. No file archived, renamed, or deleted.

### 7.3 Phase 1 — Pre-application baseline

1. Record SHA-256 of the four existing target files, as they exist in the canonical repository.
2. Record SHA-256 of `docs/governance/NAWA_REASONING_CONSTITUTION_v1.md` as the Constitution integrity baseline.
3. **Confirm the five EBD-006 target paths carry no pre-existing uncommitted changes.** A globally clean working tree is **not** required; unrelated uncommitted work elsewhere in the repository is expected and permitted.

Baseline check, scoped to the package paths only:

```
git status --porcelain -- docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md \
                          docs/governance/EBD-002_GOVERNANCE_MODEL.md \
                          docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md \
                          docs/governance/EBD-004_ENGINE_DEFINITIONS.md \
                          docs/governance/EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md \
                          docs/governance/NAWA_REASONING_CONSTITUTION_v1.md
```

Expected: empty output. Any output indicates pre-existing changes on a package path — halt and report.

### 7.4 Phase 2 — Application (atomic)

4. Create `EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md`.
5. Apply AMEND-08, 09, 14, 15, 16, 17, 18 to EBD-001.
6. Apply AMEND-11, 19 to EBD-002.
7. Apply AMEND-12, 20 to EBD-003.
8. Apply AMEND-13, 21 to EBD-004.

No partial application. If any step fails, roll back all.

### 7.5 Phase 3 — Verification

All eleven checks must pass.

| # | Check | Pass condition |
|---|---|---|
| V1 | Supremacy declaration | `Subordinate to: NAWA Reasoning Constitution v1.0` appears exactly once in each of the four amended documents |
| V2 | Versions | EBD-001 `1.1`; EBD-002 `1.1`; EBD-003 Document `1.1` and Architecture Freeze `v1.0`; EBD-004 `1.1-MVP` |
| V3 | Last updated | All four carry `2026-08-01` |
| V4 | DEBT-01 cleared | Zero occurrences of the stale Codex-specific engineering-role phrase anywhere in EBD-001, including Appendix D. AMEND-18 amendment-log wording deliberately avoids reintroducing the phrase, so a zero-occurrence check is valid document-wide. |
| V5 | Replacement present | `AI Engineering Team` present at the four DEBT-01 locations |
| V6 | Source of Truth row | Constitution row is the first data row of the EBD-001 §4 table |
| V7 | Amendment logs | Exactly one new row in each of the four documents' amendment logs |
| V8 | **Freeze untouched** | EBD-003 §12.3 still reads `Company Brain Never Overrides Facts`. **EBD-006 must not touch it — that is EBD-005 scope.** |
| V9 | **Constitution integrity** | `git diff --quiet -- docs/governance/NAWA_REASONING_CONSTITUTION_v1.md` returns clean **and** the file's SHA-256 matches the Phase 1 baseline recorded from the canonical repository. The baseline is the repository's own pre-application hash, not a hard-coded historical value, since line-ending normalization may cause the canonical hash to differ legitimately from a working-mirror hash. |
| V10 | No collateral change | `git diff` review confirms only the specified locations changed in the five package files |
| V11 | Post-application hashes | SHA-256 recorded for all five package files |

**V8 is the critical guard.** EBD-006 and EBD-005 amend the same two documents. V8 confirms EBD-006 did not stray into EBD-005 scope.

**V9 is the Constitution guard.** The Constitution must be byte-identical before and after. Verification is against the repository's own baseline plus a zero Git diff, not against an external hash.

### 7.6 Phase 4 — Rollback trigger

Any verification failure → restore the four amended files to their Phase 1 baseline, delete the new EBD-006 file, report the failure. No partial state is staged or committed.

### 7.7 Phase 5 — Staging and commit

Only after all eleven verifications pass. Explicit staging, one path at a time:

```
git add docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md
git add docs/governance/EBD-002_GOVERNANCE_MODEL.md
git add docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md
git add docs/governance/EBD-004_ENGINE_DEFINITIONS.md
git add docs/governance/EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md
```

Then `git status` to confirm exactly five staged files and no others, before committing with the message at §7.8.

### 7.8 Commit Message

```
docs(governance): EBD-006 Constitutional Governance Alignment

Align EBD-001 through EBD-004 with the ratified NAWA Reasoning
Constitution v1.0 (2026-07-31).

Constitutional supremacy declarations:
- EBD-001 Documentation Standard      v1.0 -> v1.1
- EBD-002 Governance Model            v1.0 -> v1.1
- EBD-003 Architecture Freeze         doc v1.0 -> v1.1 (Freeze remains v1.0)
- EBD-004 Engine Definitions (MVP)    v1.0-MVP -> v1.1-MVP

EBD-001 additional changes:
- Removed "Constitutional" from Status line; superseded by the
  NAWA Reasoning Constitution v1.0
- Added the Constitution as supreme authority in Section 4
  Source of Truth Rules
- DEBT-01: corrected stale Codex-specific engineering-role
  references to "AI Engineering Team" (4 locations)

EBD-003 additional changes:
- Version field split into Document version and Architecture
  Freeze version to distinguish the two axes explicitly
- Status corrected: Tier 2 active per EBD-004, no longer pending

Deferred:
- Constitutional Documents category in EBD-001 Section 3.
  Would trigger MAJOR version transition and Executive Board
  re-ratification per EBD-001 Section 12.5. Path B adopted.

Not included:
- CONFLICT-01 resolution and Tier 1 unfreeze (EBD-005, pending
  Engineering Feasibility Review)
- Architecture Freeze remains v1.0; no frozen element modified
- No runtime, contract, or product change

13 amendments applied across 4 documents; 1 deferred (AMEND-10).
Amendment logs updated in all four documents.
Authority: Founder & CEO via EBD-006.
Ref: EBD-006
```

## 8. Final Principles

- Constitutional supremacy is declared, not implied.
- No ratified document is silently edited. Every change carries a version, a date, and an amendment-log entry.
- Path B keeps governance overhead proportionate. The Constitution is satisfied without forcing a MAJOR transition that serves documentation aesthetics rather than Constitutional requirement.
- This decision touches no frozen element, no runtime behavior, and no product surface.
- Application is atomic and verified. A partial application is a failed application.

---

## Appendix A — Amendment Schedule

### EBD-001 — `docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md`

**AMEND-08 — Header block**

*Current:*
```
**Status:** Ratified as Executive Board Decision #001. Constitutional.
**Version:** 1.0
**Phase:** Runtime Validation Phase.
```

*Amended:*
```
**Status:** Ratified as Executive Board Decision #001.
**Version:** 1.1
**Subordinate to:** NAWA Reasoning Constitution v1.0 (ratified 2026-07-31). Where this Standard conflicts with a Constitutional article, the Constitution prevails and this Standard is amended.
**Phase:** Runtime Validation Phase.
```

Plus: `**Last updated:** 2026-07-03.` → `**Last updated:** 2026-08-01.`

*Note:* "Constitutional." is removed from the Status line. With the NAWA Reasoning Constitution ratified, EBD-001's claim to constitutional standing would create a supremacy ambiguity contrary to Constitution Article VIII.1.

**AMEND-09 — §4 Source of Truth Rules**

Insert as the first data row of the table, immediately after the header row:

```
| **Permanent reasoning philosophy — identity, reasoning foundations, reasoning process, decision discipline, authority, organizational memory and learning** | NAWA Reasoning Constitution v1.0 — **supreme authority over every row below** | `docs/governance/NAWA_REASONING_CONSTITUTION_v1.md` |
```

**AMEND-10 — DEFERRED. NOT APPLIED.**

Constitutional Documents category, EBD-001 §3. Triggers MAJOR version transition and Executive Board re-ratification per EBD-001 §12.5. Deferred under Path B.

**AMEND-14 — §3.5 (line 106)**

*Current:* `- **Primary owner:** CTO, with authorship by Lead Software Engineer (Codex) or delegated engineers.`
*Amended:* `- **Primary owner:** CTO, with authorship by the AI Engineering Team or delegated engineers.`

**AMEND-15 — §3.6 (line 114)**

*Current:* `- **Primary owner:** CTO, with contributions from Lead Software Engineer.`
*Amended:* `- **Primary owner:** CTO, with contributions from the AI Engineering Team.`

**AMEND-16 — §5 Ownership table (line 193)**

*Current:* `| **Lead Software Engineer (Codex)** | Implementation-close technical documents (module contracts, service designs authored during implementation) | Architecture Documents affecting their work | Implementation, test authorship, code-close documentation |`
*Amended:* `| **AI Engineering Team** | Implementation-close technical documents (module contracts, service designs authored during implementation) | Architecture Documents affecting their work | Implementation, test authorship, code-close documentation |`

**AMEND-17 — §12.1 Executive Board (line 447)**

*Current:* `- Lead Software Engineer (Codex) — execution review authority; participates when the decision affects implementation.`
*Amended:* `- AI Engineering Team — execution review authority; participates when the decision affects implementation.`

**AMEND-18 — Appendix D Amendment Log, new row**

```
| 1.1 | 2026-08-01 | Constitutional Governance Alignment per EBD-006. Removed "Constitutional" from Status line — superseded by NAWA Reasoning Constitution v1.0. Added Constitutional supremacy declaration. Added the Constitution as supreme authority in §4 Source of Truth Rules. Corrected stale Codex-specific engineering-role references to "AI Engineering Team" at §3.5, §3.6, §5, §12.1 (DEBT-01). Constitutional Documents category (§3) deferred — would trigger MAJOR per §12.5. | Founder & CEO | EBD-006 |
```

### EBD-002 — `docs/governance/EBD-002_GOVERNANCE_MODEL.md`

**AMEND-11 — Header block**

*Current:*
```
**Version:** 1.0
**Category:** Governance
```

*Amended:*
```
**Version:** 1.1
**Category:** Governance
**Subordinate to:** NAWA Reasoning Constitution v1.0 (ratified 2026-07-31). Where this decision conflicts with a Constitutional article, the Constitution prevails and this decision is amended.
```

Plus: `**Last updated:** 2026-07-03.` → `**Last updated:** 2026-08-01.`

**AMEND-19 — Appendix D Amendment Log, new row**

```
| 1.1 | 2026-08-01 | Constitutional Governance Alignment per EBD-006. Added Constitutional supremacy declaration to header block. No article, principle, KPI, approval-matrix, or role change. | Founder & CEO | EBD-006 |
```

### EBD-003 — `docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md`

**AMEND-12 — Header block**

*Current:*
```
**Status:** Ratified by Founder as Executive Board Decision #003. Tier 1 active; Tier 2 pending EBD-004.
**Version:** 1.0
**Category:** Governance (architectural constraints applied under authority granted by EBD-002).
```

*Amended:*
```
**Status:** Ratified by Founder as Executive Board Decision #003. Tier 1 active; Tier 2 active per EBD-004.
**Document version:** 1.1
**Architecture Freeze version:** v1.0
**Category:** Governance (architectural constraints applied under authority granted by EBD-002).
**Subordinate to:** NAWA Reasoning Constitution v1.0 (ratified 2026-07-31). Where this decision conflicts with a Constitutional article, the Constitution prevails and this decision is amended.
```

Plus: `**Last updated:** 2026-07-03.` → `**Last updated:** 2026-08-01.`

*Notes:* The single `**Version:**` field is replaced by the two-axis pair to distinguish document version from Architecture Freeze version explicitly. The Status line is corrected — EBD-004 ratified 2026-07-03, so Tier 2 is active, not pending. Per EBD-001 §7, cross-reference fixes do not themselves affect version.

**AMEND-20 — Appendix C Amendment Log, new row**

```
| 1.1 | 2026-08-01 | Constitutional Governance Alignment per EBD-006. Added Constitutional supremacy declaration to header block. Version field split into Document version and Architecture Freeze version. Status corrected — Tier 2 active per EBD-004, no longer pending. **Architecture Freeze remains v1.0. No freeze element modified.** | Founder & CEO | EBD-006 |
```

### EBD-004 — `docs/governance/EBD-004_ENGINE_DEFINITIONS.md`

**AMEND-13 — Header block**

*Current:*
```
**Version:** 1.0-MVP
**Category:** Governance (contracts applied under authority granted by EBD-002 and EBD-003).
```

*Amended:*
```
**Version:** 1.1-MVP
**Category:** Governance (contracts applied under authority granted by EBD-002 and EBD-003).
**Subordinate to:** NAWA Reasoning Constitution v1.0 (ratified 2026-07-31). Where this decision conflicts with a Constitutional article, the Constitution prevails and this decision is amended.
```

Plus: `**Last updated:** 2026-07-03.` → `**Last updated:** 2026-08-01.`

**AMEND-21 — Appendix C Amendment Log, new row**

```
| 1.1-MVP | 2026-08-01 | Constitutional Governance Alignment per EBD-006. Added Constitutional supremacy declaration to header block. No contract, Mission, Inputs, Outputs, Never Does, or invariant change. | Founder & CEO | EBD-006 |
```

---

## Appendix B — EBD-006 Ratification Record

| Date | Event | Authority | Reference |
|---|---|---|---|
| 2026-08-01 | Draft prepared for Founder Ratification. Thirteen amendments specified across four documents; one deferred (AMEND-10). | CTO / Chief of Staff (drafting) | TSK-CONST-002 |
| 2026-08-01 | **Formal ratification of Executive Board Decision #006, Version 1.0.** Ratified by Mubarak, Founder and CEO of NAWA. Effective 2026-08-01. Approved: Path B; thirteen applied amendments across EBD-001 through EBD-004; one deferred item (AMEND-10); removal of "Constitutional" from the EBD-001 Status line; correction of the EBD-003 Tier 2 status to active per EBD-004; amendment-log entries in all four amended EBDs; the two-phase versioning model; the atomic application and verification plan; Claude Code as canonical repository executor; and the restriction that only the five specified governance files may be staged and committed, with `git add .` prohibited. | Mubarak, Founder and CEO of NAWA | Founder Ratification, 2026-08-01 |

---

## Appendix C — Amendment Log (EBD-006 itself)

Records amendments to this decision after its own ratification.

| Version | Date | Amendment | Authority | Reference |
|---|---|---|---|---|
| *(no amendments yet)* | — | — | — | — |

---

*This decision aligns NAWA's governance stack with its supreme authority. It changes no principle, no frozen element, no contract, and no runtime behavior. It declares what is already true under Constitution Article VIII.1.*
