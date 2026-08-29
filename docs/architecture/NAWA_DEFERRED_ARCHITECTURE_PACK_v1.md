# NAWA Deferred Architecture Pack v1

**Status:** Draft — Architecture Blueprint. **Not ratified. Not activated. No engineering authorization implied.**
**Version:** 1.3 — Tombstone Consistency Amendment applied (see Appendix A).
**Category:** Architecture Document (per NAWA Documentation Standard v1 §3.1).
**Subordinate to:** NAWA Reasoning Constitution v1.0; EBD-003 Architecture Freeze v1.0; EBD-004 Engine Definitions (MVP Edition).
**Scope:** Forward architecture for two known deferred gaps — Track A (OME Lifecycle & Bounded Growth Governance) and Track B (Durable Situation Memory). Planning only.
**Non-scope:** Implementation, schema DDL, migrations, sprint tasks, milestone activation, M9 scope, jurisdiction-specific legal compliance.
**Owner:** Founder & CEO (Mubarak).
**Approval authority:** Founder & CEO.
**Effective date:** N/A — blueprint only. This document takes effect only if and when a track is reopened by Founder decision.
**Last updated:** 2026-08-29.

> **Founder Precision Amendment (v1.1).** Two Founder decisions are recorded in this version and bind the rest of the document:
>
> 1. **Retention promise.** NAWA does not promise to keep organizational memory forever. *NAWA preserves organizational memory according to the organization's governed retention policy, while protecting the provenance and auditability required for trustworthy historical reasoning.* (Recorded as DAP-A-L10.)
> 2. **Governed immutable audit spine.** The audit spine is immutable and non-prunable during governed retention, but it is not absolutely immortal — it remains subject to explicit tenant-erasure, offboarding, contractual, or legal-authority processes, and retained tombstones are themselves subordinate to that same governed erasure authority, not an exception to it. (Recorded as DAP-A-L11.)
>
> No track is activated by this amendment. No milestone is created. No engineering work is authorized.
>
> **Erasure Authority Precision Amendment (v1.2).** An independent architecture review identified two precision blockers in v1.1, both corrected in this version: (1) tombstone retention was stated in places as absolute; it is now explicitly governed — see §A.7. (2) A-OFFBOARD was described in places as the source of deletion authority; it is now framed as a candidate future execution mechanism that carries out authority established elsewhere — see §A.12. Neither correction changes Track A/B deferral status, M9 scope, or the registry's minimum-foundation principle.
>
> **Tombstone Consistency Amendment (v1.3).** A follow-up review found four live normative statements that still implied mandatory tombstone survival — DAP-A-L1, the §A.6 exit-path diagram, §A.10 citation resolution, and the future acceptance standard. All four now defer to the governed-erasure rule already ratified in §A.7: a tombstone is normally retained **only** where the governing authority permits retention of minimal, non-content, non-identifying audit metadata, and may otherwise be removed, anonymized, transformed into permitted non-identifying metadata, or omitted entirely. Where no tombstone may remain, provenance is represented honestly as *source no longer retained under governed erasure* or as an explicitly non-resolvable historical reference. NAWA never fabricates substitute evidence. No architecture direction changed.

> **Reading contract.** Nothing in this document is a task. Nothing in this document is a commitment. Every proposed capability carries an explicit classification (`CORE FUTURE REQUIREMENT` / `LIKELY FUTURE REQUIREMENT` / `OPTIONAL` / `DEFER — DO NOT BUILD YET`) and every numeric value carries the label `PROPOSED FUTURE POLICY VALUE`. A future engineer should be able to open this document and start designing without re-deriving the problem. A future engineer should **not** be able to open this document and conclude that something is owed.

---

## Executive Summary

NAWA has two known architectural gaps that are correctly deferred and correctly *not* MVP blockers, but that will be expensive to retrofit if their shape is decided under pressure later. This pack fixes their shape now, at zero implementation cost.

**Track A — OME Lifecycle & Bounded Growth.** Durable organizational memory (`ReasoningReceipt`, `DecisionMemory`, `OutcomeMemory`) has no retention, archival, or bounded-growth governance. EBD-004 §4.9 explicitly forbids OME Foundation from growing indefinitely without a lifecycle policy, and assigns that policy to Runtime Document scope rather than contract scope. That policy does not yet exist. Therefore **full EBD-004 §4.9 compliance is NOT ESTABLISHED** — this is a stated, tracked, accepted gap, not a discovered defect.

Recommended future target: **Option A5 — company-configurable retention over a *governed immutable audit core* — implemented on A3/A4 mechanics (hot/archive tiering plus governed compaction), delivered in four stages, none of which start now.**

Per Founder Decision 1, A5 is not merely the cheapest correct option — it is the **only** option compatible with NAWA's approved product principle: *NAWA preserves organizational memory according to the organization's governed retention policy, while protecting the provenance and auditability required for trustworthy historical reasoning.* Options A1 and A2 are both excluded by that principle, from opposite ends: A1 cannot honor a retention policy that ends, and A2 destroys the provenance the second half of the sentence promises.

The sharpest finding in Track A: **the first real activation trigger will almost certainly be contractual, not volumetric.** At MVP data density NAWA could run for years before storage or latency hurts. What will actually force the issue is the first enterprise contract with a retention clause, or the first "delete my company" request. Those are product-blocking obligations with a hard deadline set by someone else, not scale problems NAWA can watch grow. The pack therefore isolates tenant offboarding / erasure as **Track A's earliest-activating sub-element** — flagged, not activated.

**Track B — Durable Situation Memory.** `DecisionMemory` may reference `situation_id`, but `operational_situations` is a *mutable, current-reality* object. A pointer from an immutable historical record into a mutable current record does not preserve history — it silently rewrites it. The failure mode is not a missing record; it is a record that still renders perfectly while meaning something different than it did at decision time. This pack names that failure **pointer drift / retroactive context mutation** and treats it as the core justification for the track.

Recommended future target: **Option B3 — immutable Situation snapshot captured at ReasoningReceipt time — with content-hash deduplication, which yields B4 (versioned snapshots) as an emergent property rather than a second build.** Snapshot the *interpretation*; reference the *facts*; hash the *reference set*. This is the design move that gives historical integrity without cloning the operational system into OME.

**Both tracks remain DEFERRED.** Neither is an M9 prerequisite. Neither activates the other. Neither may mutate Company Brain. Neither may override Current Truth.

---

## Current Verified State

Recorded as given by the Founder at the time of writing. This section is a snapshot of context, not a status claim by this document.

| Item | State |
|---|---|
| Safe GitHub checkpoint | branch `claude-safe-review` @ `5afd364eed5f73234031a7eebc81f4e27e5de4d4` |
| Local / origin divergence | 0 / 0 |
| M8 | CLOSED |
| Organizational Memory Engine MVP | IMPLEMENTED |
| Post-M8 ReasoningReceipt hardening | CLOSED |
| M1–M8 documentation reconciliation | CLOSED |
| Post-push current-state reconciliation | CLOSED |
| Sprint EX-1 | PAUSED — requires explicit Founder reactivation |
| Next engineering milestone | M9 — Decision Execution Foundation |
| M9 | SELECTED — IMPLEMENTATION NOT ACTIVATED |
| Track A | DEFERRED |
| Track B | DEFERRED — NOT MVP BLOCKING |

**Governing laws in force (restated, unchanged by this document):**

- AI Recommendation ≠ Human Decision
- Human Decision ≠ Outcome
- Historical Organizational Memory ≠ Current Truth
- Historical Decision ≠ current Company Brain policy
- Historical Outcome ≠ causal proof
- Multiple active Outcomes remain separate
- `unknown` is a valid Outcome state
- No automatic Company Brain mutation
- No automatic organizational learning
- No semantic-similarity claim in current MVP retrieval

**Current organizational-memory loop:**

```
Current Truth
  → Company Brain
    → Historical Organizational Memory
      → AI Reasoning
        → Auditable Recommendation
          → Human Decision
            → Human Outcome
              → Organizational Memory
```

**Contract anchor.** EBD-004 §4.9, OME Foundation, *Never Does*: "Grow indefinitely without a lifecycle policy (lifecycle policy is Runtime Document scope, not contract)." Track A is the design of that missing Runtime Document. It does not require a Tier 2 unfreeze, because lifecycle was explicitly placed outside the contract boundary.

---

## Why These Tracks Are Deferred

Deferral here is a decision, not an oversight. The reasoning, so it is not re-litigated:

1. **Neither track changes what NAWA concludes today.** Lifecycle governance changes what NAWA *keeps*; Situation Memory changes what NAWA can *prove later*. Neither improves the quality of a single current recommendation, which is the MVP's only real risk.
2. **Both tracks are cheap to defer and expensive to guess at.** The cost of deferring is that durable records accumulate un-tiered and situation context is un-snapshotted. Both are recoverable — records can be tiered retroactively; snapshots can begin at any point going forward. Neither creates unrecoverable corruption of existing data.
3. **Both are strictly more designable with real data.** Retention thresholds set before a single company has run for a year are fiction. Snapshot field selection made before anyone has actually asked "what did the system know then?" is guesswork.
4. **Anti-bloat.** NAWA is an MVP with a two-person executive core. An enterprise data-governance program built in advance of the first enterprise customer is the most predictable way to stall.

**What deferral does NOT mean.** It does not mean the gaps are unknown, unowned, or undocumented. EBD-004 §4.9 non-compliance is stated openly. This pack is the mitigation: the gaps are held in a designed state so that reopening either one is an implementation exercise, not a redesign.

---

# Track A — OME Lifecycle & Bounded Growth

## A.1 Current Gap

Durable OME persistence can grow indefinitely. There is no retention model, no archival tier, no pruning discipline, no per-tenant configuration, and no defined behavior for what happens to retrieval, citations, or explainability when a record ages out.

Concretely, today's durable OME record types are:

| Record | Nature | Written by | Immutability today |
|---|---|---|---|
| `ReasoningReceipt` | AI artifact — what NAWA reasoned, on what evidence, with what confidence | Reasoning pipeline | Treated as append-only |
| `DecisionMemory` | Human artifact — what a person decided | Human action | Append-only + supersession |
| `OutcomeMemory` | Human artifact — what happened after | Human action | Append-only; multiple actives remain separate; `unknown` valid |

M9 may introduce durable execution/action records. This pack does not assume it will, and does not design for it beyond one structural requirement (§A.16).

**Consequence of the gap:** EBD-004 §4.9 *Never Does* is not fully satisfied. Stating that plainly is worth more than quietly carrying it.

## A.2 Architectural Principles

These are the load-bearing rules. Everything else in Track A is mechanism. Proposed as future law, each with an ID for later reference.

