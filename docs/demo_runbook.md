# AIMX Demo Runbook

This runbook prepares a local backend-only AIMX demo for investor or client presentations. It assumes the Atlas Home Supplies demo tenant and local keyword retrieval mode.

## 1. Local Setup Steps

1. Open a terminal in the project root.
2. Activate the project Python environment if you use one.
3. Install dependencies if needed:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Confirm PostgreSQL is running and `DATABASE_URL` is configured in local `.env`.
5. Set local retrieval mode to keyword:

   ```powershell
   RAG_RETRIEVAL_MODE=keyword
   ```

6. Set a local-only demo owner password for the seed command:

   ```powershell
   $env:DEMO_OWNER_PASSWORD="choose-a-local-demo-password"
   ```

Do not commit `.env` or real passwords.

## 2. Environment Requirements

Required:

- Python environment with `requirements.txt` installed.
- Local PostgreSQL reachable through `DATABASE_URL`.
- Existing AIMX migrations `001` through `004` applied.
- `RAG_RETRIEVAL_MODE=keyword` for local demo reliability.
- `DEMO_OWNER_PASSWORD` set only in the current shell before seeding.

Optional:

- `OPENAI_API_KEY` if you want real model responses.
- Without a stable model key/network, use Swagger to verify API wiring and prepared prompts, or run backend smoke tests with fake clients.

Not required for this demo:

- pgvector
- Pinecone
- frontend
- avatars
- background workers

## 3. Start Backend

Start the backend from the project root:

```powershell
python run.py
```

If your local workflow uses Uvicorn directly:

```powershell
python -m uvicorn app.main:app --reload
```

Default Swagger URL:

```text
http://localhost:8000/docs
```

## 4. Run Demo Seed

First seed:

```powershell
python -m scripts.seed_demo
```

Safe reseed/reset:

```powershell
python -m scripts.seed_demo --reset
```

The seed creates:

- Company: `Atlas Home Supplies`
- Company slug: `atlas-home-supplies`
- Owner email: `owner@atlas-demo.local`
- Departments: CEO, Sales, Finance, Marketing, Operations
- Demo memory facts
- Curated demo files ingested through RAG

The reset flow is scoped to the demo tenant slug.

## 5. Swagger Usage Steps

Open:

```text
http://localhost:8000/docs
```

Use this order:

1. `POST /auth/login`
2. Copy the returned `access_token`.
3. Click Swagger `Authorize`.
4. Enter:

   ```text
   Bearer <access_token>
   ```

5. Use `GET /departments` to copy department IDs.
6. Use `POST /ai/chat` for CEO and department AI demos.

## 6. Demo Login Flow

Swagger endpoint:

```text
POST /auth/login
```

Request body:

```json
{
  "email": "owner@atlas-demo.local",
  "password": "<your local DEMO_OWNER_PASSWORD>",
  "company_slug": "atlas-home-supplies"
}
```

Expected:

- `access_token`
- `refresh_token`
- `company`
- `user`
- `membership`

Do not paste real credentials into documentation, chat, screenshots, or tickets.

## 7. CEO AI Demo Prompts

Use `POST /ai/chat` without `department_id`.

Body shape:

```json
{
  "company_id": "<company_id>",
  "session_id": "demo-ceo-001",
  "message": "Given our current constraints, what should Atlas Home Supplies prioritize in the next 30 days?",
  "context": {
    "stage": "Growing SME",
    "size": "42 employees",
    "industry": "Retail and light distribution",
    "resources": "Limited marketing budget and Amman-focused delivery capacity"
  }
}
```

Prompts:

- Given our current constraints, what should Atlas Home Supplies prioritize in the next 30 days?
- Create a 90-day execution plan to grow B2B revenue by 25 percent.
- Which department owns each part of the B2B expansion plan?

## 8. Sales AI Demo Prompts

Use `POST /ai/chat` with the Sales department ID from `GET /departments`.

Prompts:

- Build a weekly outreach plan for hotel and restaurant accounts.
- Which sales actions should we take this week to support the 25 percent revenue goal?
- How should Sales handle discount requests above 8 percent?

