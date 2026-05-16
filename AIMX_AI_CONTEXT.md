# NAWA AI Context System

## Project Vision

NAWA is a **multi-tenant AI employee operating system** that enables companies to deploy autonomous AI agents capable of understanding institutional context, making informed decisions, and executing workflows with institutional memory.

Unlike generic chatbots, NAWA acts as a digital employee with:
- **Institutional Memory**: Persistent, queryable memory of company decisions, conflicts, and outcomes
- **Tenant Isolation**: Cryptographically enforced company boundaries
- **Reasoning Engine**: Multi-layer decision logic with root cause analysis
- **Adaptive Strategy**: AI strategies that evolve based on company profile and conflict detection

## Core Identity

NAWA is **not**:
- A conversational UI layer
- A document storage system
- A generic LLM wrapper

NAWA **is**:
- An operating system for AI agents to work autonomously within company boundaries
- A decision engine that reasons about institutional context
- A multi-tenant SaaS platform where each company has isolated institutional memory
- An extensible framework for deploying specialized AI workers (department agents)

## Multi-Tenant Architecture

### Company Isolation

Every request must be scoped to a company:
- **Authentication Boundary**: JWT token contains `company_id`
- **Authorization Layer**: `company_id` from token must match request `company_id`
- **Database Isolation**: All queries filtered by `company_id`
- **Memory Isolation**: Each company's institutional memory is sealed from others
- **No Cross-Tenant Data Leakage**: Queries across company boundaries are architecturally impossible

### Tenant Identity Claims

- `company_id`: Unique identifier for the tenant
- `user_id`: User within that company
- `exp`: Token expiration (24 hours default)
- `iat`: Token issued-at timestamp

Validation is **enforced at every endpoint**. There is no "global view" of data.

## Memory Engine Philosophy

NAWA's memory system is the core differentiator. It captures and stores:

### Event Log Structure
```
{
  "timestamp": ISO8601,
  "company_id": str,
  "session_id": str,
  "event_type": "decision|conflict|execution|outcome",
  "context": { user-provided context },
  "payload": { structured event data }
}
```

### Memory Injection Flow
1. **Context Lock**: Detect when session context is incomplete or contradictory
2. **Historical Query**: Retrieve similar past decisions from company memory
3. **Conflict Detection**: Flag new contradictions against institutional knowledge
4. **Strategy Application**: Apply adaptive company profile to reasoning
5. **Decision Logging**: Store outcome for future reference

### Facts Extraction
Decisions are analyzed to extract:
- **Root causes** identified by the AI
- **Action items** with timeline (30/90/180 days)
- **Dependencies** between actions
- **Risks** flagged during reasoning
- **Confidence scores** for predictions

All facts are **queryable and traceable** to the decision that generated them.

## Response Architecture

### Logic JSON Structure
Every `/ai/chat` response contains structured logic:
```json
{
  "logic_json": {
    "context_lock": {
      "is_locked": bool,
      "missing_fields": [str],
      "confidence": 0-1,
      "why": str
    },
    "problem_classification": {
      "type": str,
      "confidence": 0-1,
      "why": str
    },
    "truth_validation": {
      "contradictions": [{}, ...],
      "trust_score": 0-1,
      "notes": str
    },
    "root_cause_engine": {
      "root_causes": [str],
      "why_chain": [str]
    },
    "solution_generator": {
      "urgent_30_days": [str],
      "mid_term_90_days": [str],
      "long_term_6_12_months": [str]
    },
    "execution_engine": {
      "priority_order": [str],
      "quick_wins": [str],
      "high_impact_moves": [str],
      "dependencies": [str],
      "risks": [str]
    }
  },
  "ceo_text": str,
  "followup_question": str | null,
  "meta": {
    "company_id": str,
    "session_id": str,
    "context": {},
    "parse_ok": bool,
    "memory_injected": bool,
    "events_count": int
  }
}
```

### Response Guarantees
- **Structure**: Every response is valid JSON with the above schema
- **Traceability**: `meta` section identifies which company and session made the request
- **Reasoning**: `logic_json` shows all intermediate reasoning steps
- **Fallback**: If logic generation fails, `parse_ok=false` but endpoint still returns 200

## Current Technology Stack

### Backend Framework
- **FastAPI** (0.128.0): Async-first web framework with automatic OpenAPI docs
- **Pydantic** (2.12.5): Type validation and serialization
- **Uvicorn** (0.40.0): ASGI application server