| ID | Principle | Classification |
|---|---|---|
| **DAP-A-L1** | **No silent deletion.** Removal is always an act with a named authority behind it — never a side effect of a lifecycle job, and never a silent loss of provenance. The two paths differ. **Ordinary lifecycle archival, compaction, and pruning** must preserve provenance and must not destroy governed-retained audit identity; where they drop payload they leave a tombstone recording what existed, when it was removed, under what policy, and by what authority. **Governed erasure follows the governing authority:** where that authority permits retention of minimal, non-content, non-identifying audit metadata, the erasure leaves such a tombstone; where the authority requires complete deletion, the tombstone itself may be removed, anonymized, transformed into permitted non-identifying metadata, or omitted entirely. In both paths provenance is represented honestly and substitute evidence is never fabricated (§A.7, §A.10). | CORE FUTURE REQUIREMENT |
| **DAP-A-L2** | **Persistence retention ≥ retrieval window.** The window NAWA *reasons over* may shrink freely. The window NAWA *keeps* may never shrink below the governed immutable audit core for the duration of the governed retention policy. | CORE FUTURE REQUIREMENT |
| **DAP-A-L3** | **Compaction never destroys provenance.** A summary must carry pointers to, and content hashes of, every record it summarizes, and must be labeled `derived`. A summary that cannot name its sources is not a summary; it is a rumor. | CORE FUTURE REQUIREMENT |
| **DAP-A-L4** | **A citation must never break.** Archival changes access path and latency, never existence. Any citation emitted by Executive Intelligence must remain resolvable for the full retention life of its target. | CORE FUTURE REQUIREMENT |
| **DAP-A-L5** | **Archived ≠ untrue, and archived ≠ current.** Tier is a storage statement, not a truth statement. Archival must never be read as invalidation, and un-archival must never be read as re-validation. | CORE FUTURE REQUIREMENT |
| **DAP-A-L6** | **Configurable above a governed floor.** Tenants configure retention upward, never below the governed immutable audit core, for as long as the governed retention policy is in force. | CORE FUTURE REQUIREMENT |
| **DAP-A-L7** | **Derived memory is not policy.** No compacted summary, aggregate, or statistic may enter Company Brain automatically. Historical data ≠ policy. | CORE FUTURE REQUIREMENT |
| **DAP-A-L8** | **Lifecycle operations are themselves auditable events.** Every archive, compaction, and erasure run is recorded with scope, count, policy version, and actor. | CORE FUTURE REQUIREMENT |
| **DAP-A-L9** | **Lifecycle never touches Current Truth.** Operational events, situations, and the Truth Layer are governed by the operational domain. Track A governs OME durable records only. | CORE FUTURE REQUIREMENT |
| **DAP-A-L10** | **Governed retention, not perpetual retention.** *(Founder Decision 1.)* NAWA preserves organizational memory according to the organization's governed retention policy, while protecting the provenance and auditability required for trustworthy historical reasoning. NAWA makes no product, contractual, or marketing promise equivalent to "we keep your organizational memory forever." The architecture must therefore support company-specific retention policy, contractual retention requirements, future jurisdiction-specific compliance requirements, explicit tenant offboarding, explicit tenant export, and explicit authorized erasure. | CORE FUTURE REQUIREMENT |
| **DAP-A-L11** | **Governed immutable audit spine.** *(Founder Decision 2.)* The audit spine is immutable and **non-prunable by ordinary lifecycle mechanics** during governed retention — it is never removed because of age, storage pressure, compaction, summarization, archive migration, or retrieval optimization. It is **not** absolutely immortal: it remains subject to explicitly governed authority paths — tenant erasure, tenant offboarding, contractual deletion, legal/regulatory deletion authority, or other explicitly ratified deletion policy. The distinction is the mechanism, not the strength: **automatic lifecycle pruning must never destroy the audit spine; explicit governed erasure may remove or transform it under ratified authority.** | CORE FUTURE REQUIREMENT |

## A.3 Memory Classes

The single most useful output of Track A is a shared vocabulary. Five classes plus two states.

**1. Current Truth** — *not memory.* The live operational reality: operational events, situations, KPIs, current company state. Governed by the Truth Layer and the operational domain. **Out of Track A scope.** Named here only to fix the boundary.

**2. Active Operational Memory (HOT)** — durable OME records recent or relevant enough to participate in default organizational-memory retrieval. Low-latency store, fully indexed, complete payloads.

**3. Historical Organizational Memory (WARM)** — durable OME records past the hot window but still directly retrievable. Complete, immutable, indexed on the retrieval spine but possibly not on every secondary index. Eligible for retrieval when the query is explicitly historical or when a citation resolves into it.

**4. Archived Memory (COLD)** — durable OME records moved to cheaper storage. **Not** in default retrieval. Reachable by direct ID (citation resolution), audit export, and explicit historical query. Higher latency is acceptable; unavailability is not.

**5. Compacted Memory (DERIVED)** — a summary object standing *alongside* (never *instead of*) a set of archived records, carrying pointers and hashes back to them. Marked `derived: true`. May be retrieved; may never be cited as primary evidence; may never become policy.

**State: Superseded** — a record logically replaced by a newer one (e.g. a corrected `DecisionMemory`). Retained in full, linked via `superseded_by`, excluded from *current* interpretation, included in *historical* interpretation. Supersession is a relationship, not a deletion, and not a tier.

**State: Erased** — physical removal. Permitted **only** through a ratified authority path: tenant erasure, tenant offboarding, contractual deletion, legal/regulatory deletion authority, or other explicitly ratified deletion policy (DAP-A-L11). Normally leaves a tombstone (DAP-A-L1), governed by what that authority permits (§A.7) — tombstone retention is not a guarantee independent of the authority that ordered the erasure. Never a lifecycle outcome — no scheduled job, retention dial, or optimization may produce this state.

**The distinction that matters most:** *archival* is about cost and retrieval noise; *deletion* is about rights and obligations; *supersession* is about correctness; *compaction* is about summary convenience. Four different problems. Conflating them is how organizations lose their own history.

## A.4 What "Pruning" Means in NAWA

Direct answer to the question, because it drives everything downstream:

**Pruning in NAWA is a combination — tiering plus governed compaction — and never includes deletion of the audit spine. Removing the spine is not pruning at all; it is governed erasure, a different act with a different authority (DAP-A-L11).**

Decomposed:

| Mechanism | Applies to | Verdict |
|---|---|---|
| Ordinary lifecycle pruning (age, storage pressure, compaction, summarization, archive migration, retrieval optimization) | Audit spine (identity, lineage, links, hashes, timestamps, actor) | **Never.** Non-prunable during governed retention, without exception |
| Governed erasure (tenant erasure, offboarding, contractual deletion, legal/regulatory authority, other ratified deletion policy) | Audit spine | **Permitted under ratified authority only**, count-verified, with a minimized tombstone where that authority permits one and removal / anonymization / transformation where it requires complete deletion (§A.7). Not a lifecycle mechanism |
| Physical deletion | Bulky derived payloads (rendered narrative text, full prompt/response bodies, duplicated context blocks) after archival + hash retention | Permitted under policy, tombstoned, `CORE FUTURE REQUIREMENT` |
| Logical archival (tier move) | All durable OME records past the hot window | Primary mechanism, `CORE FUTURE REQUIREMENT` |
| Cold storage | Archived records | `LIKELY FUTURE REQUIREMENT` (activates on cost, not correctness) |
| Summarization | Sets of archived records, as `derived` objects | `OPTIONAL` — value unproven until real density exists |
| Compaction (dedup by content hash) | Repeated context blocks across receipts | `LIKELY FUTURE REQUIREMENT` — highest storage-saving-per-unit-risk |

**The spine / payload split is the core design decision of Track A.** Every durable OME record is conceptually two things:

- **Spine** — `id`, `company_id`, `type`, `created_at`, `actor`, links to related records, evidence references, content hash, policy version. Small, fixed-size, and **non-prunable for the life of the governed retention policy**.
- **Payload** — narrative text, full reasoning context, rendered explanation, duplicated snapshots of upstream content. Large, variable, compressible, eventually droppable-with-hash.

Storage grows because of payload. Auditability depends on spine. Once those are separated, bounded growth stops being a hard problem and becomes a policy dial.

"Permanent" is the wrong word for the spine, and this document deliberately avoids it. The spine is **durable under lifecycle and removable under authority**. Both halves matter: without the first, history rots quietly; without the second, NAWA cannot honor an erasure obligation it will eventually be given.

## A.5 Retention Model Options

Evaluated on the nine required criteria. Scores are comparative judgements, not measurements: **H/M/L** = high/medium/low, and for cost/complexity lower is better.

| | **A1** Keep everything forever | **A2** Blind time-based deletion | **A3** Hot/Archive split | **A4** A3 + governed compaction | **A5** Company-configurable over governed immutable core |
|---|---|---|---|---|---|
| Data integrity | H | **L** | H | H | H |
| Auditability | H | **L** | H | H (with DAP-A-L3) | H |
| Cost | **L** (grows unbounded) | H | M | H | M |
| Complexity | **H** (best) — none | H — trivial | M | L | **L** (worst) — policy engine + config surface |
| Privacy / erasure rights | **L** — cannot satisfy erasure | M | L | L | **H** — the only option that can |
| Retrieval quality | M — degrades with noise | **L** — history vanishes | H | H | H |
| Future scale | **L** | H | H | H | H |
| Company Brain safety | H | H | H | M — summaries invite drift | M — mitigated by DAP-A-L7 |
| Organizational-memory safety | H | **L** — irreversible loss | H | M | H |

**Reading the table:**

- **A1 is where NAWA is today**, and it remains an acceptable *operating posture* for an MVP with no retention obligations. It is **not** available as a *product promise*: Founder Decision 1 (DAP-A-L10) forbids "we keep your organizational memory forever." A1 is what NAWA currently does, not what NAWA says.
- **A2 is the trap.** It is the cheapest to build and the most damaging thing NAWA could do to itself. A product whose thesis is institutional memory cannot delete institutional memory on a timer. **Blind time-based deletion is rejected permanently, not deferred.**
  **What that rejection does *not* mean.** It does not mean every record and every metadata field must survive forever regardless of tenant policy or legal authority. What is rejected is *blind, automatic, timer-driven* deletion of organizational history with no governing authority behind it. Deletion executed under a ratified authority path — tenant erasure, offboarding, contract, or law — is a different act entirely and is fully supported (DAP-A-L11). Time may legitimately appear *inside* a governed retention policy as a customer-configured parameter; what is rejected is time acting as the authority rather than as a parameter of one.
- **A3 is the correct first mechanism** — it solves cost and retrieval noise without touching integrity.
- **A4 adds the storage lever** but introduces the one genuinely dangerous idea in Track A: a summary that outlives its sources. DAP-A-L3 exists specifically to defuse it.
- **A5 is the correct target shape** — but A5 is a *policy layer over A3/A4 mechanics*, not an alternative to them. Choosing A5 does not skip A3. Under Founder Decision 1, A5 is also the only option that can express the approved product principle, because it is the only one where the customer's governed policy — not NAWA's storage convenience and not a hardcoded promise — determines how long memory lives.

