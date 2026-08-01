# EFR-EBD-005 — Governance Mirror Refresh Manifest

**Operation:** Refresh the COWORK governance mirror from Git-tracked content at the pinned canonical commit.
**Status:** ✅ **Refresh complete. All six files exported and verified identical.**
**Executed by:** COWORK (CTO / Chief of Staff), under direct Founder instruction of 2026-08-01.
**Export timestamp (UTC):** `2026-08-01T16:11:12Z` (local `2026-08-01 19:11:12 +03:00`).
**Authority:** EFR-EBD-005 Draft 3 §14.1; Founder instruction, 2026-08-01.
**Last updated:** 2026-08-01.

> ⚠️ **Disclosure — read §6 before accepting this manifest.** Two unintended side effects were produced inside the canonical repository's `.git` directory by read-only Git commands. No tracked content, commit, branch, or working-tree file changed. One side effect (a stale `index.lock`) requires action before the next canonical Git operation.

---

## 1. Source Confirmation

| Field | Value |
|---|---|
| Canonical repository | `C:\AIMX_PROJECTS` |
| Source branch | `claude-safe-review` |
| Pinned source commit (short) | `6d5d042` |
| Pinned source commit (full SHA) | `6d5d04277d91dda988c81876ca50318297b9e878` |
| Commit subject | `docs(governance): EBD-006 Constitutional Governance Alignment` |
| Commit date | `Sat Aug 1 18:04:55 2026 +0300` |
| Object type | `commit` |
| Branch contains commit | ✅ `claude-safe-review` |
| Repository HEAD at export time | `6d5d04277d91dda988c81876ca50318297b9e878` — **HEAD equals the pinned commit** |
| Root tree of pinned commit | `ce7430d5bf13c6a44969ec5d5256cf92f4aab89d` |
| Extraction method | `git show 6d5d042:<path>` — Git object database, **not** the working tree |
| COWORK mirror target | `C:\Users\oshub\Documents\Claude\Projects\NAWA AI` |

All six paths were confirmed present in the pinned commit before extraction. No file was absent.

## 2. Six-File Hash Table

Source SHA-256 is computed over the blob content emitted by `git show 6d5d042:<path>`. Mirror SHA-256 is computed over the file as written to the COWORK mirror.

### 2.1 File 1 — NAWA Reasoning Constitution v1.0

| Field | Value |
|---|---|
| Source Git path | `docs/governance/NAWA_REASONING_CONSTITUTION_v1.md` |
| Mirror destination | `docs/governance/NAWA_REASONING_CONSTITUTION_v1.md` |
| Git blob OID | `696b273408559e39d0a436770df6c2e1e83d9fb4` |
| Blob size | 37,424 bytes |
| Source SHA-256 | `e8abc9e4e0b9acf59534e62f905b74192217c81c1e848ff4e87291c9cc2c1812` |
| Mirror SHA-256 | `e8abc9e4e0b9acf59534e62f905b74192217c81c1e848ff4e87291c9cc2c1812` |
| Raw identity | ✅ **PASS** |
| Normalized LF identity | ✅ **PASS** (not required — see §3) |

### 2.2 File 2 — EBD-001 Documentation Standard

| Field | Value |
|---|---|
| Source Git path | `docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md` |
| Mirror destination | `docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md` |
| Git blob OID | `c4ab5a22f3990bb5a1ade790560e8156a65d1446` |
| Blob size | 34,870 bytes |
| Source SHA-256 | `d8f125c4c913d85785e016283691e65ef1cab984dc6fd535d594cc3e7691bea0` |
| Mirror SHA-256 | `d8f125c4c913d85785e016283691e65ef1cab984dc6fd535d594cc3e7691bea0` |
| Raw identity | ✅ **PASS** |
| Normalized LF identity | ✅ **PASS** |

### 2.3 File 3 — EBD-002 Governance Model

