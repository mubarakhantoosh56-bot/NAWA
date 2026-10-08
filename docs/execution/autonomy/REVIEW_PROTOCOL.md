# Review Protocol

**Status:** Founder-ratified as amended on 2026-10-08 (`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`; Bootstrap Amendment `docs/decisions/EBD-008-harness-bootstrap-amendment.md`: §2.6, §9.2, §9.7). Not ACTIVE until `G3b-G` PASS on the harness governance commit.
**Version:** 1.1
**Category:** Agent Instructions
**Scope:** When independent review happens during an autonomous run, what it checks, and how verdicts are issued and recorded.
**Non-scope:** Routine engineering self-checks, and Executive Board review authority under EBD-002.
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10.
**Approval authority:** Founder (scope and authority rules).
**Effective date:** On successful remote verification (`G3b-G`) of the harness governance commit. Founder-ratified 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. Principle

Independent review is scarce and decisive. Codex is invoked at designated gates
only, verifies from the repository itself, and is the only party that can issue
an independent verdict.

An independent Codex `PASS` does **not** replace an EBD-002 approval, and an
EBD-002 approval never counts as a gate verdict. The approvals EBD-002 requires
are separate, explicit exit conditions in the loop — checkpoints `EBD-A`,
`EBD-B`, and `EBD-C`, defined in `AUTONOMOUS_LOOP.md` §8.

Engineering closure and governance closure are two distinct sequences, each
with its own post-commit and remote verification. A governance closure commit
is never described as verified because the engineering commit was verified.

## 2. The gates

### 2.1 Gate registry

Gate ids are fixed. Documents, run state, verdicts, and the Founder Review
Package use these ids and no others.

| Gate id | Name | Sequence | Object verified | Blocks |
|---|---|---|---|---|
| `G1` | Gate 1 — Architecture Review | Engineering | The design in the batch task document | Checkpoint `EBD-A`, then implementation |
| `G2` | Gate 2 — Final Implementation / Pre-Commit Review | Engineering | The worktree content; issues the Gate 2 Review Manifest | Checkpoint `EBD-B`, then the engineering commit |
| `G3a-E` | Gate 3a-E — Engineering Post-Commit / Pre-Push Verification | Engineering | The engineering commit against the Gate 2 Review Manifest | The engineering push |
| `G3b-E` | Gate 3b-E — Engineering Remote Verification | Engineering | Live origin against the commit verified at `G3a-E` | Governance closure |
| `G3a-G` | Gate 3a-G — Governance Post-Commit / Pre-Push Verification | Governance | The governance closure commit against the Governance Closure Manifest, and its content | The governance push |
| `G3b-G` | Gate 3b-G — Governance Remote Verification | Governance | Live origin against the commit verified at `G3a-G` | The Founder Review Package |

Six gates, six separate verdicts. There is no gate called "Gate 3", "Gate 3a",
or "Gate 3b" without the `-E` or `-G` suffix.

### 2.2 `G1` — Gate 1 — Architecture Review

- **When:** after Architecture Investigation, before checkpoint `EBD-A` and
  before any implementation.
- **Codex verifies:** root cause is evidenced; the design closes the defect;
  the design stays inside the batch scope and the existing architecture
  contracts; no migration, schema change, or other stop condition is implied
  unless the activation record grants it; files to change and files left
  untouched are named.
- **Also serves as:** the Engineering Team's written review that EBD-002 §5.3
  requires before a CTO approval. It is review, not approval.

### 2.3 `G2` — Gate 2 — Final Implementation / Pre-Commit Review

- **When:** after implementation and required tests and validation, before
  checkpoint `EBD-B` and before the engineering commit.
- **Codex verifies:** the worktree content implements the `G1` design and
  nothing else; only in-scope paths changed; tests exist, are meaningful, and
  pass; regressions pass; any runtime validation evidence supports what is
  claimed; tenant isolation, auth, and the `CLAUDE.md` production safety
  checklist hold; no secrets, migrations, or data files changed.
- **Codex issues:** the **Gate 2 Review Manifest** (Section 9.2), with its
  `manifest_id`, verbatim inside the verdict. A `G2` `PASS` without a manifest is not a `PASS`.

### 2.4 `G3a-E` — Gate 3a-E — Engineering Post-Commit / Pre-Push Verification