## A.6 Recommended Future Architecture

**Target: A5 over A3+A4 mechanics, staged.**

**Product principle this architecture serves (Founder Decision 1, DAP-A-L10):** *NAWA preserves organizational memory according to the organization's governed retention policy, while protecting the provenance and auditability required for trustworthy historical reasoning.* Every mechanism below exists to make that sentence true — the tiering to keep it affordable, the governed immutable core to keep it trustworthy, the erasure path to keep it honest.

```
                 ┌─────────────────────────────────┐
                 │  Governed Immutable Audit Core  │  ← non-prunable by lifecycle;
                 │  (spine of every OME record)    │     removable only via ratified
                 └────────────────┬────────────────┘     erasure authority
                                  │
        ┌──────────────┬──────────┴───────────┬──────────────┐
        │              │                      │              │
     ┌──▼──┐        ┌──▼───┐              ┌───▼───┐     ┌────▼─────┐
     │ HOT │ ─────▶ │ WARM │ ───────────▶ │ COLD  │     │ DERIVED  │
     │     │        │      │              │archive│ ◀── │ compacted│
     └─────┘        └──────┘              └───────┘     │ summary  │
   default          historical            citation +    └──────────┘
   retrieval        retrieval             audit only    never primary evidence

   Tier transitions driven by: TenantRetentionPolicy (configurable) ∩ GovernedFloor
   Every transition: logged as a lifecycle audit event (DAP-A-L8)

   Two distinct exit paths — never conflated:
     lifecycle pruning ──▶ may drop payload, may move tier, NEVER removes spine
     governed erasure  ──▶ ratified authority only; may remove spine
                           ├─ tombstone retained if authority permits
                           └─ otherwise remove / anonymize / transform as required
```

**Staging — each stage is a separate future decision, not a plan:**

| Stage | Content | Trigger to consider it | Classification |
|---|---|---|---|
| **A-S0** | Growth telemetry only: per-company durable-record counts, byte footprint, OME retrieval latency attribution. No lifecycle behavior. | The cheapest possible first slice whenever Track A opens; also the thing that makes every later threshold real instead of invented | CORE FUTURE REQUIREMENT (first slice, not now) |
| **A-S1** | Hot/Warm/Cold tiering + tier-aware retrieval + citation resolution across tiers | Volumetric or latency trigger fires (§A.14) | CORE FUTURE REQUIREMENT |
| **A-S2** | Payload/spine split, hash-preserving payload drop, context-block dedup | Storage cost becomes a real line item | LIKELY FUTURE REQUIREMENT |
| **A-S3** | Tenant retention configuration + governed floor enforcement + policy versioning | First contract with a retention clause | LIKELY FUTURE REQUIREMENT |
| **A-S4** | Governed compaction / summarization | Only after A-S1–A-S3 and only if retrieval quality demonstrably suffers from volume | OPTIONAL |
| **A-OFFBOARD** | Governed erasure path: tenant export, data inventory, authorized erasure, controlled deletion, retention-policy termination, with tombstones where the governing authority permits them (§A.7) | **First offboarding or erasure request** — contract-triggered, independent of all volumetric triggers | LIKELY FUTURE REQUIREMENT — earliest activating |

**A-OFFBOARD is deliberately not numbered inside the staging sequence.** It does not depend on A-S1. It is a small, self-contained obligation that can be built on its own, and it is the element most likely to be demanded first by someone outside NAWA. Flagging it is the single most practically useful thing this track does.

**A-OFFBOARD is a candidate future execution/coordinating mechanism for governed tenant offboarding and erasure.** It does not itself create the authority to delete data; it executes an authority established by contract, tenant instruction, legal/regulatory requirement, retention policy, or other ratified governance source (§A.12). That separation is what makes the two Founder decisions structurally consistent rather than merely verbally reconciled: the spine is untouchable by every lifecycle stage (A-S0 through A-S4) acting on its own initiative, and removable only when a ratified authority instructs it — with A-OFFBOARD as the candidate mechanism that carries out that instruction. It remains **deferred, not activated, and not an M9 requirement.**

## A.7 Governed Immutable Audit Core (the Audit Spine)

**Definition (Founder Decision 2, DAP-A-L11).** The governed immutable audit core — the *audit spine* — is the set of fields that is **immutable and non-prunable during governed retention, but remains subject to explicit tenant-erasure, offboarding, contractual, or legal-authority processes.**

Two properties, held together:

| Property | Meaning |
|---|---|
| **Immutable** | Never rewritten in place. Corrections create new records; they never edit the spine of an existing one |
| **Non-prunable during governed retention** | Never removed by age, storage pressure, compaction, summarization, archive migration, or retrieval optimization — for as long as the governed retention policy is in force |
| **Governed, not immortal** | Removable through an explicitly ratified authority path: tenant erasure, tenant offboarding, contractual deletion, legal/regulatory deletion authority, or other explicitly ratified deletion policy |

**The distinction that must never blur:**

| | Automatic lifecycle pruning | Explicit governed erasure |
|---|---|---|
| Who initiates | A scheduled job, a policy dial, a storage optimization | A named authority: the tenant, a contract, a regulator, a ratified policy |
| May drop payload | Yes, with hash retention | Yes |
| May move tier | Yes | N/A |
| **May remove the spine** | **Never** | **Yes, under that authority** |
| Leaves a tombstone | Yes (for any payload drop) | Normally, if the authority permits retention of non-content audit metadata — but the authority may instead require the tombstone itself to be removed, anonymized, or transformed (§A.7) |
| Reversible | Tier moves yes; payload drop no | No |
| Auditable | Logged as a lifecycle run (DAP-A-L8) | Logged with authority, scope, counts, and date |

This is not a weakening of audit integrity. Audit integrity means NAWA cannot *quietly lose* history. It has never meant that NAWA can refuse a customer's lawful instruction about the customer's own data — and a system that could not honor such an instruction would be unshippable, not principled.

**Proposed core (per durable OME record) — `CORE FUTURE REQUIREMENT`:**

- `id`, `company_id`, `record_type`, `created_at`, `created_by` (human user or runtime component)
- Lineage links: `reasoning_receipt_id`, `decision_memory_id`, `outcome_memory_id`, `situation_id` — whichever apply
- `evidence_refs` — identifiers of the evidence the record stood on
- `content_hash` — hash of the full record as originally written
- `superseded_by` / `supersedes`
- `retention_class`, `tier`, `policy_version`, `archived_at`
- For `OutcomeMemory`: outcome state including `unknown`, and its separateness from other active outcomes

**What must never be removed by lifecycle mechanics, for the life of the governed retention policy — `CORE FUTURE REQUIREMENT`:**

1. Any element of the audit core above.
2. Any `ReasoningReceipt` that has ever been surfaced to a human. If a person saw it, NAWA must be able to say what they saw.
3. Any `DecisionMemory`. A human decision is the highest-value record in the system and the one NAWA has the least right to discard on its own initiative.
4. Any `OutcomeMemory` linked to a retained decision — including `unknown` outcomes. An `unknown` that disappears silently becomes a false implication that no outcome was ever sought.
5. The link structure between the three. Records surviving with their relationships severed is a subtler loss than deletion and harder to detect.
6. Any tombstone.

**Scope of that list.** It binds every lifecycle mechanism — tiering, archival, compaction, summarization, payload drop, retrieval optimization — absolutely and without exception. It does **not** bind governed erasure: an authorized tenant erasure, offboarding, contractual deletion, or legal-authority instruction may remove any of items 1–6 within that tenant's scope, including the tombstone itself, if the governing authority requires complete deletion of tenant/customer data. **Governed tombstone retention, not absolute tombstone retention, is the rule.** A tombstone SHOULD normally survive governed erasure when the governing authority permits retention of non-content, non-identifying audit metadata — that is the default, and it is what lets a fully erased tenant leave NAWA's own record that the erasure happened, under what authority, and over how many records, holding no tenant content (§A.12). But if the governing authority requires complete deletion of even that record, the system must be able to remove the tombstone, anonymize it, transform it into non-tenant-identifying aggregate/audit metadata, or otherwise comply with the ratified erasure authority. The specific treatment is governed by the authority and retention policy in force, not fixed by this document.

**Tombstone data minimization (future architecture only — not required now).** Where governing authority permits tombstone retention, the tombstone should carry only the minimum information necessary to preserve honest provenance semantics — never a copy of what was erased. Potential future tombstone content: an opaque record identifier; record class/type; erasure state; a non-sensitive timestamp; a hash or provenance marker where permitted; and an authority category, without retaining unnecessary tenant content. None of these fields is mandated now; the exact set is a future design decision. A tombstone must **not** preserve the original payload, decision text, outcome text, situation content, customer-identifying data, or other erased content merely to maintain provenance — doing so would defeat the erasure it is meant to attest to.

## A.8 Archive Strategy

- **Trigger:** age-based by default, relevance-aware only as a later refinement (§A.15). Age is boring, predictable, explainable to a customer, and cheap to reason about. Relevance-based tiering is where clever systems quietly lose the record someone needed.
- **Unit:** the individual record, not the batch — but executed in batches for cost.
- **Reversibility:** archival is reversible. Any archived record can be promoted back to warm on access. `LIKELY FUTURE REQUIREMENT`.
- **Chain integrity:** a `DecisionMemory` and its `OutcomeMemory` should not be split across tiers in a way that breaks a single explanation. Proposed rule: **archive by lineage cluster, not by row.** `CORE FUTURE REQUIREMENT`.
- **An open outcome pins its cluster.** While an `OutcomeMemory` is in `unknown` or otherwise open state, its lineage cluster stays warm regardless of age. Unresolved history is not history yet. `CORE FUTURE REQUIREMENT`.
- **Legal hold:** a per-company or per-cluster flag that suspends every lifecycle transition. Concept only. `DEFER — DO NOT BUILD YET` (the workflow engine around it is pure speculation until a real obligation exists; the *flag field* is trivial to add at A-S1 time).

## A.9 Retrieval Behavior

**Question: do archived records remain eligible for Organizational Memory retrieval?**

**Answer: not by default; always by explicit path.** Three retrieval modes, proposed:

| Mode | Tiers searched | Purpose |
|---|---|---|
| `default` | HOT (+ WARM within retrieval window) | Normal reasoning. Bounded, fast, recency-weighted. |
| `historical` | HOT + WARM + COLD | Explicit historical inquiry. Slower, allowed. |
| `resolve` | any tier, by ID | Citation resolution and audit. Must always succeed. |

**Rules — `CORE FUTURE REQUIREMENT`:**

