# NAWA Demo Runbook

This runbook prepares a local NAWA demo for investor or client presentations. It assumes the Northstar Commercial Group demo tenant and local keyword retrieval mode.

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

6. Set the local demo owner password for the seed command:

   ```powershell
   $env:DEMO_OWNER_PASSWORD="password123"
   ```

Do not commit `.env` or real production passwords.

## 2. Environment Requirements

Required:

- Python environment with `requirements.txt` installed.
- Local PostgreSQL reachable through `DATABASE_URL`.
- Existing NAWA migrations applied.
- `RAG_RETRIEVAL_MODE=keyword` for local demo reliability.
- `DEMO_OWNER_PASSWORD=password123` set before seeding the local demo.

Optional:

- `OPENAI_API_KEY` if you want real model responses.
- Without a stable model key/network, use the frontend and Swagger to verify auth, API wiring, prepared prompts, and seeded company context.

Not required for this demo:

- n8n
- pgvector
- Pinecone
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

Safe reseed/reset:

```powershell
$env:DEMO_OWNER_PASSWORD="password123"
python -m scripts.seed_demo --reset
```

The seed creates:

- Company: `Northstar Commercial Group`
- Company slug: `northstar-commercial`
- Owner email: `owner@northstar-demo.local`
- Owner password: `password123`
- Departments: CEO, Sales, Finance, Marketing, Operations
- Demo memory facts and events
- Curated demo files ingested through RAG

The reset flow is scoped to the Northstar demo tenant slug.

## 5. Frontend Login Flow

Open the frontend login page and use:

```text
Company slug: northstar-commercial
Email: owner@northstar-demo.local
Password: password123
```

Expected:

- Login succeeds.
- User lands in `/workspace`.
- CEO AI appears as the default workspace.
- Sales, Finance, Marketing, and Operations are available in the sidebar.
- KPI cards, demo reports, company files, and chat history are populated.

## 6. Swagger Login Flow

Swagger endpoint:

```text
POST /auth/login
```

Request body:

```json
{
  "email": "owner@northstar-demo.local",
  "password": "password123",
  "company_slug": "northstar-commercial"
}
```

Expected:

- `access_token`
- `refresh_token`
- `company`
- `user`
- `membership`

Then call:

```text
GET /auth/me
```

Expected:

- Company slug is `northstar-commercial`.
- User email is `owner@northstar-demo.local`.
- Role is the owner role.

## 7. Demo Prompts

Use `POST /ai/chat` without `department_id` for CEO AI.

CEO AI prompts:

- Give me the CEO briefing for this week: risks, priorities, and recommended actions.
- What should Northstar focus on before a NAWA investor demo?
- Summarize the top cross-department decisions we should make today.

Use `POST /ai/chat` with the matching department ID for department AI.

Sales AI prompts:

- Summarize the sales pipeline and highlight the best next actions.
- Which expansion accounts should Sales prioritize this month?
- What should Sales report to the CEO before the demo?

Finance AI prompts:

- Give me a finance briefing with cash, margin, and spending risks.
- Which costs should Finance review before the next planning meeting?
- What finance questions should the CEO ask today?

Marketing AI prompts:

- Summarize current marketing priorities and campaign opportunities.
- Which messages should Marketing emphasize for growth this month?
- What marketing proof points should we show in an investor demo?

Operations AI prompts:

- What fulfillment risks could block the expansion plan?
- Which commitments should Operations review before Sales sends proposals?

## 8. Expected Behavior Notes

Expected:

- CEO AI is selected when `department_id` is omitted.
- Department AI is selected when `department_id` is supplied.
- Responses keep the existing `/ai/chat` contract:
  - `ceo_text`
  - `logic_json`
  - `followup_question`
  - `meta`
- RAG snippets are injected internally as untrusted company knowledge.
- Keyword retrieval should work locally from seeded Northstar documents.
- Department prompts should use department-scoped files when possible.

Not expected:

- n8n workflow execution
- Avatar behavior
- Pinecone retrieval
- pgvector-only semantic search
- Response schema changes

## 9. Troubleshooting

### Login Fails

Check:

- Demo seed was run with `DEMO_OWNER_PASSWORD=password123`.
- `company_slug` is exactly `northstar-commercial`.
- Email is exactly `owner@northstar-demo.local`.
- Backend is running and reachable by the frontend.

### Swagger Returns 401

Check:

- The `Authorize` value starts with `Bearer `.
- The token is from the same local backend and company.
- You did not paste the refresh token instead of the access token.

### Departments Missing

Run:

```powershell
$env:DEMO_OWNER_PASSWORD="password123"
python -m scripts.seed_demo --reset
```

Then retry `GET /departments`.

### RAG Does Not Seem To Use Files

Check:

- `RAG_RETRIEVAL_MODE=keyword`
- Demo seed completed successfully.
- Your prompt contains a useful keyword such as `discount`, `margin`, `campaign`, `pipeline`, `capacity`, or `delivery`.

### pgvector Error Appears

Local demos should use:

```powershell
RAG_RETRIEVAL_MODE=keyword
```

Do not run pgvector-only flows locally unless pgvector is installed for the local PostgreSQL server.

## 10. Demo Safety Checklist

Before presenting:

- `.env` is local and not committed.
- `RAG_RETRIEVAL_MODE=keyword`.
- `DEMO_OWNER_PASSWORD=password123` is set for local demo seeding.
- Backend starts cleanly.
- `python -m scripts.seed_demo --reset` completes.
- Frontend login works.
- `POST /auth/login` works.
- `GET /auth/me` works.
- `GET /departments` returns CEO, Sales, Finance, Marketing, Operations.
- CEO AI works without `department_id`.
- Sales AI works with Sales `department_id`.
- Finance AI works with Finance `department_id`.
- Marketing AI works with Marketing `department_id`.
- Demo prompts are ready.
- No screenshots expose API keys, production credentials, or `.env` values.
