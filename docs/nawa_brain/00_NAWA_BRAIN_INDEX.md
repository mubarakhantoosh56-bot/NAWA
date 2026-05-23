# NAWA Brain — Document Index

**Audience:** AI coding agents and human engineers working on the NAWA codebase.  
**Rule:** Read this index before reading any other document in this folder.  
**Last updated:** 2026-05-23

---

## 1. Reading Order

Documents must be read in this order. Each document assumes the prior ones are understood.

### 1.1 Foundation (required for all changes)

| Order | File | Purpose |
|---|---|---|
| 1 | `01_vision.md` | What NAWA is and is not |
| 2 | `02_product_philosophy.md` | Design and product principles |
| 3 | `09_agent_instructions.md` | How AI agents must behave in this codebase |

### 1.2 Architecture and domain (read for the relevant change area)

| Order | File | Purpose |
|---|---|---|
| 4 | `03_company_brain_architecture.md` | Core intelligence layers and company brain structure |
| 5 | `04_jannat_alfirdaws_model.md` | First enterprise model: Jannat Al-Firdaws divisions and departments |
| 6 | `05_organizational_intelligence.md` | Organizational structure, roles, and department dependency model |
| 7 | `06_data_capture_architecture.md` | How operational signals enter the system |
| 8 | `07_ai_behavior_rules.md` | Rules that govern AI reasoning and response generation |
| 9 | `08_ui_experience_principles.md` | UI and UX design rules |

### 1.3 Dairtna operational intelligence (required for any Dairtna or interpreter change)

| Order | File | Purpose |
|---|---|---|
| 10 | `DAIRTNA_OPERATIONAL_INTERPRETATION.md` | Interpreter signal levels, metric thresholds, and CEO response constraints for Dairtna |
| 11 | `DAIRTNA_OPERATIONAL_SEMANTICS.md` | Domain operational semantics layer governing meaning before interpretation; semantics constrains interpretation and reasoning |

> **Note on reading order 10 → 11:** Read the interpretation doctrine first to understand the signal vocabulary and threshold structure. Then read the semantics layer to understand the domain meaning constraints that the interpretation rules depend on. The semantics document is positioned here because it requires familiarity with the interpretation layer to be applied correctly — but architecturally it operates before interpretation (see Section 3).

---

## 2. Document Purpose Table

| File | Type | Scope | Summary |
|---|---|---|---|
| `01_vision.md` | Vision | Platform-wide | Defines what NAWA is (company brain, not ERP or chatbot), what it is not, and the first enterprise environment |
| `02_product_philosophy.md` | Philosophy | Platform-wide | Design principles, what the product must feel like, and the values that constrain product decisions |
| `03_company_brain_architecture.md` | Architecture | Platform-wide | Intelligence layers: raw input → entity extraction → classification → events → pattern detection → decision context → organizational intelligence → AI output |
| `04_jannat_alfirdaws_model.md` | Domain model | Jannat Al-Firdaws | Structure of the first enterprise environment: Dairtna Poultry, Caesar Beverage, Shared Corporate Departments |
| `05_organizational_intelligence.md` | Intelligence layer | Platform-wide | Organizational memory, role hierarchy, department dependency graph, HR signal handling |
| `06_data_capture_architecture.md` | Infrastructure | Platform-wide | Ingestion pipeline: chat, forms, files, structured events, future automations; source confidence and normalization |
| `07_ai_behavior_rules.md` | Behavior rules | Platform-wide | What AI must and must not do: grounding requirements, cross-department escalation rules, evidence standards |
| `08_ui_experience_principles.md` | UX | Platform-wide | Executive workspace design, bilingual AR/EN rules, density, responsiveness, and tone |
| `09_agent_instructions.md` | Agent operating rules | Platform-wide | How AI coding agents must read, plan, implement, and verify changes in this codebase |
| `DAIRTNA_OPERATIONAL_INTERPRETATION.md` | Interpreter doctrine | Dairtna only | Signal levels (`normal / watch / warning / critical / unknown`), provisional metric thresholds, missing-baseline behavior, CEO response constraints |
| `DAIRTNA_OPERATIONAL_SEMANTICS.md` | Semantics layer | Dairtna only | Domain operational semantics layer governing meaning before interpretation; defines what Dairtna operational concepts mean in their field context; semantics constrains what the interpreter may conclude and what the reasoning layer may infer |

---

## 3. Architecture Relationship Map

This map shows how documents relate to the processing pipeline. Position in the map reflects dependency, not reading order.

```
Company Brain Architecture (03)
    │
    ├── Jannat Al-Firdaws Model (04)
    │       │
    │       └── Dairtna Poultry division
    │
    ├── Data Capture Architecture (06)
    │       │
    │       └── Operational signals enter the pipeline
    │
    ├── Organizational Intelligence (05)
    │       │
    │       └── Roles, departments, dependency graph
    │
    └── Intelligence processing chain:
            │
            ▼
        Raw Signal Capture
            │
            ▼
        Classification → Operational Events
            │
            ▼
        ┌─────────────────────────────────────────────┐
        │  DAIRTNA_OPERATIONAL_SEMANTICS.md           │
        │  Domain semantics layer                     │
        │  Governs meaning BEFORE interpretation      │
        │  Constrains what concepts and measurements  │
        │  mean in the Dairtna poultry field context  │
        └──────────────────┬──────────────────────────┘
                           │  semantics constrains ↓
                           ▼
        ┌─────────────────────────────────────────────┐
        │  DAIRTNA_OPERATIONAL_INTERPRETATION.md      │
        │  Interpreter doctrine                       │
        │  Applies thresholds to compute signal level │
        │  Produces: normal/watch/warning/critical/   │
        │  unknown signal blocks                      │
        └──────────────────┬──────────────────────────┘
                           │  interpretation constrains ↓
                           ▼
        AI Behavior Rules (07)
        CEO reasoning layer
        Response generation
```

**Constraint direction:**
- `DAIRTNA_OPERATIONAL_SEMANTICS.md` constrains `DAIRTNA_OPERATIONAL_INTERPRETATION.md`
- `DAIRTNA_OPERATIONAL_INTERPRETATION.md` constrains the AI reasoning layer via CEO response rules
- Neither layer may be bypassed or upgraded by the reasoning layer without new evidence

**Scope boundary:** Both Dairtna documents govern Dairtna operational measurements only. Other divisions define their own semantics and interpretation doctrine independently when the time comes.

---

## 4. Document Ownership and Stability

| File | Stability | Who may change it |
|---|---|---|
| `01_vision.md` | High — changes require product decision | Strategic owner |
| `02_product_philosophy.md` | High | Strategic owner |
| `03_company_brain_architecture.md` | Medium — may evolve as layers are built | Architecture review |
| `04_jannat_alfirdaws_model.md` | Medium | Domain and architecture review |
| `05_organizational_intelligence.md` | Medium | Domain review |
| `06_data_capture_architecture.md` | Medium | Engineering + architecture review |
| `07_ai_behavior_rules.md` | High — changes affect all AI outputs | Product + engineering review |
| `08_ui_experience_principles.md` | Medium | Design + engineering review |
| `09_agent_instructions.md` | High — changes affect all AI agents | Strategic owner |
| `DAIRTNA_OPERATIONAL_INTERPRETATION.md` | High — thresholds are provisional but must not be changed without field validation | Domain + engineering review |
| `DAIRTNA_OPERATIONAL_SEMANTICS.md` | High — semantics underpin interpretation correctness | Domain review |
