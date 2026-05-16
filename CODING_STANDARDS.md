# NAWA Coding Standards

All code must conform to these standards. Violations block merge.

## Type Annotations Mandatory

### Rule: Every Function Has Type Hints

âŒ **FORBIDDEN**:
```python
def create_token(company_id, user_id, expires_in_hours=24):
    # Missing type hints
    pass

async def get_events(repo, company_id):
    # Missing return type
    result = await repo.fetch(company_id)
    return result
```

âœ… **REQUIRED**:
```python
def create_token(
    company_id: str,
    user_id: str,
    expires_in_hours: int = 24,
) -> str:
    """Generate JWT token with company scope."""
    pass

async def get_events(
    repo: EventRepository,
    company_id: str,
) -> list[Event]:
    """Retrieve events for a company."""
    result = await repo.fetch(company_id)
    return result
```

### Type Annotation Rules
- All parameters must have type hints
- All functions must have return type hints (including `-> None`)
- Use standard types: `str`, `int`, `bool`, `float`, `bytes`
- Use collection types: `list[T]`, `dict[K, V]`, `set[T]`, `tuple[T, ...]`
- Use union types: `str | None` (Python 3.10+) or `Optional[str]`
- Use custom types: Pydantic models, dataclasses, enums
- Avoid `Any` except as last resort (document why)

### Type Examples
```python
from typing import Literal, Optional
from pydantic import BaseModel
from datetime import datetime

class Event(BaseModel):
    company_id: str
    session_id: str
    event_type: Literal["decision", "conflict", "execution", "outcome"]
    created_at: datetime
    payload: dict[str, Any]

async def process_event(
    event: Event,
    repo: EventRepository,
) -> Event | None:
    """Process event and return updated version or None if failed."""
    if not event.company_id:
        return None
    
    updated = await repo.update(event)
    return updated
```

## Docstrings Mandatory

### Rule: Every Public Function/Class Has a Docstring

âŒ **FORBIDDEN**:
```python
async def chat(self, message: str) -> dict:
    pass

class AIService:
    pass
```

âœ… **REQUIRED**:
```python
async def chat(self, message: str, company_id: str) -> dict[str, Any]:
    """
    Process chat message and return structured response.
    
    Args:
        message: User message text
        company_id: Company ID from auth token
    
    Returns:
        Dictionary with keys: logic_json, ceo_text, followup_question, meta
    
    Raises:
        InvalidCompanyID: If company_id is empty or invalid
        MemoryQueryFailed: If event repository is unavailable
    """
    pass

class AIService:
    """
    Orchestrator for AI reasoning engine and institutional memory.
    
    Manages OpenAI API calls, memory injection, event logging, and response
    generation. All operations are scoped to a single company.
    """
    
    def __init__(self, openai_key: str, event_repo: EventRepository) -> None:
        """
        Initialize AI service with required dependencies.
        
        Args:
            openai_key: OpenAI API key for authentication
            event_repo: Repository for storing decision events
        """
        pass
```

