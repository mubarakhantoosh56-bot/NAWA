# First Private Staging Deploy Checklist

1. Create the Neon PostgreSQL database.
2. Copy the Neon connection string with `sslmode=require`.
3. Add Render backend env vars: `DATABASE_URL`, `OPENAI_API_KEY`, `DEMO_OWNER_PASSWORD`, `FRONTEND_URL`, `ENVIRONMENT`, and `JWT_SECRET_KEY`.
4. Deploy the Render backend from `render.yaml`.
5. Run migrations with `python scripts/migrate.py`.
6. Seed the demo tenant with `python scripts/seed_demo.py`.
7. Add Vercel frontend env var `NEXT_PUBLIC_AIMX_API_URL` with the Render backend URL.
8. Deploy the Vercel frontend from `frontend/`.
9. Test login with the seeded demo owner.
10. Verify file uploads.
11. Verify chat responses.
12. Verify the intelligence panel and department visibility.
13. Confirm Render `/health` returns `{"status":"ok"}`.
14. Confirm browser requests are accepted by CORS from the Vercel domain.