Expected Sales AI focus:

- Pipeline
- Outreach
- Discovery calls
- Sample orders
- Discount escalation to Finance

## 9. Finance AI Demo Prompts

Use `POST /ai/chat` with the Finance department ID.

Prompts:

- Can we afford the proposed marketing campaign?
- What budget guardrails should Sales and Marketing follow?
- What financial risks could block the 90-day growth target?

Expected Finance AI focus:

- 4,000 JOD monthly marketing budget
- 28 percent gross margin target
- Discount limits
- Cash flow and payment terms

## 10. Marketing AI Demo Prompts

Use `POST /ai/chat` with the Marketing department ID.

Prompts:

- Create a campaign plan for hotels and restaurants in Amman.
- Which channels should we use based on the current marketing budget?
- What KPIs should Marketing track weekly?

Expected Marketing AI focus:

- LinkedIn outreach
- WhatsApp follow-up
- Case-study posts
- Landing page
- Qualified visits, replies, bookings, and cost per lead

## 11. Expected Behavior Notes

Expected:

- CEO AI is selected when `department_id` is omitted.
- Department AI is selected when `department_id` is supplied.
- Responses keep the existing `/ai/chat` contract:
  - `ceo_text`
  - `logic_json`
  - `followup_question`
  - `meta`
- RAG snippets are injected internally as untrusted company knowledge.
- Keyword retrieval should work locally from seeded demo files.
- Department prompts should use department-scoped files when possible.

Not expected:

- Avatar behavior
- Frontend UI behavior
- Pinecone retrieval
- pgvector-only semantic search
- Response schema changes

## 12. Troubleshooting

### Login Fails

Check:

- Demo seed was run.
- Password matches the shell value used for `DEMO_OWNER_PASSWORD`.
- `company_slug` is exactly `atlas-home-supplies`.

### Swagger Returns 401

Check:

- The `Authorize` value starts with `Bearer `.
- The token is from the same local backend and company.
- You did not paste the refresh token instead of the access token.

### Departments Missing

Run:

```powershell
python -m scripts.seed_demo --reset
```

Then retry `GET /departments`.

### RAG Does Not Seem To Use Files

Check:

- `RAG_RETRIEVAL_MODE=keyword`
- Demo seed completed successfully.
- Your prompt contains a useful keyword such as `discount`, `budget`, `campaign`, `B2B`, or `delivery`.

### pgvector Error Appears

Local demos should use:

```powershell
RAG_RETRIEVAL_MODE=keyword
```

Do not run migration `005` locally unless pgvector is installed for the local PostgreSQL server.

### Model Call Fails

Check:

- `OPENAI_API_KEY` is configured locally.
- Network access is available.
- For offline demo rehearsal, validate backend flow with smoke tests and prepared prompts.

## 13. Keyword vs Semantic Retrieval Note

For local demos, use keyword retrieval.

Keyword mode:

- Does not require pgvector.
- Uses existing PostgreSQL keyword matching.
- Works with the seeded Atlas documents.
- Is the recommended local investor/client demo mode.

Semantic mode:

- Requires pgvector migration and extension readiness.
- Should be enabled only after local PostgreSQL supports `CREATE EXTENSION vector`.
- Is not required for the Atlas demo runbook.

## 14. Demo Safety Checklist

Before presenting:

- `.env` is local and not committed.
- `RAG_RETRIEVAL_MODE=keyword`.
- `DEMO_OWNER_PASSWORD` is set only in the local shell.
- Backend starts cleanly.
- `python -m scripts.seed_demo --reset` completes.
- Login works in Swagger.
- `GET /departments` returns CEO, Sales, Finance, Marketing, Operations.
- CEO AI works without `department_id`.
- Sales AI works with Sales `department_id`.
- Finance AI works with Finance `department_id`.
- Marketing AI works with Marketing `department_id`.
- Demo prompts are ready.
- No screenshots expose tokens, passwords, API keys, or `.env` values.