- The reasoning pipeline uses `default`. Widening it is a deliberate, logged act, not a fallback.
- Retrieval results must carry `tier` and `age`, so Executive Intelligence can label historical material as historical.
- **Empty ≠ nonexistent.** If `default` returns nothing but `historical` would return something, the response must say so rather than implying the company has no history. Silent recency bias is how a memory product starts lying by omission.
- A record's tier must never change what it *says*, only how it is *reached*.

**Architectural hygiene observation (not a task):** all of the above is cheap *if* OME retrieval already passes through a single repository-level entry point, and expensive if retrieval calls are scattered. That is worth knowing now; it is not worth refactoring for now.

## A.10 Provenance Preservation

- **Citations are durable for the life of the governed retention policy (DAP-A-L4).** A citation emitted in a 2026 Executive Brief must resolve in 2029, whatever tier the target sits in. If the target has been erased under a ratified authority, the citation resolves to whatever that authority permits to remain: a governed-erasure tombstone where one is retained, and otherwise an explicit erased/unavailable state or a controlled, declared non-resolvable reference. What is never permitted is *deceptive* silence — a citation must never appear satisfied while the evidence behind it is gone (next bullet but one).
- **Citations resolve by ID + hash, never by content match.** If the hash no longer matches, the citation resolves as `provenance_degraded` with an explanation — never silently, and never as a clean success.
- **Tombstones are resolvable, where retained.** Resolving a citation to a record erased under ratified authority must return "erased under authority X on date Y", not a 404, whenever a tombstone survives that erasure (§A.7). The absence must itself be explainable. **If the governing authority requires removal of even the tombstone, the system must not fabricate a replacement.** The citation instead resolves honestly to a state equivalent to "source no longer retained under governed erasure," or becomes non-resolvable in a controlled, explicit way. The system must never silently substitute another record, pretend erased evidence still exists, turn a summary into the original evidence, or fabricate provenance to paper over a governed removal.
- **Derived summaries never satisfy a citation.** A citation to a compacted set resolves to the summary *and* the list of source IDs and their state. `CORE FUTURE REQUIREMENT`.

## A.11 Tenant Configuration

Proposed configuration surface — `LIKELY FUTURE REQUIREMENT`, stage A-S3:

| Setting | Configurable | Floor |
|---|---|---|
| Hot window | Yes | Proposed floor: 90 days — `PROPOSED FUTURE POLICY VALUE` |
| Warm window | Yes | Bounded by audit core retention |
| Cold retention period | Yes, upward | Audit spine retained for the full governed retention period; removable only via a ratified erasure authority (§A.12) |
| Payload drop after archival | Yes (on/off) | Spine retained under every lifecycle path |
| Compaction enabled | Yes (on/off) | Off by default |
| Governed retention period (the policy itself) | Yes — this is the customer's promise, not NAWA's | Must be stated; may end |
| Erasure on offboarding / termination | Contractual or legal authority, not a toggle | Tombstone normally retained where the governing authority permits; otherwise removed, anonymized, or transformed per that authority (§A.7) |

**Rules:** configuration is versioned; every record records the `policy_version` under which it was tiered; changing policy never retroactively deletes anything already protected under a stricter prior policy (**ratchet rule** — a tenant can loosen the future, never the past). The ratchet governs *lifecycle*; it does not restrain a governed erasure authority, which by definition overrides prior policy. `CORE FUTURE REQUIREMENT`.

**Regulatory variability** is handled by making retention a *tenant configuration* and refusing to encode any jurisdiction in NAWA. NAWA ships dials and a governed floor; the customer's counsel sets the dials. Any jurisdiction-specific behavior is `DEFER — DO NOT BUILD YET`. This is exactly what Founder Decision 1 requires the architecture to support: the retention period is the organization's to declare, and NAWA's obligation is to honor it faithfully and prove it did — not to outlive it.

## A.12 Governed Erasure — Data Deletion / Tenant Offboarding (A-OFFBOARD)

The earliest-activating element of Track A. **A-OFFBOARD is a candidate future execution/coordinating mechanism for governed tenant offboarding and erasure. It does not itself create the authority to delete data; it executes an authority established by contract, tenant instruction, legal/regulatory requirement, retention policy, or other ratified governance source.** Everything else in Track A is forbidden from removing the audit spine on its own initiative — only a ratified authority, carried out through a mechanism such as A-OFFBOARD, may do so (DAP-A-L11).

**Three distinct concepts, kept separate:**

- **Authority source** — *why* deletion is permitted or required: a tenant/customer request, a tenant offboarding instruction, contractual retention expiry, a contractual deletion obligation, a legal order, a regulatory requirement, a privacy/compliance process, a company-specific retention policy, or other ratified governance authority. This architecture does not assume A-OFFBOARD creates or owns these authorities, and none of them is designed here.
- **Erasure execution mechanism** — *how* NAWA carries the instruction out safely and audibly. A-OFFBOARD is the candidate future mechanism for this role — export, inventory, authorized erasure, controlled deletion. A future standalone privacy/compliance mechanism may also exist; none is designed now.
- **Erasure result** — *what remains, if anything*, after the governed operation (§A.7): a minimized tombstone where the authority permits retention, or complete removal/anonymization where the authority requires it.

**Eventual scope of A-OFFBOARD (concept only — `LIKELY FUTURE REQUIREMENT`, not activated, not an M9 requirement):**

- tenant export
- data inventory (what exists, per record type, per company)
- authorized erasure
- controlled deletion
- retention-policy termination
- cryptographic or logical deletion approaches, if future architecture supports them — `OPTIONAL`; crypto-shredding is attractive because it can satisfy an erasure obligation while leaving tombstones and counts intact, but it presupposes a key-management design NAWA does not have and must not be assumed

Proposed shape:

1. **Export before erase.** Offboarding produces a complete, structured export of the tenant's durable OME before anything is removed. A customer leaving with nothing is a reputational event NAWA cannot afford.
2. **Scoped by `company_id`, verified by count.** Erasure enumerates every durable record type; the operation reports per-type counts and fails loudly on any record it cannot classify. Silent partial erasure is worse than refusal.
3. **Tombstone at tenant granularity**, retained outside the tenant's own data where the governing authority permits (§A.7), minimized to non-content, non-identifying fields: what was erased, how many records, under what authority, when. This is NAWA's own audit trail, not the customer's data. If the governing authority requires removal of even this tombstone, the system must comply rather than treat its retention as unconditional.
4. **Cross-tenant reference check.** No durable OME record may reference another company's record; offboarding is the moment that assumption gets tested, so it must be *verified*, not assumed.
5. **Backups are in scope conceptually, out of scope architecturally at MVP.** Erasure from backup snapshots is a storage-operations problem with its own timeline; the policy must state a backup-expiry window rather than pretend immediate erasure. `PROPOSED FUTURE POLICY VALUE`: backup rotation window ≤ 35 days.
6. **Authority is recorded, not inferred.** Every erasure names the authority it executed under — tenant instruction, contract clause, legal/regulatory order, or ratified internal policy. An erasure with no recorded authority is a defect, not a lifecycle event. This is what keeps DAP-A-L11's second half from becoming a loophole in its first half.

## A.13 Scaling Risks

Ordered by realistic likelihood of biting first:

1. **Contractual/erasure obligation before any technical pressure.** Most likely trigger by a wide margin. Mitigation: A-OFFBOARD is separable and small.
2. **Retrieval noise before retrieval latency.** Long before the database is slow, `default` retrieval starts returning stale, low-value history that dilutes reasoning quality. This degrades the *product* before it degrades the *system*, and it is easy to misdiagnose as a prompt problem. Mitigation: A-S0 telemetry plus recency weighting in the retrieval window.
3. **Payload bloat from repeated context.** Receipts that embed the same context blocks repeatedly grow storage superlinearly with usage while adding no information. Mitigation: content-hash dedup (A-S2).
4. **Index growth on the durable tables.** Predictable, cheap, solved by tiering/partitioning.
5. **Cost.** Last. At MVP density, real but small.
6. **Cross-track amplification.** If Track B ships, each reasoning cycle may add one more durable record, pulling volumetric triggers closer. Accounted for in §Cross-Track.

## A.14 Activation Triggers

Track A moves from **DEFERRED** to **READY FOR ENGINEERING DESIGN** when any *hard* trigger fires, or when two *soft* triggers fire together.

**Hard triggers (any one, immediately):**

| ID | Trigger | Note |
|---|---|---|
| **TA-H1** | First customer contract containing a data-retention, data-residency, or erasure clause | Contract-driven, not measurable in advance |
| **TA-H2** | First tenant offboarding or erasure request | Activates A-OFFBOARD specifically |
| **TA-H3** | First external audit, security review, or enterprise procurement questionnaire asking for a retention policy | Answering "we don't have one" costs a deal |
| **TA-H4** | Any incident where a citation fails to resolve, or a durable record is lost or orphaned | Correctness event |

**Soft triggers (two or more, together):**

| ID | Trigger | Proposed value |
|---|---|---|
| **TA-S1** | Durable OME records for a single company | ≥ 50,000 — `PROPOSED FUTURE POLICY VALUE` |
| **TA-S2** | `ReasoningReceipt` count for a single company | ≥ 25,000 — `PROPOSED FUTURE POLICY VALUE` |
| **TA-S3** | Durable OME storage footprint | ≥ 5 GB single company, or ≥ 50 GB total — `PROPOSED FUTURE POLICY VALUE` |
| **TA-S4** | p95 OME retrieval latency attributable to durable-table growth | > 300 ms — `PROPOSED FUTURE POLICY VALUE` |
| **TA-S5** | Companies in production | ≥ 5 — `PROPOSED FUTURE POLICY VALUE` |
| **TA-S6** | Continuous production operation for one company | ≥ 12 months — `PROPOSED FUTURE POLICY VALUE` |
| **TA-S7** | Observed retrieval-quality degradation attributed to historical volume in Founder or customer review | Qualitative, Founder-judged |

**Explicit caveat:** every number above is invented. They are placeholders with the right order of magnitude, not measurements. A-S0 telemetry exists precisely to replace them with real ones before any of them is used to authorize work.

## A.15 Time-Based vs Relevance-Based Retention

- **Time-based** is the recommended default for tier transitions: predictable, auditable, explainable, cheap.
- **Relevance-based** is attractive and dangerous. "Keep what matters" requires NAWA to decide what matters, which is a reasoning act performed on memory by a component that is contractually forbidden from reasoning (EBD-004 §4.9: OME "does not conclude"). A relevance-pruning OME would violate its own contract.
- **Recommended split:** relevance may weight **retrieval** (what surfaces first, within the retrieval window). Time alone governs **persistence tier**. Retrieval ranking is reversible; storage tiering that quietly buries records is not.
- **Hybrid exception, `OPTIONAL`:** lineage clusters containing a recorded Decision with a resolved Outcome may be held warm longer than age alone would allow, because they are the highest-value retrieval targets in the system. That is relevance used to *extend* retention, never to shorten it — which is the safe direction.

