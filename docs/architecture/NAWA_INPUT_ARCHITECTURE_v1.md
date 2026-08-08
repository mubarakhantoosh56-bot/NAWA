# NAWA Input Architecture v1

## Vision

This document defines NAWA's universal input architecture.

Core principle:

> Users never choose an AI engine.
> Users only provide Company Inputs.
> NAWA classifies the input and routes it automatically.

NAWA does not receive files.

NAWA receives Company Inputs.

Files are only one transport format. A spreadsheet, PDF, chat message, voice note, ERP event, image, or sensor reading may look different at the transport layer, but inside NAWA each one is treated as new company information entering the Company Brain.

The user experience must remain simple: people provide information in the format they already have, and NAWA determines what it is, where it belongs, which engine should process it, and whether more evidence is needed.

## Why Input Architecture Matters

Traditional systems think:

```text
File
  |
  v
Storage
```

NAWA thinks:

```text
Company Input
  |
  v
Classification
  |
  v
Knowledge Acquisition
  |
  v
Operational Intelligence
  |
  v
Reasoning
  |
  v
Executive Intelligence
  |
  v
Organizational Memory
```

The difference is fundamental.

In a traditional system, upload is the end of the flow. The file is stored, indexed, and maybe retrieved later.

In NAWA, input is the beginning of the flow. A new piece of information enters the organization, and NAWA must decide what kind of information it is, which part of the company it belongs to, what evidence it contains, what operational or knowledge objects can be derived from it, and whether it should become part of durable organizational memory.

This prevents the product from becoming a file repository. It keeps NAWA aligned with its purpose as the Company Brain.

## Company Input

A Company Input is any new information entering an organization.

Examples include:

- Excel
- PDF
- Text
- Operational Update
- Voice Note
- Image
- Video
- ERP Event
- API Event
- WhatsApp Message
- Email
- IoT Sensor
- Future Integrations

Every future integration becomes just another Company Input.

This means new channels should not create new architectural paths. A WhatsApp message, ERP webhook, or IoT sensor event should not bypass the Company Brain. Each enters through the input architecture, receives classification, and is routed through the correct NAWA engines.

## Input Categories

NAWA classifies Company Inputs into categories before routing.

### Operational

Operational inputs describe what is happening in the business.

Examples:

- Poultry daily reports
- Production updates
- Feed shortages
- Mortality reports
- Warehouse incidents
- Delivery delays
- Manual operational notes

Operational inputs usually route toward Operational Intelligence, Operational Context, reasoning readiness checks, executive briefings, and organizational memory.

### Knowledge

Knowledge inputs describe stable or semi-stable company knowledge.

Examples:

- Policies
- SOPs
- Training documents
- Product catalogs
- Department descriptions
- Company profile documents

Knowledge inputs usually route toward Knowledge Acquisition and the Company Brain knowledge layer. They may support reasoning later, but they are not automatically operational events.

### Financial

Financial inputs describe money, costs, budgets, revenue, cash flow, profitability, or financial obligations.

Examples:

- Finance reports
- Budgets
- Invoices
- Cost sheets
- Sales revenue summaries
- Procurement spend

Financial inputs may route to future finance intelligence capabilities while still following the same input lifecycle.

### Human

Human inputs describe people, roles, attendance, performance, decisions, accountability, staffing, communication, or organizational behavior.

Examples:

- HR updates
- Attendance summaries
- Manager notes
- Decision confirmations
- Responsibility assignments
- Team capacity reports

Human inputs are important because NAWA must understand the company as an operating organization, not only as numbers and files.

### Media

Media inputs contain visual, audio, or video evidence.

Examples:

- Voice notes
- Images
- Videos
- Screenshots
- Site photos
- Audio reports

Media inputs may require transcription, vision analysis, or future media interpretation before entering Knowledge Acquisition.

### Machine

Machine inputs come from systems, automations, sensors, or structured integrations.

Examples:

- ERP events
- API events
- IoT sensor readings
- System alerts
- Automation logs
- Integration webhooks

Machine inputs are often structured and high-volume. They still need company resolution, department resolution, validation, and routing.

### External

External inputs originate outside the organization but may affect it.

Examples:

- Market updates
- Supplier notices
- Regulatory changes
- Customer messages
- Competitor signals
- News or external reports

External inputs should be treated carefully. NAWA must preserve source context and evidence before allowing them to influence conclusions.

## Input Lifecycle

Every Company Input follows the same lifecycle:

```text
Company Input
  |
  v
Authentication
  |
  v
Company Resolution
  |
  v
Department Resolution
  |
  v
Input Classification
  |
  v
Validation
  |
  v
Routing
  |
  v
Engine Execution
  |
  v
Evidence Generation
  |
  v
Executive Output
  |
  v
Memory
```

### Authentication

NAWA must know who submitted the input. Anonymous or untrusted inputs must not enter the Company Brain as authoritative evidence.

### Company Resolution

NAWA must resolve the input to the authenticated company. Request-provided company IDs must not override authenticated tenant context.

### Department Resolution

NAWA should identify the relevant department, division, workspace, or company-wide scope. If department confidence is low, the system should ask for clarification.

### Input Classification

NAWA classifies the input type, category, likely domain, and intended processing path.

### Validation

NAWA checks whether the input is readable, supported, safe, complete enough, and structurally valid for the selected path.