- **When:** after the engineering commit exists locally, before any push.
- **Codex verifies — all required:**
  1. **Exact content equivalence.** The committed content is exactly the
     content reviewed at `G2`: the canonical manifest reconstructed from the
     commit is byte-for-byte equal to the Gate 2 Review Manifest, and so has
     the same `manifest_id` (Section 9.4). Matching file names with different
     content fail.
  2. **Lineage.** The manifest's `baseline_commit` is an ancestor of HEAD, and
     `git rev-list <baseline_commit>..HEAD` lists exactly the commits in the
     run file's `Ahead State` and nothing else.
  3. **No drift.** No manifest path has an uncommitted change in the worktree.
  4. **Scope.** The commit contains engineering paths only — no batch
     documentation, run state, or tracker.
  5. **Run state.** The `Ahead State` in `CURRENT_AUTONOMOUS_RUN.md` matches
     Git exactly (`SESSION_RECOVERY_PROTOCOL.md` §5).
- **Verdict states:** the full hash, parent, and author of the commit verified.
- **On any difference:** `G3a-E` fails and execution returns to `G2`
  (Section 3.1). Nothing is pushed.

### 2.5 `G3b-E` — Gate 3b-E — Engineering Remote Verification

- **When:** after the engineering push.
- **Codex verifies:** live `origin/claude-safe-review` equals the exact commit
  hash stated in the `G3a-E` verdict; the push was a normal fast-forward;
  ahead/behind is 0/0.

### 2.6 `G3a-G` — Gate 3a-G — Governance Post-Commit / Pre-Push Verification

- **When:** after the governance closure commit exists locally, before any
  push. Never before `G3b-E` has passed — except in the bootstrap closure
  (Section 9.2), where no engineering commit exists and so no `G3b-E` exists
  to wait for.
- **Codex verifies — all required:**
  1. **Exact content equivalence.** The canonical manifest reconstructed from
     the governance commit — path set, statuses, modes, blob identities, the
     normalized-content identity of `CURRENT_AUTONOMOUS_RUN.md`, and the
     canonical `manifest_id` — is byte-for-byte equal to the finalized
     Governance Closure Manifest in that file's derived-metadata region
     (Section 9.7). This is a deterministic comparison; reading the file does
     not replace it.
  2. **Lineage.** The manifest's `baseline_commit` is the engineering commit
     verified at `G3b-E` — or, in the bootstrap closure only, the baseline
     fixed in Section 9.2 and verified as in Section 9.7 step 1 — and
     `baseline_commit..HEAD` contains exactly the commits in the run file's
     `Ahead State` and nothing else.
  3. **Scope.** The commit contains closure documentation only — no product
     code, tests, migrations, data, or knowledge.
  4. **Content.** Every closure claim matches the recorded evidence: commit
     hashes, verdicts quoted verbatim, statuses, and the three EBD-002
     checkpoint records. The `EBD-C` record is present in the committed
     content.
  5. **Run state.** The `Ahead State` matches Git exactly.
- **Verdict states:** the full hash, parent, and author of the commit verified.

### 2.7 `G3b-G` — Gate 3b-G — Governance Remote Verification

- **When:** after the governance push.
- **Codex verifies:** live `origin/claude-safe-review` equals the exact commit
  hash stated in the `G3a-G` verdict; the push was a normal fast-forward;
  ahead/behind is 0/0.

## 3. Verdicts

Exactly one of:

| Verdict | Meaning | Routing |
|---|---|---|
| `PASS` | Gate criteria met | Proceed to the next stage |
| `FAIL — IN SCOPE` | Findings exist and can be closed inside the batch scope | Automatic bounded correction, routed as in Section 3.1 |
| `FAIL — FOUNDER STOP` | A finding triggers a Founder Stop Condition (cite the FSC id) | STOP FOR FOUNDER |

A verdict states the gate id, the reviewer, the date, the exact commit hash or
manifest reviewed, and the findings.

### 3.1 Where an in-scope failure returns to

| Gate | `FAIL — IN SCOPE` returns to |
|---|---|
| `G1` | Architecture Investigation, then `G1` |
| `G2` | Bounded correction by Claude Code, then `G2` |
| `G3a-E` | `G2` — Codex re-reviews the cumulative content and issues a new manifest revision; then `G3a-E` |
| `G3b-E` | Not applicable: a remote mismatch is a Git-state mismatch (FSC-15) |
| `G3a-G` | If the correction changes any byte outside the derived-metadata region: Governance Closure Documentation, then `EBD-C` again, then manifest finalization, then `G3a-G`. If it changes only that region: manifest finalization, then `G3a-G` (Section 9.6 step 11) |
| `G3b-G` | Not applicable: a remote mismatch is a Git-state mismatch (FSC-15) |

