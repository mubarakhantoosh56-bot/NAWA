# Executive Board Decision #008 — Bootstrap Amendment to the NAWA Autonomous Development Harness v1

**Status:** Ratified. Records the Founder's decision of 2026-10-08.
**Version:** 1.0
**Category:** Decision Logs
**Scope:** The Founder's decision to allow the initial governance closure of the harness itself — and only that closure — to use the last remotely verified baseline as `baseline_commit`, with `batch = NONE`.
**Non-scope:** Every other governance closure; every engineering batch; the content of the harness beyond the three sections named below; any commit, push, or deployment.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** Founder & CEO.
**Effective date:** 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. Why this record exists

`docs/governance/EBD-002_GOVERNANCE_MODEL.md` §4.1 states that a Founder
decision without a Decision Log entry is not an official decision, and §10
requires the entry at `docs/decisions/<ID>-<slug>.md`. This is a new Founder
decision, made after the ratification recorded in
`docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md`, so
it has its own entry. It records the decision; it adds nothing to it.

## 2. Context

The ratified harness defines the baseline of a Governance Closure Manifest as
the engineering commit verified at `G3b-E`, and takes the manifest's `batch`
from the activated engineering batch
(`docs/execution/autonomy/REVIEW_PROTOCOL.md` §2.6, §9.2, §9.7).

The harness's own first governance closure has neither: Engineering Batch is
NONE, no engineering commit exists for the harness setup and ratification run,
and so no `G3b-E`-verified commit exists. An independent Codex finding, as
referred to by the Founder, identified those three sections as the
requirements the closure could not meet as written.

## 3. Options considered

The instruction that recorded the decision lists no alternative, and none is
reconstructed here.

## 4. Decision

On 2026-10-08, Founder Mubarak stated:

```text
I approve a Bootstrap Amendment to the NAWA Autonomous Development Harness v1,
allowing ONLY the initial Harness governance closure, when Engineering Batch = NONE
and no G3b-E engineering commit exists, to use the last remotely verified baseline
as baseline_commit, with batch = NONE.
```

**The rule.** For the initial harness governance closure only, if all of these
are true:

1. Engineering Batch = NONE;
2. no engineering commit exists for the harness setup and ratification run;
3. no `G3b-E` engineering-verified commit therefore exists;
4. the closure is governance-only;
5. the harness itself is being closed for the first time;

then the Governance Closure Manifest uses:

| Field | Value |
|---|---|
| `baseline_commit` | `9e2463fda8dad102601296f7e5bec33da5d68757` — which must be the last remotely verified repository baseline |
| `batch` | `NONE` |

## 5. Reasoning

No reasoning beyond the explicit decision was recorded, and none is added.

## 6. Consequences accepted

**What the decision does:** it lets the harness's own first governance closure
be manifested and verified at `G3a-G` and `G3b-G` without an engineering
commit.

**Limits stated with the decision.** The rule applies once, to the initial
harness closure. It does not apply to future engineering batches, and it is
not to be generalized into "use any prior baseline", "skip `G3b-E` when
inconvenient", "governance-only work never needs engineering verification", or
any other bypass of the normal closure model. After initial harness
activation, the standard `G3b-E`-based governance baseline rule remains
authoritative wherever an engineering commit exists.

**What it does not authorize:**

- A2
- any engineering batch
- migrations
- production deployment
- destructive data operations
- staging
- commit
- push
- history rewrite
- future bypass of `G3b-E`

After the decision: Engineering Batch **NONE**; A2 **NOT ACTIVATED**; Product
Development **NOT ACTIVE**; Migration Authorization **NONE**. The harness is
**FOUNDER RATIFIED AS AMENDED — NOT YET GIT/REMOTE CLOSED**, and is not ACTIVE
until its governance commit passes `G3b-G`.

## 7. Documents affected

- `docs/execution/autonomy/REVIEW_PROTOCOL.md` — §2.6, §9.2, and §9.7 amended
  for the bootstrap closure; version 1.0 → 1.1; amendment log added. No other
  rule in it changes.
- `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` — governance state.

Not changed: the canonical manifest hashing algorithm, the normalized
`CURRENT_AUTONOMOUS_RUN.md` identity, the `EBD-C` sequence, the six-gate
model, any authority, the history-rewrite protection, the session recovery
rules, and EBD-002.

## 8. Ratification

| Role | Record |
|---|---|
| Founder & CEO — approver | Mubarak, 2026-10-08. Statement quoted in Section 4. |
| AI Engineering Team — independent review | Codex identified the affected sections, as referred to by the Founder. The finding text is not held in this repository. A focused Codex verification of the amended text is a later step; its result is not recorded here. |
| CTO — steward | Claude Cowork drafted the amended text under Founder instruction, and this record. A CTO record is not an independent review. |
| CPO (Aboura) | No separate written review is held in this repository. |

## 9. Record notes

- **Identifier.** `EBD-008` is the next unused EBD identifier; `EBD-001` to
  `EBD-007` are in use. It is open to correction by the Founder.
