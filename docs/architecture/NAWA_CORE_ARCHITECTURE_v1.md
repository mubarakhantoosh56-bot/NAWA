# NAWA Core Architecture v1

## Architectural Constitution

NAWA is an **Enterprise Cognitive Operating System**.

It is the Company Brain for real operating companies: a cognitive layer that receives operational inputs, converts them into structured intelligence, builds context, supports reasoning, preserves memory, and turns knowledge into executive, departmental, and operational action.

NAWA does not replace operational systems. It sits above them.

NAWA does not begin as an ERP, chatbot, dashboard, or BI tool. Those may become interfaces, inputs, or outputs. The core product is the cognitive operating layer that understands the company as a living organization made of divisions, departments, workflows, people, files, events, signals, risks, decisions, and history.

This document is the official architecture reference for NAWA.

---

## Core Architecture Overview

```text
Human Inputs / Files / Systems / Automations
                |
                v
Knowledge Acquisition Engine (KAE)
                |
                v
Operational Intelligence Engine (OIE)
                |
                v
Operational Context Engine (OCE)
                |
                v
Reasoning Engine
                |
                v
Executive Intelligence
                |
                v
Future Engine / Organizational Memory Engine (OME)
```

NAWA follows one governing principle:

```text
No input is meaningless.
No reasoning happens without context.
No AI conclusion may override facts.
No decision is final without evidence.
```

---

## 1. Knowledge Acquisition Engine (KAE)

### Purpose

The Knowledge Acquisition Engine receives raw company knowledge from every available source and prepares it for structured interpretation.

KAE is the intake layer of NAWA. Its responsibility is not to reason, decide, or summarize prematurely. Its responsibility is to capture inputs, preserve source integrity, identify what type of knowledge arrived, and make the input available to downstream intelligence engines.

### Responsibilities

- Receive company inputs from human, file, system, and automation sources.
- Preserve raw input and source metadata.
- Detect input type, source, company, department, and operational domain when possible.
- Route the input to the correct downstream processing path.
- Preserve bilingual content, especially Arabic and English operational language.
- Maintain source traceability from raw input to later evidence.
- Support companies with or without mature ERP infrastructure.

### Supported Inputs

KAE supports or is designed to support:

- Excel files
- PDFs
- Word documents
- CSV files
- Images
- Chat messages
- Manual notes
- Forms
- Voice transcripts
- ERP exports
- HR data
- Accounting data
- Attendance data
- Sales data
- Warehouse data
- Procurement records
- Operational logs
- Automation outputs

### Examples

For Jannat Al-Firdaws, early KAE inputs include:

- Daily poultry technical reports.
- Feed mill inventory files.
- Dairtna operational semantics.
- Dairtna decision rules.
- Finance and production spreadsheets.
- Future HR, sales, attendance, and warehouse records.

### Future Connectors

KAE should eventually support connectors for:

- ERP systems
- HR systems
- Accounting systems
- Warehouse systems
- Sales systems
- Attendance devices
- IoT sensors
- Veterinary systems
- Production equipment
- n8n automations
- Email and messaging platforms
- File storage systems

KAE treats each connector as an input source, not as the center of the product. NAWA remains the cognitive layer above all sources.

---

## 2. Operational Intelligence Engine (OIE)

### Purpose

The Operational Intelligence Engine converts captured operational inputs into structured operational intelligence.

OIE is the transformation layer. It turns raw input into facts, facts into metrics, metrics into events, events into signals, and signals into situations.

OIE does not perform root cause reasoning. It does not make business decisions. It detects, structures, normalizes, and classifies operational reality.

### Pipeline

```text
Operational Facts
        |
        v
Metrics
        |
        v
Events
        |
        v
Signals
        |
        v
Situations
```

### Operational Facts

Operational Facts are the smallest trustworthy facts extracted from a source.

Examples:

- Date: `2026-05-11`
- Bird balance: `77037`
- Daily mortality: `14`
- Water consumption: `22000`
- Daily production rate: `91.2%`
- Standard production rate: `93.4%`

Facts must remain traceable to their source row, sheet, file, system, or human input.

### Metrics

Metrics are named operational measurements derived from facts.

Examples:

- `bird_balance`
- `daily_mortality`
- `weekly_mortality_rate`
- `daily_tray_production`
- `box_production`
- `daily_production_rate`
- `standard_production_rate`
- `broken_eggs`
- `dirty_eggs`
- `water_consumption`

Metrics are not interpretations by themselves. They are structured measurements.

### Events

Events are operational occurrences built from records and metrics.

Example:

```text
event_type: poultry_daily_report
entity_type: poultry_hall
date: 2026-05-11
summary: daily poultry production and mortality record
```

