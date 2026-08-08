# NAWA System Orchestration v1

## NAWA Cognitive Orchestrator (NCO)

The NAWA Cognitive Orchestrator is the system layer that coordinates all NAWA engines.

NCO is not an AI model.

NCO is not a business engine.

NCO does not reason, extract operational intelligence, create memory, produce executive briefs, or own company logic directly.

NCO decides which NAWA engine should run, in what order, under what conditions, and when the system must stop, wait, or request more evidence.

Its purpose is to keep NAWA modular, trustworthy, and expandable as the Company Brain grows across companies, departments, reports, files, workflows, and future automations.

---

## 1. Vision

NAWA is a Company Brain made of specialized engines.

Each engine has a clear responsibility:

- Capture knowledge.
- Convert inputs into operational intelligence.
- Build context.
- Reason with evidence.
- Create executive outputs.
- Preserve organizational memory.

Without orchestration, these engines would become tightly coupled. One engine would begin calling another directly, owning logic outside its domain, and assuming too much about the internal behavior of the rest of the system.

That would weaken NAWA.

NCO exists to prevent that weakness.

### Why Orchestration Is Needed

Orchestration is needed because real company intelligence is sequential, conditional, and evidence-aware.

A report upload is not the same as a CEO question. A missing evidence case is not the same as a ready-for-reasoning case. A decision outcome is not the same as an executive brief request.

NAWA must know:

- Which engine should run first.
- Which engine should run next.
- Which engine should not run yet.
- Which evidence is missing.
- Whether reasoning is safe.
- Whether memory should be updated.
- Whether an executive output is needed.
- Whether the system should wait for more human or system input.

NCO provides this coordination discipline.

### Why Engines Must Not Call Each Other Directly

Engines must not call each other directly because direct engine-to-engine ownership creates hidden dependencies.

If KAE directly owns OIE, then intake becomes coupled to operational interpretation.

If OIE directly owns OCE, then record generation becomes coupled to context readiness.

If OCE directly owns NCE, then context preparation can trigger reasoning before orchestration rules have checked readiness, permissions, output intent, and evidence gaps.

If NCE directly owns Executive Intelligence, then reasoning becomes coupled to presentation.

If any engine directly owns OME, then memory may be created before the correct decision, outcome, or evidence state exists.

NAWA must avoid this pattern.

### How NCO Prevents Tight Coupling

NCO prevents tight coupling by acting as the coordination boundary.

Engines execute their own responsibilities and return structured results.

NCO reads those results, applies orchestration rules, and decides the next step.

This keeps each engine independent, testable, replaceable, and expandable.

The orchestration principle is:

```text
Engines do their work.
NCO decides what happens next.
```

---

## 2. Core Engines Managed by NCO

### KAE: Knowledge Acquisition Engine

KAE receives raw company knowledge from files, chat, forms, manual notes, system integrations, images, and future automations.

KAE preserves source integrity, identifies input type, captures metadata, and prepares raw knowledge for downstream interpretation.

NCO invokes KAE when new knowledge enters NAWA.

### OIE: Operational Intelligence Engine

OIE converts captured inputs into structured operational intelligence.

OIE generates records, metrics, events, signals, situations, entities, classifications, and operational facts.

NCO invokes OIE after KAE has produced an intake result that is ready for operational interpretation.

### OCE: Operational Context Engine

OCE prepares decision context before reasoning.

OCE builds evidence graphs, identifies missing evidence, connects departments and workflows, evaluates context readiness, and determines whether a situation is ready for cognitive reasoning.

NCO invokes OCE when operational intelligence requires context building.

### NCE: NAWA Cognitive Engine

NCE constructs trustworthy operational reasoning.

NCE does not merely answer questions. It reasons through evidence, confidence, risk, hypotheses, decision options, and uncertainty.

NCO invokes NCE only when context is ready for reasoning or when a cautious preliminary reasoning mode is explicitly allowed.

### OME: Organizational Memory Engine

OME preserves long-term company memory.

OME stores important situations, evidence, decisions, outcomes, repeated patterns, institutional knowledge, and learning signals.

NCO invokes OME when there is memory-worthy information, a decision, an outcome, or a reasoning event that should affect future intelligence.

### Executive Intelligence

Executive Intelligence converts structured context and reasoning into leadership-ready outputs.

It may produce CEO briefs, department briefs, operational summaries, board narratives, PPT outlines, avatar/video scripts, voice-ready responses, or automation-ready action plans.

NCO invokes Executive Intelligence when an authorized user or workflow requires an executive output.

---

## 3. Orchestration Rules

NCO follows explicit orchestration rules.

These rules keep NAWA from reasoning too early, producing executive outputs without evidence, or storing memory without a meaningful situation, decision, or outcome.

### Report Upload Rule

```text
New report uploaded
    |
    v
KAE
    |
    v
OIE
    |
    v
OCE
```

When a new report is uploaded, NCO first routes it to KAE for intake.

After KAE preserves the source and prepares the input, NCO routes it to OIE.

After OIE generates operational intelligence, NCO routes the result to OCE for context building and evidence readiness.

### Situation Detected Rule

```text
Situation detected
    |
    v
OCE
    |
    v
Reasoning readiness check
```

When OIE detects a situation, NCO routes the situation to OCE before any reasoning occurs.

OCE must identify context, evidence, missing information, affected departments, and readiness for reasoning.

### Missing Evidence Rule

```text
context_ready_for_reasoning = false
    |
    v
Request missing evidence
    |
    v
Wait
```

If context is not ready for reasoning, NCO does not route the situation to full NCE reasoning.

NCO requests missing evidence from the appropriate user, department, file, system, or future automation source.