A correction made after a commit exists is a **new forward commit**. The
reviewed commit is never amended, rebased, reset, or recreated without explicit
Founder authorization (Charter §9, FSC-09).

## 4. What Codex is not used for

Routine debugging, test failures during development, exploratory questions, or
re-deriving analysis Claude Code has already evidenced. Claude Code handles:

```text
debug → test → correct → rerun
```

without Founder involvement and without spending independent-review capacity.

## 5. Reviewer rules

1. **Read-only.** Codex does not modify the repository during a gate. It does
   not stage, commit, push, or write objects. Computing a manifest
   (Sections 9.2–9.5) writes nothing to the repository.
2. **No implementation.** Codex must not implement the change it reviews. If it
   has, it is disqualified from that gate and the situation is a Founder Stop
   (FSC-19).
3. **Verify, don't trust.** Codex checks Git and the files directly. The
   implementer's summary is a guide to where to look, never evidence.
4. **Scope verification.** Every changed path is checked against the
   activation record's scope.
5. **Git identity verification.** Repository root, branch, HEAD, parent,
   tracking origin, and live origin are re-read by Codex, not copied from
   `CURRENT_AUTONOMOUS_RUN.md`.
6. **Chain check.** At each gate Codex confirms that the recorded verdict of
   the preceding gate — including the manifest at `G2` and the commit hash at
   `G3a-E` and `G3a-G` — matches what it issued. A mismatch is a Founder Stop
   (FSC-19).
7. **No approvals.** Codex does not issue, and its verdict does not stand in
   for, a CTO approval under EBD-002.

## 6. Invocation

### 6.1 The gate request (fixed text)

The request is fixed so that the reviewed party does not frame its own review:

```text
Read docs/execution/autonomy/NAWA_AUTONOMOUS_DEVELOPMENT_CHARTER.md,
docs/execution/autonomy/ACTIVE_BATCH.md,
docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md and
docs/execution/autonomy/REVIEW_PROTOCOL.md. Execute the gate named in
"Next Exact Action" for the active batch. Read-only. Verify from Git and the
files directly. Return exactly one verdict from REVIEW_PROTOCOL.md §3.
```

Everything else Codex needs is in the repository.

### 6.2 Current mode: Founder-initiated

Codex automation classification:
**`CODEX_INTERFACE_PRESENT_BUT_AUTOMATION_NOT_PROVEN`**.

Every independent gate — all six in Section 2.1 — is started by the Founder,
who gives Codex the fixed request above. That is one fixed line per gate, with
no prompt drafting and no state relay — but it is a Founder touchpoint, and the harness is LIMITED
AUTONOMY because of it (Charter §14).

At a gate the orchestrator brings the run to a clean handoff: `Next Exact
Action` in `CURRENT_AUTONOMOUS_RUN.md` names the gate by its id, and the run
waits. No
agent substitutes for the reviewer while it waits.

### 6.3 Evidence — H0.1 probe, 2026-10-05

**Discovered**

- Codex is installed as a desktop surface: the "Codex" mode of the ChatGPT
  Windows app (package `OpenAI.Codex`), signed in, with earlier NAWA review
  threads present. A Codex VS Code extension is also installed.
- A Codex CLI was **not confirmed**. Cowork has no native Windows shell — its
  device shell is a Linux VM, and its desktop control of terminals and IDEs is
  view-and-click only — so no version or help command could be run.
- The desktop surface offers three approval modes (Ask for approval, Approve
  for me, Full access) and **no read-only mode**. Through that surface,
  read-only can be instructed but not enforced.
- No credentials or Codex configuration were read or changed.

**The single probe.** Cowork opened a new Codex thread on the desktop surface
and asked for nine read-only Git commands against the repository.

| Evidence item | Result |
|---|---|
| 1. Invocation originated from the autonomous engineering environment | YES — Cowork drove the Codex desktop surface; no prompt was transferred by the Founder |
| 2. Codex ran independently | YES — new Codex thread, "Run NAWA H0.1 read-only probe" |
| 3. Codex returned a result | YES — and the result was a failure (verbatim below) |
| 4. Repository remained unchanged | YES — HEAD, refs, index, worktree status, and content hashes identical before and after |