Events give NAWA a timeline of what happened.

### Signals

Signals are rule-based detections that indicate something may require attention.

Examples:

- `production_below_standard`
- `production_declining_trend`
- `high_daily_mortality`
- `data_quality_warning`

Signals are not conclusions. They are detected patterns.

### Situations

Situations are grouped operational conditions formed from related signals.

Example:

```text
situation_type: poultry_production_drop
severity: warning
title: Production decline detected in poultry hall
```

A situation means there is enough structured signal evidence to form an operational condition worth contextualizing. It does not mean NAWA knows why the condition occurred.

---

## 3. Operational Context Engine (OCE)

### Purpose

The Operational Context Engine prepares the information needed before reasoning.

OCE answers:

```text
What information is relevant before reasoning?
```

OCE does not make decisions.

OCE does not identify root cause.

OCE does not recommend business action.

OCE builds a context packet from situations, related metrics, related events, related signals, company knowledge, available evidence, and missing evidence.

### Why OCE Exists Before Reasoning

Operational reasoning without context is dangerous. A production drop may be caused by feed, water, mortality, temperature, ventilation, disease, staffing, equipment, breed age, reporting gaps, or normal operational variation.

The OCE prevents premature conclusions by forcing NAWA to ask:

- What evidence do we have?
- What evidence is missing?
- Which departments are relevant?
- Which operational entities are involved?
- What time window matters?
- Which knowledge documents apply?
- Is the context sufficient for reasoning?

Only after OCE prepares this context can the Reasoning Engine responsibly form hypotheses.

### Evidence

Evidence is any available or missing item that matters to the situation.

Each evidence item has:

- Source
- Type
- Status
- Description
- Date range

Evidence statuses:

- `available`
- `missing`

Examples of available evidence:

- Production trend signal.
- Daily mortality metrics.
- Water consumption metrics.
- Feed mill inventory workbook.
- Company decision rules.
- Operational semantics.
- Previous production history.

Examples of missing evidence:

- Vet reports.
- Temperature and ventilation readings.
- Additional hall observations.

### Evidence Graph

The Evidence Graph is the relationship map between:

- Situation
- Metrics
- Events
- Signals
- Source files
- Company rules
- Operational semantics
- Departments
- Entities
- Missing evidence

Conceptually:

```text
poultry_production_drop
        |
        +-- production_declining_trend signal
        +-- production_below_standard signals
        +-- daily poultry records
        +-- water consumption metrics
        +-- mortality metrics
        +-- feed mill inventory evidence
        +-- decision rules
        +-- operational semantics
        +-- missing vet reports
        +-- missing temperature / ventilation evidence
```

The graph allows future reasoning to inspect what is known and unknown without confusing evidence with conclusions.

### Missing Evidence

Missing evidence is first-class context.

NAWA must explicitly record what is not available. This prevents false confidence and makes reasoning honest.

If a situation lacks temperature readings, NAWA must say so. If vet reports are unavailable, NAWA must not imply disease. If feed records exist but water records do not, NAWA must distinguish the two.

### Context Readiness

`context_ready_for_reasoning` indicates whether enough evidence exists to proceed into reasoning.

The readiness flag is conservative.

It becomes `true` only when sufficient operational evidence exists for the situation type. If key operational evidence is missing, OCE keeps readiness `false`.

This protects the Reasoning Engine from making unsupported conclusions.

### Cross-Department Context

OCE also prepares cross-department context.

For example, a poultry production drop may involve:

- Poultry production
- Feed mill
- Veterinary
- Maintenance
- Environment control
- Procurement
- Warehouse
- Finance

OCE identifies which departments may hold relevant evidence. It does not accuse, decide, or assign responsibility.

---

## 4. Reasoning Engine

### Purpose

The Reasoning Engine interprets operational context and produces hypotheses, decision options, risk analysis, and next-step intelligence.

Reasoning begins only after OCE prepares context.

### Three-Layer Reasoning Model

```text
Truth Layer
        |
        v
Company Brain
        |
        v
AI Reasoning
```

### Truth Layer

The Truth Layer contains source-grounded facts and evidence.

Examples:

- Extracted Excel values.
- Parsed metrics.
- Verified events.
- Available evidence.
- Missing evidence.
- Source files.
- Date ranges.

The Truth Layer is authoritative. It cannot be overridden by business doctrine, memory, or AI-generated language.

### Company Brain

The Company Brain contains company-specific context:

- Company structure.
- Departments.
- Workflows.
- Operating rules.
- Decision rules.
- Operational semantics.
- Historical patterns.
- Known dependencies.
- Role and KPI ownership.
- Institutional knowledge.

The Company Brain interprets facts, but it never overrides facts.

