# NAWA AI Agent Workflow

This document guides how AI agents (Claude) should modify the NAWA codebase safely, efficiently, and in alignment with architecture.

## Before You Start

### Read These First
1. **NAWA_AI_CONTEXT.md** â€” Understand the vision, multi-tenancy model, and memory system
2. **ARCHITECTURE_RULES.md** â€” Know the non-negotiable structural rules
3. **CODING_STANDARDS.md** â€” Follow the typing, naming, and style guidelines
4. **This file** â€” How to apply these rules when modifying code

### Principles
- **Safety First**: Never compromise tenant isolation or auth
- **Minimal Change**: Only modify code necessary for the task
- **Backwards Compatible**: Don't break existing APIs without versioning
- **Testable**: All changes are testable without major test infrastructure
- **Auditable**: Every commit has a clear purpose and message

## Feature Development Workflow

### Step 1: Understand the Request

The user describes what needs to be built:
- âœ… "Add a new endpoint to fetch company events"
- âœ… "Implement memory pruning to remove old events"
- âŒ "Refactor everything to use dependency injection" (too broad)

### Step 2: Design Before Implementation

Before writing code, design the solution:

```
User: "Add endpoint to fetch recent events for a company"

AI Design (before coding):
1. Create EventResponse Pydantic model with event schema
2. Add GET /events endpoint that:
   - Requires JWT auth (AuthContext dependency)
   - Validates company_id matches token
   - Calls event_repo.get_recent(company_id, limit=100)
   - Returns paginated response
3. Add event_repo.get_recent() method if not exists
4. Update requirements.txt if new dependencies added
5. Test with curl or test script

Architecture Notes:
- Endpoint only parses request, validates auth, delegates to service
- Repository owns all DB queries
- Response must be a Pydantic model
- Company_id filtering mandatory
```

### Step 3: Implementation Checklist

Before starting code changes:
- [ ] Read the existing module containing related code
- [ ] Identify all files that need modification
- [ ] Plan the order (dependency-first: models â†’ repositories â†’ services â†’ routes)
- [ ] Verify no production files are modified unnecessarily

### Step 4: Implement Incrementally

Implement in dependency order:

1. **Models First**: Define request/response Pydantic models
2. **Repository Layer**: Add database access methods
3. **Service Layer**: Add business logic
4. **Route Handlers**: Add endpoints that use services
5. **Tests**: Write minimal tests to verify functionality

Example:
```python
# 1. Model
class EventResponse(BaseModel):
    id: str
    company_id: str
    event_type: str
    created_at: datetime

# 2. Repository method
async def get_recent(self, company_id: str, limit: int = 100) -> list[Event]:
    pass

# 3. Service method (if needed)
async def get_recent_events(self, company_id: str) -> list[EventResponse]:
    events = await self.event_repo.get_recent(company_id)
    return events

# 4. Route
@router.get("/events")
async def list_events(
    company_id: str,
    auth_context: AuthContext = Depends(get_auth_context),
) -> list[EventResponse]:
    if company_id != auth_context.company_id:
        raise HTTPException(403)
    return await ai_engine.get_recent_events(company_id)
```

## Refactoring Safely

### Rule: Refactor Only What's Required

âŒ **FORBIDDEN**:
```
User: "Fix the JWT auth bug"
AI: "I'll also refactor the entire service layer to use dependency injection
    and implement a new logging system and add caching..."
```

âœ… **REQUIRED**:
```
User: "Fix the JWT auth bug"
AI: "The JWT signature verification is failing because the token was
    generated with a different secret key. I'll:
    1. Check that JWT_SECRET_KEY is loaded correctly from .env
    2. Generate a fresh token using current settings
    3. Test with the fresh token
    
    No refactoring â€” just fixing the bug."
```

### When Refactoring is Acceptable

Refactoring is acceptable ONLY if:
1. **It's required for the feature**: You need to extract a function to avoid duplication
2. **It's in the same module**: Don't refactor unrelated modules
3. **It's backwards compatible**: Existing code still works
4. **It's limited scope**: Under 50 lines of actual logic changes

### Safe Refactoring Patterns

