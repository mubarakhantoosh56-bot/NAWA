# Active Batch

**Status:** Founder-ratified as amended on 2026-10-08 (`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`; Bootstrap Amendment `docs/decisions/EBD-008-harness-bootstrap-amendment.md`). ACTIVE since 2026-10-08 — `G3b-G` PASS on the harness governance commit `4aec1e48a7ee9aac71d2769f11643ebb450b5959`.
**Version:** 1.0
**Category:** Agent Instructions (autonomous-run operational record)
**Scope:** The single record of which batch, if any, the Founder has activated for autonomous execution.
**Non-scope:** Project status in general — `CURRENT_STATE.md` is authoritative for that; this file is derived from it.
**Owner:** CTO (Claude Cowork), per Documentation Standard §3.10.
**Approval authority:** Founder. Only an explicit Founder instruction may change the activation state below.
**Effective date:** 2026-10-08.
**Last updated:** 2026-10-08.

---

## Current activation state

```text
ACTIVE AUTONOMOUS ENGINEERING BATCH:
NONE

HARNESS:
ACTIVE — since 2026-10-08 (G3b-G REMOTE VERIFIED)

PRODUCT DEVELOPMENT:
NOT ACTIVE

NEXT ELIGIBLE ENGINEERING BATCH:
A2 / DEFECT-002

A2 IS NOT ACTIVATED.
```

No engineering work is authorized. No migration is currently authorized.

## Harness setup — authorization on record

**H0 — setup.**

- **Authorized by:** Founder, 2026-10-03.
- **Authorized scope:** creation of the NAWA Autonomous Development Harness v1
  — governance / orchestration infrastructure only.

**H0.1 — hardening pass.**

- **Authorized by:** Founder; Founder decisions 1–7 recorded in Charter §15.
- **Authorized scope:** governance / orchestration hardening only — role
  reconciliation with EBD-002, relocation to `docs/execution/autonomy/`,
  rule refinements, native Git verification, and one read-only Codex
  invocation probe.

**H0.1-R1 — correction after independent review.**

- **Authorized by:** Founder, who accepted all four MAJOR findings and the one
  MINOR finding of the H0.1 independent review (Charter §16).
- **Authorized scope:** bounded governance / documentation correction of those
  findings only. No redesign, no autonomy expansion, no change to EBD-002.

**H0.1-R2 — correction after re-review.**

- **Authorized by:** Founder, who accepted the two MAJOR findings and the one
  MINOR finding remaining after the H0.1-R1 re-review (Charter §17).
- **Authorized scope:** narrowly bounded governance correction of those
  findings only.

**Explicitly not authorized by H0, H0.1, H0.1-R1, or H0.1-R2:** activating A2; modifying
product code or tests; modifying database schema; creating migrations;
modifying real pilot data or Company Brain knowledge; changing production
behaviour; deploying; touching secrets; merging to `main`; staging, committing,
or pushing the harness itself; rewriting Git history.

**Baseline HEAD:** `9e2463fda8dad102601296f7e5bec33da5d68757` on
`claude-safe-review`.

H0, H0.1, H0.1-R1, and H0.1-R2 are setup batches, not engineering batches. They grant
none of the autonomous authority in Charter §5.

**Founder ratification.** The Founder ratified the harness on 2026-10-08
(Charter §18;
`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`).
The ratification activates no engineering batch and authorizes no staging,
commit, or push. It did not itself make the harness ACTIVE.

**Bootstrap Amendment.** On 2026-10-08 the Founder approved a one-time
exception for the initial harness governance closure
(`docs/decisions/EBD-008-harness-bootstrap-amendment.md`; Charter §19). It
activates no engineering batch.

**Conditional governance commit authorization.** On 2026-10-08 the Founder
authorized staging and creating the one governance commit that closes the
harness, executable only after `EBD-C` is approved and the Governance Closure
Manifest and its derived metadata are finalized and confirmed
(`docs/decisions/EBD-009-harness-governance-commit-authorization.md`). It
grants no push and activates no engineering batch.