If a company rule says a metric is usually safe, but the source data shows an exception, the source data remains true. The Company Brain may contextualize the exception, not erase it.

### AI Reasoning

AI Reasoning operates only after Truth Layer and Company Brain context are assembled.

AI may:

- Generate hypotheses.
- Compare likely explanations.
- Explain business implications.
- Draft decision options.
- Identify risks.
- Recommend next evidence to collect.
- Prepare executive narratives.

AI may not:

- Invent missing facts.
- Treat assumptions as facts.
- Override source evidence.
- Produce unsupported root cause claims.
- Hide uncertainty.

### Hypotheses

Hypotheses are possible explanations, not conclusions.

Example:

```text
Hypothesis: Production decline may be connected to environmental conditions.
Evidence status: Temperature / ventilation data missing.
Confidence: not ready.
```

Hypotheses must state:

- Supporting evidence.
- Missing evidence.
- Confidence level.
- Alternative explanations.

### Decision Options

Decision options are possible actions a leader may consider.

They must be generated from evidence and context, not from isolated signals.

A good decision option includes:

- Action
- Owner
- Evidence basis
- Operational impact
- Risk
- Required follow-up data

### Risk Analysis

Risk analysis evaluates potential operational consequences.

Examples:

- Production risk
- Mortality risk
- Feed risk
- Water risk
- Veterinary risk
- Customer fulfillment risk
- Financial impact
- Cross-department dependency risk

Risk analysis must distinguish:

- Observed risk
- Inferred risk
- Unknown risk due to missing evidence

---

## 5. Executive Intelligence

Executive Intelligence converts structured context and reasoning into leadership-ready outputs.

### CEO Brief

CEO Briefs are concise executive summaries.

They should include:

- Headline
- Severity
- What happened
- Why it matters
- Evidence summary
- Recommended next actions
- Confidence

The CEO Brief must remain evidence-aware and honest about missing context.

### Department Brief

Department Briefs translate situations into department-specific operational views.

Examples:

- Production brief
- Feed mill brief
- Veterinary brief
- Maintenance brief
- Finance brief
- HR brief
- Sales brief

Each department brief should answer:

- What concerns this department?
- What evidence is available?
- What evidence is missing?
- What should the department check?
- Which other departments are connected?

### Operational Brief

Operational Briefs support managers and field teams.

They are more detailed than CEO briefs and may include:

- Daily situation summaries.
- Metric tables.
- Evidence gaps.
- Hall-level or unit-level detail.
- Follow-up checklists.

### Predictions

Prediction is a future capability.

Predictions must be based on:

- Historical data.
- Current signals.
- Operational context.
- Company patterns.
- Known dependencies.

Predictions must always show confidence and evidence basis.

### Automation

Automation is a future execution layer.

NAWA may eventually trigger:

- Alerts
- Follow-up requests
- Report generation
- Task creation
- Workflow handoffs
- n8n automations

Automation must be controlled by permissions, company policy, and evidence thresholds.

---

## 6. Future Engine: Organizational Memory Engine (OME)

### Purpose

The Organizational Memory Engine preserves long-term company memory.

OME allows NAWA to learn from the company over time without confusing memory with current facts.

### Long-Term Company Memory

OME stores:

- Historical situations.
- Resolved issues.
- Repeated patterns.
- Operational cycles.
- Department dependencies.
- Known risks.
- Prior decisions.
- Decision outcomes.
- Institutional knowledge.

### Historical Learning

OME supports historical learning by connecting current situations to previous cases.

Example:

```text
Current: poultry production drop
Historical memory: similar drops occurred during previous ventilation issues
Evidence rule: historical similarity is context, not proof
```

### Decision Memory

Decision Memory records:

- What was decided.
- Who decided.
- When it was decided.
- What evidence was used.
- What assumptions were made.
- What happened afterward.

This allows NAWA to learn from outcomes, not only from inputs.

### Institutional Knowledge

Institutional Knowledge includes:

- SOPs
- Company rules
- Operating doctrine
- Department practices
- Local language and terminology
- Vendor patterns
- Seasonal patterns
- Management preferences

OME makes the organization less dependent on individual memory and scattered files.

---

## End-to-End Data Flow

```text
Source Input
  |
  |  Excel, PDF, chat, form, ERP, HR, finance, warehouse, automation
  v
KAE
  |
  |  Capture raw input, metadata, source, type
  v
OIE
  |
  |  Facts -> Metrics -> Events -> Signals -> Situations
  v
OCE
  |
  |  Evidence, missing evidence, time window, entities, departments
  v
Reasoning Engine
  |
  |  Hypotheses, options, risks, next evidence
  v
Executive Intelligence
  |
  |  CEO briefs, department briefs, operational briefs, predictions
  v
OME
  |
  |  Decision memory, historical learning, institutional knowledge
```