## A.16 Future Implementation Impact

| Layer | Expected impact | Notes |
|---|---|---|
| Database | Additive columns on durable OME tables (`tier`, `retention_class`, `archived_at`, `policy_version`, `content_hash`, `superseded_by`); new `retention_policy`, `lifecycle_run`, `tombstone` tables; likely time-partitioning | Additive, no destructive change to existing records |
| Migrations | Additive with backfill defaults; no data loss; reversible | Straightforward |
| Repositories | **Largest hidden cost.** Every durable-OME read becomes tier-aware. Cheap if reads funnel through one entry point; painful if scattered | The one place a retrofit hurts |
| Domain services | New: `RetentionPolicyService`, `ArchivalService`, `CitationResolver`, `OffboardingService`; later `CompactionService` | Self-contained |
| APIs | Admin retention config, tenant export, erasure request, lifecycle-run history | New surface, small |
| Reasoning pipeline | **Near-zero** if retrieval is behind one interface. NCE Lite consumes the memory surface; tier is invisible to it | By design |
| OME retrieval | Mode-aware (`default` / `historical` / `resolve`), tier metadata on results | Core work |
| Explainability | Citation resolver must handle warm/cold/tombstoned/degraded states; UI must show them honestly | Cannot be skipped |
| Frontend | Retention settings screen; "archived"/"historical" labeling on cited records; export/erasure flows | Modest |
| Tests | Tier transition correctness; citation-resolves-after-archive; lineage cluster never split; open-outcome pinning; tombstone integrity; offboarding completeness by count; ratchet rule | Meaningful suite |
| Browser E2E | Archive a record → open the brief that cites it → citation still resolves and is labeled | One high-value scenario |
| Storage operations | Cold store selection, restore drills, backup expiry window, cost monitoring | Ops, not product |

**One structural requirement that makes M9 and Track B cheap later — `CORE FUTURE REQUIREMENT` when built:** whenever Track A is built, it must be built around a **durable OME record registry** — a declared list of record types with their retention class, audit-core fields, and lineage links — rather than hardcoding three record types. Any future durable record (an M9 Action, a Track B SituationMemory) then registers itself instead of forcing a lifecycle redesign.

**Minimum-foundation principle (Founder-approved) — binds every future reader of this paragraph:** *the first activated capability that genuinely requires the durable OME record registry should build only the minimum extensible registry foundation required for its own scope. Deferred tracks may inherit that foundation later.* The registry is **not** a milestone, **not** a prerequisite project, **not** a standalone platform, and **not** a lifecycle framework that must exist before M9. See §Cross-Track for what this means if M9 turns out to be that first capability.

## A.17 Explicit Non-Goals

`DEFER — DO NOT BUILD YET`, all of it:

- A general enterprise data-governance framework.
- Jurisdiction-specific compliance (GDPR/CCPA/local) as encoded behavior. Configurable dials only.
- A legal-hold workflow engine.
- An analytics warehouse, data lake, or reporting store over OME.
- Cross-tenant aggregation, benchmarking, or industry statistics of any kind.
- ML- or relevance-based automatic pruning of persistence.
- Automatic learning of Company Brain policy from historical records or summaries (forbidden by DAP-A-L7 and by standing law).
- End-user-facing "manage your memory" UX.
- Lifecycle governance over operational events, situations, or the Truth Layer — different domain, different owners.

## A.18 Status

**TRACK A = DEFERRED — ARCHITECTURE BLUEPRINT READY.**

EBD-004 §4.9 full compliance remains **NOT ESTABLISHED** and is openly carried as a known gap. This document does not close it; it makes closing it a bounded implementation exercise. No engineering work is authorized.

---

# Track B — Durable Situation Memory

## B.1 Current Gap

`operational_situations` exists and is mutable. `DecisionMemory` may carry `situation_id`. There is no durable `SituationMemory` inside OME.

## B.2 Operational Situation vs Situation Memory

| | **Operational Situation** | **Situation Memory** (proposed) |
|---|---|---|
| Domain | Operational / Truth Layer | Organizational Memory (OME) |
| Mutability | Mutable — status, severity, summary, event set all evolve | Immutable once written |
| Question answered | "What is happening?" | "What did we believe was happening at time T?" |
| Time reference | Now | A fixed moment in the past |
| Authority | Current Truth | History and context only |
| Lifecycle | Opens, changes, resolves, closes | Written once, never altered |
| Retrieval role | Drives current reasoning | Explains past reasoning |

They are not two versions of the same thing. One is a **live entity**; the other is an **observation of that entity**. Conflating them is exactly the bug this track exists to prevent.

## B.3 The Historical Integrity Problem

Today's chain:

```
DecisionMemory ──(situation_id)──▶ operational_situations  ← MUTABLE
```

Render an explanation of that decision six months later and NAWA shows the situation *as it is now*: possibly resolved, possibly re-classified from `warning` to `normal`, possibly re-summarized, possibly grown to include events that did not exist at decision time.

**Name the failure: pointer drift / retroactive context mutation.**

Why it is worse than a missing record:

1. **It is invisible.** The explanation renders cleanly. Nothing errors. Nothing is flagged. It simply means something different than it did.
2. **It systematically flatters the past.** Situations tend to get resolved and downgraded, so historical decisions drift toward looking like overreactions to problems that "were only `normal` anyway."
3. **It corrupts the governing laws.** "Historical Decision ≠ current Company Brain policy" is upheld structurally, but "what the human was looking at" quietly becomes "what the system currently believes" — and that is the one thing an audit trail must never do.
4. **It cannot be fixed retroactively.** Once the situation row has mutated, the prior state is gone. Every day Track B stays deferred is a day of unrecoverable context, at a currently negligible rate.

That last point is the honest argument *for* eventually building it, and the honest reason it is *still* not urgent: at MVP density the volume of decisions whose context will ever be re-examined is close to zero.

## B.4 Snapshot Timing Options

*When* a snapshot is captured is a separate question from *what model* holds it. Four candidate triggers:

| Trigger | Captures | Misses | Volume | Verdict |
|---|---|---|---|---|
| **T1 — at `ReasoningReceipt` creation** | Every context NAWA actually reasoned over, decision or not | Nothing NAWA saw | One per distinct situation state, deduped | **Recommended.** The moment context is consumed is the moment worth freezing |
| **T2 — at `DecisionMemory` creation** | Context behind human decisions only | Every reasoning-only cycle — the majority — leaving "why did NAWA say that?" unanswerable | Lowest | Insufficient alone; fully covered by T1 via the receipt chain |
| **T3 — at Situation resolution** | A clean closing state | Everything *before* resolution, which is precisely what decisions were made on. Also never fires for situations that stay open | Lowest | **Rejected as a primary trigger.** It captures the least useful moment |
| **T4 — at first OME retrieval referencing the situation** | Whatever the situation happens to look like when someone later looks | Introduces a snapshot whose timestamp has no relationship to any decision — a snapshot of a *query*, not of a *reasoning moment* | Unpredictable | **Rejected.** Retrieval is a read; making it write history is both a side effect in the wrong layer and a record that means nothing |

**Recommended timing: T1, with T3 as an `OPTIONAL` closing snapshot.** A resolution snapshot adds a tidy final state for the "as it was / as it is now" view, costs almost nothing, and is safe because it is clearly labeled as a closing capture rather than a decision context. It is a nicety, not a requirement.

**Non-obvious point about T4:** it is the option that looks cheapest and is the most corrupting. A snapshot must be an observation made *at the moment of reasoning*. A snapshot created because someone ran a query in 2029 records 2029's situation state under the appearance of history.

## B.5 Model Options

| | **B1** No SituationMemory | **B2** Snapshot at Decision | **B3** Snapshot at ReasoningReceipt | **B4** Versioned snapshots | **B5** Event-sourced reconstruction |
|---|---|---|---|---|---|
| Historical accuracy | **L** — pointer drift | M — misses reasoning-only cycles | H | H | H in theory, M in practice |
| Auditability | L | M | H | H | M — reconstruction is itself a claim |
| Complexity | **H** (best) — none | M | M | M–L | **L** (worst) — bitemporal store |
| Storage | H — none | H — few | M — one per changed context | M | H — none new, but heavy event store |
| Duplication risk | none | low | low with references+hash | low | none |
| Retrieval quality | L | M | H | H | L — cannot retrieve what must be computed |
| Future learning capability | L | M | H | H | M |
| Implementation risk | none | low | low–medium | medium | **high** |
| MVP necessity | — | no | no | no | no |

**Why B3 over B2.** The `ReasoningReceipt` is the auditable artifact and the moment context is actually *consumed*. Many reasoning cycles produce no human decision at all; under B2, all of that context is lost, and the question "why did NAWA say that?" — which is asked far more often than "why did the human do that?" — stays unanswerable. Under B3, the Decision inherits context through the chain `DecisionMemory → ReasoningReceipt → SituationMemory`, so B3 delivers B2's coverage plus the reasoning-only cases.

**Why B4 is not a separate build.** Give `SituationMemory` a `source_hash` of the situation row at capture time and a `snapshot_seq`, and deduplicate: if the hash is unchanged since the last snapshot of that situation, reuse the existing record instead of writing a new one. The result is automatically versioned — one snapshot per distinct state, shared by every receipt that saw that state. **B4 is an emergent property of B3 done correctly, not a later migration.**

**Why B5 is rejected.** Event-sourced reconstruction is the theoretically pure answer and the wrong engineering call here. It requires a strictly append-only, correction-free, bitemporal operational event store. NAWA's operational events are backfilled, corrected, late-arriving, and classified after the fact. Reconstruction would produce a *computed claim about history* that is itself unauditable — replacing a small honest snapshot with a large confident guess. `DEFER — DO NOT BUILD YET`, permanently as far as this pack is concerned.

**Recommendation: B3 with hash-dedup versioning (B3 ⊕ B4).**

## B.6 Recommended Future Architecture

**Snapshot the interpretation. Reference the facts. Hash the reference set.**

```
operational_situations (mutable, Truth Layer)
        │
        │  at ReasoningReceipt creation:
        │  hash situation row + referenced event-id set
        │
        ├── hash unchanged ──▶ reuse existing SituationMemory
        │
        └── hash changed ────▶ write new immutable SituationMemory (snapshot_seq + 1)
                                      │
        ReasoningReceipt ──(situation_memory_id)──┘
                │
                └── DecisionMemory ──(reasoning_receipt_id)──▶ inherits historical context
                        │            ──(situation_id)────────▶ live pointer, "is this still open?"
                        │
                        └── OutcomeMemory
```

Two pointers with two different jobs, and this is deliberate:

- `situation_memory_id` (via the receipt) — **immutable history.** "This is what we saw."
- `situation_id` — **live pointer.** "Is that situation still open today?"

Keeping both is what lets NAWA answer "we decided this when the situation looked like X; it now looks like Y" — which is more valuable than either pointer alone, and is the actual product insight hiding inside this track.

## B.7 Minimum Future Model

Proposed minimum useful `SituationMemory` — `CORE FUTURE REQUIREMENT` if and when Track B activates. Field selection is deliberately conservative.

**Identity & provenance**

- `id`, `company_id` (stored directly, never inferred through a join)
- `situation_id` — source pointer
- `snapshot_seq` — ordinal within that situation
- `captured_at`, `capture_trigger` (`reasoning_receipt` | `decision` | `resolution`)
- `captured_by_component` — which runtime component wrote it
- `source_hash` — hash of the situation row as captured
- `evidence_digest` — hash of the ordered referenced-event-id set
- `policy_version` (for Track A alignment)

**Snapshotted interpretation (the actual payload)**

- `title`, `summary` — as they read at T
- `situation_type`, `severity`, `status` — as at T
- `window_start`, `window_end`
- `department_scope`
- `detection_method`, `detection_confidence`

**References (not copies)**

- `event_refs` — ordered list of operational event IDs
- `event_count`

**Explicitly NOT duplicated — `CORE FUTURE REQUIREMENT`:**

| Not stored | Because it lives in |
|---|---|
| Raw operational event payloads | `operational_events` — referenced + hashed instead |
| Reasoning text, hypotheses, confidence | `ReasoningReceipt` |
| Recommendations | `ReasoningReceipt` |
| The decision and its rationale | `DecisionMemory` |
| The outcome | `OutcomeMemory` |
| Company profile / Company Brain state | Company Brain |
| Recomputed KPIs or metrics | Derived at read time from evidence |
| Embeddings | Derived, recomputable, never provenance (§B.12) |

**How duplication of the operational system is avoided:** by storing *judgements* (severity, status, summary, type — small, textual, interpretive, and genuinely lost when the row mutates) and *referencing* facts (events — large, numerous, and independently retained). The `evidence_digest` closes the gap: if the referenced event set is later altered, the digest mismatches and provenance is reported as **degraded** rather than silently misrepresented. Detection instead of duplication.

## B.8 Provenance

- Immutable. No updates, no deletes. Corrections produce a new snapshot, never an edit. `CORE FUTURE REQUIREMENT`.
- Every snapshot names the component that wrote it and the trigger that caused it.
- `source_hash` + `evidence_digest` allow later verification that neither the situation row nor the event set has drifted.
- Retrieval of a snapshot whose digest no longer verifies must return `provenance_degraded` with detail. Never a clean success, never a hard failure.

## B.9 Relationship to Other Records

**To `ReasoningReceipt`.** The receipt records *what NAWA thought*; the snapshot records *what NAWA was looking at*. Keeping them separate means many receipts share one snapshot (dedup), and it prevents receipt payloads from ballooning with duplicated situation context — which also helps Track A's payload problem. The receipt is the reasoning; the snapshot is the setting.

**To `DecisionMemory`.** No direct link required. Decision inherits context through its receipt. **Edge case, must be handled honestly:** a `DecisionMemory` recorded with no receipt (a human decided independently of NAWA). That record has only the live `situation_id` and must be labeled `historical_context: unavailable` rather than rendered as if fully explained. `CORE FUTURE REQUIREMENT` if Track B activates.

**To `OutcomeMemory`.** No direct link. Outcome attaches to Decision. The pack explicitly warns against a Situation→Outcome link: it would invite "this situation type usually ends badly", which is a causal claim the system is forbidden to make (`Historical Outcome ≠ causal proof`). `DEFER — DO NOT BUILD YET`.

**To Operational Events.** Reference and hash. Never copy. Events remain governed by the operational domain; snapshots never become a shadow event store.

**To Organizational Memory retrieval.** Eventually the highest-value query in the entire product:

> "Show me past situations that looked like this one, what was decided, and what actually happened."

That is the loop NAWA is ultimately selling, and `SituationMemory` is its natural substrate — a stable, immutable, textual object with a fixed interpretation. This is the strategic argument for Track B and simultaneously the reason it is not urgent: the query is worthless until there is a real corpus of decisions and outcomes to search, which MVP does not have. `LIKELY FUTURE REQUIREMENT`.

## B.10 Multiple Decisions, Multiple Snapshots

- **Can several Decisions share one SituationMemory?** Yes — that is the intended and common case, produced automatically by hash dedup.
- **Can one Situation produce several snapshots?** Yes — one per distinct captured state, ordered by `snapshot_seq`.
- **How is changing severity/status represented?** As a sequence of snapshots, never as a mutated field.

**Mandatory honesty rule — `CORE FUTURE REQUIREMENT`:** `SituationMemory` is a **sampled** history, not a continuous one. It captures only at reasoning/decision moments, so gaps are expected and normal. It must never be rendered to a user as "the history of this situation." It is "what NAWA saw, at these moments." A sampled series presented as a complete timeline is a new class of the same lie this track was built to prevent.

## B.11 Tenant Isolation

- `company_id` stored on the snapshot itself, never inferred through `situation_id`.
- Write-time rejection of any `situation_id` belonging to another company.
- Repository-layer filtering on every read; no service-layer-only enforcement.
- Snapshots are included in tenant export and tenant erasure (Track A §A.12) — via the durable OME record registry (§A.16), not as a special case.
- No cross-tenant reference of any kind, including in future similarity retrieval.

## B.12 Semantic Similarity — Future Safety

Standing law: **no semantic-similarity claim in current MVP retrieval.** Unchanged by this document.

A forward observation worth recording: **an immutable snapshot is a safe embedding target; a mutable row is not.** Embedding `operational_situations` would produce vectors that silently decay as rows change, with no way to detect the drift. Embedding an immutable `SituationMemory` produces a vector that is permanently valid for its text.

So if NAWA ever adds semantic retrieval, `SituationMemory` is the correct substrate — and the following would bind:

- Embeddings are **derived**, versioned by model, and fully recomputable. `CORE FUTURE REQUIREMENT` if semantic retrieval is ever approved.
- An embedding is **never** provenance. Similarity may surface a candidate; only the snapshot and its evidence may support a claim.
- Similarity is never presented as causation, correlation, or precedent. `Historical Outcome ≠ causal proof` binds here directly.
- Enabling semantic retrieval is its **own** governance decision, separate from Track B activation. Building Track B does not authorize it. `DEFER — DO NOT BUILD YET`.

## B.13 Activation Triggers

**Hard triggers (any one):**

| ID | Trigger |
|---|---|
| **TB-H1** | First observed case where a rendered historical explanation is provably wrong because the referenced situation changed after the fact |
| **TB-H2** | First customer, auditor, or Founder question of the form "what did the system know at the time?" that NAWA cannot answer |
| **TB-H3** | Organizational Memory retrieval is approved to move from ID lookup toward similarity — Track B becomes a prerequisite, not an enhancement |
| **TB-H4** | M9 introduces deferred or conditional execution, where authorization context and execution context can diverge (see §M9) |

**Soft triggers:**

| ID | Trigger | Proposed value |
|---|---|---|
| **TB-S1** | **Context mutation rate** — share of `ReasoningReceipt`s whose referenced situation row has `updated_at` > `receipt.created_at` | > 5% — `PROPOSED FUTURE POLICY VALUE` |
| **TB-S2** | Decisions recorded against situations that later changed severity or status | ≥ 25 — `PROPOSED FUTURE POLICY VALUE` |
| **TB-S3** | Explanations of decisions older than 90 days actually being read | Any regular occurrence |
| **TB-S4** | Companies in production with sustained decision-recording activity | ≥ 3 — `PROPOSED FUTURE POLICY VALUE` |

**TB-S1 is the metric worth knowing.** It is measurable today from existing data with a single read-only query, it requires no new structure, and it converts "is pointer drift real?" from an argument into a number. If it turns out to be near zero, Track B stays deferred with evidence rather than with intuition. Recording it here as the recommended first question whenever the track is revisited — **not as a task, and not as work to schedule now.**

## B.14 Future Implementation Impact

| Layer | Expected impact |
|---|---|
| Database | One new table `situation_memory` (+ index on `company_id`, `situation_id`, `snapshot_seq`); one nullable FK on `reasoning_receipt` |
| Migrations | Additive, non-breaking; no backfill possible (history before activation is unrecoverable — accepted) |
| Repositories | New repository; hash-dedup lookup on write path |
| Domain services | Snapshot capture in the reasoning pipeline's receipt-creation path; hashing utility; provenance verifier |
| APIs | Read-only snapshot retrieval; snapshot reference in explanation payloads |
| Reasoning pipeline | One capture call at receipt creation. **Must not change what NCE Lite reasons over** — snapshotting is a recording act, not a reasoning input |
| OME retrieval | Optional retrieval by situation lineage; later, the substrate for similarity if separately approved |
| Explainability | Historical explanations resolve context from the snapshot rather than the live row; `historical_context: unavailable` and `provenance_degraded` states rendered honestly |
| Frontend | "Situation as it was at the time" vs "situation now" comparison view — small feature, disproportionate credibility payoff |
| Tests | Immutability; dedup correctness; digest mismatch detection; receipt-less decision labeling; tenant isolation on write and read; sampled-history rendering |
| Browser E2E | Record decision → mutate situation → reopen explanation → historical context unchanged and clearly labeled |
| Storage operations | Small. Bounded by distinct situation states, not by reasoning volume |

## B.15 Explicit Non-Goals

`DEFER — DO NOT BUILD YET`:

- A second copy of the operational system inside OME.
- A continuous change-log of every situation mutation.
- Snapshotting raw operational event payloads.
- A Situation → Outcome direct link, or any situation-level outcome statistics.
- Automatic pattern learning across snapshots.
- Semantic/vector retrieval (separate governance decision).
- Backfilling snapshots for history that predates activation — impossible, and any attempt would be fabrication.
- Exposing snapshots as an editable user surface.

## B.16 Status

**TRACK B = DEFERRED — ARCHITECTURE BLUEPRINT READY.**

Not MVP blocking. Not an M9 prerequisite. No engineering work is authorized.

---

# Cross-Track Relationship

The two tracks are **not merged and must not be merged.**

- **Track A** governs *how durable memory is managed over time*. It is a policy and storage concern over records that already exist.
- **Track B** decides *whether a new historical record type should exist*. It is a modeling concern.

**Directional relationships:**