### Routing

NAWA dispatches the input to the correct engine sequence. Users do not choose the engine.

### Engine Execution

The selected engines execute their own responsibilities. The orchestrator coordinates; it does not replace engine logic.

### Evidence Generation

NAWA extracts evidence, derived records, events, metrics, signals, situations, source links, and missing evidence.

### Executive Output

When appropriate, NAWA creates CEO-ready or manager-ready outputs.

### Memory

Durable organizational understanding is stored in memory when the input produces situations, decisions, outcomes, or stable knowledge.

## NCO Responsibilities

NCO is the universal entry controller for Company Inputs.

NCO responsibilities:

- identify input type
- detect company
- detect department
- determine confidence
- request clarification if confidence is low
- dispatch to the correct engine
- never perform reasoning itself

NCO does not own business logic. NCO does not replace KAE, OIE, OCE, NCE, OME, or Executive Intelligence.

NCO coordinates the path. Engines execute the work.

## Routing Examples

### Excel Poultry Report

```text
Excel Poultry Report
  |
  v
KAE
  |
  v
OIP
  |
  v
OIE
  |
  v
OCE
  |
  v
NCE
  |
  v
Executive Brief
  |
  v
OME
```

An Excel poultry report is not merely a file. It is an operational Company Input. NAWA should acquire the data, normalize it, derive operational records and signals, build context, check readiness for reasoning, generate executive output when justified, and store durable memory when decisions or outcomes exist.

### PDF Policy

```text
PDF Policy
  |
  v
KAE
  |
  v
Knowledge
  |
  v
Company Brain
```

A policy document is a knowledge input. It may become part of company knowledge and support future answers, but it should not automatically become an operational event.

### Voice Note

```text
Voice Note
  |
  v
Speech
  |
  v
KAE
  |
  v
Operational Event
```

A voice note may become an operational event after transcription and classification. If confidence is low, NAWA should ask the user to clarify department, date, or meaning.

### Image

```text
Image
  |
  v
Vision
  |
  v
KAE
```

An image is media evidence. It may require vision interpretation before the content can be classified, validated, and routed.

### ERP API

```text
ERP API
  |
  v
Operational Event
```

An ERP API event may already be structured enough to become an operational event directly after authentication, tenant resolution, validation, and department mapping.

## Input Confidence

NAWA must assign confidence to input classification and routing.

### High

The input type, company, department, and route are clear.

Example: an authenticated Jannat user uploads a known Dairtna poultry daily report template in `.xlsx` format from the Dairtna workspace.

### Medium

The input type is clear, but one part of the context may need confirmation.

Example: a spreadsheet looks operational, but the department could be poultry production or warehouse.

### Low

The system can make a plausible guess, but the risk of misrouting is meaningful.

Example: a PDF mentions costs and production but does not clearly indicate whether it is a financial report, operational report, or procurement note.

### Unknown

NAWA cannot safely classify the input.

Example: an unsupported file, ambiguous text, unclear voice transcription, or unrecognized machine event.

When confidence is low or unknown, NAWA asks the user for clarification instead of guessing.

Clarification may include:

- Which department does this belong to?
- Is this a report, policy, decision, or update?
- What date or period does this input describe?
- Should this be treated as evidence, an operational event, or stable knowledge?

## Human Experience Principles

The user should never need to know:

- OIE
- OCE
- NCE
- OME
- NCO

Users only interact with Company Inputs.

The interface should speak in business language:

- Upload report
- Add update
- Attach evidence
- Record decision
- Submit policy
- Connect system
- Add voice note

The internal engine names remain architectural concepts, not user-facing choices.

## MVP Scope

The MVP supports:

- Excel
- PDF
- Text
- Operational Updates

These MVP inputs establish the first universal input path:

- authenticated tenant input
- department or company-wide scope
- input classification
- file/text extraction where needed
- routing to existing backend services
- evidence generation
- executive output when available
- memory foundation where appropriate

Future versions add:

- Voice
- Images
- Video
- Email
- WhatsApp
- ERP Integrations
- IoT

These future inputs must enter through the same Company Input architecture instead of creating isolated routes around the Company Brain.

## Architectural Laws

### 1. Every Company Input Enters Through NCO

NCO is the universal entry controller. No future input channel should bypass orchestration.

### 2. Users Never Manually Select Engines

Users provide information. NAWA classifies and routes it.

### 3. Classification Precedes Reasoning

NAWA must understand what the input is before reasoning over it.

### 4. Evidence Precedes Conclusions

NAWA must extract, preserve, and evaluate evidence before producing conclusions.

### 5. Unknown Inputs Require Clarification

If confidence is low or unknown, NAWA asks the user for clarification instead of guessing.

### 6. Memory Stores Organizational Understanding, Not Raw Uploads

Raw uploads may be stored as source material, but OME stores durable organizational memory: situations, decisions, outcomes, patterns, and stable knowledge.

### 7. Engines Execute; NCO Coordinates

NCO does not perform reasoning, extraction, operational analysis, or memory modeling itself. It coordinates engine execution.

### 8. Future Integrations Must Become Company Inputs

Voice, images, video, email, WhatsApp, ERP, IoT, and API integrations are all Company Inputs. They must comply with this architecture.

This document defines how information enters NAWA.

It is one of the constitutional documents of the Company Brain architecture.

All future integrations must comply with this specification.