#### 1. Extract Method (Safe)
```python
# Before
class EventRepository:
    async def get_recent(self, company_id: str) -> list[Event]:
        query = "SELECT * FROM events WHERE company_id = $1 ORDER BY created_at DESC"
        rows = await self.pool.fetch(query, company_id)
        events = [Event.from_row(row) for row in rows]
        return events
    
    async def get_by_session(self, company_id: str, session_id: str) -> list[Event]:
        query = "SELECT * FROM events WHERE company_id = $1 AND session_id = $2"
        rows = await self.pool.fetch(query, company_id, session_id)
        events = [Event.from_row(row) for row in rows]
        return events

# After (acceptable refactoring)
class EventRepository:
    async def _rows_to_events(self, rows: list) -> list[Event]:
        """Convert database rows to Event models."""
        return [Event.from_row(row) for row in rows]
    
    async def get_recent(self, company_id: str) -> list[Event]:
        query = "SELECT * FROM events WHERE company_id = $1 ORDER BY created_at DESC"
        rows = await self.pool.fetch(query, company_id)
        return await self._rows_to_events(rows)
    
    async def get_by_session(self, company_id: str, session_id: str) -> list[Event]:
        query = "SELECT * FROM events WHERE company_id = $1 AND session_id = $2"
        rows = await self.pool.fetch(query, company_id, session_id)
        return await self._rows_to_events(rows)
```

#### 2. Add Type Hints (Safe)
```python
# Before
def validate_token(token):
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return payload

# After (acceptable)
def validate_token(token: str) -> Dict[str, Any]:
    """Validate and decode JWT token."""
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return payload
```

#### 3. Move Unused Code to Dead Branch (NOT SAFE)
```python
# âŒ DON'T DO THIS
# Dead code marker (reduces searchability, confuses future readers)
if False:  # Old implementation (removed)
    async def get_events_old(company_id):
        pass
```

## Feature Creation Process

### Example: Add Event Filtering by Event Type

**1. Design (user input â†’ AI understanding)**
```
User: "Let users filter events by type (decision, conflict, etc)"

Understand:
- New query parameter: ?event_type=decision
- New repository method: get_by_event_type(company_id, event_type)
- Updated endpoint: GET /events?event_type=decision&limit=100
- Validation: Ensure event_type is one of valid types
```

**2. Identify Files to Change**
```
- app/models/response.py: Add EventType enum (decision, conflict, execution, outcome)
- app/services/repository/event_repository.py: Add get_by_event_type method
- app/api/chat.py: Update /events endpoint to accept event_type parameter
- No changes to: security.py, config.py, main.py (unrelated)
```

**3. Implement in Order**
```python
# File 1: app/models/response.py
from enum import Enum

class EventType(str, Enum):
    DECISION = "decision"
    CONFLICT = "conflict"
    EXECUTION = "execution"
    OUTCOME = "outcome"

# File 2: app/services/repository/event_repository.py
async def get_by_event_type(
    self,
    company_id: str,
    event_type: EventType,
    limit: int = 100,
) -> list[Event]:
    """Retrieve events of a specific type for a company."""
    query = """
    SELECT * FROM events 
    WHERE company_id = $1 AND event_type = $2 
    ORDER BY created_at DESC 
    LIMIT $3
    """
    rows = await self.pool.fetch(query, company_id, event_type.value, limit)
    return [Event.from_row(row) for row in rows]

# File 3: app/api/chat.py
@router.get("/events")
async def list_events(
    company_id: str,
    event_type: EventType | None = None,
    auth_context: AuthContext = Depends(get_auth_context),
) -> list[EventResponse]:
    """List events for a company, optionally filtered by type."""
    if company_id != auth_context.company_id:
        raise HTTPException(403)
    
    if event_type:
        events = await self.event_repo.get_by_event_type(company_id, event_type)
    else:
        events = await self.event_repo.get_recent(company_id)
    
    return events
```

**4. Test the Feature**
```bash
# Test without filter (existing behavior)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/events?company_id=acme-corp"

# Test with filter (new behavior)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/events?company_id=acme-corp&event_type=decision"

# Test invalid filter
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/events?company_id=acme-corp&event_type=invalid"
# Should return 422 Validation Error (Pydantic)
```

## Bug Debugging Process

### Find the Root Cause First