| From | To | Relationship |
|---|---|---|
| Track B → Track A | If B ships, `SituationMemory` becomes a durable OME record and falls under A's lifecycle when A ships | **Dependency of scope, not of activation** |
| Track B → Track A | B adds at most one durable record per distinct situation state (deduped — typically far below 1:1 per receipt), pulling A's volumetric triggers marginally closer | **Quantitative influence only** |
| Track A → Track B | None. Lifecycle governance says nothing about whether a snapshot entity should exist | **No relationship** |

**No auto-activation in either direction.** Activating A does not activate B. Activating B does not activate A. B shipping before A simply means one more record type accumulating under the current keep-everything posture — which is the status quo for three record types already and is acceptable for the same reasons.

**The one shared artifact:** the **durable OME record registry** (§A.16). Whichever capability activates first should create it, and the others inherit it. That registry is also what makes an M9 Action record a registration rather than a redesign. If a future engineer reads only one line of this pack, it should be that one.

**Minimum-foundation principle — the guard against that line being over-read (Founder-approved):**

> The first activated capability that genuinely requires the durable OME record registry should build only the minimum extensible registry foundation required for its own scope. Deferred tracks may inherit that foundation later.

The registry is a small declaration table plus the discipline of writing new record types into it. It is **not** a new milestone, a prerequisite project, a standalone platform, or a lifecycle framework owed before M9.

**If M9 becomes that first capability**, M9 may build the minimum registry only — enough to declare its own Action record type alongside the three existing ones. M9 must **not**, on that basis, implement any of: Track A lifecycle governance, Track B Situation Memory, retention policy engines, archival frameworks, compaction, or tenant offboarding. Building a registry entry is not the same as building the machinery that will one day read it, and this paragraph exists specifically so that nobody later argues otherwise.

---

# Relationship to M9 — Decision Execution Foundation

M9 status is unchanged: **SELECTED — IMPLEMENTATION NOT ACTIVATED.** Neither track is in M9 scope. This pack proposes no new milestone and no scope change.

**Would future M9 Action records need Track A lifecycle governance?**
Yes — eventually, and for the same reasons as every other durable record. An Action record is durable, auditable, tenant-scoped, and lineage-linked. It should be registered in the durable OME record registry, with a retention class, when Track A activates. This is **not** a reason to activate Track A alongside M9: M9 can ship under the current keep-everything posture exactly as M8 did. Adding a fourth durable record type to an un-governed set changes nothing structurally.

**Can Action provenance inherit situation context without Track B?**

```
Action → DecisionMemory → situation_id (live pointer)
```

**Yes, for M9 as currently scoped.** The provenance question M9 raises is *"who authorized this action, and on what decision?"* — and `DecisionMemory` answers it completely. The action executes against Current Truth at execution time; the human decision is the authorizing artifact. Nothing in that chain requires a frozen historical situation. **Track B is therefore not an M9 prerequisite.**

**M9 MVP EXECUTION BOUNDARY — Founder-confirmed.**

> **M9 MVP must NOT introduce deferred or condition-triggered future execution that automatically executes when a later condition becomes true.**

**Reason.** Under autonomous conditional execution, an action is authorized against one state of the world and fires against another. Authorization context and execution context diverge, the question "was this still the right action when it fired?" becomes both real and unanswerable, and Track B's historical Situation Memory stops being a deferred nicety and becomes a prerequisite. That is trigger **TB-H4**. Holding this boundary is what keeps Track B deferred — it is the cheapest way M9 can avoid pulling a second track into its own scope.

**What remains permitted conceptually:** human-updated execution status. A person marking an action as started, done, blocked, or abandoned is a record of human activity against a current state, not a machine acting on a stale one. The line is not "immediate vs. later" — it is **who decides that the moment has come.** A human deciding later is fine. A condition deciding later is not.

**What is out of bounds for M9 MVP:** autonomous conditional execution, scheduled auto-fire, trigger-based action dispatch, and any mechanism where NAWA itself determines that a previously authorized action should now run.

**Default assumption stands: both tracks remain outside M9.**

---

# Relationship to Truth Layer

- **Current Truth always wins for present reasoning.** A `SituationMemory` snapshot is context and history only; it can never be an input to Current Truth, and it can never override a validated Company Input fact (EBD-004 §5, *Company Brain Never Overrides Facts*).
- Historical memory enters reasoning **only** through the historical/organizational memory channel and must be **labeled historical** where it influences output.
- **A conflict between a snapshot and current reality is a signal, not a contest.** "Severity was `critical` in March; it is `normal` now" is useful information. It is never a reason to doubt the present. Surfacing the divergence is permitted; resolving it in history's favor is not.
- Track A likewise never touches Current Truth (DAP-A-L9). Lifecycle governs OME durable records only; operational events and situations belong to the operational domain.

---

# Relationship to Company Brain

- Neither track mutates Company Brain. Ever. Automatically or otherwise.
- Compacted summaries, aggregates, and statistics are **derived data**, not policy (DAP-A-L7).
- Repeated outcomes across snapshots are **not** learning and must never be promoted into policy by any mechanism in either track. `Historical Outcome ≠ causal proof` binds both.
- If NAWA ever builds organizational learning, it is a **separately governed mechanism** with its own Executive Board Decision, its own evidence standard, and human ratification of every policy change. Neither track may be used as a back door into it.
- The temptation is real and specific, so it is named: a compaction service that summarizes a year of outcomes is exactly one small step from "NAWA learned that X causes Y." That step is forbidden, and DAP-A-L7 exists to make the prohibition structural rather than cultural.

---

# Security / Tenant Boundaries

Applies to both tracks:

| Concern | Requirement | Classification |
|---|---|---|
| Company isolation | `company_id` stored on every durable record directly; never inferred through joins | CORE FUTURE REQUIREMENT |
| Enforcement point | Repository layer, on both read and write. Service-layer-only enforcement is insufficient | CORE FUTURE REQUIREMENT |
| Cross-tenant references | Forbidden. Verified at write time and again at offboarding | CORE FUTURE REQUIREMENT |
| Retrieval | No retrieval mode, tier, or similarity path may cross a company boundary | CORE FUTURE REQUIREMENT |
| Deletion / offboarding | Complete, enumerated, count-verified, export-first; minimized tombstone where the governing authority permits one, removal / anonymization / transformation where it requires complete deletion (§A.7) | LIKELY FUTURE REQUIREMENT |
| Audit history | NAWA's own lifecycle audit trail normally survives tenant erasure, holding no tenant content — subject to the same governed-erasure authority as tombstones (§A.7) | CORE FUTURE REQUIREMENT |
| Retention rights | Tenant-configurable above a governed floor; ratchet rule applies to lifecycle, not to ratified erasure authority | LIKELY FUTURE REQUIREMENT |
| Role / permission | Retention configuration and erasure are Founder/admin-level, not user-level. Reading archived history follows the same permissions as reading current history — tier is not a permission boundary | LIKELY FUTURE REQUIREMENT |
| Sensitive operational history | Snapshots may contain sensitive operational content; they inherit the same access controls as the source situation. No new exposure surface may be created by archival or by snapshotting | CORE FUTURE REQUIREMENT |
| Jurisdictional compliance | Not designed. Configurable policy only | DEFER — DO NOT BUILD YET |

---

# Future Ratification Requirements

If a track is reopened, these documents would need to be created or amended before implementation:

**Track A**

| Document | Action | Authority |
|---|---|---|
| `docs/runtime/OME_LIFECYCLE_POLICY_v1.md` | **New.** The Runtime Document EBD-004 §4.9 explicitly points to. Its existence is what closes the §4.9 gap | CTO authors; Founder ratifies (product-facing retention commitments) |
| Durable OME Record Registry | **New.** Declared record types, retention classes, audit-core fields | CTO |
| EBD-004 | Amendment only if lifecycle is ever promoted from Runtime Document scope into Tier 2 contract. **Not required** for A as designed | Founder, Tier 2 process |
| `CURRENT_STATE.md` | Update on activation and on completion | CTO |
| Sprint/milestone document | Required before any engineering task exists (Repository First Policy) | Founder |

**Track B**

| Document | Action | Authority |
|---|---|---|
| Architecture Document — `SituationMemory` model | **New.** Field-level specification | CTO; Founder review |
| EBD-004 §4.9 OME Foundation Inputs | **Backward-compatible addition** — a new preserved input type. Permitted without Tier 2 unfreeze per EBD-003 §15.4; filed as an ADR | CTO approves as ADR |
| Company Brain doc — situation semantics | Amendment, if snapshot field selection encodes domain meaning | Founder |
| Separate governance decision | Required **only** if semantic retrieval is proposed. Not part of Track B | Founder, new EBD |
| Sprint/milestone document | Required before any engineering task exists | Founder |

**Acceptance standards that should exist before either is called done**

*Track A:* a record archived at every tier still resolves by citation; a lineage cluster is never split across tiers; an open (`unknown`) outcome pins its cluster warm; every lifecycle run is logged with counts and policy version; offboarding / governed erasure erases every registered record type with verified counts and produces an auditable result **consistent with the governing authority** — where retention of minimal audit metadata is permitted, a tombstone remains and is minimized to non-content, non-identifying fields; where complete deletion is required, the test verifies that the removal, anonymization, or transformation actually occurred and that no remaining reference falsely claims retained evidence (the standard tests governed compliance, not mandatory tombstone survival); the ratchet rule holds under policy change; no default-mode retrieval silently hides the existence of historical material.

*Track B:* a snapshot is byte-stable after the source situation mutates; identical situation state produces exactly one shared snapshot; a mutated event set produces `provenance_degraded`, never a clean read; a receipt-less decision renders `historical_context: unavailable`; cross-tenant writes and reads are rejected at the repository; snapshot series are never rendered as a complete situation history.

---

# Deferred Capability Register