Codex's verdict, verbatim:

```text
PROBE VERDICT: FAILED - All nine commands failed to start: helper_unknown_error: apply deny-read ACLs; no commands ran and nothing was modified.
```

**Conclusion.** A request can reach Codex and an answer comes back, but in
that invocation Codex could not start a single command: its command sandbox
failed before any Git read. A reviewer that cannot read the repository cannot
run a gate. The handoff is therefore **not proven**.

Even with the sandbox error resolved, that path would still depend on a
per-session desktop-control approval from the user, an unlocked desktop, and a
stable device link, and it cannot enforce read-only.

**Not attempted** (outside H0.1 authority): a second probe, changing Codex's
approval mode or project configuration, installing software, building an
adapter.

### 6.4 What would change the classification

A Founder-authorized controller or adapter — or a demonstrated non-interactive,
sandbox-enforced read-only Codex invocation from Claude Code — followed by a
probe in which Codex itself reads the repository, returns the correct root,
branch, and HEAD, and leaves the repository unchanged. Only then are this
section, `AUTONOMOUS_LOOP.md` §7, and Charter §14 amended.

## 7. Recording verdicts

- Each verdict is recorded under its gate id, verbatim, with reviewer, date,
  and the exact commit hash or manifest reviewed.
- `G1`, `G2` (with its manifest), `G3a-E`, and `G3b-E` verdicts are recorded in
  the batch task document and summarised in `CURRENT_AUTONOMOUS_RUN.md`. They
  are committed with the governance closure commit.
- `G3a-G` and `G3b-G` verdicts cannot be inside the commit they verify. They
  are recorded in the worktree copy of `CURRENT_AUTONOMOUS_RUN.md`
  (`SESSION_RECOVERY_PROTOCOL.md` class B3) and in the Founder Review Package,
  and are committed with the next governance commit — never by amending.
- Recording is clerical. Cowork and Claude Code may record a verdict; they may
  not author, upgrade, or reinterpret one.
- Internal validation by Claude Code or Cowork is always labelled
  "internal validation" and never appears as a gate verdict.
- A CTO approval at an EBD-002 checkpoint is recorded as an approval, under its
  checkpoint id, and never in a gate's verdict field.

## 8. Correction cycles

Two is a **reassessment threshold, not an automatic stop.**

After two unsuccessful bounded correction cycles at the same gate (any of the
six), the orchestrator (Cowork) performs a root-cause reassessment before any third
attempt, and records it in the batch task document: why the two corrections
failed, whether the failures share a cause, and what the next correction will
do differently.

The loop **may continue without Founder intervention** when all of these hold:

- the issue remains inside the active batch;
- architecture remains closed;
- no scope expansion is required;
- no migration, schema, security, or production stop condition exists;
- measurable progress is being made — the open findings are narrowing or
  changing in substance, not repeating unchanged.

**Founder escalation is required** when repeated failure reveals:

- unresolved architecture uncertainty;
- material scope expansion;
- contradictory reviewer requirements;
- no credible bounded correction path;
- or another Founder Stop Condition.

A finding the implementer disputes rather than fixes is an unresolved material
disagreement (FSC-14) regardless of the cycle count. The reassessment is
orchestration, not review: it never changes, softens, or overrides a verdict.

## 9. Review manifests and exact content equivalence

### 9.1 Purpose

A commit passes its post-commit gate (`G3a-E` or `G3a-G`) only if its content
is exactly the content that was reviewed. File-list equality is not sufficient:
the same paths with different content fail. The comparison is deterministic —
two byte strings are equal or they are not. Reading the content and judging it
acceptable never substitutes for it.

### 9.2 Canonical manifest (schema 2)

A manifest is one canonical byte string — the **canonical body** — followed by
its `manifest_id`.

The canonical body is exactly these lines, in this order:

```text
REVIEW-MANIFEST
schema: 2
kind: <GATE-2 or GOVERNANCE-CLOSURE>
batch: <batch id>
revision: <positive integer>
baseline_commit: <40 lowercase hexadecimal characters>
entry_count: <number of entry lines>
<status> <mode> <content-id> <path>
END
```

with one `<status> <mode> <content-id> <path>` line per entry.

**Serialization rules — all mandatory:**