| Field | Value |
|---|---|
| Source Git path | `docs/governance/EBD-002_GOVERNANCE_MODEL.md` |
| Mirror destination | `docs/governance/EBD-002_GOVERNANCE_MODEL.md` |
| Git blob OID | `5da9690d578d8d00889f9e2f426bb6a4911a1efd` |
| Blob size | 62,661 bytes |
| Source SHA-256 | `b25756f9627ceb27de509fe462296a83d98891a5befde568488a577fe486953f` |
| Mirror SHA-256 | `b25756f9627ceb27de509fe462296a83d98891a5befde568488a577fe486953f` |
| Raw identity | ✅ **PASS** |
| Normalized LF identity | ✅ **PASS** |

### 2.4 File 4 — EBD-003 Architecture Freeze

| Field | Value |
|---|---|
| Source Git path | `docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md` |
| Mirror destination | `docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md` |
| Git blob OID | `c75bfc3437f3ec900a6358922eafe4570e7e1acc` |
| Blob size | 55,756 bytes |
| Source SHA-256 | `080b66ac1479d730a55e16d22f01a7e000457a3581a615c82fb02ef68d35cc60` |
| Mirror SHA-256 | `080b66ac1479d730a55e16d22f01a7e000457a3581a615c82fb02ef68d35cc60` |
| Raw identity | ✅ **PASS** |
| Normalized LF identity | ✅ **PASS** |

### 2.5 File 5 — EBD-004 Engine Definitions

| Field | Value |
|---|---|
| Source Git path | `docs/governance/EBD-004_ENGINE_DEFINITIONS.md` |
| Mirror destination | `docs/governance/EBD-004_ENGINE_DEFINITIONS.md` |
| Git blob OID | `b33703307acbd4dca91d15937725b72c7ba71b36` |
| Blob size | 25,738 bytes |
| Source SHA-256 | `eb7e93af2bb45b37a95b630e53be4dba3876fda6037f066488447fcce90b25c8` |
| Mirror SHA-256 | `eb7e93af2bb45b37a95b630e53be4dba3876fda6037f066488447fcce90b25c8` |
| Raw identity | ✅ **PASS** |
| Normalized LF identity | ✅ **PASS** |

### 2.6 File 6 — EBD-006 Constitutional Governance Alignment

| Field | Value |
|---|---|
| Source Git path | `docs/governance/EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md` |
| Mirror destination | `docs/governance/EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md` |
| Git blob OID | `8ad27d157db18e3222c4894a692732e5badafab4` |
| Blob size | 20,604 bytes |
| Source SHA-256 | `fd6aa107d18b9b429b650b2a6a0b39565c4d3bf6014623120e82b79a19dba42b` |
| Mirror SHA-256 | `fd6aa107d18b9b429b650b2a6a0b39565c4d3bf6014623120e82b79a19dba42b` |
| Raw identity | ✅ **PASS** |
| Normalized LF identity | ✅ **PASS** |

### 2.7 Summary

| # | File | Raw identity | Normalized LF identity |
|---|---|---|---|
| 1 | NAWA_REASONING_CONSTITUTION_v1.md | ✅ PASS | ✅ PASS |
| 2 | NAWA_DOCUMENTATION_STANDARD_v1.md | ✅ PASS | ✅ PASS |
| 3 | EBD-002_GOVERNANCE_MODEL.md | ✅ PASS | ✅ PASS |
| 4 | EBD-003_ARCHITECTURE_FREEZE_v1.md | ✅ PASS | ✅ PASS |
| 5 | EBD-004_ENGINE_DEFINITIONS.md | ✅ PASS | ✅ PASS |
| 6 | EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md | ✅ PASS | ✅ PASS |

**6 of 6 raw identity PASS. No failures. No fallback to normalized comparison was required.**

## 3. Line-Ending Note

Normalized LF comparison was computed but **was not needed**. All six source blobs contain **zero carriage-return bytes** — they are stored LF-only in the object database, and were written LF-only to the mirror.

| File | CR byte count in source blob |
|---|---|
| NAWA_REASONING_CONSTITUTION_v1.md | 0 |
| NAWA_DOCUMENTATION_STANDARD_v1.md | 0 |
| EBD-002_GOVERNANCE_MODEL.md | 0 |
| EBD-003_ARCHITECTURE_FREEZE_v1.md | 0 |
| EBD-004_ENGINE_DEFINITIONS.md | 0 |
| EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md | 0 |

