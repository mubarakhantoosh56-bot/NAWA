# NAWA Architecture Rules

**Scope of authority:** this document is the canonical **Engineering Implementation Architecture** — folder structure, layering, and coding-level rules for building NAWA. For the canonical **NAWA Cognitive/System Architecture** — the product-level engine model (KAE, OIE, OCE, Reasoning, Executive Intelligence, OME) and how NAWA reasons about a company — see [`docs/architecture/`](docs/architecture/). The two are complementary: this file governs *how code is structured*; `docs/architecture/` governs *what the system cognitively does*. Neither supersedes the other.

These are non-negotiable architectural constraints. Violations undermine security, performance, or maintainability.

## Folder Structure

### Mandatory Structure
```
app/
â”œâ”€â”€ __init__.py
â”œâ”€â”€ main.py                 # FastAPI app initialization only
â”œâ”€â”€ core/
â”‚   â”œâ”€â”€ config.py          # Settings from .env
â”‚   â”œâ”€â”€ security.py        # JWT token operations
â”‚   â”œâ”€â”€ dependencies.py    # FastAPI dependency injection
â”‚   â””â”€â”€ errors.py          # Custom exceptions
â”œâ”€â”€ api/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ chat.py            # POST /ai/chat endpoint
â”‚   â”œâ”€â”€ health.py          # GET /health endpoint
â”‚   â””â”€â”€ v2/                # Future versioned endpoints
â”œâ”€â”€ services/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ openai_client.py   # AIService class (orchestration)
â”‚   â”œâ”€â”€ memory/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ event_log.py   # Event persistence
â”‚   â””â”€â”€ repository/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ event_repository.py
â”‚       â””â”€â”€ connection.py
â””â”€â”€ models/
    â”œâ”€â”€ __init__.py
    â”œâ”€â”€ request.py         # Pydantic request models
    â””â”€â”€ response.py        # Pydantic response models
```

### Rules
- **No root-level modules**: Business logic must be in `app/` folder
- **No circular imports**: Use dependency injection instead
- **No `*` imports**: Import specific symbols
- **No mixed concerns**: Each module has one responsibility
- **No utility dumping grounds**: Utilities belong in their domain

## Routing & Handlers

### Rule: No Business Logic in Routes

âŒ **FORBIDDEN**:
```python
@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # âŒ SQL query in endpoint
    result = await db.query(f"SELECT * FROM events WHERE company_id='{request.company_id}'")
    
    # âŒ OpenAI call in endpoint
    response = await openai.chat.completions.create(...)
    
    # âŒ Business logic in endpoint
    if request.message.startswith("DELETE"):
        ...
    
    return result
```

âœ… **REQUIRED**:
```python
@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    auth_context: AuthContext = Depends(get_auth_context)
):
    # 1. Validate authorization
    if request.company_id != auth_context.company_id:
        raise HTTPException(status_code=403, detail="Unauthorized company_id")
    
    # 2. Delegate to service
    result = await ai_engine.chat(
        session_id=request.session_id,
        message=request.message,
        context=request.context,
        company_id=auth_context.company_id,
    )
    
    # 3. Return result
    return result
```

### Endpoint Responsibilities
- **Receive**: Parse request from HTTP layer
- **Validate**: Check authorization, input types
- **Delegate**: Call service layer
- **Respond**: Return structured response

Endpoints are **routing adapters**, not business logic containers.

## Services Layer

### Rule: All Business Logic in Services

Services are the **only** place where:
- OpenAI calls happen
- Database queries happen
- Business decisions are made
- Errors are handled
- Logs are written

### Service Pattern
```python
class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(...)
        self.event_repo = EventRepository(...)
    
    async def chat(
        self,
        session_id: str,
        message: str,
        context: dict,
        company_id: str,
    ) -> ChatResponse:
        # Service owns the workflow
        
        # 1. Load company memory
        events = await self.event_repo.get_recent(company_id, limit=50)
        memory = self._inject_memory(events)
        
        # 2. Build prompt
        prompt = self._build_prompt(message, memory, context)
        
        # 3. Call OpenAI
        llm_response = await self.client.chat.completions.create(...)
        
        # 4. Parse response
        logic = self._parse_logic_json(llm_response)
        
        # 5. Store event
        await self.event_repo.insert_event(
            company_id=company_id,
            session_id=session_id,
            event_type="decision",
            payload=logic,
        )
        
        # 6. Return structured response
        return ChatResponse(
            logic_json=logic,
            ceo_text=llm_response.choices[0].message.content,
            meta=Meta(company_id=company_id, session_id=session_id),
        )
```