### Database
- **PostgreSQL**: Primary data store with JSONB support for flexible schemas
- **Async Drivers**: asyncpg for non-blocking database access
- **Repository Pattern**: Data access abstraction layer

### AI & LLM
- **OpenAI API**: gpt-4o-mini for chat completions and reasoning
- **Async Client**: AsyncOpenAI (2.16.0) for non-blocking API calls
- **Prompt Engineering**: Context-aware prompts with institutional memory injection

### Authentication & Security
- **JWT Tokens**: HS256 signed tokens with company_id claim
- **Bearer Scheme**: `Authorization: Bearer {token}` header validation
- **Secret Management**: JWT_SECRET_KEY from environment, 64-byte URL-safe tokens
- **Tenant Isolation**: Company_id validation at every endpoint

### Institutional Memory
- **Event Logging**: Async event storage with idempotency keys
- **JSONB Storage**: Flexible event schema in PostgreSQL
- **Memory Injection**: Historical context retrieved and injected into prompts
- **Session Tracking**: Linked events within a session for coherent workflows

### Environment & Configuration
- **python-dotenv** (1.2.1): Environment variable loading
- **Settings Pattern**: Dataclass-based configuration (frozen, immutable)
- **No Secrets in Code**: All sensitive data from .env

## Core Modules

### `app/core/`
- **config.py**: Settings loaded from .env, frozen dataclass
- **security.py**: JWT creation, validation, token extraction
- **dependencies.py**: FastAPI dependency injection for auth context
- **errors.py**: Custom exception hierarchy

### `app/api/`
- **chat.py**: `/ai/chat` endpoint with tenant validation
- **health.py**: `/health` status checks

### `app/services/`
- **openai_client.py**: AIService class orchestrating reasoning engine
- **memory/event_log.py**: Event persistence and memory injection

### `app/services/repository/`
- **event_repository.py**: Event CRUD with company_id filtering
- **connection.py**: Database connection pool management

## Future Architectural Goals

### Phase 2: Department AI Agents
- **Finance Agent**: Autonomous AP/AR, forecasting, reconciliation
- **HR Agent**: Payroll, benefits, compliance, hiring workflows
- **Ops Agent**: Inventory, supply chain, logistics coordination
- **Sales Agent**: Opportunity management, deal sizing, territory planning

Each agent will:
- Have isolated memory namespace within company
- Report to CEO intelligence layer
- Execute multi-step workflows with human approval gates
- Maintain decision audit trail

### Phase 3: Autonomous Workflows
- **Cross-Agent Coordination**: Multiple agents collaborating on company goals
- **Approval Gates**: Human-in-the-loop for high-stakes decisions
- **Scheduler**: Cron-like execution of regular agent workflows
- **Webhook Events**: External systems triggering agent actions
- **State Machine**: Workflow states with rollback capability

### Phase 4: CEO Intelligence Layer
- **Executive Dashboard**: Aggregated insights from all department agents
- **Conflict Resolution**: AI mediator for inter-agent decision conflicts
- **Strategy Optimization**: Meta-learning from company outcomes
- **Predictive Alerts**: Flagging risks before they materialize
- **Board Reporting**: Automated executive summaries

### Phase 5: Digital Employees
- **Persistent Identity**: Agent personas that evolve over time
- **Skill Trees**: Agents gaining capabilities through successful task execution
- **Performance Reviews**: Metrics on agent decision quality and outcomes
- **Termination/Promotion**: Agents evolving or being retired based on performance
- **Institutional Knowledge Transfer**: Knowledge from high-performing agents reused by others

## Design Principles for AI Agents

### 1. Fail Safely
- Always validate `company_id` matches token
- Always use parameterized queries (no SQL injection)
- Always handle exceptions without leaking sensitive data
- Always return structured errors with request context

### 2. Maintain Isolation
- Never query across company boundaries
- Never modify auth tokens or claims
- Never bypass JWT validation
- Never store secrets in code or logs

### 3. Trace Everything
- Log all decisions with `company_id` and `session_id`
- Include reasoning in structured fields
- Capture intermediate steps for debugging
- Enable audit trails for compliance

### 4. Think Async-First
- Use `async def` for all I/O operations
- Use `await` for database and API calls
- Never block the event loop with synchronous operations
- Design for 1000s of concurrent requests per company

### 5. Respect Data Boundaries
- Treat `company_id` as a security boundary, not just metadata
- Filter queries by `company_id` before fetching
- Validate `company_id` after fetching from untrusted sources
- Never return data from the wrong company to a client