**Debugging JWT Token Issue:**
```
User: "JWT auth is failing with 'Signature verification failed'"

Steps:
1. Read error message carefully: "Signature verification failed"
   â†’ Token was signed with different key than verification key

2. Check token source:
   - Where was token generated?
   - What secret key was used?
   - What secret key is used for verification?

3. Verify settings are correct:
   - Read .env file
   - Check settings.JWT_SECRET_KEY is loaded correctly
   - Confirm token in test matches secret

4. Generate fresh token with current settings:
   ```python
   from app.core.security import create_token
   token = create_token("acme-corp", "user-456")
   ```

5. Test with fresh token:
   - Update test_auth_request.py with new token
   - Run test
   - Verify 200 response

6. Commit fix:
   - Only modified: test file, requirements.txt if deps changed
   - Message: "Fix JWT auth: use current SECRET_KEY for token generation"
```

### Common Issues & Solutions

#### Issue: 403 Unauthorized (Company ID Mismatch)
```python
# Problem:
# Token has company_id="acme-corp"
# Request has company_id="widgets-inc"

# Solution in endpoint:
if request.company_id != auth_context.company_id:
    raise HTTPException(
        status_code=403,
        detail="Unauthorized: company_id does not match token"
    )

# This is correct behavior (isolating tenants)
```

#### Issue: 401 Invalid Token (Expired)
```python
# Problem: Token was generated 25 hours ago (expires after 24)

# Solution: Generate fresh token
token = create_token("acme-corp", "user-456", expires_in_hours=24)

# Or adjust expiry if needed:
token = create_token("acme-corp", "user-456", expires_in_hours=72)
```

#### Issue: 500 Internal Server Error (Database)
```python
# Problem: Event repository query failed

# Debug steps:
1. Check database is running: psql postgresql://...
2. Check company_id filter is present in query
3. Check parameterized query (no string interpolation)
4. Log full error in catch block
5. Check database permissions for user

# Example fix:
async def get_recent(self, company_id: str) -> list[Event]:
    try:
        query = """
        SELECT * FROM events 
        WHERE company_id = $1 
        ORDER BY created_at DESC 
        LIMIT 50
        """
        rows = await self.pool.fetch(query, company_id)
        return [Event.from_row(row) for row in rows]
    except Exception as e:
        logger.error(f"DB error for company {company_id}: {e}", exc_info=True)
        raise MemoryQueryFailed(f"Could not fetch events: {e}")
```

## Testing Auth Flows

### Test 1: Valid Token, Valid Company

```bash
# Generate fresh token for acme-corp
TOKEN=$(python3 -c "
from app.core.security import create_token
print(create_token('acme-corp', 'user-456'))
")

# Make request with matching company_id
curl -X POST http://localhost:8000/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "acme-corp",
    "session_id": "session-123",
    "message": "Hello",
    "context": {}
  }'

# Expected: 200 OK with logic_json response
```

### Test 2: Valid Token, Wrong Company

```bash
TOKEN=$(python3 -c "
from app.core.security import create_token
print(create_token('acme-corp', 'user-456'))
")

# Request with different company_id than token
curl -X POST http://localhost:8000/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "widgets-inc",
    "session_id": "session-123",
    "message": "Hello",
    "context": {}
  }'

# Expected: 403 Forbidden with detail="Unauthorized company_id"
```

### Test 3: Invalid Token

```bash
# Missing Authorization header
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"company_id": "acme-corp", ...}'

# Expected: 403 Forbidden

# Invalid signature
curl -X POST http://localhost:8000/ai/chat \
  -H "Authorization: Bearer invalid.token.here" \
  -H "Content-Type: application/json" \
  -d '{"company_id": "acme-corp", ...}'

# Expected: 401 Unauthorized with detail="Invalid token"
```

## Database Migrations

### When to Create a Migration

- Adding a new table
- Adding a column to existing table
- Changing column type or constraints
- Adding indexes for performance

### Migration Process

**1. Create Migration File**
```bash
# Manually create migration file with timestamp
# migrations/001_add_company_events_table.sql

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    event_type VARCHAR(50),
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_company FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_events_company_id ON events(company_id);
CREATE INDEX idx_events_company_session ON events(company_id, session_id);
```

**2. Test Migration Locally**
```bash
# Connect to local database
psql postgresql://user:pass@localhost:5432/NAWA

# Run migration
\i migrations/001_add_company_events_table.sql

# Verify table
\dt events
SELECT * FROM events WHERE company_id = 'test-company';
```

