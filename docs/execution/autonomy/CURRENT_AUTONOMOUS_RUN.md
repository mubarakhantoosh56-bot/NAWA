# Current Autonomous Run — Checkpoint

**Status:** Founder-ratified as amended on 2026-10-08 (`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`; Bootstrap Amendment `docs/decisions/EBD-008-harness-bootstrap-amendment.md`). Not ACTIVE until `G3b-G` PASS on the harness governance commit.
**Version:** 1.0
**Category:** Agent Instructions (autonomous-run operational record)
**Scope:** The live checkpoint of the autonomous run — enough for a new session to resume with no conversation history.
**Non-scope:** Project status in general (`CURRENT_STATE.md` is authoritative) and batch evidence (lives in the batch's task document under `docs/execution/`).
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10. Maintained by Claude Cowork and Claude Code.
**Approval authority:** Founder (scope and authority rules).
**Effective date:** On successful remote verification (`G3b-G`) of the harness governance commit. Founder-ratified 2026-10-08.
**Last updated:** 2026-10-08.

---

## Checkpoint

The block below is YAML. Field names are fixed; do not rename them. Gate and
checkpoint ids are the fixed ids in `REVIEW_PROTOCOL.md` §2.1 and
`AUTONOMOUS_LOOP.md` §8.

```yaml
Harness Version: v1
Harness Phase: "Bootstrap governance closure — AUTONOMOUS_LOOP.md stages 15–21. Stage 15 documentation is at its substantive final state. Progress through stages 16–21 is read from the EBD-C, G3a-G, and G3b-G fields and from Git, not from this line."
Harness Ratification: "FOUNDER RATIFIED AS AMENDED — NOT YET ACTIVE"
Founder Ratification Date: 2026-10-08
Founder Ratification Record: "docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md (Charter §18)"
Harness Active: "NO — the harness is marked ACTIVE only after its governance commit passes G3b-G"
Bootstrap Amendment: "APPROVED — INITIAL HARNESS CLOSURE ONLY"
Bootstrap Amendment Date: 2026-10-08
Bootstrap Amendment Record: "docs/decisions/EBD-008-harness-bootstrap-amendment.md (REVIEW_PROTOCOL.md §9.2; Charter §19)"
Bootstrap Baseline: 9e2463fda8dad102601296f7e5bec33da5d68757
Bootstrap Batch: NONE
Bootstrap Amendment Review: "Codex — all substantive checks PASSED; one MINOR state inconsistency in this file's checkpoint fields (as stated by the Founder)"
Governance Commit Authorization: "CONDITIONALLY AUTHORIZED BY FOUNDER — 2026-10-08"
Governance Commit Authorization Record: "docs/decisions/EBD-009-harness-governance-commit-authorization.md (Charter §19)"
Governance Commit Authorization Scope: "Staging and creating the one harness governance closure commit. Nothing else."
Governance Commit Subject: "Docs: add NAWA Autonomous Development Harness v1 (Founder-ratified, bootstrap closure)"
Governance Commit Execution Conditions:
  - "EBD-C = APPROVED"
  - "Governance Closure Manifest finalized"
  - "manifest_id finalized"
  - "Deterministic derived metadata inserted"
  - "Normalized CURRENT_AUTONOMOUS_RUN.md identity confirmed"
Push Authorization: "NOT AUTHORIZED — EBD-009 grants no push. A push needs G3a-G PASS and a separate Founder or governed push authorization, recorded when it is given. None is recorded in this file."
Engineering Batch: NONE
Product Development: NOT ACTIVE
A2: NOT ACTIVATED
Migration Authorization: NONE
Active Batch: "NONE (engineering). Harness: FOUNDER RATIFIED AS AMENDED — NOT YET ACTIVE."
Authorization: "Founder — H0 (2026-10-03): create the NAWA Autonomous Development Harness v1. H0.1: harden it per Founder decisions 1–7 (Charter §15). H0.1-R1: correct the four MAJOR findings and one MINOR finding of the H0.1 independent review (Charter §16). H0.1-R2: correct the two MAJOR findings and one MINOR finding remaining after the H0.1-R1 re-review (Charter §17). H0.1-R2 final state sync: correct only the one MINOR stale-state finding of the H0.1-R2 focused re-review, in this file. H0.1-R2 final stale-state cleanup: correct only the stale state references found by the Codex final confirmation, in this file. Ratification recording (2026-10-08): record the Founder Ratification — governance state only. Bootstrap Amendment recording (2026-10-08): amend REVIEW_PROTOCOL.md §2.6, §9.2, §9.7 for the initial harness governance closure only, and record it. Bootstrap checkpoint-state correction (2026-10-08): correct the checkpoint fields in this file only. Pre-EBD-C closure preparation (2026-10-08, EBD-009): update CURRENT_STATE.md, make the pre-EBD-C wording and state corrections, and prepare the prospective Ahead State. Conditional governance commit authorization (2026-10-08, EBD-009): stage and create the one harness governance closure commit, with the exact subject recorded above, only after every execution condition recorded above holds. Governance/documentation only. Not authorized: A2 activation, any engineering batch, product code, tests, schema, migrations, data, Company Brain knowledge, secrets, production behaviour, deploy, destructive data operations, merge to main, any other commit, pushing, or any Git history rewrite."
Autonomy Level: "LIMITED — every independent gate requires a Founder-initiated Codex invocation (Charter §14)"
Codex Automation: CODEX_INTERFACE_PRESENT_BUT_AUTOMATION_NOT_PROVEN

Repository: 'D:\nawa\AIMX_PROJECTS'
Branch: claude-safe-review
Baseline HEAD: 9e2463fda8dad102601296f7e5bec33da5d68757
Baseline Parent: 0090d00c0de0c757c9618148c8b354c5bc4e3a0b
Last Verified Product Baseline: 9e2463fda8dad102601296f7e5bec33da5d68757
Tracking Origin: "origin/claude-safe-review @ 9e2463fda8dad102601296f7e5bec33da5d68757 — as last verified on 2026-10-08, before the governance commit (then ahead 0, behind 0)"
Live Origin: "https://github.com/mubarakhantoosh56-bot/NAWA.git refs/heads/claude-safe-review @ 9e2463fda8dad102601296f7e5bec33da5d68757 (git ls-remote, 2026-10-08, before the governance commit)"

Ahead State:
  Expected Local Commit: "Before the governance commit exists: NONE — local HEAD equals the remote checkpoint. Once it exists: exactly one commit — the harness governance closure commit, which carries this file. It is identified beforehand (SESSION_RECOVERY_PROTOCOL.md §5) by parent 9e2463fda8dad102601296f7e5bec33da5d68757, by the subject 'Docs: add NAWA Autonomous Development Harness v1 (Founder-ratified, bootstrap closure)', and by the exact 16-path list under Prospective Governance Commit. Its hash is written to the worktree copy of this file immediately after the commit (class B3)."
  Expected Remote Checkpoint: 9e2463fda8dad102601296f7e5bec33da5d68757
  Why Ahead: "Governance window — AUTONOMOUS_LOOP.md stage 18, Governance Closure Commit (bootstrap closure). It applies only once that commit exists."
  Push Authorized: "NO — NOT AUTHORIZED until G3a-G PASS and a separate Founder or governed push authorization. EBD-009 grants no push."
  Next Required Gate: "G3a-G — once the governance commit exists. G3b-G follows the governance push."

Prospective Governance Commit:
  Parent: 9e2463fda8dad102601296f7e5bec33da5d68757
  Branch: claude-safe-review
  Subject: "Docs: add NAWA Autonomous Development Harness v1 (Founder-ratified, bootstrap closure)"
  Authorized By: "EBD-009 — conditional; staging and this one commit only"
  Path Count: 16
  Paths:
    - "M AGENTS.md"
    - "M CLAUDE.md"
    - "M CURRENT_STATE.md"
    - "A docs/decisions/ADR-001-harness-v1-bootstrap-closure-ebd-c.md"
    - "A docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md"
    - "A docs/decisions/EBD-008-harness-bootstrap-amendment.md"
    - "A docs/decisions/EBD-009-harness-governance-commit-authorization.md"
    - "A docs/execution/autonomy/ACTIVE_BATCH.md"
    - "A docs/execution/autonomy/AUTONOMOUS_LOOP.md"
    - "A docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md"
    - "A docs/execution/autonomy/FOUNDER_REVIEW_PACKAGE_TEMPLATE.md"
    - "A docs/execution/autonomy/FOUNDER_STOP_CONDITIONS.md"
    - "A docs/execution/autonomy/NAWA_AUTONOMOUS_DEVELOPMENT_CHARTER.md"
    - "A docs/execution/autonomy/REVIEW_PROTOCOL.md"
    - "A docs/execution/autonomy/ROLE_MATRIX.md"
    - "A docs/execution/autonomy/SESSION_RECOVERY_PROTOCOL.md"
  Path Note: "A = added, M = modified, relative to the parent. The commit contains exactly these 16 paths and no other. The ADR-001 path is the EBD-C record: it is created only when EBD-C is decided, and the commit cannot be made without an APPROVED EBD-C. The authoritative path set is the finalized Governance Closure Manifest; if it differs from this list, the closure stops and nothing is committed."

Current Phase: "EBD-C APPROVED — SUBSTANTIVE GOVERNANCE STATE FROZEN — GOVERNANCE MANIFEST FINALIZATION NEXT"
Last Verified Safe Checkpoint: 9e2463fda8dad102601296f7e5bec33da5d68757

Original H0.1 Native Git Verification: "PASSED — as stated by the Founder; the command output is not held in this file"
Original H0.1 Independent Review: "FAIL — Codex; four MAJOR findings and one MINOR finding, all accepted by the Founder"
H0.1-R1 Corrections: COMPLETED
H0.1-R1 Native Windows Git Verification: "PASSED — as stated by the Founder; the command output is not held in this file"
H0.1-R1 Independent Codex Re-Review: "FAIL — two MAJOR + one MINOR remaining; all accepted by the Founder. Findings 1 and 4 of the original review: RESOLVED."
H0.1-R2 Corrections: COMPLETED
H0.1-R2 Native Windows Git Verification: "PASSED — as stated by the Founder; the command output is not held in this file"
H0.1-R2 Focused Independent Codex Re-Review: "FAIL — one MINOR stale-state finding only (in this file)"
All Substantive R2 Governance and Integrity Checks: "PASSED — Codex found no remaining architecture, manifest, EBD-C, authority, or integrity defects (as stated by the Founder)"
H0.1-R2 Final State Sync: "COMPLETED 2026-10-08 — this file only"
H0.1-R2 Final State Sync Native Verification: "PASSED — as stated by the Founder; the command output is not held in this file"
Codex Final Confirmation (first): "FAIL — stale state references only (in this file)"
Substantive Harness Review: "PASSED — Codex found no substantive harness defect (as stated by the Founder)"
H0.1-R2 Final Stale-State Cleanup: "COMPLETED 2026-10-08 — this file only; the stale references to the final state sync native verification corrected"
Independent Review: "PASS — H0.1-R2 HARNESS SAFE FOR FOUNDER RATIFICATION (Codex; as stated by the Founder)"
Founder Ratification: "On 2026-10-08, Founder Mubarak: 'I approve Founder Ratification of the NAWA Autonomous Development Harness v1.'"

Bootstrap Checkpoint-State Correction: "COMPLETED 2026-10-08 — this file only"
Codex Bootstrap Checkpoint Confirmation: "PASS — BOOTSTRAP CHECKPOINT STATE SAFE — PROCEED TO EBD-C (Codex; as stated by the Founder)"
First EBD-C Review: "BLOCKED 2026-10-08 — Claude Cowork as CTO. No approval was issued and no file was changed. The closure documents were not at their substantive final state: no prospective Ahead State, no recorded commit authorization, and status wording that would have been false inside the commit."
Founder Conditional Governance Commit Authorization: "2026-10-08 — recorded in EBD-009. Staging and the one governance commit only; no push."
Pre-EBD-C Closure Preparation: "COMPLETED 2026-10-08 by Claude Cowork under EBD-009. Internal work — not independently verified at the time of writing."

Architecture Gate: "G1 — N/A, no engineering batch active"
Implementation Gate: "G2 — N/A, no engineering batch active"
Post-Commit Gate:
  Engineering: "G3a-E — N/A — no engineering commit exists in this bootstrap closure"
  Governance: "G3a-G — PENDING — APPLICABLE AFTER GOVERNANCE COMMIT"
Remote Verification Gate:
  Engineering: "G3b-E — N/A — no engineering commit exists in this bootstrap closure"
  Governance: "G3b-G — PENDING — APPLICABLE AFTER GOVERNANCE PUSH"
EBD-002 Approvals:
  EBD-A: "N/A — no engineering implementation / architecture transition in this bootstrap closure"
  EBD-B: "N/A — no engineering runtime-validation / engineering commit in this bootstrap closure"
  EBD-C: "APPROVED — CTO — 2026-10-08"
  EBD-C Record: "docs/decisions/ADR-001-harness-v1-bootstrap-closure-ebd-c.md"
Review Manifests:
  Gate 2 Review Manifest: "NONE — no engineering batch active"
  Governance Closure Baseline: 9e2463fda8dad102601296f7e5bec33da5d68757
  Governance Closure Manifest: "NONE — when one exists it appears only in the derived-metadata region below, never in this block"

EBD-C Record Path: "docs/decisions/ADR-001-harness-v1-bootstrap-closure-ebd-c.md — reserved for the EBD-C record of this bootstrap closure. ADR-001 is the first ADR identifier allocated in this repository (EBD-002 §10: ADR prefix for CTO decisions). The reservation is not an approval. The file is created only when EBD-C is decided; the EBD-C field above says whether it has been."

Completed Work:
  - "H0: nine harness documents authored; harness pointer section appended to AGENTS.md and CLAUDE.md (additive only)."
  - "H0.1: harness relocated to docs/execution/autonomy/; role model reconciled with EBD-002; correction-cycle, ahead-of-checkpoint, and Git-authority rules written; Codex invocation probed and classified."
  - "H0.1-R1: six-gate engineering/governance split; review manifests; EBD-002 checkpoints EBD-A, EBD-B, EBD-C; Founder protection of every Git history rewrite."
  - "H0.1-R2 MAJOR 1: manifest_id is now the SHA-256 of the complete canonical manifest; the SELF exception is removed and replaced by a normalized-content identity for this file (REVIEW_PROTOCOL.md §9.2, §9.5, §9.7)."
  - "H0.1-R2 MAJOR 2: one governance closure sequence — documentation, EBD-C, manifest finalization, commit, G3a-G — used everywhere (REVIEW_PROTOCOL.md §9.6, AUTONOMOUS_LOOP.md §2 and §8.4, ROLE_MATRIX.md)."
  - "H0.1-R2 MINOR: this file brought current."
  - "H0.1-R2 native Windows Git verification: PASSED (per the Founder)."
  - "H0.1-R2 focused Codex re-review: all substantive governance and integrity checks PASSED; one MINOR stale-state finding in this file."
  - "H0.1-R2 final state sync (2026-10-08): the stale-state finding corrected in this file only."
  - "H0.1-R2 final state sync native Windows verification: PASSED (per the Founder)."
  - "Codex final confirmation: substantive harness review PASSED; FAIL on stale state references in this file only."
  - "H0.1-R2 final stale-state cleanup (2026-10-08): those references corrected in this file only."
  - "Internal H0.1-R2 consistency review by Claude Cowork. Internal validation is not an independent verdict."
  - "Independent Codex verdict: PASS — H0.1-R2 HARNESS SAFE FOR FOUNDER RATIFICATION (per the Founder)."
  - "Founder Ratification, 2026-10-08. Recorded in the Decision Log entry, Charter §18, ACTIVE_BATCH.md, the header metadata of the nine harness documents, and this file. No harness rule changed."
  - "Founder Bootstrap Amendment, 2026-10-08. Recorded in Decision Log entry EBD-008, in REVIEW_PROTOCOL.md §2.6, §9.2, §9.7 (version 1.1, amendment log), and in this file. It applies to the initial harness governance closure only."
  - "Codex Bootstrap Amendment review: all substantive checks PASSED; one MINOR state inconsistency (per the Founder)."
  - "Bootstrap checkpoint-state correction (2026-10-08): EBD-C, G3a-G, and G3b-G recorded as applicable to the bootstrap governance closure; EBD-A, EBD-B, G3a-E, and G3b-E recorded as not applicable to it. This file only."
  - "Codex confirmation of the bootstrap checkpoint state: PASS — BOOTSTRAP CHECKPOINT STATE SAFE — PROCEED TO EBD-C (per the Founder)."
  - "First EBD-C review (2026-10-08): BLOCKED by Claude Cowork as CTO. No approval issued."
  - "Founder conditional governance commit authorization, 2026-10-08. Recorded in Decision Log entry EBD-009, Charter §19, ACTIVE_BATCH.md, CURRENT_STATE.md, and this file. It grants no push."
  - "Pre-EBD-C closure preparation (2026-10-08): harness milestone entry added to CURRENT_STATE.md; status wording made true both before and after the governance commit in the nine harness headers, Charter §18, ACTIVE_BATCH.md, and EBD-007 §6; Charter §19 added; the commit authorization, the prospective Ahead State, the exact prospective commit path list, and the reserved EBD-C record path recorded in this file. No harness rule changed."
  - "Independent Codex verification of the pre-EBD-C closure state: PASS — PRE-EBD-C CLOSURE STATE VERIFIED — CTO MAY PERFORM EBD-C (per the Founder)."
  - "EBD-C (2026-10-08): APPROVED by Claude Cowork as CTO. Recorded in Decision Log entry ADR-001 and under EBD-002 Approvals."
Current Work:
  - "No engineering work. Bootstrap governance closure only; the remaining sequence is under Pending Work."
Pending Work:
  - "This list is the remaining closure sequence, in order, as of Last Updated By. A step is complete when its own checkpoint field or Git shows it; its presence here is not a claim that it is still outstanding (see Notes — State as of)."
  - "3. Governance Closure Manifest finalization (REVIEW_PROTOCOL.md §9.6 steps 5–8), natively, by Claude Code, with the bootstrap baseline and batch."
  - "4. Staging and the governance commit by Claude Code, under EBD-009, with the exact recorded subject and exactly the manifest's paths."
  - "5. G3a-G — independent verdict by Codex."
  - "6. A separate Founder or governed push authorization, then the governance push by Claude Code."
  - "7. G3b-G — independent verdict by Codex."
  - "8. Marking the harness ACTIVE — only after G3b-G PASS, in a later governance update."

Expected Worktree Delta:
  Before The Governance Commit: "Exactly the paths of Prospective Governance Commit that exist in the worktree, and nothing else: each 'M' path as ' M', each 'A' path as '??'. That is 15 paths (3 ' M', 12 '??') until the EBD-C record is created, and all 16 (3 ' M', 13 '??') from then on. Nothing is staged until Claude Code stages under EBD-009."
  After The Governance Commit: "None of those paths. Only ' M docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md' may appear: the worktree copy is updated with the commit hash and later gate records (class B3)."

Tests: "None run. H0, H0.1, H0.1-R1, H0.1-R2, the ratification and amendment recordings, and the closure preparation change documentation only; no application, test, migration, data, or knowledge path changed."
Reviewer Verdicts: "Harness reviews (Codex): H0.1 — FAIL; H0.1-R1 re-review — FAIL, two MAJOR + one MINOR remaining; H0.1-R2 focused re-review — FAIL, one MINOR stale-state finding only, all substantive checks PASSED; Codex final confirmation (first) — FAIL, stale state references only, substantive harness review PASSED; Codex final verdict — PASS — H0.1-R2 HARNESS SAFE FOR FOUNDER RATIFICATION; Bootstrap Amendment review — all substantive checks PASSED, one MINOR state inconsistency; bootstrap checkpoint confirmation — PASS — BOOTSTRAP CHECKPOINT STATE SAFE — PROCEED TO EBD-C. All as stated by the Founder. No loop gate verdict is recorded in this file: G3a-G and G3b-G verdicts are recorded per REVIEW_PROTOCOL.md §7, never inside the commit they verify. No engineering batch has run under this harness. Prior A1 verdicts are recorded in docs/execution/pilot/PV1_SLICE3_REAL_OPERATIONAL_REASONING_VALIDATION.md §0.1."

Known Blockers:
  - "The harness is FOUNDER RATIFIED AS AMENDED but not ACTIVE. It becomes ACTIVE only after G3b-G PASS on its governance commit."
  - "No push authorization is recorded. EBD-009 grants none."
  - "Codex automation is not proven; the harness is LIMITED AUTONOMY until a controller or adapter is authorized and proven."
Founder Stop Condition Triggered?: "NO — none triggered as of Last Updated By."

Next Exact Action: "Finalize Governance Closure Manifest → compute manifest_id → insert deterministic derived metadata → confirm normalized CURRENT_AUTONOMOUS_RUN identity → execute Founder-authorized governance stage/commit → G3a-G → obtain push authorization → push → G3b-G → Harness ACTIVE only after G3b-G PASS"

Last Updated By: "Claude Cowork — 2026-10-08 02:45 Asia/Amman (UTC+3)"
```

## Governance manifest derived metadata

The region between the two marker lines below holds only values mechanically
derived from a finalized Governance Closure Manifest
(`REVIEW_PROTOCOL.md` §9.5). It is Idle unless a governance closure commit is
being prepared. Nothing else is ever written inside it, and the marker lines
appear nowhere else in this file.

<!-- BEGIN GOVERNANCE MANIFEST DERIVED METADATA -->
```text
REVIEW-MANIFEST
schema: 2
kind: GOVERNANCE-CLOSURE
batch: NONE
revision: 1
baseline_commit: 9e2463fda8dad102601296f7e5bec33da5d68757
entry_count: 16
M 100644 blob:5933d42a9c05ca69d8f4cedadefc388db66886f1 AGENTS.md
M 100644 blob:793a6eaca7d4f1010923f541219c6da4262268f1 CLAUDE.md
M 100644 blob:98ea66ec9cec8ad2900bcd64c6e900a0c9bc9627 CURRENT_STATE.md
A 100644 blob:fdd2b9a183517278e603cda9ced58b8765b2bd77 docs/decisions/ADR-001-harness-v1-bootstrap-closure-ebd-c.md
A 100644 blob:7d5edcd180ba7bcd930b22449a20d11fb37a09d4 docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md
A 100644 blob:8b15f6f3e7191df37ceab24b188594304fac0fef docs/decisions/EBD-008-harness-bootstrap-amendment.md
A 100644 blob:6f1fb90b1d60b717e135e77a4eb8e856beb474b8 docs/decisions/EBD-009-harness-governance-commit-authorization.md
A 100644 blob:7f4915861f8b557dfa5c6f0a3a637420b8fc09fc docs/execution/autonomy/ACTIVE_BATCH.md
A 100644 blob:cdafb6039334b14744b11b70cd925e6af34ebf6c docs/execution/autonomy/AUTONOMOUS_LOOP.md
A 100644 nsha256:aec4a2cdaffeacc581c669f76f4e306086eae340f9f3b2c9884f8a5eaac52caf docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md
A 100644 blob:c632996c27b5dbf6ae00841c98a201945281f202 docs/execution/autonomy/FOUNDER_REVIEW_PACKAGE_TEMPLATE.md
A 100644 blob:c303544e4d2338da011a4d4fb338d4ef86f6bd57 docs/execution/autonomy/FOUNDER_STOP_CONDITIONS.md
A 100644 blob:96ba4d233c3e3197d05456be8d19839dbcf779e0 docs/execution/autonomy/NAWA_AUTONOMOUS_DEVELOPMENT_CHARTER.md
A 100644 blob:18f709df98124e06c32ba4ececfacd0143ca5f18 docs/execution/autonomy/REVIEW_PROTOCOL.md
A 100644 blob:b8bf7b920126a909e9de4ca7fde53031734b9af6 docs/execution/autonomy/ROLE_MATRIX.md
A 100644 blob:9c9c34114ed9c26c14bbdd0dcdd480ca68bbb856 docs/execution/autonomy/SESSION_RECOVERY_PROTOCOL.md
END
manifest_id: 8d771114223044399ae7141c7f99a53d8aa625fa61bcbd435ea594a9bf310a5d
```
<!-- END GOVERNANCE MANIFEST DERIVED METADATA -->

## Native verification commands (run after any edit to this file)

Run natively in `D:\nawa\AIMX_PROJECTS`. All are read-only. Do not normalize
line endings.

```text
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
git diff --cached --name-only
git diff --name-only
git diff --check
git rev-list --left-right --count HEAD...origin/claude-safe-review
```

Expected **before the governance commit**: branch `claude-safe-review`; HEAD
`9e2463fda8dad102601296f7e5bec33da5d68757`; ahead/behind `0 0`; nothing staged
until Claude Code stages under `EBD-009`; the worktree delta exactly as
`Expected Worktree Delta` describes.

Expected **after the governance commit**: HEAD is the governance closure
commit and its parent is `9e2463fda8dad102601296f7e5bec33da5d68757`;
ahead/behind `1 0` until the governance push and `0 0` after it; the `Ahead State`
rule of `SESSION_RECOVERY_PROTOCOL.md` §5 applies.

## Notes

- **State as of.** Every point-in-time value in the checkpoint is stated as
  of `Last Updated By`. Once the `EBD-C` approval is recorded, this file is
  frozen outside the derived-metadata region (`REVIEW_PROTOCOL.md` §9.6
  step 3). The copy carried
  by the governance commit therefore cannot record that commit's hash, the
  `G3a-G` or `G3b-G` verdict, a push authorization, the push, or activation.
  Those are recorded afterwards in the worktree copy
  (`SESSION_RECOVERY_PROTOCOL.md` class B3 and §5; `REVIEW_PROTOCOL.md` §7)
  and in the Founder Review Package. In a committed copy, a `PENDING` gate
  field means "no verdict is recorded in this copy" — not "no verdict exists".
- This checkpoint is written before the steps named in `Next Exact Action`,
  and it is not edited merely to record that one of them has since been done.
  `Next Exact Action` is the sequence as of the last edit: a step in it that
  has already been carried out when the file is read is complete, not stale.
  Results are recorded in the next substantive update (maintenance rule 5).
- A second remote, `old-origin` (legacy AIMX backend), exists. It is never a
  push or verification target.
- **Placement (NOTE).**
  `docs/governance/NAWA_DOCUMENTATION_STANDARD_v1.md` §9.1 does not list
  `docs/execution/` in its folder structure. The harness stays in
  `docs/execution/autonomy/` by Founder decision.
- **Decision Log location.** EBD-002 §10 places Decision Log entries in
  `docs/decisions/`. The directory was created on 2026-10-08 by the Founder
  ratification record, `EBD-007`, its first entry. `EBD-008` records the
  Bootstrap Amendment and `EBD-009` the conditional governance commit
  authorization. The `EBD-C` record path is reserved under
  `EBD-C Record Path` in the checkpoint.
- The H0.1 Codex probe left one thread in the Codex desktop surface, titled
  "Run NAWA H0.1 read-only probe". It changed nothing in the repository.

## Maintenance rules

1. Update this file at every stage transition in `AUTONOMOUS_LOOP.md`, at every
   gate verdict and EBD-002 checkpoint, and before any session ends
   deliberately.
2. Record facts verified from Git, tests, or reviewer output — never intentions.
   Anything not verified is written as `UNVERIFIED`; anything reported by
   someone else is attributed to them.
3. Commit hashes are always the full 40 characters.
4. `Next Exact Action` names one concrete action, by gate or checkpoint id
   where one applies, and who performs it.
5. The file is overwritten in place. Its history is Git history. Updates are
   made in the worktree first and committed with the next governance commit —
   never by amending an existing commit.
6. Whenever local HEAD is ahead of the last remotely verified checkpoint, the
   `Ahead State` block must be complete and must match Git. See
   `SESSION_RECOVERY_PROTOCOL.md` §5 (ahead-of-checkpoint rule).
7. A gate verdict is copied verbatim under its gate id, with reviewer identity,
   date, and the exact commit or manifest reviewed. Engineering and governance
   verdicts are never merged. Cowork and Claude Code never write `PASS` for an
   independent gate on their own authority.
8. A CTO approval is recorded under `EBD-002 Approvals`, by checkpoint id,
   never in a gate field.
9. The file is always written with LF line endings and no byte-order mark.
10. The derived-metadata region is changed only at Governance Closure Manifest
    finalization, and only between Idle and Finalized. No `manifest_id` of a
    Governance Closure Manifest is ever written outside that region.