### Docstring Format
- Use triple-quoted strings (""")
- First line is a one-sentence summary
- Blank line separates summary from rest
- Use Args, Returns, Raises sections
- Keep docstrings concise (2-6 lines typical)
- No need to repeat parameter names

### When to Write Docstrings
- âœ… All public functions
- âœ… All public classes
- âœ… All async functions
- âœ… All service methods
- âŒ Private functions (prefixed with _) unless complex
- âŒ Simple getters/setters (self-explanatory names)
- âŒ Override methods that match parent signature

## Exception Handling

### Rule: Catch Specific Exceptions, Never Bare except

âŒ **FORBIDDEN**:
```python
try:
    result = await api.call()
except:
    pass

try:
    result = await db.fetch()
except Exception:
    raise HTTPException(status_code=500)
```

âœ… **REQUIRED**:
```python
try:
    result = await api.call()
except asyncio.TimeoutError:
    logger.warning(f"API call timed out for company {company_id}")
    raise
except openai.AuthenticationError as e:
    logger.error(f"Invalid OpenAI key: {e}")
    raise HTTPException(status_code=500, detail="LLM service unavailable")
except Exception as e:
    logger.error(f"Unexpected error calling API: {e}", exc_info=True)
    raise
```

### Exception Handling Rules
- Catch specific exception types
- Log the error with context (company_id, operation)
- Log full traceback with `exc_info=True` for unexpected errors
- Re-raise if you can't handle it
- Transform to HTTPException only at endpoint layer
- Never suppress exceptions silently

### Exception Hierarchy
```python
# app/core/errors.py

class AIServiceError(Exception):
    """Base exception for AI service failures."""
    pass

class InvalidCompanyID(AIServiceError):
    """Company ID validation failed."""
    pass

class MemoryQueryFailed(AIServiceError):
    """Event repository query returned no results."""
    pass

class LLMError(AIServiceError):
    """LLM API call failed."""
    pass

class TokenGenerationFailed(AIServiceError):
    """JWT token generation or validation failed."""
    pass
```

## Naming Conventions

### Module & File Names
- **Lowercase with underscores**: `event_log.py`, `openai_client.py`
- **Reflect contents**: `event_log.py` contains event logging logic
- **No abbreviations**: `openai_client` not `oai_cli`

### Class Names
- **PascalCase**: `AIService`, `EventRepository`, `ChatRequest`
- **Nouns or roles**: `Repository`, `Service`, `Manager`, `Handler`
- **No redundant prefixes**: `EventRepository` not `EventRepositoryClass`

### Function Names
- **snake_case**: `create_token`, `validate_request`, `inject_memory`
- **Verb + object**: `get_events`, `insert_event`, `build_prompt`
- **Question form for boolean**: `is_valid`, `has_permission`, `should_retry`
- **Avoid single letters**: `request` not `r`, `company_id` not `c`

### Variable Names
- **snake_case**: `company_id`, `session_id`, `event_type`
- **Descriptive**: `memory_context` not `mc`, `llm_response` not `resp`
- **Consistent across codebase**: Use `company_id` everywhere (not `cid`, `company`, `tenant`)
- **Boolean prefixes**: `is_valid`, `has_events`, `should_cache`

### Constant Names
- **UPPER_SNAKE_CASE**: `JWT_ALGORITHM`, `TOKEN_EXPIRY_HOURS`, `MAX_RETRIES`
- **Module-level only**: Define at top of file
- **Used for values that never change**

### Examples
```python
# Good naming
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

class EventRepository:
    async def get_recent_events(self, company_id: str, limit: int = 50) -> list[Event]:
        pass
    
    async def insert_event(self, event: Event) -> Event:
        pass

async def validate_company_authorization(
    request_company_id: str,
    token_company_id: str,
) -> bool:
    """Check if request company matches authenticated company."""
    return request_company_id == token_company_id

# Bad naming (avoid)
def cie(rid, tid):  # Abbreviations unclear
    pass

def get(cid):  # Too generic
    pass

class Handler:  # Too generic, doesn't describe purpose
    pass
```

## Response Formatting Standards

### Rule: Pydantic Models for All Responses

âŒ **FORBIDDEN**:
```python
@router.post("/ai/chat")
async def chat_endpoint(request: ChatRequest):
    result = await ai_engine.chat(...)
    return result  # Raw dict, unstructured

@router.get("/events")
async def list_events(company_id: str):
    events = await repo.get_all(company_id)
    return events  # List of dicts, no validation
```

âœ… **REQUIRED**:
```python
# app/models/response.py

class LogicJSON(BaseModel):
    context_lock: dict[str, Any]
    problem_classification: dict[str, Any]
    truth_validation: dict[str, Any]
    root_cause_engine: dict[str, Any]
    solution_generator: dict[str, Any]
    execution_engine: dict[str, Any]

class Meta(BaseModel):
    company_id: str
    session_id: str
    context: dict[str, Any]
    parse_ok: bool
    memory_injected: bool
    events_count: int

class ChatResponse(BaseModel):
    logic_json: LogicJSON
    ceo_text: str
    followup_question: str | None
    meta: Meta

# Usage
@router.post("/ai/chat")
async def chat_endpoint(request: ChatRequest):
    result = await ai_engine.chat(...)
    # âœ… Returns ChatResponse (validated, serializable)
    return result
```

### Response Model Rules
- Define models in `app/models/response.py`
- Inherit from `pydantic.BaseModel`
- Use `|` for optional (Python 3.10+) or `Optional`
- Use `model_validate()` to convert dicts to models
- Models are automatically serialized to JSON by FastAPI

### Pagination Response
```python
class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool
```

### Error Response
```python
class ErrorResponse(BaseModel):
    error: str
    detail: str
    request_id: str | None
    timestamp: datetime
```

## API Versioning Rules

### Versioning Strategy
- New endpoints go to `/v2/` namespace
- Old endpoints stay at `/` or `/v1/` and are deprecated
- Database schema versioning handled separately via migrations

### Version Structure
```python
# app/api/v1/chat.py
@router.post("/chat")
async def chat_v1(request: ChatRequest) -> ChatResponseV1:
    pass

# app/api/v2/chat.py (future)
@router.post("/chat")
async def chat_v2(request: ChatRequestV2) -> ChatResponseV2:
    pass

# In main.py
app.include_router(v1_router, prefix="/v1", tags=["chat"])
app.include_router(v2_router, prefix="/v2", tags=["chat"])
```

### Backwards Compatibility
- Never modify existing request/response models (breaks clients)
- Create new versions instead
- Maintain old versions for 6 months minimum
- Communicate deprecation in logs and docs

## File Naming Rules

### Python Files
- **snake_case**: `event_log.py`, `openai_client.py`
- **Singular nouns**: `event_log.py` not `events_log.py`
- **Verb nouns for actions**: `event_log.py` (logs events)
- **One class per file is acceptable**: `AIService` in `openai_client.py`

### Test Files
- **Prefix with test_**: `test_auth_request.py`, `test_openai_client.py`
- **Mirror module name**: Tests for `event_log.py` go in `test_event_log.py`
- **Keep in same folder or tests/**: Choose one pattern and be consistent

### Configuration Files
- **.env**: Environment variables (root level)
- **requirements.txt**: Python dependencies
- **pyproject.toml**: Project metadata (future)
- **.gitignore**: Files to exclude from git

## Line Length & Formatting

### Line Length
- **Maximum 100 characters** per line
- Exceptions: URLs, long strings (unavoidable)
- Break long lines using implicit line continuation

### Long Lines
```python
# âŒ TOO LONG
response = await ai_engine.chat(session_id=request.session_id, message=request.message, context=request.context, company_id=auth_context.company_id)

# âœ… CORRECT: Break at sensible points
response = await ai_engine.chat(
    session_id=request.session_id,
    message=request.message,
    context=request.context,
    company_id=auth_context.company_id,
)
```

### Formatting Style
- Use **4 spaces** for indentation (Python standard)
- **No tabs**: Only spaces
- **Blank line** between methods in a class
- **Blank line** between functions at module level

## Comments

### When to Write Comments
- âœ… Non-obvious business logic
- âœ… Workarounds for specific bugs or framework quirks
- âœ… Performance trade-offs or limitations
- âŒ Repeating what the code obviously does
- âŒ Commenting out code (delete instead)

### Comment Style
```python
# âœ… Explains WHY, not WHAT
# Company_id from JWT is trusted; validate request against it
if request.company_id != auth_context.company_id:
    raise HTTPException(403)

# âŒ Stating the obvious
# Check if company_id matches
if request.company_id != auth_context.company_id:
    pass
```

### Docstring vs Comment
- **Docstrings** (triple quotes): Document public APIs
- **Comments** (#): Explain non-obvious implementation choices

## Imports Organization

### Import Order
1. Standard library: `import os`, `from datetime import datetime`
2. Third-party: `from fastapi import APIRouter`, `from pydantic import BaseModel`
3. Local: `from app.services.openai_client import AIService`

### Import Style
```python
# âœ… Correct
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.dependencies import get_auth_context

# âŒ Incorrect
from datetime import *
from fastapi import *
import app.core.config
from app.core.config import settings
from app.core.dependencies import *
```

## Variable Scope & Mutability

### Rule: Prefer Immutability

âŒ **FORBIDDEN**:
```python
# Mutable default argument
def process(config: dict = {}):
    config["new_key"] = "value"  # Modifies default!
    pass

# Global state
cache = {}

async def fetch(company_id: str):
    cache[company_id] = result  # Race conditions
    return cache[company_id]
```

âœ… **REQUIRED**:
```python
# Immutable default
def process(config: dict | None = None) -> dict:
    config = config or {}
    new_config = {**config, "new_key": "value"}
    return new_config

# Use dependency injection
class AIService:
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo  # Stored, not mutated
```

### Scope Rules
- Module-level variables must be constants (UPPER_SNAKE_CASE)
- No module-level mutable state (use classes instead)
- Pass dependencies via `__init__`, not globals
- Return new values; don't mutate inputs

## Async/Await Guidelines

### Rule: Mark All Async Functions with async def

```python
# âœ… Correct
async def fetch_events(company_id: str) -> list[Event]:
    events = await repo.get(company_id)
    return events

# Usage
result = await fetch_events("acme-corp")

# âŒ Wrong: Function is async but not marked
def fetch_events(company_id: str):  # Missing async
    events = await repo.get(company_id)  # SyntaxError
    return events
```

### Async Context Managers
```python
# âœ… Correct: Use async with
async with db.transaction() as tx:
    await tx.execute(query)
    await tx.commit()

# âŒ Wrong: Regular context manager on async operation
with db.transaction() as tx:  # Won't block properly
    await tx.execute(query)
```

## Testing Guidelines

### Test Structure
```python
# test_event_log.py

import pytest
from app.services.memory.event_log import log_event
from app.models.event import Event

class TestEventLogging:
    """Tests for event logging system."""
    
    @pytest.mark.asyncio
    async def test_log_event_stores_company_id(self):
        """Event logger includes company_id in stored events."""
        event = Event(
            company_id="acme-corp",
            event_type="decision",
            payload={"test": True},
        )
        
        result = await log_event(event)
        
        assert result.company_id == "acme-corp"
    
    @pytest.mark.asyncio
    async def test_log_event_raises_on_missing_company_id(self):
        """Event logger raises if company_id is empty."""
        event = Event(
            company_id="",
            event_type="decision",
            payload={},
        )
        
        with pytest.raises(InvalidCompanyID):
            await log_event(event)
```

### Test Naming
- **Test functions**: `test_<what_is_tested>`
- **Test classes**: `Test<Subject>`
- **Fixtures**: `@pytest.fixture`
- **Mark async**: `@pytest.mark.asyncio`
