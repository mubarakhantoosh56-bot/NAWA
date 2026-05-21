# Render Backend

## Service

Use the root `render.yaml` blueprint to create the `nawa-backend` web service.

Render commands:

- Build: `pip install -r requirements.txt`
- Pre-deploy: `python scripts/migrate.py`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`

## Environment Variables

Required for staging/production:

- `DATABASE_URL`: Neon pooled or direct PostgreSQL URL, including `sslmode=require`
- `OPENAI_API_KEY`: OpenAI API key for NAWA intelligence features
- `DEMO_OWNER_PASSWORD`: private demo password used by `scripts/seed_demo.py`
- `FRONTEND_URL`: Vercel frontend origin, for example `https://nawa-staging.vercel.app`
- `ENVIRONMENT`: `staging`
- `JWT_SECRET_KEY`: long random signing secret for auth tokens

Optional:

- `CORS_ORIGINS`: comma-separated override when more than one frontend origin is needed
- `EMBEDDING_MODEL`: defaults to `text-embedding-3-small`
- `EMBEDDING_DIMENSIONS`: defaults to `1536`
- `RAG_RETRIEVAL_MODE`: defaults to `semantic`

## Startup Safety

When `ENVIRONMENT` is `staging` or `production`, the backend validates required env vars and the PostgreSQL URL before serving traffic. Startup errors are logged with readable messages in Render logs.
