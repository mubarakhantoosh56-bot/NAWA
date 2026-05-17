# Northstar Commercial Group Demo

This demo seed creates a realistic NAWA tenant for investor and client demos.

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

- Company: Northstar Commercial Group
- Slug: `northstar-commercial`
- Owner email: `owner@northstar-demo.local`
- Departments: CEO, Sales, Finance, Marketing, Operations

The script uses the existing company bootstrap, department runtime, file ingestion, memory events, and RAG chunking paths. It does not require pgvector locally; embedding failures are allowed to degrade safely while keyword retrieval remains available.

## Suggested Flow

1. Login as the demo owner.
2. Start with CEO AI and review the executive summary, KPI cards, reports, and chat history.
3. Move through Sales AI, Finance AI, and Marketing AI to show department-specific context.
4. Open Company Knowledge to show seeded operating files and reports.
5. Ask questions from `sample_prompts.md`.
