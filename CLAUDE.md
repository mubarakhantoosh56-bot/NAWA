# CLAUDE.md: AIMX Operating Instructions

This file instructs Claude Code on how to safely modify the AIMX codebase.

## Before Any Code Change: Read These Files

1. **AIMX_AI_CONTEXT.md** — Understand the vision, multi-tenancy, memory system
2. **ARCHITECTURE_RULES.md** — Know the non-negotiable structural rules
3. **CODING_STANDARDS.md** — Follow typing, naming, style guidelines
4. **AI_AGENT_WORKFLOW.md** — Learn the safe modification workflow

These files contain the complete operating system design. Skipping them risks introducing security bugs, violating tenant isolation, or breaking production.

## Core Principles (Non-Negotiable)

### 1. Multi-Tenant Isolation is a Security Boundary
- Every request is scoped to a `company_id`
- JWT token is the **source of truth** for company identity
- Request `company_id` must be **validated against token** at every endpoint
- **Every database query** must filter by `company_id`
- Never query across company boundaries
- Company data is cryptographically isolated

### 2. Layered Architecture Prevents Bugs
```
Request → Route Handler → Service Layer → Repository → Database
  ↑           ↓              ↓              ↓
validate   delegate      orchestrate     query
 auth      only          logic           data
```

- **Routes**: Parse request, validate auth, delegate to service, return response
- **Services**: Own business logic, coordinate repositories, handle errors
- **Repositories**: Own all SQL, filter by company_id, return typed objects
- **Never** put business logic in routes
- **Never** call database from routes
- **Never** bypass repository pattern

### 3. Type Safety Prevents Runtime Errors
- All functions have parameter type hints
- All functions have return type hints (including `-> None`)
- Use `str`, `int`, `bool`, `list[T]`, `dict[K, V]`, not `Any`
- Pydantic models for all request/response validation

### 4. Async-First Prevents Blocking
- All I/O operations are `async def`
- Use `await` on all database calls
- Use `await` on all OpenAI API calls
- No `requests.get()`, only `await client.get()`
- No `time.sleep()`, only `await asyncio.sleep()`

### 5. Security Boundary Prevents Leaks
- Never hardcode secrets (API keys, passwords) in code
- All secrets from `.env` file only
- Never log JWT tokens or full API responses
- Always include `company_id` in error context
- Use parameterized queries: `$1, $2` not string interpolation

## Production Safety Checklist

Before committing **any** change, verify ALL of these:

- [ ] **Auth boundary held**: No code bypasses JWT validation
- [ ] **Tenant isolation preserved**: All queries filter by `company_id`
- [ ] **Secrets not hardcoded**: All from `.env` or `settings`
- [ ] **Type hints present**: All functions typed (parameters + return)
- [ ] **Docstrings present**: All public functions/classes documented
- [ ] **Error handling correct**: Catch specific exceptions, log with context
- [ ] **Async/await used**: No blocking I/O, all `await` for I/O
- [ ] **No refactoring creep**: Only modifications for the stated task
- [ ] **Backwards compatible**: Existing APIs not broken
- [ ] **Testable**: Change can be tested with curl or simple script
- [ ] **Commit message clear**: Describes WHAT changed and WHY

## Safe Modification Workflow

### Step 1: Understand the Request
- Clarify what needs to be built or fixed
- Reject vague requests ("optimize the code", "refactor everything")
- Ask if unclear

### Step 2: Design Before Coding
- Identify which files need modification
- Plan the order (dependency-first: models → repos → services → routes)
- Don't start coding until design is clear

### Step 3: Implement Incrementally
- Create/update models (Pydantic, request/response)
- Add repository methods (database access)
- Add service methods (business logic)
- Add route handlers (endpoints)
- Test manually

### Step 4: Review Against Checklist
- Run through production safety checklist
- Verify no security violations
- Verify architecture maintained

### Step 5: Commit with Clear Message
- Include only files necessary for the task
- Write commit message that describes WHAT and WHY
- Never commit `.env`, test files (unless needed), or generated code

## Common Mistakes to Avoid

### ❌ Mistake: Business Logic in Routes
```python
# FORBIDDEN
@router.post("/ai/chat")
async def chat_endpoint(request: ChatRequest):
    # Calling OpenAI directly in endpoint
    response = await openai.chat.completions.create(...)
    return response
```

**Fix**: Call service layer
```python
# REQUIRED
@router.post("/ai/chat")
async def chat_endpoint(request: ChatRequest, auth_context: AuthContext = Depends(get_auth_context)):
    if request.company_id != auth_context.company_id:
        raise HTTPException(403)
    return await ai_service.chat(request)
```

### ❌ Mistake: Queries Without company_id Filter
```python
# FORBIDDEN
SELECT * FROM events ORDER BY created_at DESC

# REQUIRED
SELECT * FROM events WHERE company_id = $1 ORDER BY created_at DESC
```

### ❌ Mistake: Missing Type Hints
```python
# FORBIDDEN
def validate_token(token):
    return jwt.decode(token, settings.JWT_SECRET_KEY)

# REQUIRED
def validate_token(token: str) -> dict[str, Any]:
    """Validate and decode JWT token."""
    return jwt.decode(token, settings.JWT_SECRET_KEY)
```