**Harness activation.** The harness became ACTIVE on 2026-10-08, when its
governance commit `4aec1e48a7ee9aac71d2769f11643ebb450b5959` passed `G3b-G` remote
verification. Activation activates no engineering batch: the active
autonomous engineering batch stays `NONE`, and A2 / DEFECT-002 stays NOT
ACTIVATED. Founder Review Package: `docs/execution/autonomy/H0_FOUNDER_REVIEW_PACKAGE.md`.

## Batch register

State source: `CURRENT_STATE.md` and
`docs/execution/pilot/PV1_SLICE3_REAL_OPERATIONAL_REASONING_VALIDATION.md` §20.
If this table disagrees with them, they win and this table is corrected.

| Item | State |
|---|---|
| M9 | CLOSED |
| PV1 Slice 1 | CLOSED |
| PV1 Slice 2 | CLOSED |
| PV1 Slice 3 | ACTIVE — FOUNDER BLOCKER REVIEW |
| A1 / DEFECT-007 | FORMALLY CLOSED — ENGINEERING + GOVERNANCE REMOTE VERIFIED |
| A2 / DEFECT-002 | NOT ACTIVATED |
| A3 / DEFECT-008 | NOT ACTIVATED |
| B1 / DEFECT-006 | NOT ACTIVATED |
| B2 / DEFECT-010 | NOT ACTIVATED |
| C1 / DEFECT-005 + D003 | NOT ACTIVATED |
| C2 / DEFECT-001 | NOT ACTIVATED |
| C3 / DEFECT-004 | NOT ACTIVATED |
| D / DEFECT-009 | NOT ACTIVATED |
| Slice 4 | NOT ACTIVATED |

A1 checkpoints:

- Engineering checkpoint: `0090d00c0de0c757c9618148c8b354c5bc4e3a0b`
- Governance closure: `9e2463fda8dad102601296f7e5bec33da5d68757`

Carried forward from the Slice 3 record: A2 requires its **Architecture Gate
before activation** — race-safe exact-content deduplication across
duplicate-sensitive durable writes is architecture-unproven. Being "next
eligible" changes nothing about that. "Architecture Gate" there is the Slice 3 record's own term for a
pre-activation requirement; it is not gate `G1` of the loop, which runs after
activation. How that requirement is met is a Founder decision at activation.

## Activation rules

1. Only the Founder activates a batch. Eligibility is not activation.
2. One engineering batch is active at a time.
3. Activating one batch never activates another. "Finish A2" does not
   authorize A3.
4. When a batch closes, this file returns to
   `ACTIVE AUTONOMOUS ENGINEERING BATCH: NONE` and the team stops.
5. An activation record is valid only if every field in the template below is
   filled from the Founder's instruction. A missing field is a Founder Stop,
   not something to infer.

## Activation record template

Copy this block into "Current activation state" when the Founder activates a
batch. Do not fill it speculatively.

```text
ACTIVE AUTONOMOUS ENGINEERING BATCH:
<batch id> / <defect id(s)>

ACTIVATED BY: Founder
ACTIVATION DATE: <YYYY-MM-DD>
AUTHORIZATION (quoted or precisely referenced):
<text>

BASELINE HEAD AT ACTIVATION:
<full commit hash>

IN SCOPE:
- <item>

OUT OF SCOPE:
- <item>

ACCEPTANCE CRITERIA:
- <criterion>

EXCEPTIONS EXPLICITLY GRANTED (migration / schema / other):
NONE | <exact exception>

RUNTIME VALIDATION RESULT IS A MILESTONE (EBD-002 Appendix A row 17 —
Founder review before CTO acceptance at EBD-B):
YES | NO | NO RUNTIME VALIDATION IN THIS BATCH

TASK DOCUMENT:
<path under docs/execution/>
```
