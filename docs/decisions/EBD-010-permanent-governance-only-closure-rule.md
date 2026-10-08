# Executive Board Decision #010 — Permanent Governance-Only Closure Rule

**Status:** Ratified. Records the Founder's decision of 2026-10-08.
**Version:** 1.2 — adds the Supplemental Decision (Section 10) and the Second Supplemental Decision (Section 11), both of 2026-10-08.
**Category:** Decision Logs
**Scope:** The permanent rule for governance closures made while no engineering batch is active: the canonical `batch` value `GOVERNANCE-ONLY`, its eligibility, its baseline, and the gates it keeps.
**Non-scope:** Engineering batches and their closures; the bootstrap closure (`EBD-008`); any stage, commit, or push.
**Owner:** CTO (Claude Cowork), as steward of the Decision Log.
**Approval authority:** Founder & CEO.
**Effective date:** 2026-10-08.
**Last updated:** 2026-10-08.

---

## 1. Why this record exists

`docs/governance/EBD-002_GOVERNANCE_MODEL.md` §4.1 states that a Founder
decision without a Decision Log entry is not an official decision, and §10
requires the entry at `docs/decisions/<ID>-<slug>.md`. This is a new Founder
decision, so it has its own entry. It records the decision; it adds nothing to
it.

## 2. Context

The harness became ACTIVE on 2026-10-08, when its governance commit
`4aec1e48a7ee9aac71d2769f11643ebb450b5959` passed `G3b-G`. The bootstrap
exception (`EBD-008`) — `batch: NONE` with a fixed baseline — ended with that
closure and may not be reused.

The post-activation governance reconciliation that followed is
governance-only, with Engineering Batch `NONE`. `REVIEW_PROTOCOL.md` §9.2 then
gave such a closure no valid `batch` value and no baseline rule, so it could
not be manifested. The question was reserved to the Founder and the run
stopped for the Founder's decision.

## 3. Options considered

The instruction that recorded the decision lists no alternative, and none is
reconstructed here.

## 4. Decision

**Founder:** Mubarak. **Decision date:** 2026-10-08. **Decision:** APPROVED.

The canonical rule, as given:

```text
1. `batch: GOVERNANCE-ONLY` is the permanent canonical batch identity for
   governance-only closures when Engineering Batch = NONE.

2. Baseline must be the exact last remotely verified branch checkpoint
   recorded before drafting begins.

3. Scope must be governance/documentation only.

4. If product, tests, migrations, data, knowledge, secrets, or engineering
   implementation changes are present, GOVERNANCE-ONLY is invalid.

5. EBD-C remains mandatory.

6. Governance Closure Manifest remains mandatory.

7. G3a-G remains mandatory.

8. Push requires separate Founder authorization after G3a-G PASS.

9. G3b-G remains mandatory.

10. `batch: NONE` remains bootstrap-only and may not be reused.

11. Governance-only closure must not piggyback on an arbitrary engineering
    batch to bypass governance gates.
```

| Element | Rule |
|---|---|
| Canonical `batch` value | `GOVERNANCE-ONLY` — permanent |
| Eligibility | Engineering Batch = `NONE` |
| Baseline | The last remotely verified branch checkpoint, captured before governance drafting begins |
| Baseline of the current reconciliation | `4aec1e48a7ee9aac71d2769f11643ebb450b5959` |
| Scope | Governance / documentation only |
| Excluded — any one makes `GOVERNANCE-ONLY` invalid | product; tests; migrations; data; knowledge; secrets; engineering implementation |
| Required, unchanged | `EBD-C`; Governance Closure Manifest; `G3a-G`; separate Founder push authorization after `G3a-G` PASS; `G3b-G` |
| `batch: NONE` | Bootstrap-only; not reusable |

Founder authority, the history-rewrite protections, independent review, and
remote verification are unchanged. No gate is removed or weakened.

## 5. Reasoning

No reasoning beyond the explicit decision was recorded, and none is added.

## 6. Consequences accepted

**What the decision does:** it gives governance-only work done while no
engineering batch is active a permanent, defined closure path, with every
existing gate kept.

**What it does not authorize:**

- A2 or any engineering batch
- migrations
- product changes
- staging or committing — each governance-only closure still needs its own
  Founder stage/commit authorization
- push — still a separate Founder authorization after `G3a-G` PASS
- amend, rebase, reset, or any history rewrite

The decision also resolves the Founder stop raised by the post-activation
reconciliation (Section 2).

## 7. Documents affected

- `docs/execution/autonomy/REVIEW_PROTOCOL.md` — §2.6, §9.2, and §9.7 amended
  for `GOVERNANCE-ONLY`; version 1.1 → 1.2; amendment log. Manifest
  serialization and schema unchanged.
- `docs/execution/autonomy/CURRENT_AUTONOMOUS_RUN.md` — governance state: the
  closure batch and baseline, and the Founder-stop history.
- `docs/execution/autonomy/H0_FOUNDER_REVIEW_PACKAGE.md` — the gap recorded
  there marked resolved.

