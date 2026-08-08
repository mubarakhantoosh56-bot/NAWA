# EFR-EBD-005 — Post-Seal Custody Addendum

**Document type:** Post-Seal Custody Addendum.
**Reviewer:** Engineering Reviewer #1 — Claude Code, Senior AI Software Engineer, AI Engineering Team (EBD-002 §4.4).
**Reviewed commit:** `26d5bab03cdad52a0d7febd34d6600bee742ce82`
**Nature of this document:** Custody/integrity record only. It does not revise, re-open, or alter the sealed finding's body. Per EFR-EBD-005 §5.1 item 6, a sealed finding "is not revised after sealing"; this addendum is the dated, attributed record contemplated by that rule for anything relevant to custody discovered post-seal. This is a revision of an addendum of the same name filed earlier at `2026-08-05T01:44` local; that version is superseded by this one at the same path, per this task's own instruction to create the addendum at this path.

---

## 1. Correction required before any of the requested confirmations could be made

This addendum was requested on the premise that the sealed file is at `docs/execution/governance_obligations/EFR-EBD-005_FINDING_CLAUDE_CODE.md`, and that I should "work from the original isolated worktree in which your final finding was produced." Both premises needed checking against the actual filesystem before I could honestly confirm anything, and both turned out to need correction:

1. **That exact path does not exist.** Confirmed just now: `ls docs/execution/governance_obligations/EFR-EBD-005_FINDING_CLAUDE_CODE.md` → "No such file or directory." There is no file there to locate.
2. **The original review worktree no longer exists, and the finding was never produced inside it.** `git worktree list` currently shows only `C:/AIMX_PROJECTS` (main) and `C:/AIMX_PROJECTS/_codex_efr005_reviewer2` (Codex's own isolated worktree, not mine). My review worktree, `C:\aimx_efr_ebd_005_claude`, was removed via `git worktree remove` immediately after the finding was sealed, per EFR-EBD-005 §14's expectation that review isolation is temporary. The worktree was used only to read the pinned commit's code in isolation (§5.1 item 2); the finding document itself was written directly into the canonical repository, not into the worktree, and was never present inside `C:\aimx_efr_ebd_005_claude` at any point. "Working from" that worktree now is not possible (it doesn't exist) and would not have been the right place to look even when it did exist.

Given both premises don't hold, I searched the canonical repository directly for the actual current state of the sealed finding rather than assuming a location, and found two candidate files, only one of which matches.

---

## 2. What actually exists on disk, checked fresh for this addendum

| Path | SHA-256 | Size | Lines | Matches sealed content? |
|---|---|---|---|---|
| `docs/execution/governance_obligations/EFR-EBD-005_FINDING_CLAUDE_CODE.md` | — (file absent) | — | — | N/A — does not exist |
| `docs/execution/governance_obligations/reviews/EFR-EBD-005_FINDING_CLAUDE_CODE.md` | `f80a39627a9b2ee2952470bd72b682acc87ed71b8f009811d3403f3682a88f87` | 39,554 bytes | 265 | **Yes** — verified below |
| `docs/execution/governance_obligations/ARCHIVE_EFR-EBD-005_FINDING_CLAUDE_CODE.md` | `90f3e80cd0d5e4b5960d948ffa003bf085895b250be4cf1abbd3d6e807ed8b2f` | 30,833 bytes | 270 | **No** — see §2.2 |

### 2.1 The genuine sealed report

`docs/execution/governance_obligations/reviews/EFR-EBD-005_FINDING_CLAUDE_CODE.md` contains, verified by direct read just now:

- The literal line `SEALED`, followed by "This report was produced independently.", "No previous engineering review was consulted.", and "Engineering Reviewer #1 (Claude Code)" — present, unchanged.
- Reviewed commit recorded as `26d5bab03cdad52a0d7febd34d6600bee742ce82` — matches this task's stated commit, and matches the commit SHA appearing in the file's own Execution Baseline table and Signature block.
- Content compared line-by-line against the finding I authored and sealed in the turn that produced it (retained in this session's own record — the original `Write` call plus the two `Edit` calls that inserted the seal hash): **identical**, including the twelve question answers, the D1/D2/D3 assessment, the §7 Non-conformant classification, the Adjacent Finding, the Signature block, and the internally-recorded Seal SHA-256 (`8a748e117e499bb67fccef1c2769f1125e4358df820d41b198a411b383f5e9b2`) and seal timestamp (`2026-08-04T21:36:29Z`).
- **The only thing that changed since sealing is its filesystem location** — it now sits in a `reviews/` subdirectory that did not exist at seal time, rather than directly in `governance_obligations/`. **The report body is unmodified.**

This is the file this addendum treats as the sealed report for all confirmations below.

### 2.2 A second, non-matching file — not certified

`docs/execution/governance_obligations/ARCHIVE_EFR-EBD-005_FINDING_CLAUDE_CODE.md` has existed, unchanged, across this addendum and the prior one (same hash, `90f3e80c...`, both times checked). Its name implies it is an archived copy of the original, but its content is materially different from what I sealed:

- 270 lines vs. the genuine report's 265.
- Its own header reads *"Submission timestamp (UTC): 2026-08-04T20:25:05Z"* and its own internal seal line reads *"Seal timestamp (UTC): 2026-08-04T20:25:05Z"* — a timestamp that does not appear anywhere in the file I actually sealed (mine is `21:36:29Z`).
- Its internally-recorded seal hash, `871b40a7e422b6e8d18b96f3aa666ee4390bc9d8cb752e8f1be064aa9f6dd41d`, does not match my recorded internal hash (`8a748e11...`) and does not match its own current raw file hash (`90f3e80c...`) either.
- Wording throughout (author line, review-status line, section structure) differs from what I wrote.

**I am not treating this file as the sealed finding, a valid copy of it, or my work product**, and this addendum does not compute or certify a hash for it as if it were. It is reported here as an unresolved custody anomaly for the Founder/requester's attention, not corrected or removed by this addendum (out of scope — see §5).

### 2.3 Codex finding — not opened

`docs/execution/governance_obligations/reviews/EFR-EBD-005_FINDING_CODEX.md` is present (confirmed via directory listing only: size and mtime, not content) alongside the genuine report. Consistent with this task's instruction and the independence requirement carried over from the sealed finding itself, **it was not opened, read, or inspected**, now or previously.

---

## 3. Required confirmations

| Item | Value / Confirmation |
|---|---|
| Reviewed commit | `26d5bab03cdad52a0d7febd34d6600bee742ce82` — confirmed present and correct in the genuine sealed report (§2.1) |
| Original worktree absolute path | `C:\aimx_efr_ebd_005_claude` — **no longer exists** (removed post-seal via `git worktree remove`); the finding was written to the canonical repository, not to this worktree, at any point (§1) |
| Original sealed report relative path (as stated in this task) | `docs/execution/governance_obligations/EFR-EBD-005_FINDING_CLAUDE_CODE.md` — **does not exist at this path currently** |
| Current relative path of the genuine sealed report | `docs/execution/governance_obligations/reviews/EFR-EBD-005_FINDING_CLAUDE_CODE.md` |
| Raw SHA-256 of the sealed report (current, whole-file, computed via `sha256sum` just now) | `f80a39627a9b2ee2952470bd72b682acc87ed71b8f009811d3403f3682a88f87` |
| Report byte size | 39,554 bytes |
| Report line count | 265 |
| Addendum timestamp (UTC) | 2026-08-04T22:50:00Z |
| Addendum timestamp (local) | 2026-08-05 01:50:00 +03:00 |
| Original seal timestamp, for reference (unchanged, read from the report body) | 2026-08-04T21:36:29Z (UTC) / 2026-08-05 00:36:29 +03:00 (local) |
| Sealed report body modified since sealing? | **No** — content verified identical line-for-line (§2.1); only its filesystem path changed |
| Previous engineering review consulted? | **No** — none existed before this finding was sealed (established in the sealed finding's own §0/§1); the Codex finding exists alongside it now but was not opened (§2.3) |
| Previously recorded internal report hash | `8a748e117e499bb67fccef1c2769f1125e4358df820d41b198a411b383f5e9b2` — recorded in the report's own §13, computed via `sha256sum` over the document's content as it stood immediately *before* that hash value and the seal timestamp were written into placeholders in the signature table and §13 (a pre-image hash, by construction excluding its own output) |
| Is that historical internal hash reproducible under its stated method? | **No, and it is not expected to be.** Hashing the finished file (which contains the actual hash string written into the two places that were placeholders when `8a748e11...` was computed) necessarily yields a different digest. This is the documented, by-design behavior stated in the report's own §13, not evidence of tampering. |
| Authoritative custody hash | **The raw whole-file SHA-256 recorded in this addendum, `f80a39627a9b2ee2952470bd72b682acc87ed71b8f009811d3403f3682a88f87`, is the authoritative custody hash for the sealed report as it currently exists on disk.** It supersedes the internal pre-image hash (`8a748e11...`) for custody-verification purposes, since the internal hash is, by its own stated method, not a hash of any file that has ever existed in finished form — it is a hash of an intermediate editing state. The raw whole-file hash is reproducible by anyone at any time by running `sha256sum` against the current file, which the internal hash is not. |

---

## 4. Answers requested at the top level of this task

- **Sealed report raw SHA-256:** `f80a39627a9b2ee2952470bd72b682acc87ed71b8f009811d3403f3682a88f87`
- **Addendum raw SHA-256:** computed after this file is written; see §6 below for the value and method (this addendum's own hash cannot be embedded in itself before it is complete, for the same reason the report's internal hash could not include itself).
- **File size and line count:** 39,554 bytes; 265 lines.
- **Exact original worktree path:** `C:\aimx_efr_ebd_005_claude` (removed; the finding was never stored inside it — §1).
- **Confirmation the sealed report remains unchanged:** Yes, for the genuine report at its current path (§2.1). No such confirmation is extended to `ARCHIVE_EFR-EBD-005_FINDING_CLAUDE_CODE.md` (§2.2), which is a different, non-matching document.

---

## 5. Actions not taken, per this task's constraints

- The sealed report's body was not edited, and no hash was embedded into it.
- The Codex finding was not opened or read.
- No commit, push, or git write operation was performed.
- No runtime or implementation change was made.
- No file other than this addendum was created or modified.
- The `ARCHIVE_` file discrepancy (§2.2) was reported, not corrected, deleted, or overwritten.

---

**Addendum timestamp (UTC):** 2026-08-04T22:50:00Z
**Addendum timestamp (local):** 2026-08-05 01:50:00 +03:00
**Addendum author:** Engineering Reviewer #1 — Claude Code, Senior AI Software Engineer, AI Engineering Team (EBD-002 §4.4)

## 6. This addendum's own hash

- **Raw SHA-256 of this addendum file:** `297d8331a1a88d6c26194b24a14485b8df0753ae2c75a5039e495005c9090302`, computed via `sha256sum` over this file exactly as it stood immediately before this value was inserted (i.e., excluding this line's own output, for the same self-reference reason given in §3's discussion of the report's internal hash). Note: since this value is itself now embedded in the file, re-hashing the finished file will not reproduce it, by the same logic explained in §3 for the report's internal hash — this is expected, not a discrepancy.