### ❌ Mistake: Hardcoded Secrets
```python
# FORBIDDEN
API_KEY = "sk-proj-12345..."

# REQUIRED
from app.core.config import settings
api_key = settings.OPENAI_API_KEY
```

### ❌ Mistake: Blocking I/O
```python
# FORBIDDEN
import requests
response = requests.post("https://api.openai.com/...")

# REQUIRED
response = await client.chat.completions.create(...)
```

### ❌ Mistake: Refactoring Beyond Scope
```
User: "Fix the JWT auth bug"
AI: "I'll also refactor the entire service layer and add caching..."
```

**Fix**: Only fix the stated bug. Refactoring is only acceptable if required for the feature (under 50 lines of logic changes).

## When to Ask the User

Before proceeding with significant changes:
- **Unclear requirements**: "Should this return paginated results or all events?"
- **Architecture decision**: "Cache in memory or query DB each time?"
- **Breaking change**: "This changes the request schema; is that OK?"
- **Risky operation**: "This modifies the auth system; should I proceed?"
- **Scope uncertainty**: "Should I also update the v2 API?"

## Git Workflow Rules

- **Branch names**: `feature/event-filtering`, `fix/jwt-validation`, `refactor/service-layer`
- **Commits**: One logical change per commit, atomic, traceable
- **Messages**: Imperative, short summary, longer explanation if needed
- **Files**: Only modified files necessary for the task (never `.env`, test artifacts, etc.)

### Example Commit

```
Add event filtering by type

- Create EventType enum in models
- Add get_by_event_type() to EventRepository
- Update /events endpoint to accept event_type parameter
- All queries include company_id filter for isolation

Endpoint now supports: ?event_type=decision&limit=100
```

## Repository Structure Reference

```
app/
├── __init__.py
├── main.py                      # FastAPI app initialization only
├── core/
│   ├── config.py               # Settings from .env
│   ├── security.py             # JWT token operations
│   ├── dependencies.py         # FastAPI dependency injection
│   └── errors.py               # Custom exceptions
├── api/
│   ├── __init__.py
│   ├── chat.py                 # POST /ai/chat endpoint
│   └── health.py               # GET /health endpoint
├── services/
│   ├── __init__.py
│   ├── openai_client.py        # AIService class (orchestration)
│   ├── memory/
│   │   ├── __init__.py
│   │   └── event_log.py        # Event persistence
│   └── repository/
│       ├── __init__.py
│       ├── event_repository.py
│       └── connection.py
└── models/
    ├── __init__.py
    ├── request.py              # Pydantic request models
    └── response.py             # Pydantic response models
```

## Tenant Isolation Checklist

Before merging ANY code that touches data:
- [ ] All GET queries include `WHERE company_id = $1`
- [ ] All INSERT statements include `company_id` in payload
- [ ] All UPDATE queries include `WHERE company_id = $1`
- [ ] All DELETE queries include `WHERE company_id = $1`
- [ ] Every endpoint validates request `company_id` against JWT token
- [ ] Test: request with `company_id != token.company_id` returns 403
- [ ] Test: request with another company's session_id returns 403 or empty

## Key Files and Their Responsibilities

| File | Owns | Modifies |
|------|------|----------|
| `app/core/config.py` | Settings from .env, frozen dataclass | When adding new env vars |
| `app/core/security.py` | JWT token creation/validation | Never without security review |
| `app/core/dependencies.py` | Auth context injection | When changing auth model |
| `app/api/chat.py` | Route handlers | When adding endpoints |
| `app/services/openai_client.py` | Business logic orchestration | When changing workflows |
| `app/services/memory/event_log.py` | Event storage | When changing event schema |
| `app/services/repository/event_repository.py` | Database queries | When adding data queries |
| `app/models/request.py` | Request validation | When adding endpoints |
| `app/models/response.py` | Response serialization | When changing responses |

## Production Deployment Safeguards

This codebase is **production-facing SaaS**. Every modification must:
- Maintain backwards compatibility (or explicitly version it)
- Never leak data between companies
- Never expose secrets in logs or error messages
- Never block event loop
- Never skip type checking or tests
- Include audit trail (clear git history)

## Emergency Rollback

If a commit breaks production:
1. Identify the commit with `git log`
2. **Do not modify the database** (data corruption risk)
3. Revert with: `git revert <commit-hash>`
4. Fix the issue in a new commit
5. Post-mortem: What violated the checklist?

## Summary

**Safe modifications follow this formula:**

1. **Read** AIMX_AI_CONTEXT.md, ARCHITECTURE_RULES.md, CODING_STANDARDS.md, AI_AGENT_WORKFLOW.md
2. **Understand** the request thoroughly
3. **Design** before coding (identify files, plan order)
4. **Implement** in layers (models → repos → services → routes)
5. **Review** against production safety checklist
6. **Test** manually (curl or simple script)
7. **Commit** with clear message, only necessary files

When in doubt, **ask the user** before modifying production code.

---

**Updated**: 2026-05-08  
**Branch**: claude-safe-review  
**Audience**: Claude AI agents modifying AIMX codebase
