# Atlas Home Supplies Demo

This backend-only demo seed creates a realistic AIMX tenant for investor and client demos.

## Local Setup

Use keyword retrieval locally unless pgvector is installed:

```powershell
RAG_RETRIEVAL_MODE=keyword
```

Set a local demo owner password before seeding:

```powershell
$env:DEMO_OWNER_PASSWORD="choose-a-local-demo-password"
```

Run the seed:

```powershell
python -m scripts.seed_demo
```

Run it again safely with reset:

```powershell
python -m scripts.seed_demo --reset
```

## Demo Tenant

- Company: Atlas Home Supplies
- Slug: `atlas-home-supplies`
- Owner email: `owner@atlas-demo.local`
- Departments: CEO, Sales, Finance, Marketing, Operations

The script uses the existing company bootstrap, department runtime, file ingestion, and RAG chunking paths. It does not require pgvector locally; embedding failures are allowed to degrade safely while keyword retrieval remains available.

## Suggested Flow

1. Login as the demo owner.
2. List departments.
3. Ask CEO AI a company-wide question without `department_id`.
4. Ask Sales, Finance, Marketing, or Operations AI with the matching `department_id`.
5. Ask questions from `sample_prompts.md`.