1. Encoding is UTF-8 with no byte-order mark.
2. Every line, including `END`, ends with exactly one LF (byte `0x0A`). There
   is no CR, no blank line, no trailing space, and nothing after the LF that
   ends `END`.
3. Header lines are `key`, a colon, one space, the value. The seven header
   lines appear exactly as shown, in that order. No other header field exists.
   The body contains no timestamp, no person or agent name, and no free text.
4. `schema` is the literal `2`.
5. `kind` is `GATE-2` or `GOVERNANCE-CLOSURE`.
6. `batch` is the batch id: the text of the line that follows
   `ACTIVE AUTONOMOUS ENGINEERING BATCH:` in the activation record, with
   leading and trailing whitespace removed. It equals the `Engineering Batch`
   value in `CURRENT_AUTONOMOUS_RUN.md`.
7. `revision` is a decimal integer without leading zeros.
   - `GATE-2`: `1` for the first manifest Codex issues for the batch, and one
     more for each later one.
   - `GOVERNANCE-CLOSURE`: the number of commits in
     `baseline_commit..<governance commit>` — `1` for the first governance
     closure commit, `2` after one forward correction commit. Before the
     commit exists it is `git rev-list --count <baseline_commit>..HEAD` plus 1.
8. `baseline_commit` is the last remotely verified commit the content builds
   on. `GATE-2`: the batch's baseline checkpoint. `GOVERNANCE-CLOSURE`: the
   engineering commit verified at `G3b-E`.
9. Each entry line is four fields separated by single spaces. The path is
   everything after the third space, up to the LF.
   - `status`: `A` added, `M` modified, `D` deleted. A rename is one `D` line
     and one `A` line.
   - `mode`: the six-digit Git mode the commit records for the path
     (`100644`, `100755`); `000000` for `D`.
   - `content-id`: `blob:` followed by the 40-character Git blob id, for `A`
     and `M`; the literal `DELETED` for `D`; `nsha256:` followed by a
     64-character SHA-256, used for exactly one path as Section 9.5 defines.
   - `path`: repository-relative, forward slashes, the exact UTF-8 bytes Git
     stores, unquoted. A path containing LF or CR cannot be entered; the gate
     fails.
10. Entries are sorted ascending by path, comparing the paths as raw UTF-8
    bytes. A path appears at most once.
11. `entry_count` equals the number of entry lines.

**Bootstrap closure — one-time exception (`EBD-008`).** Rules 6 and 8 assume
an activated engineering batch and an engineering commit verified at `G3b-E`.
The initial governance closure of the harness itself has neither. For that
closure only, and only if **all** of these are true:

1. Engineering Batch is `NONE`;
2. no engineering commit exists for the harness setup and ratification run;
3. no `G3b-E`-verified commit therefore exists;
4. the closure is governance-only — it contains documentation paths and no
   engineering path;
5. the harness itself is being closed for the first time — `baseline_commit`
   contains no file under `docs/execution/autonomy/`;

the Governance Closure Manifest uses:

- `baseline_commit`: `9e2463fda8dad102601296f7e5bec33da5d68757`, which must be the last
  remotely verified repository baseline — the commit live
  `origin/claude-safe-review` points to when the closure is verified;
- `batch`: `NONE`.

This exception is used once and ends when the initial harness governance
commit passes `G3b-G`. It applies to no engineering batch. It does not permit
any other prior baseline, does not permit skipping `G3b-E` where an engineering
commit exists, and does not exempt governance-only work in general from
engineering verification. `NONE` is not a valid `batch` value in any other
manifest. Outside the bootstrap closure, rules 6 and 8 apply unchanged: the
governance baseline is the engineering commit verified at `G3b-E`.

Where another harness document says governance closure follows `G3b-E`, it
describes the standard sequence; for the bootstrap closure only, this
paragraph governs.

**`manifest_id`** is the SHA-256 of the complete canonical body — every byte
from the `R` of `REVIEW-MANIFEST` through the LF that ends `END` — written as
64 lowercase hexadecimal characters. It binds kind, schema, batch, revision,
baseline, the ordered path set, every status, every mode, and every content
identity. The only thing outside the hash is the `manifest_id` line itself.

A manifest is recorded as the canonical body followed by one line:

```text
manifest_id: <64 lowercase hexadecimal characters>
```

**Test vector.** This canonical body (346 bytes, each line ending in one LF):

