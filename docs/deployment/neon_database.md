# Neon Database

## Create Database

Create a Neon project for private staging and copy the PostgreSQL connection string. Use a URL that includes SSL, for example:

```text
postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

Set that value as `DATABASE_URL` in Render.

## Extensions

The migrations enable required extensions, including `vector` for RAG embeddings. Confirm the selected Neon plan supports pgvector before first deploy.

## Migrations

Run migrations from the repo root:

```bash
python scripts/migrate.py
```

The Render blueprint also runs the same command as `preDeployCommand`.

## Demo Seed

After migrations complete, seed the private demo tenant:

```bash
python scripts/seed_demo.py
```

Set `DEMO_OWNER_PASSWORD` before running the seed command.