Raw identity therefore carries the full verification weight. The line-ending normalization concern anticipated in EBD-006 §7.5 check V9 does not arise for this export.

## 4. Post-Refresh Governance State Verification

Read from the refreshed mirror files.

| Document | Required state | Observed | Result |
|---|---|---|---|
| NAWA Reasoning Constitution | v1.0, ratified and in force | `Status: Ratified. In force.` / `Version: 1.0` / `Last updated: 2026-07-31.` | ✅ |
| EBD-001 Documentation Standard | v1.1 | `Version: 1.1` / `Subordinate to:` present / `Last updated: 2026-08-01.` / Status no longer claims "Constitutional." | ✅ |
| EBD-002 Governance Model | v1.1 | `Version: 1.1` / `Subordinate to:` present / `Last updated: 2026-08-01.` | ✅ |
| EBD-003 Architecture Freeze | Document v1.1 / Freeze v1.0 | `Document version: 1.1` / `Architecture Freeze version: v1.0` / `Subordinate to:` present / Status reads `Tier 2 active per EBD-004` / `Last updated: 2026-08-01.` | ✅ |
| EBD-004 Engine Definitions | v1.1-MVP | `Version: 1.1-MVP` / `Subordinate to:` present / `Last updated: 2026-08-01.` | ✅ |
| EBD-006 Constitutional Governance Alignment | v1.0, ratified and in force | `Status: Ratified. In force.` / `Version: 1.0` / `Subordinate to:` present / `Last updated: 2026-08-01.` | ✅ |

**All six expected states confirmed.**

### 4.1 Supplementary integrity observations

| Check | Basis | Observed | Result |
|---|---|---|---|
| V8 — freeze untouched | EBD-006 §7.5 | `EBD-003` line 340 reads `### 12.3 Company Brain Never Overrides Facts` — unmodified, pre-EBD-005 state | ✅ |
| V4 — DEBT-01 cleared | EBD-006 §7.5 | Zero occurrences of the stale Codex-specific engineering-role phrase in EBD-001 | ✅ |
| V5 — replacement present | EBD-006 §7.5 | `AI Engineering Team` present 5× in EBD-001 | ✅ |

These are observations recorded during the refresh. They do **not** constitute the COWORK revalidation required by EFR-EBD-005 Draft 3 §14.2 (checks R1–R8), which is a separate step.

## 5. Files Written

**Exactly seven files were written. All seven are inside the COWORK mirror.**

| # | Path | Action |
|---|---|---|
| 1 | `docs/governance/NAWA_REASONING_CONSTITUTION_v1.md` | Overwritten from pinned commit |
| 2 | `docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md` | Overwritten from pinned commit |
| 3 | `docs/governance/EBD-002_GOVERNANCE_MODEL.md` | Overwritten from pinned commit |
| 4 | `docs/governance/EBD-003_ARCHITECTURE_FREEZE_v1.md` | Overwritten from pinned commit |
| 5 | `docs/governance/EBD-004_ENGINE_DEFINITIONS.md` | Overwritten from pinned commit |
| 6 | `docs/governance/EBD-006_CONSTITUTIONAL_GOVERNANCE_ALIGNMENT.md` | Overwritten from pinned commit |
| 7 | `docs/execution/governance_obligations/EFR-EBD-005_MIRROR_REFRESH.md` | Created — this manifest |

**Not written, not modified:** EFR-EBD-005 Draft 3; EFR-EBD-005 tracker; EBD-005; Sprint EX-1 documents; Sprint EX-2; runtime code; product documents; `CURRENT_STATE.md`; any `nawa_brain` document; any file in the canonical repository.

A temporary staging copy was made at `/tmp/efr_export` inside the ephemeral Linux sandbox for source-side hashing. It is outside both the mirror and the canonical repository and does not persist.

## 6. Canonical Repository — Integrity Statement and Disclosure

### 6.1 Tracked content, commit, and branch state — unchanged