```text
REVIEW-MANIFEST
schema: 2
kind: GATE-2
batch: EXAMPLE-BATCH
revision: 1
baseline_commit: 0123456789abcdef0123456789abcdef01234567
entry_count: 3
A 100644 blob:1111111111111111111111111111111111111111 app/example/new_file.py
D 000000 DELETED app/example/old_file.py
M 100644 blob:2222222222222222222222222222222222222222 tests/test_example.py
END
```

has `manifest_id`
`845d997f9b87d16bad0128256c6b22563f099e4cb58e5c2afb7f0664a16afd49`. An
implementation that does not reproduce this value is not conformant.

### 9.3 Computing content identities — read-only, no staging

- **Path set:** `git -c core.quotepath=false diff --name-status --no-renames
  <baseline_commit>` for tracked paths, plus
  `git -c core.quotepath=false ls-files --others --exclude-standard` for
  untracked ones. Only paths that were reviewed and that the commit will
  contain are entered. Any other changed path is listed in the verdict as
  excluded and must not appear in the commit.
- **Blob id:** `git hash-object -- <path>`. Without `-w` this writes nothing to
  the repository, and it applies the same conversion `git add` applies, so it
  equals the blob id the commit will contain.
- **Mode before the commit exists:** for `M`, the mode of the path in
  `baseline_commit` (`git ls-tree <baseline_commit> -- <path>`); for `A`,
  `100644`. A reviewed change that deliberately alters a mode records the new
  mode.
- Nothing is staged, no object is written, no ref or index entry changes, and
  **no repository file is rewritten or normalized in order to compute a
  manifest**.
- A manifest is computed in the native repository, under the Git configuration
  the commit will be made with. Blob ids depend on line-ending conversion, so a
  manifest computed through a non-native mount is invalid.

The binding Gate 2 Review Manifest is the one Codex computes and includes
verbatim in its `G2` verdict. Claude Code may prepare a candidate; a candidate
binds nothing.

### 9.4 Verification at `G3a-E`

Codex reconstructs the manifest from the commit:

```text
git -c core.quotepath=false diff --raw --no-renames --no-abbrev <baseline_commit> HEAD
```

Each output line gives the new mode, the new blob id (all zeros for a
deletion), the status, and the path. Codex builds the entry lines from that
output, takes `kind`, `batch`, `revision`, and `baseline_commit` from the Gate
2 Review Manifest in its own recorded `G2` verdict, serializes the canonical
body as in Section 9.2, and computes its SHA-256.

`G3a-E` passes only if:

- the reconstructed canonical body is byte-for-byte equal to the canonical body
  of the Gate 2 Review Manifest, and therefore the two `manifest_id` values are
  equal;
- `baseline_commit` is an ancestor of HEAD and `baseline_commit..HEAD` contains
  exactly the expected commits.

If anything differs, `G3a-E` fails and execution returns to `G2`. Codex then
reviews the cumulative content against the same `baseline_commit` and issues a
manifest with the next `revision`. A manifest always describes the cumulative
content of `baseline_commit..HEAD`, so a forward correction commit is covered
by the next revision rather than by rewriting the earlier commit.

### 9.5 Normalized-content identity of `CURRENT_AUTONOMOUS_RUN.md`

The governance closure commit contains `CURRENT_AUTONOMOUS_RUN.md`, and that
file carries the finalized Governance Closure Manifest. A file cannot contain a
hash of itself. The circularity is removed by one narrow, deterministic
normalization — not by leaving the file unbound.

**The derived-metadata region.** `CURRENT_AUTONOMOUS_RUN.md` contains exactly
one region delimited by these two marker lines, each a complete line:

```text
<!-- BEGIN GOVERNANCE MANIFEST DERIVED METADATA -->
<!-- END GOVERNANCE MANIFEST DERIVED METADATA -->
```

The region is the lines strictly between the two markers. It may hold only one
of two things:

- **Idle** — exactly one line:
  `GOVERNANCE-MANIFEST-DERIVED-METADATA-PLACEHOLDER`
- **Finalized** — exactly these lines and nothing else: a line containing
  three backticks followed by `text`; the canonical body of the finalized
  Governance Closure Manifest; its `manifest_id:` line; a line containing
  three backticks.

Every value in the region is mechanically derived from the finalized manifest.
The region never holds a governance decision, activation state, an approval, a
scope statement, product status, Founder or CTO authority, or any closure
statement. All of that stays outside the region and is hash-bound.