| # | Capability | Track | Status now | Why deferred | Activation trigger | Future architectural dependency | Classification |
|---|---|---|---|---|---|---|---|
| 1 | OME growth telemetry (counts, bytes, latency attribution) | A | Deferred | No pressure; numbers today would be noise | Any Track A trigger — first slice | None | CORE FUTURE REQUIREMENT |
| 2 | Durable OME record registry (**minimum extensible foundation only**) | A / shared | Deferred | Only three record types; a list is not yet an abstraction | First activated capability that genuinely requires it — may be M9 | None | CORE FUTURE REQUIREMENT *when a capability needs it*; never a milestone or prerequisite project |
| 3 | Hot / Warm / Cold tiering | A | Deferred | Volume is trivial | TA-S1–S4 | #2 | CORE FUTURE REQUIREMENT |
| 4 | Tier-aware OME retrieval (`default`/`historical`/`resolve`) | A | Deferred | No tiers exist to be aware of | With #3 | #3 | CORE FUTURE REQUIREMENT |
| 5 | Citation resolution across tiers + tombstones | A | Deferred | Nothing is archived yet | With #3 | #3, #4 | CORE FUTURE REQUIREMENT |
| 6 | Governed immutable audit core (spine) definition | A | Deferred | Implicit today (nothing is deleted) | With #3 | #2 | CORE FUTURE REQUIREMENT |
| 7 | Spine/payload split + hash-preserving payload drop | A | Deferred | Storage is not a cost yet | TA-S3 | #3, #6 | LIKELY FUTURE REQUIREMENT |
| 8 | Context-block dedup by content hash | A | Deferred | Receipt volume is low | TA-S2/S3 | #7 | LIKELY FUTURE REQUIREMENT |
| 9 | Tenant retention configuration + governed floor + ratchet + governed retention period | A | Deferred | No customer has asked | TA-H1, TA-H3 | #3, #6 | LIKELY FUTURE REQUIREMENT |
| 10 | A-OFFBOARD — governed erasure path: export, data inventory, authorized erasure, controlled deletion, retention-policy termination, tombstones. **A candidate execution mechanism that carries out ratified erasure authority; it does not itself create that authority (§A.12)** | A | Deferred | No offboarding has occurred | **TA-H2 — earliest likely trigger of any item here** | #2, #6 | LIKELY FUTURE REQUIREMENT |
| 11 | Legal-hold flag | A | Deferred | Speculative | Real legal obligation | #3 | OPTIONAL (field cheap; workflow: DEFER) |
| 12 | Governed compaction / summarization | A | Deferred | Value unproven; risk real | Only after #3, #7, #9 and demonstrated retrieval degradation | #3, #5, DAP-A-L3 | OPTIONAL |
| 13 | Relevance-based persistence pruning | A | Not planned | Would require OME to reason — contract violation | — | — | DEFER — DO NOT BUILD YET |
| 14 | **Blind** time-based hard deletion (Option A2) | A | **Rejected** | Timer-driven destruction of organizational history with no governing authority. Does *not* imply all metadata survives forever: deletion under ratified authority is #10, and is supported | Never | — | DEFER — DO NOT BUILD YET |
| 15 | Jurisdictional compliance encoding | A | Not planned | Configurable dials instead; future jurisdiction-specific requirements are met by tenant policy, not hardcoded law | — | #9 | DEFER — DO NOT BUILD YET |
| 16 | Context mutation rate measurement (TB-S1) | B | Deferred | Answerable from existing data whenever the track is revisited | Track B review | None | LIKELY FUTURE REQUIREMENT |
| 17 | `SituationMemory` entity (B3 ⊕ hash-dedup versioning) | B | Deferred | No explainability failure has occurred; MVP density too low | TB-H1–H4, or TB-S1 above threshold | None (self-contained) | LIKELY FUTURE REQUIREMENT |
| 18 | Provenance verification (`source_hash`, `evidence_digest`, degraded state) | B | Deferred | Ships with #17 | With #17 | #17 | CORE FUTURE REQUIREMENT (if B activates) |
| 19 | "As it was / as it is now" comparison view | B | Deferred | Needs #17 | With #17 | #17 | OPTIONAL (high credibility value, low cost) |
| 20 | Retrieval by situation lineage | B | Deferred | Needs a corpus | Post-#17, real decision volume | #17 | LIKELY FUTURE REQUIREMENT |
| 21 | Semantic similarity over snapshots | B | Not planned | Standing law forbids similarity claims; separate governance | Separate EBD only | #17, #18 | DEFER — DO NOT BUILD YET |
| 22 | Event-sourced situation reconstruction (B5) | B | **Rejected** | Requires guarantees NAWA's operational data does not have; produces unauditable computed history | Never, as designed | — | DEFER — DO NOT BUILD YET |
| 23 | Situation → Outcome direct link / situation-level outcome statistics | B | Not planned | Invites causal claims the system is forbidden to make | — | — | DEFER — DO NOT BUILD YET |
| 24 | Automatic Company Brain learning from history | Both | **Forbidden** | Standing law; DAP-A-L7 | Separate EBD with human ratification | — | DEFER — DO NOT BUILD YET |
| 25 | Lifecycle governance over M9 Action records | A/M9 | Deferred | M9 not activated; keep-everything posture is adequate | Track A activation after M9 ships | #2 | LIKELY FUTURE REQUIREMENT |
| 26 | Cryptographic / logical deletion (crypto-shredding) as an erasure mechanism | A | Deferred | Presupposes a key-management design NAWA does not have | Only inside an activated #10, if the architecture then supports it | #10 | OPTIONAL |
| 27 | Autonomous conditional / deferred action execution | M9 | **Out of M9 MVP bounds** | Authorization context and execution context would diverge, reopening Track B (TB-H4) | Separate Founder decision; would activate Track B | #17 | DEFER — DO NOT BUILD YET |

---

# Final Recommendation

**TRACK A = DEFERRED — ARCHITECTURE BLUEPRINT READY**

**TRACK B = DEFERRED — ARCHITECTURE BLUEPRINT READY**

Neither track is reopened. Neither is converted into M9 scope. No milestone number is proposed. No engineering work is authorized. Sprint EX-1 remains PAUSED. M9 remains SELECTED — IMPLEMENTATION NOT ACTIVATED.

**Four things a future reader should carry away:**

1. **NAWA's promise is governed retention, not perpetual retention.** *NAWA preserves organizational memory according to the organization's governed retention policy, while protecting the provenance and auditability required for trustworthy historical reasoning.* Nothing in this architecture may be built or sold in a way that contradicts that sentence.
2. **Track A's first real trigger will be a contract or an erasure request, not a storage graph.** `A-OFFBOARD` is separable, small, the item most likely to be demanded by someone outside NAWA, and the leading candidate execution mechanism through which a ratified authority may remove the audit spine. Watch for it; do not pre-build it.
3. **Track B's recommended design is B3 with hash-dedup, which makes B4 free.** Snapshot the interpretation, reference the facts, hash the reference set. Do not build B5. Keep the M9 MVP execution boundary intact and Track B stays deferred.
4. **The durable OME record registry is the one artifact that both tracks and M9 share — and the first capability that needs it builds only its own minimum.** Everything else in this pack is a policy dial or a table.

**The open question from v1.0 is now closed.** It asked whether NAWA's promise is "we keep your institutional memory indefinitely" or "we keep it under your policy." Founder Decision 1 answers: **under your policy.** A5 is therefore not just the recommended architecture but the required one, and the audit core is governed rather than immortal (DAP-A-L10, DAP-A-L11).

---

---

# Appendix A — Amendment Log

| Version | Date | Change | Authority |
|---|---|---|---|
| 1.0 | 2026-08-29 | Initial blueprint. Track A and Track B architecture, options analysis, activation triggers, deferred capability register. Both tracks DEFERRED — ARCHITECTURE BLUEPRINT READY. | CTO (draft) |
| 1.1 | 2026-08-29 | **Founder Precision Amendment.** (1) **Retention promise** — recorded as DAP-A-L10: NAWA makes no promise equivalent to "we keep your organizational memory forever"; the approved principle is governed retention with preserved provenance and auditability. (2) **Governed immutable audit spine** — recorded as DAP-A-L11: the audit spine is immutable and non-prunable by ordinary lifecycle mechanics during governed retention, but remains subject to explicit tenant-erasure, offboarding, contractual, or legal-authority processes. Sections amended: header, Executive Summary, A.2, A.4, A.5, A.6, A.7 (renamed), A.11, A.12 (renamed, scope expanded), A.16, Cross-Track, M9, Security, Deferred Capability Register, Final Recommendation. A2 remains rejected with an explicit clarification of what the rejection does not imply. A5 retained with refined semantics. A-OFFBOARD retained as a separate deferred capability and identified as the sole authority path for spine removal. M9 MVP execution boundary recorded. Durable OME record registry constrained by the minimum-foundation principle. **No track activated. No milestone created. No engineering authorized.** | Founder & CEO (decisions); CTO (amendment) |
| 1.2 | 2026-08-29 | **Erasure Authority Precision Amendment.** Independent architecture review identified two precision blockers in v1.1. (1) **Absolute tombstone-retention semantics** — several passages stated tombstones as unconditionally surviving (state: Erased, §A.7 scope-of-list, §A.11 config table, §A.12 item 3, Security table). Corrected: tombstone retention is now explicitly governed, not absolute — a tombstone SHOULD normally survive governed erasure where the authority permits, but the authority may instead require removal, anonymization, or transformation, including of the tombstone itself (§A.7). New data-minimization guidance added for future tombstone content (§A.7), and citation resolution after complete erasure now resolves honestly rather than fabricating replacement evidence (§A.10). (2) **Conflation of erasure authority source with A-OFFBOARD execution mechanism** — §A.6 and §A.12 previously called A-OFFBOARD "the sole ratified authority path" / "the only mechanism" through which the spine may be removed. Corrected: A-OFFBOARD is now framed as a candidate future execution/coordinating mechanism that carries out an authority established elsewhere (tenant request, contract, legal/regulatory order, retention policy, other ratified governance source); it does not itself create that authority. §A.12 now names authority source, execution mechanism, and erasure result as three distinct concepts. Sections amended: header, front-matter amendment note, A.6, A.7, A.10, A.11, A.12, Security, Deferred Capability Register (#10), Final Recommendation. Track A/B deferral status, M9 scope, registry minimum-foundation principle, A2 rejection, and A5 recommendation are unchanged. **No track activated. No milestone created. No engineering authorized.** | Founder & CEO (decisions); CTO (amendment) |
| 1.3 | 2026-08-29 | **Tombstone Consistency Amendment.** Independent Codex re-review confirmed the v1.2 authority-source vs execution-mechanism blocker RESOLVED, and found four residual **live normative** statements that still implied mandatory tombstone survival: **DAP-A-L1** ("any removal leaves a tombstone"), the **§A.6 exit-path diagram** ("leaves tombstone", unconditional), **§A.10 provenance** (erased citations resolve to a tombstone "never to silence"), and the **future acceptance standard** (offboarding must "leave a tombstone"). All four now align with the governed-erasure rule already ratified in §A.7: a tombstone is normally retained only where the governing authority permits minimal, non-content, non-identifying audit metadata, and may otherwise be removed, anonymized, transformed, or omitted. Where nothing may remain, provenance resolves honestly as *source no longer retained under governed erasure* or as an explicitly non-resolvable reference; substitute evidence is never fabricated. Three adjacent non-blocking statements were aligned for consistency (§A.4 governed-erasure row, §A.6 A-OFFBOARD staging row, Security table deletion row). No architecture direction changed: A2 rejection, A5 recommendation, A-OFFBOARD authority/mechanism separation, Track A and Track B deferral, M9 scope, and the registry minimum-foundation principle are all unchanged. **No track activated. No milestone created. No engineering authorized.** | Founder & CEO (decisions); CTO (amendment) |

---

*This document is a future architecture blueprint. It confers no authorization, creates no obligation, and changes no execution status. It exists so that when either track is reopened, the design work is already done.*