| Check | Before | After | Result |
|---|---|---|---|
| HEAD | `6d5d04277d91dda988c81876ca50318297b9e878` | `6d5d04277d91dda988c81876ca50318297b9e878` | ✅ unchanged |
| Branch | `claude-safe-review` | `claude-safe-review` | ✅ unchanged |
| Reflog head | `6d5d04277d91dda988c81876ca50318297b9e878` | `6d5d04277d91dda988c81876ca50318297b9e878` | ✅ unchanged — no new ref movement |
| Working-tree status digest | `ed35cacd54ca704c51bf2a54595faf9f292ca4f54818df6e9c45a9940264c477` | `ed35cacd54ca704c51bf2a54595faf9f292ca4f54818df6e9c45a9940264c477` | ✅ byte-identical |
| `docs/governance/` working-tree status | clean | clean | ✅ unchanged |
| Six governance blob OIDs at HEAD | as §2 | as §2 | ✅ unchanged |

**No canonical file was created, modified, deleted, staged, committed, or checked out. No branch was created, moved, or deleted. No commit was made. No working-tree item changed.** The 31 unrelated uncommitted items present in the canonical repository before this operation are still present, unaltered.

*Note on an apparent discrepancy:* an early working-tree status line count read 32 rather than 31. That reading captured a transient Git stderr line because stderr was merged into the count; the content digest was byte-identical across both readings, and subsequent stdout-only readings return 31 consistently. No working-tree change occurred.

### 6.2 Disclosure — two side effects inside `.git`

Both were produced by **read-only Git commands** — `git status`, run to fingerprint the repository state before and after the export. `git status` refreshes the index stat-cache as a normal part of its operation. Neither side effect altered repository content.

**Side effect 1 — `.git/index` stat-cache refresh.**

| Field | Value |
|---|---|
| Path | `C:\AIMX_PROJECTS\.git\index` |
| Size | 26,838 bytes |
| Modified | `2026-08-01 19:10:51 +03:00` — during this session |
| Cause | `git status` refreshing cached file stat data |
| Content effect | **None.** The index stat-cache records filesystem metadata for performance. No staged content, no tracked file, no commit, no branch is affected. |

**Side effect 2 — stale `.git/index.lock` left in place. ⚠️ Requires action.**

| Field | Value |
|---|---|
| Path | `C:\AIMX_PROJECTS\.git\index.lock` |
| Size | **0 bytes** |
| Created | `2026-08-01 19:10:52 +03:00` — during this session, 0.78s after the index refresh |
| Cause | A `git status` invocation acquired the index lock and did not release it |
| Evidence it is stale | Zero-byte; subsequent `git status` runs left `.git/index` mtime frozen at 19:10:51, meaning Git could no longer acquire the lock and fell back to read-only behaviour |

**Operational impact:** while `.git/index.lock` exists, the next canonical Git operation requiring the index — `git add`, `git commit`, `git checkout`, `git worktree add` — will fail with `Unable to create '.git/index.lock': File exists.` **This will block Claude Code's EFR-EBD-005 worktree creation and any subsequent canonical commit.**

**COWORK has not removed it.** Removing it is a write to the canonical repository, which EBD-006 §7.1 prohibits COWORK from performing and which the Founder's instruction for this operation expressly excluded. Two remediation paths, both requiring authorization:

| Option | Action |
|---|---|
| A | Claude Code deletes `C:\AIMX_PROJECTS\.git\index.lock` as canonical executor under EBD-006 §7.1 |
| B | Founder authorizes COWORK to delete the single stale lock file, as a one-time exception limited to that path |

Before removal under either option, confirm no host-side Git process (IDE, terminal, Git GUI) is actively holding the lock. Sandbox process inspection cannot see host processes; the file's timestamp and zero length indicate it originated in this session, but host-side confirmation is prudent.

### 6.3 Honest summary

The canonical repository's **content, history, refs, and working tree are untouched and verified identical before and after**. The canonical repository's **`.git` metadata was touched** — an index stat-cache refresh and a stale lock file — as an unintended consequence of read-only status commands. This manifest does not claim the canonical repository is "completely untouched," because that claim would be inaccurate at the `.git` metadata level.

## 7. What This Manifest Does Not Do