The system waits until more evidence arrives or until cautious preliminary reasoning is explicitly acceptable.

### Reasoning Readiness Rule

```text
context_ready_for_reasoning = true
    |
    v
NCE
```

If context is ready for reasoning, NCO routes the situation to NCE.

NCE then constructs evidence-aware reasoning, confidence, risks, hypotheses, and decision options.

### Decision and Outcome Rule

```text
Decision or outcome exists
    |
    v
OME
```

If a decision, outcome, correction, or important reasoning event exists, NCO routes it to OME.

OME preserves the memory so NAWA can learn from what happened and reason better in the future.

### Executive Output Rule

```text
Executive output needed
    |
    v
Executive Intelligence
```

If a CEO brief, department brief, operational brief, PPT narrative, avatar script, voice-ready response, or automation-ready action plan is needed, NCO routes the structured context and reasoning to Executive Intelligence.

Executive Intelligence must not replace NCE. It presents intelligence; it does not independently validate truth.

---

## 4. Execution Flow Diagrams

### Report Upload Flow

```text
User uploads report
        |
        v
NCO receives upload event
        |
        v
KAE reads and preserves source file
        |
        v
NCO checks intake result
        |
        v
OIE extracts records, metrics, events, signals, situations
        |
        v
NCO checks operational intelligence result
        |
        v
OCE builds context, evidence graph, missing evidence
        |
        v
NCO evaluates context readiness
        |
        +-- context_ready_for_reasoning = false --> request missing evidence
        |
        +-- context_ready_for_reasoning = true  --> NCE or Executive Intelligence as needed
```

### CEO Question Flow

```text
CEO asks operational question
        |
        v
NCO identifies intent and authorized scope
        |
        v
OCE gathers existing context and evidence
        |
        v
NCO checks reasoning readiness
        |
        +-- insufficient context --> request missing evidence or provide cautious limitation
        |
        +-- sufficient context ----> NCE
                                      |
                                      v
                            Evidence-aware reasoning
                                      |
                                      v
                            Executive Intelligence
                                      |
                                      v
                                CEO Brief
```

### Missing Evidence Flow

```text
OCE identifies missing evidence
        |
        v
NCO evaluates whether missing evidence blocks reasoning
        |
        +-- blocking evidence missing
        |       |
        |       v
        |   Request evidence from user, department, file, system, or automation
        |       |
        |       v
        |   Wait for new input
        |
        +-- non-blocking evidence missing
                |
                v
            Allow cautious reasoning with declared uncertainty
```

### Decision Memory Flow

```text
Decision made or outcome observed
        |
        v
NCO receives decision/outcome event
        |
        v
NCO links decision to situation, evidence, reasoning, confidence
        |
        v
OME stores decision memory and outcome memory
        |
        v
Future NCO orchestration can reuse memory through OCE and NCE
```

---

## 5. MVP Orchestration

The current MVP path for Jannat Al-Firdaws is focused on poultry report intelligence.

The MVP must prove that NAWA can receive an operational report, convert it into structured intelligence, build context, reason cautiously only when ready, create a CEO-ready brief, and preserve memory when decisions or outcomes become available.

```text
User uploads poultry report
        |
        v
KAE reads file
        |
        v
OIE generates records, metrics, events, signals, situations
        |
        v
OCE builds context and missing evidence
        |
        v
NCE MVP generates cautious reasoning only if ready
        |
        v
Executive Intelligence creates CEO Brief
        |
        v
OME stores situation, decision, and outcome when available
```

### MVP Operating Rule

For the MVP, NCO should prefer a narrow, reliable orchestration path over broad automation.

The first orchestration proof is not every possible company workflow.

The first proof is:

- A Jannat Al-Firdaws user uploads a poultry report.
- NAWA understands the file as company knowledge.
- NAWA generates operational intelligence.
- NAWA builds context and identifies missing evidence.
- NAWA reasons only when the context is ready or clearly labels cautious preliminary reasoning.
- NAWA creates a CEO Brief.
- NAWA stores the situation, decision, and outcome when available.

This MVP path should become the working spine for future company and report expansion.

---

## 6. Engine Independence Law

No engine should directly own another engine.

NCO coordinates; engines execute.

KAE does not own OIE.

OIE does not own OCE.

OCE does not own NCE.

NCE does not own Executive Intelligence.

Executive Intelligence does not own OME.

OME does not own the other engines.

Each engine is responsible for its domain.

NCO is responsible for sequence, readiness, stopping conditions, waiting conditions, and routing.

The Engine Independence Law protects NAWA from becoming a tightly coupled system where changing one engine forces a rewrite of the entire Company Brain.

---

## 7. Future

NCO allows NAWA to expand without rewriting the core brain.

The same orchestration constitution can support:

- A second company.
- A third company.
- Finance reports.
- Sales reports.
- Warehouse reports.
- HR and attendance reports.
- Accounting reports.
- Procurement reports.
- Caesar Beverage workflows.
- Shared Corporate Department workflows.
- Future ERP, HR, accounting, attendance, sales, and warehouse integrations.
- Future n8n automations.

Expansion should add new intake types, context rules, memory patterns, and executive outputs while preserving the same orchestration principle:

```text
NCO coordinates.
Engines execute.
Evidence controls readiness.
Memory improves the future.
```

This structure lets NAWA add more companies and domains without converting the Company Brain into isolated modules or forcing one engine to absorb another engine's responsibility.

The result is a modular cognitive operating system where new operational domains can join the brain through orchestration rather than rewriting the brain itself.

---

This document is the official orchestration constitution of NAWA.

After this document, architecture discovery pauses and MVP implementation becomes the priority.