### Service Guidelines
- Receive fully-typed parameters (no dict/Any unless documented)
- Raise specific exceptions (InvalidCompanyID, MemoryQueryFailed)
- Return structured responses (Pydantic models)
- Log all operations with company_id for audit
- Handle retries and backoff internally

## Repository Pattern for Database

### Rule: All Database Access Through Repositories

âŒ **FORBIDDEN**:
```python
# Direct queries in services
async def get_events(company_id: str):
    query = "SELECT * FROM events WHERE company_id = $1"
    return await db.fetch(query, company_id)
```

âœ… **REQUIRED**:
```python
class EventRepository:
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    async def get_recent(self, company_id: str, limit: int = 50):
        query = """
        SELECT * FROM events 
        WHERE company_id = $1 
        ORDER BY created_at DESC 
        LIMIT $2
        """
        rows = await self.pool.fetch(query, company_id, limit)
        return [Event.from_row(row) for row in rows]

# Usage in services
events = await self.event_repo.get_recent(company_id)
```

### Repository Responsibilities
- Own all SQL/database details
- Filter by company_id at query construction
- Use parameterized queries (SQL injection prevention)
- Return typed objects (Pydantic, dataclasses)
- Handle connection pool lifecycle

### Query Rules
- **Parameterized always**: Use `$1, $2` placeholders, never string interpolation
- **Company_id first**: Filter by company_id before any other condition
- **Limit results**: Add LIMIT clauses to prevent runaway queries
- **Index awareness**: Write queries that can use existing indexes

## Tenant Isolation Mandatory

### Rule: Every Operation is Company-Scoped

**Every single database query** must include company_id:
```python
# âŒ FORBIDDEN: Query without company_id
SELECT * FROM events ORDER BY created_at DESC

# âœ… REQUIRED: Query includes company_id filter
SELECT * FROM events WHERE company_id = $1 ORDER BY created_at DESC
```

**Every endpoint must validate company_id**:
```python
@router.post("/ai/chat")
async def chat_endpoint(
    request: ChatRequest,
    auth_context: AuthContext = Depends(get_auth_context)
):
    # âœ… REQUIRED: Validate company_id matches
    if request.company_id != auth_context.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized company_id"
        )
    # Safe to proceed
```

### Company_id Sources
1. **JWT token** (trusted, set by auth system)
2. **Request body** (untrusted, must validate against JWT)
3. **Path parameter** (untrusted, must validate against JWT)

Always trust the JWT's company_id, validate request data against it.

### Isolation Testing
Before merging any code:
- [ ] Create request with company_id != token.company_id â†’ returns 403
- [ ] Create request with another company's session_id â†’ returns 403 or empty
- [ ] Verify database filters by company_id in all queries

## Authentication & Authorization

### Rule: JWT Required on Protected Routes

Every endpoint that accesses company data requires valid JWT:

```python
from app.core.dependencies import get_auth_context, AuthContext

@router.post("/ai/chat")
async def chat_endpoint(
    request: ChatRequest,
    auth_context: AuthContext = Depends(get_auth_context)
):
    # âœ… auth_context contains validated claims
    # âœ… Endpoint cannot be called without valid JWT
    pass

@router.get("/health")
async def health():
    # âœ… No auth required for health checks
    return {"status": "ok"}
```

### JWT Claims Structure
```python
class AuthContext:
    company_id: str      # From JWT token
    user_id: str         # From JWT token
    exp: datetime        # Expiration timestamp
    iat: datetime        # Issued-at timestamp
```

### Token Generation
```python
from app.core.security import create_token

token = create_token(
    company_id="acme-corp",
    user_id="user-123",
    expires_in_hours=24
)
```

### Token Validation
- Tokens expire after 24 hours (configurable)
- Signature verified with JWT_SECRET_KEY
- Claims required: company_id, user_id
- Invalid tokens â†’ 401 Unauthorized
- Missing Authorization header â†’ 401 Unauthorized

## Secrets & Configuration

### Rule: No Hardcoded Secrets

âŒ **FORBIDDEN**:
```python
API_KEY = "sk-proj-..."  # Hardcoded
PASSWORD = "admin123"     # Hardcoded
```