---

## Evidence Flow

```text
Raw Source
   |
   v
Extracted Fact
   |
   v
Metric / Event / Signal
   |
   v
Situation
   |
   v
Evidence Item
   |
   +-- available evidence
   |
   +-- missing evidence
   |
   v
Operational Context
```

Evidence must retain source traceability.

Missing evidence must remain visible.

Evidence is not the same as conclusion.

---

## Reasoning Flow

```text
Operational Context
       |
       v
Truth Layer Check
       |
       v
Company Brain Context
       |
       v
Hypothesis Formation
       |
       v
Risk and Option Analysis
       |
       v
Executive / Department / Operational Output
```

If context is not ready, the Reasoning Engine should not produce confident conclusions. It may request missing evidence or produce explicitly limited hypotheses.

---

## Sequence Diagram: Poultry Production Drop

```text
Daily Poultry Excel Report
        |
        v
KAE captures file and metadata
        |
        v
OIE parses poultry records
        |
        v
OIE generates metrics
        |
        v
OIE generates daily report events
        |
        v
OIE detects production below standard
        |
        v
OIE detects declining production trend
        |
        v
OIE generates poultry_production_drop situation
        |
        v
OCE collects related metrics, events, and signals
        |
        v
OCE checks feed, water, mortality, vet, temperature, history, rules, semantics
        |
        v
OCE separates available evidence from missing evidence
        |
        v
OCE sets context_ready_for_reasoning
        |
        v
Reasoning Engine may proceed only if context is sufficient
```

---

## Sequence Diagram: Evidence Readiness

```text
Situation: poultry_production_drop
        |
        v
OCE Required Context Check
        |
        +-- Production trend available?
        +-- Water consumption available?
        +-- Feed evidence available?
        +-- Mortality trend available?
        +-- Vet reports available?
        +-- Temperature / ventilation available?
        +-- Previous production history available?
        +-- Company decision rules available?
        +-- Operational semantics available?
        |
        v
Available Evidence + Missing Evidence
        |
        v
Context Ready?
        |
        +-- Yes: allow reasoning
        |
        +-- No: request missing evidence / limit conclusions
```

---

## Why NAWA Is Not an ERP

ERP systems are transaction systems. They manage structured operational records such as invoices, inventory movements, purchase orders, payroll, and accounting entries.

NAWA is not ERP-first.

NAWA can consume ERP data, but NAWA's purpose is to understand the company across systems, files, people, workflows, and decisions. ERP is an input to NAWA, not the architecture center.

---

## Why NAWA Is Not a Chatbot

A chatbot is an interface.

NAWA may include chat, voice, and conversational experiences, but the product is not defined by conversation. NAWA is defined by company understanding, evidence, context, memory, reasoning, and operational intelligence.

Chat is one way to access the Company Brain.

---

## Why NAWA Is Not a Dashboard

A dashboard displays metrics.

NAWA interprets operational reality.

Dashboards show what is visible. NAWA also tracks what is missing, what is connected, what may be affected, what evidence is available, what context is needed, and what should be reasoned about next.

Dashboards are outputs. NAWA is the intelligence layer beneath them.

---

## Why NAWA Is Not a BI Tool

BI tools analyze historical structured data.

NAWA works with structured and unstructured inputs, operational events, human updates, files, organizational relationships, missing evidence, live context, and decision memory.

BI explains data. NAWA understands the company.

---

## Why NAWA Is a Company Brain

NAWA is a Company Brain because it:

- Receives knowledge from every part of the company.
- Preserves source evidence.
- Structures operational facts.
- Detects metrics, events, signals, and situations.
- Builds context before reasoning.
- Distinguishes available evidence from missing evidence.
- Understands departments, entities, workflows, and dependencies.
- Applies company-specific rules and semantics without overriding facts.
- Supports executive and departmental intelligence.
- Learns from history through organizational memory.
- Enables future automation through evidence-aware intelligence.

NAWA's purpose is not to store data for its own sake.

NAWA's purpose is to help a company understand itself.

---

## Architectural Laws

1. Facts are sovereign.
2. Context precedes reasoning.
3. Missing evidence must be visible.
4. The Company Brain contextualizes facts but never overrides them.
5. AI reasoning must declare uncertainty when context is incomplete.
6. ERP, dashboards, chat, and BI are interfaces or inputs, not the core architecture.
7. Every operational signal must remain traceable to evidence.
8. Every decision should become memory.
9. Every memory must remain distinguishable from current truth.
10. NAWA must strengthen the organization as a connected operating system.

