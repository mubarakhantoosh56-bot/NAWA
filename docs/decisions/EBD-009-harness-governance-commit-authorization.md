# Executive Board Decision #009 — Conditional Authorization to Stage and Create the Harness Governance Commit

**Status:** Ratified. Records the Founder's decision of 2026-10-08.
**Version:** 1.0
**Category:** Decision Logs
**Scope:** The Founder's conditional authorization to stage and create the one governance commit that closes the NAWA Autonomous Development Harness v1, and the closure preparation approved with it.
**Non-scope:** Any push; any other commit; any engineering batch; the content of the harness.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** Founder & CEO.
**Effective date:** 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. Why this record exists

`docs/governance/EBD-002_GOVERNANCE_MODEL.md` §4.1 states that a Founder
decision without a Decision Log entry is not an official decision, and §10
requires the entry at `docs/decisions/<ID>-<slug>.md`. This is a new, explicit
Founder authorization, so it has its own entry. It records the decision; it
adds nothing to it.

## 2. Context

The harness was ratified (`EBD-007`) and amended for its own first closure
(`EBD-008`). Neither decision authorized staging or committing it. The CTO's
first `EBD-C` review on 2026-10-08 withheld approval because the closure
documents were not yet at their substantive final state: the run file carried
no prospective `Ahead State` for the governance commit, it stated that no
commit authorization existed, and several documents carried wording that would
be false inside the commit. An authorization recorded only after `EBD-C` would
itself have been a substantive change and would have invalidated the approval.

## 3. Options considered

The instruction that recorded the decision lists no alternative, and none is
reconstructed here.

## 4. Decision

**Founder:** Mubarak. **Decision date:** 2026-10-08.

**Authorization:** CONDITIONAL STAGE + GOVERNANCE COMMIT AUTHORIZATION.

The Founder's authorization, as given:

```text
1. Pre-recording conditional authorization to STAGE and CREATE the governance
   commit that closes NAWA Autonomous Development Harness v1.

2. The exact commit subject is:

Docs: add NAWA Autonomous Development Harness v1 (Founder-ratified, bootstrap closure)

3. This stage/commit authorization may be executed ONLY AFTER:

- EBD-C = APPROVED
- Governance Closure Manifest = finalized
- manifest_id = finalized
- deterministic derived metadata = inserted
- normalized CURRENT_AUTONOMOUS_RUN identity = confirmed

4. PUSH IS NOT AUTHORIZED.

5. Founder also approves:
- updating CURRENT_STATE.md
- the required pre-EBD-C closure wording/state corrections
- preparing the exact prospective Ahead State needed before EBD-C
```

**Authorized governance commit subject:**

```text
Docs: add NAWA Autonomous Development Harness v1 (Founder-ratified, bootstrap closure)
```

**Execution conditions — all required before staging:**

- `EBD-C` APPROVED
- Governance Closure Manifest finalized
- `manifest_id` finalized
- deterministic derived metadata inserted
- normalized run-file identity confirmed

**Push authorization:** NOT GRANTED by this decision.

## 5. Reasoning

No reasoning beyond the explicit decision was recorded, and none is added.

## 6. Consequences accepted

**What the decision does:** once every execution condition holds, Claude Code
may stage exactly the paths of the finalized Governance Closure Manifest and
create one commit with the subject above, on `claude-safe-review`, with parent
`9e2463fda8dad102601296f7e5bec33da5d68757`. Recording the authorization before
`EBD-C` lets it be part of the content `EBD-C` approves and the manifest binds.

**What it does not authorize:**

- A2
- engineering batch activation
- migrations
- production deployment
- destructive data operations
- history rewrite
- push

A push needs `G3a-G` PASS and a separate Founder push authorization. The
harness is not ACTIVE until `G3b-G` PASS.

## 7. Documents affected

- `CURRENT_STATE.md` — one entry recording the harness milestone.
- The nine harness documents under `docs/execution/autonomy/` — status wording
  that stays true before and after the governance commit; in
  `CURRENT_AUTONOMOUS_RUN.md`, the commit authorization, the prospective
  `Ahead State`, and the exact prospective commit path list.
- `docs/execution/autonomy/NAWA_AUTONOMOUS_DEVELOPMENT_CHARTER.md` — a record
  of the decisions taken after ratification (§19).
- `docs/decisions/EBD-007-autonomous-development-harness-v1-ratification.md` —
  one sentence reworded so that it stays true inside the commit.

No harness rule changes. EBD-002 is unchanged.

## 8. Ratification

| Role | Record |
|---|---|
| Founder & CEO — approver | Mubarak, 2026-10-08. Authorization quoted in Section 4. |
| CTO — steward | Claude Cowork drafted this record and the closure preparation under Founder instruction. A CTO record is not an independent review, and this record is not the `EBD-C` approval. |
| AI Engineering Team — independent review | None is recorded here. Independent verification of the prepared closure state is a later step. |
| CPO (Aboura) | No separate written review is held in this repository. |

## 9. Record notes

- **Identifier.** `EBD-009` is the next unused EBD identifier; `EBD-001` to
  `EBD-008` are in use. It is open to correction by the Founder.