âœ… **REQUIRED**:
```python
# In .env
OPENAI_API_KEY=sk-proj-...
JWT_SECRET_KEY=...
DATABASE_URL=postgresql://...

# In code
from app.core.config import settings
api_key = settings.OPENAI_API_KEY
```

### .env Usage Rules

**Structure:**
```
# .env at project root
OPENAI_API_KEY=sk-proj-...
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
JWT_SECRET_KEY=<64-byte-url-safe-token>
```

**Loading:**
```python
# app/core/config.py
load_dotenv(dotenv_path=BASE_DIR / ".env")

@dataclass(frozen=True)
class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
```

**Rules:**
- .env is **never committed** to git (gitignored)
- Secrets are 64+ bytes from `secrets.token_urlsafe(64)`
- Each environment has its own .env (dev, staging, prod)
- Settings class is **frozen** (immutable, prevents accidental mutation)
- No defaults for secrets (explicit errors if missing)

## Async-First Architecture

### Rule: All I/O is Async

âŒ **FORBIDDEN**:
```python
# Blocking database call
result = db.query("SELECT * FROM events")

# Blocking API call
response = requests.post("https://api.openai.com/...")

# Blocking sleep
time.sleep(5)
```

âœ… **REQUIRED**:
```python
# Non-blocking database call
result = await db.fetch("SELECT * FROM events")

# Non-blocking API call
response = await client.chat.completions.create(...)

# Non-blocking sleep
await asyncio.sleep(5)
```

### Async Patterns

**Route Handler:**
```python
@router.post("/ai/chat")
async def chat_endpoint(request: ChatRequest):
    # âœ… Always async
    return await ai_engine.chat(...)
```

**Service Method:**
```python
class AIService:
    async def chat(self, ...):
        # âœ… Always async for I/O
        events = await self.event_repo.get_recent(...)
        response = await self.client.chat.completions.create(...)
```

**Repository Method:**
```python
class EventRepository:
    async def insert_event(self, ...):
        # âœ… Always async for DB
        return await self.pool.execute(query, *params)
```

**Dependency:**
```python
async def get_auth_context(request: Request) -> AuthContext:
    # âœ… Can be async if needing I/O
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return validate_token(token)  # sync, no I/O
```

### Concurrency Model
- FastAPI runs on **Uvicorn** with multiple worker processes
- Each worker handles **multiple concurrent requests** via asyncio
- Never block the event loop; async everything
- Use `await` for all I/O operations

## Error Handling

### Rule: Specific Exceptions, Never Generic Exception

âŒ **FORBIDDEN**:
```python
try:
    result = await db.fetch(...)
except Exception as e:
    raise HTTPException(status_code=500, detail="Error")
```

âœ… **REQUIRED**:
```python
class InvalidCompanyID(Exception):
    """Company ID does not match authenticated context."""
    pass

class MemoryQueryFailed(Exception):
    """Event repository returned no results."""
    pass

try:
    result = await db.fetch(...)
except MemoryQueryFailed as e:
    raise HTTPException(status_code=404, detail="No events found")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Exception Hierarchy
- Define custom exceptions in `app/core/errors.py`
- Inherit from appropriate base (RuntimeError, ValueError, etc.)
- Use specific exceptions in catch blocks
- Log full tracebacks for debugging
- Return user-safe error messages in HTTP responses

## Import Rules

### Rule: Explicit Imports, Never Wildcards

âŒ **FORBIDDEN**:
```python
from app.services import *
from datetime import *
```

âœ… **REQUIRED**:
```python
from app.services.openai_client import AIService
from datetime import datetime, timedelta
```

### Circular Import Prevention
- Never import from parent packages into modules
- Use dependency injection (Depends) instead
- Services receive dependencies in `__init__`

## Logging Standards

### Rule: Structured Logging with Company Context

Every log must include `company_id` and operation context:

```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Event stored",
    extra={
        "company_id": company_id,
        "session_id": session_id,
        "event_type": event_type,
    }
)

logger.error(
    "Auth validation failed",
    extra={
        "company_id": company_id,
        "reason": "Mismatched company_id",
    },
    exc_info=True
)
```

### Logging Rules
- Never log full JWT tokens or API responses containing secrets
- Include company_id and session_id in every relevant log
- Use appropriate log levels (debug, info, warning, error)
- Include exc_info=True for exceptions