EBD-002 is unchanged. No other harness rule changes.

## 8. Ratification

| Role | Record |
|---|---|
| Founder & CEO — approver | Mubarak, 2026-10-08. Rule quoted in Section 4. |
| CTO — steward | Claude Cowork drafted this record and the protocol amendment under Founder instruction. A CTO record is not an independent review. |
| AI Engineering Team — independent review | None is recorded here. A focused independent review is a later step. |
| CPO (Aboura) | No separate written review is held in this repository. |

## 9. Record notes

- **Identifier.** `EBD-010` is the next unused EBD identifier; `EBD-001` to
  `EBD-009` are in use. It is open to correction by the Founder.

## 10. Supplemental Founder decision — derived-metadata region lifecycle

**Founder:** Mubarak. **Decision date:** 2026-10-08. **Decision:** APPROVED,
as a supplement to this decision. It is not a separate EBD.

**Context.** The derived-metadata region of `CURRENT_AUTONOMOUS_RUN.md` still
held the finalized manifest of the bootstrap closure when the first
governance-only closure opened. The protocol allowed the region to change only
between Idle and Finalized, so how a new closure should treat it was undefined.

**The rule, as given.** For every governance closure, the region has an
independent lifecycle:

```text
Finalized(previous) → Idle(new closure) → Finalized(new closure)
```

1. When a new governance closure is opened and the region still contains the
   finalized manifest of the previous closure, it may be reset to the
   canonical Idle placeholder.
2. That reset may occur only before `EBD-C` for the new closure.
3. The previous finalized manifest remains preserved, immutably, in the
   previous commit and in Git history.
4. A direct `Finalized(previous) → Finalized(new)` transition is forbidden.
5. After `EBD-C`, the only allowed transition is the deterministic
   `Idle → Finalized(new closure)`.
6. Any substantive governance-content change after `EBD-C` invalidates
   `EBD-C`. Before a new `EBD-C` may be issued, the closure lifecycle is
   restarted consistently with this rule.
7. The Governance Manifest schema version does not change.
8. `manifest_id` remains forbidden outside the designated derived-metadata
   region of `CURRENT_AUTONOMOUS_RUN.md`.
9. The supplemental decision grants no authority to stage, commit, or push,
   to activate A2, to authorize migrations, or to change the product.

**Documents affected.** `docs/execution/autonomy/REVIEW_PROTOCOL.md` §9.5 and
§9.6 (version 1.2 → 1.3, amendment log); `CURRENT_AUTONOMOUS_RUN.md` — the
region reset to Idle for the current `GOVERNANCE-ONLY` closure, and its
maintenance rule 10.

## 11. Second Supplemental Founder Decision — G3a-G Failure / Correction Restart Rule

**Founder:** Mubarak. **Decision date:** 2026-10-08. **Decision:** APPROVED,
as a permanent rule and a supplement to this decision. It is not a separate
EBD.

**Context.** After the first supplemental decision, the protocol still said
that a correction after a failed `G3a-G` which changed only the
derived-metadata region returned straight to manifest finalization. That would
have changed the region from one Finalized manifest to another after `EBD-C`,
which the lifecycle in Section 10 forbids.

**The rule, as given.** If `G3a-G` fails for any governance closure:

1. The closure becomes NOT PUSHABLE.
2. Amend, rebase, reset, and any history rewrite are forbidden.
3. Before any correction, the current `EBD-C` is recorded as
   `INVALIDATED FOR CORRECTION RESTART`.
4. Once `EBD-C` is invalidated, the closure is considered returned to a
   pre-`EBD-C` state for correction purposes.
5. The derived-metadata region may then transition `Finalized → canonical Idle`
   as part of the correction restart.
6. The governance closure baseline does not move to the failed local commit.
   It remains the last remotely verified checkpoint from which the closure
   originally began.
7. Corrections are forward-only.
8. If a new commit is required, it is a forward correction commit above the
   failed local commit.
9. Revision increases according to the existing protocol.
10. After correction: independent review is performed when required; a new
    `EBD-C` is required; the derived region transitions deterministically
    `Idle → Finalized`; and `G3a-G` is run again on the corrected tip.
11. Push remains forbidden until the corrected `G3a-G` is PASS and the Founder
    grants a separate push authorization.
12. After the authorized push, `G3b-G` remains mandatory.
13. The failed local closure commit is never pushed by itself.
14. The Governance Manifest schema version does not change because of this
    rule.
15. This approval grants no authority to stage, commit, or push, to activate
    A2, to authorize migrations, or to change the product.

**Documents affected.** `docs/execution/autonomy/REVIEW_PROTOCOL.md` §3.1,
§9.5, and §9.6 step 11 (version 1.3 → 1.4, amendment log);
`docs/execution/autonomy/AUTONOMOUS_LOOP.md` §3 — its description of a failed
`G3a-G` replaced by a reference to the protocol; `CURRENT_AUTONOMOUS_RUN.md` —
governance state.
