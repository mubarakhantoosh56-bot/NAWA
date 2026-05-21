# NAWA Deployment Notes

This folder covers the first private staging deployment:

- Frontend: Vercel
- Backend: Render
- PostgreSQL: Neon

The deployment keeps the existing NAWA runtime behavior intact. The only startup guard added for staging/production is configuration validation so missing secrets, invalid PostgreSQL URLs, or missing CORS origins fail loudly during boot.

Use `docs/deployment/first_deploy_checklist.md` as the source of truth for the first staging pass.