**3. Update Repository**
```python
class EventRepository:
    async def insert_event(self, event: Event) -> Event:
        query = """
        INSERT INTO events (company_id, session_id, event_type, payload, created_at)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, company_id, session_id, event_type, payload, created_at
        """
        row = await self.pool.fetchrow(
            query,
            event.company_id,
            event.session_id,
            event.event_type,
            event.payload.model_dump_json() if hasattr(event.payload, 'model_dump_json') else str(event.payload),
            datetime.utcnow(),
        )
        return Event.from_row(row)
```

**4. Commit Changes**
```bash
git add migrations/001_add_company_events_table.sql
git add app/services/repository/event_repository.py
git commit -m "Add events table and repository methods

- Create events table with company_id isolation
- Add indexes on company_id and session_id
- Implement insert_event, get_recent, get_by_session methods"
```

## Production Safety Checklist

Before committing ANY changes, verify:

- [ ] **Auth boundary held**: No code bypasses JWT validation
- [ ] **Tenant isolation preserved**: All queries filter by company_id
- [ ] **Secrets not hardcoded**: All secrets from .env or settings
- [ ] **Type hints present**: All functions have type annotations
- [ ] **Docstrings present**: All public functions documented
- [ ] **Error handling correct**: Exceptions caught and logged
- [ ] **Async/await used**: No blocking I/O operations
- [ ] **No refactoring creep**: Only necessary changes included
- [ ] **Backwards compatible**: Existing APIs still work
- [ ] **Testable**: Can be tested without complex setup
- [ ] **Commit message clear**: Describes WHAT and WHY

## Git Workflow Rules

### Branching
- Branch name: `feature/event-filtering`, `fix/jwt-validation`, `refactor/service-layer`
- Avoid generic names: `fix1`, `changes`, `update`

### Commits
- **One logical change per commit**: Don't mix features in one commit
- **Atomic**: Each commit should be independently runnable
- **Traceable**: Future `git blame` should tell a story

### Commit Message Format
```
Short imperative summary (under 70 characters)

Longer explanation if needed (72 character wrap):
- What changed and why
- Not how (code shows that)
- Not what-was-wrong (git blame tells that)

Fixes: (if applicable)
Related-To: (if applicable)
```

### Examples

Good:
```
Add JWT auth and tenant isolation

- Create security.py with token generation/validation (HS256)
- Add dependencies.py for auth context injection
- Update chat endpoint to validate company_id against token
- Enforce isolation: all queries filtered by company_id

All protected endpoints now require valid JWT.
```

Bad:
```
Fix bug
Update files
Refactored code
Added stuff
```

## When to Ask the User

Before proceeding in these cases:

1. **Unclear requirements**: "Should this endpoint return paginated results or all events?"
2. **Architecture decision**: "Should we cache events in memory or always query DB?"
3. **Breaking change**: "This requires changing the request schema; is that OK?"
4. **Risky operation**: "This requires modifying the auth system; should I proceed?"
5. **Scope uncertainty**: "Should I also update the v2 API or just v1?"

## Code Review Checklist for AI Agents

When reviewing your own code before commit:

- [ ] **Architecture**: Code follows ARCHITECTURE_RULES.md
- [ ] **Style**: Code follows CODING_STANDARDS.md
- [ ] **Security**: No tenant isolation bypasses, no hardcoded secrets
- [ ] **Readability**: Clear naming, types, docstrings
- [ ] **Performance**: No N+1 queries, no blocking operations
- [ ] **Testing**: Can the change be tested?
- [ ] **Backward compatibility**: Does this break existing clients?
- [ ] **Error handling**: Are exceptions caught and logged?
- [ ] **Logging**: Can issues be debugged from logs?
- [ ] **Git history**: Is the commit message clear?

## Summary

**Safe, effective AI agent modifications follow this process:**

1. **Understand** the request thoroughly
2. **Design** the solution before coding
3. **Implement** in dependency order (models â†’ repos â†’ services â†’ routes)
4. **Test** the change (manually or with minimal test code)
5. **Review** against checklists
6. **Commit** with clear message and only necessary files
7. **Document** if the architecture or workflow changes

When in doubt, **ask the user** before making significant changes.