- It does **not** constitute the COWORK revalidation required by EFR-EBD-005 Draft 3 §14.2 (checks R1–R8). That is a separate step, now unblocked.
- It does **not** grant final Founder approval to EFR-EBD-005 Draft 3.
- It does **not** apply EFR-EBD-005 to the canonical repository.
- It does **not** execute, begin, or prepare the Engineering Feasibility Review. **No review was performed. No finding was filed. No runtime or application code was read, inspected, or modified.**
- It does **not** activate Sprint EX-2 or alter Sprint EX-1.

## 8. Change Log

| Date | Event | By |
|---|---|---|
| 2026-08-01 | Governance mirror refreshed from pinned canonical commit `6d5d042` via `git show`. Six files exported, all raw-identity PASS. Post-refresh governance state confirmed. Two `.git` metadata side effects disclosed at §6.2; stale `index.lock` flagged as requiring authorized removal. | COWORK (CTO / Chief of Staff) |
| 2026-08-01 | Stale `.git/index.lock` (0 bytes) removed by Claude Code as canonical executor under EBD-006 §7.1, after confirming no active `git.exe` process and no in-flight Git command. Branch (`claude-safe-review`) and HEAD (`6d5d04277d91dda988c81876ca50318297b9e878`) confirmed unchanged post-removal. | Claude Code (canonical repository executor) |
| 2026-08-01 | Supplemental single-file mirror refresh — `docs/execution/EXECUTION_BOARD.md` — see §9. | Claude Code (canonical repository executor) |

## 9. Supplemental Entry — EXECUTION_BOARD.md Mirror Refresh

**Operation:** Read-only, single-file supplemental mirror refresh, executed by Claude Code (canonical repository executor), not COWORK.

**Purpose:** Verification of the Executive Board Directive #001 citation used by EFR-EBD-005.

| Field | Value |
|---|---|
| Pinned source commit (full SHA) | `6d5d04277d91dda988c81876ca50318297b9e878` |
| Source branch | `claude-safe-review` |
| Source path | `docs/execution/EXECUTION_BOARD.md` |
| Existence at pinned commit | ✅ confirmed via `git cat-file -e 6d5d042:docs/execution/EXECUTION_BOARD.md` (exit 0) |
| Git blob OID | `720861de37bde680ef778a7ec78c9fa115f282ea` |
| Blob size | 7,558 bytes |
| Extraction method | `git show 6d5d042:docs/execution/EXECUTION_BOARD.md` — Git object database, **not** the canonical working tree |
| Mirror destination | `C:\Users\oshub\Documents\Claude\Projects\NAWA AI\docs\execution\EXECUTION_BOARD.md` |
| Source SHA-256 (exported blob) | `818913e007b28d5257193cca30b26aab26f125243d08a1d9748207d5b2a4f6b0` |
| Mirror SHA-256 (written file) | `818913e007b28d5257193cca30b26aab26f125243d08a1d9748207d5b2a4f6b0` |
| Raw identity | ✅ **PASS** |
| CR bytes in exported blob | 0 |
| Normalized LF identity | ✅ **PASS** (not required — blob is LF-only, same as the six-file export at §3) |
| Export timestamp (local) | `2026-08-01T19:31:06+03:00` |
| Export timestamp (UTC) | `2026-08-01T16:31:06Z` |

**Files written by this supplemental entry:** exactly two — the mirror copy of `docs/execution/EXECUTION_BOARD.md`, and this manifest entry. No canonical repository file was created, modified, or deleted. EFR-EBD-005 Draft 3, previously-refreshed governance files, runtime/product files, Sprint EX-1, and Sprint EX-2 were not touched. No Engineering Feasibility Review step was begun; no review worktree was created.

**Canonical repository state, before and after this operation:**

| Check | Value | Result |
|---|---|---|
| Branch | `claude-safe-review` | ✅ unchanged |
| HEAD | `6d5d04277d91dda988c81876ca50318297b9e878` | ✅ unchanged |
| `.git/index.lock` | absent | ✅ absent (removed prior session step; not recreated) |
| Working tree | same 12 pre-existing unrelated items as before this operation | ✅ unchanged |