**Normalization `N`.** Input: the exact bytes `F` of the file.

1. `F` must be valid UTF-8, must not begin with the bytes `EF BB BF`, and must
   not contain the byte `0x0D`. Otherwise the identity cannot be computed and
   the step that needs it fails. These are checks; nothing is converted.
2. Let `BEGIN` be the bytes of the begin marker line followed by one LF, and
   `END_MARK` the bytes of the end marker line followed by one LF. An
   occurrence counts only at the start of the file or immediately after an LF.
   `BEGIN` must occur exactly once, at offset `b`. `END_MARK` must occur
   exactly once, at offset `e`, with `e ≥ b + length(BEGIN)`. Otherwise fail.
3. `N(F)` = `F[0 : b + length(BEGIN)]`, then the bytes
   `GOVERNANCE-MANIFEST-DERIVED-METADATA-PLACEHOLDER` and one LF, then
   `F[e : end]`.
4. Nothing else is changed, ignored, trimmed, or reordered. Every byte outside
   the region, including both marker lines, is hashed as it is.

The **normalized-content identity** is the SHA-256 of `N(F)`, 64 lowercase
hexadecimal characters. In the manifest it is the content-id
`nsha256:<identity>`. It is used for `CURRENT_AUTONOMOUS_RUN.md` in a
`GOVERNANCE-CLOSURE` manifest and for no other path and no other kind.

Two consequences follow directly from the definition:

- changing the region's content does not change the identity;
- changing any byte outside the region changes it.

**Where the bytes come from.**

- *Before the commit:* the worktree file, read in binary. It must be
  storage-identical: `git hash-object -- <path>` equals
  `git hash-object --no-filters -- <path>`. If the two differ, Git would store
  different bytes than the worktree holds, and the manifest cannot be
  finalized. The run file is rewritten at every stage and is always written
  with LF line endings and no byte-order mark; that is how this one file is
  written, not a normalization of the repository.
- *After the commit:* the blob bytes of `<commit>:<path>`
  (`git cat-file blob <commit>:<path>`), read without any re-encoding.
  **Byte-fidelity check:** the SHA-1 of the bytes `blob `, the decimal length,
  one `0x00`, then the content must equal the Git blob id
  `git rev-parse <commit>:<path>`. If it does not, the bytes were altered in
  transit and are read again.

**Test vector.** For a file of exactly these six lines, each ending in one LF:

```text
alpha
<!-- BEGIN GOVERNANCE MANIFEST DERIVED METADATA -->
anything here
more
<!-- END GOVERNANCE MANIFEST DERIVED METADATA -->
omega
```

`N(F)` is 163 bytes and the normalized-content identity is
`adfb3c4d8884348818a852e497a0992da9a67a86828937ec3f4dd9a5cc457f25`.

### 9.6 Governance closure sequence

There is one sequence. `AUTONOMOUS_LOOP.md` stages 15–19 are these steps.

1. **Draft.** The governance closure documents are brought to their
   substantive final state. The derived-metadata region is Idle.
2. **`EBD-C`.** The CTO reviews and approves that substantive state, as
   EBD-002 requires (`AUTONOMOUS_LOOP.md` §8.4). The `EBD-C` approval record is
   written **before** any final manifest computation, and is itself part of
   the closure content.
3. **Freeze.** After `EBD-C`, no substantive governance content may change.
   Substantive content is every byte of every closure path except the content
   of the derived-metadata region.
4. **Invalidation.** If `EBD-C` causes, requests, or requires any substantive
   change, or any substantive change happens after it for any reason, that
   `EBD-C` approval is invalid. The draft is updated and `EBD-C` is repeated.
5. **Final manifest.** With a valid `EBD-C` and every approval record that
   belongs in the closure present, Claude Code computes the entries natively:
   `blob:` identities as in Section 9.3 for every closure path, and the
   `nsha256:` identity of Section 9.5 for `CURRENT_AUTONOMOUS_RUN.md`.
6. **`manifest_id`.** The canonical body is serialized and its SHA-256
   computed (Section 9.2).
7. **Insert derived metadata.** The region is changed from Idle to Finalized.
   Nothing else in any file is touched.
8. **Confirm.** The normalized-content identity of `CURRENT_AUTONOMOUS_RUN.md`
   is recomputed and must equal the value in the manifest. Because `N`
   replaces the region, the insertion cannot have changed it: this is a single
   check, not an iteration, and the algorithm ends here. If the value differs,
   a byte outside the region changed; the manifest is discarded and step 4
   applies.
9. **Governance closure commit**, by Claude Code, containing exactly the
   manifest's paths.
10. **`G3a-G`** reconstructs and verifies (Section 9.7).
11. **On mismatch**, `G3a-G` fails and nothing is pushed. The correction is a
    forward commit. If it changes any byte outside the derived-metadata
    region, in any closure path, the sequence returns to step 1 and `EBD-C` is
    repeated. If it changes only the region, the sequence returns to step 5.

### 9.7 Verification at `G3a-G`

Codex performs every step and compares byte strings. Inspection of the content
does not replace any of them.

1. **Lineage.** Read `baseline_commit` from the `Governance Closure Baseline`
   field of the run file in the commit (outside the region, so hash-bound). It
   must equal the commit Codex verified at `G3b-E`, be an ancestor of the governance commit, and
   `baseline_commit..<commit>` must contain exactly the expected commits.

   **Bootstrap closure only (Section 9.2).** No `G3b-E` commit exists, so in
   place of that one equality Codex verifies every one of the following, and
   the gate fails if any does not hold:
   - the run file in the commit, outside the region, records
     `Engineering Batch: NONE` and the Bootstrap Amendment as approved;
   - `baseline_commit` is exactly
     `9e2463fda8dad102601296f7e5bec33da5d68757`;
   - `baseline_commit` equals the commit live `origin/claude-safe-review`
     points to — it is the last remotely verified baseline;
   - `git ls-tree -r --name-only <baseline_commit> -- docs/execution/autonomy/`
     returns nothing — the harness has never been committed, so this is its
     first closure;
   - no engineering commit exists in `baseline_commit..<commit>`, and every
     path in the range is documentation.

   The ancestor and expected-commits checks above still apply.
2. **Path set and blob identities.** Run
   `git -c core.quotepath=false diff --raw --no-renames --no-abbrev <baseline_commit> <commit>`
   and build one entry line per path: status, new mode, and `blob:` plus the
   new blob id, or `000000` and `DELETED` for a deletion.
3. **Normalized identity.** For `CURRENT_AUTONOMOUS_RUN.md`, read the committed
   blob bytes, pass the byte-fidelity check, apply `N`, compute the SHA-256,
   and use `nsha256:<identity>` as that path's content-id in place of the blob
   id.
4. **Header.** `kind` is `GOVERNANCE-CLOSURE`; `schema` is `2`; `batch` is the
   `Engineering Batch` value in the committed run file, outside the region
   (`NONE` only in the bootstrap closure);
   `revision` is `git rev-list --count <baseline_commit>..<commit>`;
   `entry_count` is the number of entries.
5. **Canonical `manifest_id`.** Serialize the canonical body as in Section 9.2
   and compute its SHA-256.
6. **Derived metadata.** Extract the region from the committed run file. It
   must be Finalized, and byte-for-byte equal to: the opening fence line, the
   canonical body from step 5, the line `manifest_id: ` followed by the value
   from step 5, and the closing fence line.

`G3a-G` passes the equivalence check only if step 6 holds exactly. Any change
outside the region after the manifest was finalized changes a blob id or the
normalized identity, so the reconstruction no longer equals the region and the
gate fails. Any change inside the region that is not the finalized manifest
fails the same comparison.

The remaining `G3a-G` checks — scope, closure claims against evidence, the
presence of the `EBD-C` record, run state — are made in addition
(Section 2.6).

### 9.8 What is pushed is what was verified

`G3a-E` and `G3a-G` verdicts state the full hash of the commit verified.
`G3b-E` and `G3b-G` pass only if live origin equals that exact hash. A commit
created or changed after its post-commit gate has not been verified and is not
pushed.

## 10. Amendment log

| Version | Date | Amendment | Authority | Decision Log |
|---|---|---|---|---|
| 1.0 | 2026-10-08 | Ratified with the harness. | Founder | `docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md` |
| 1.1 | 2026-10-08 | Bootstrap Amendment: one-time exception for the initial harness governance closure — fixed `baseline_commit` and `batch: NONE` (§2.6, §9.2, §9.7). No other rule changed. | Founder | `docs/decisions/EBD-008-harness-bootstrap-amendment.md` |
