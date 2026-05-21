# Vercel Frontend

## Project

Deploy the `frontend/` directory as the Vercel project root.

Vercel commands:

- Install: `npm install`
- Build: `npm run build`
- Output: managed by Next.js

## Environment Variables

Set this in Vercel for the staging environment:

- `NEXT_PUBLIC_AIMX_API_URL`: Render backend URL, for example `https://nawa-backend.onrender.com`

The frontend API client reads `NEXT_PUBLIC_AIMX_API_URL`, strips any trailing slash, and calls backend routes with absolute URLs. Keep the legacy env var name for now because the existing client already depends on it.

## Build Checks

Run these from `frontend/` before deployment:

- `npm run typecheck`
- `npm run lint`
- `npm run build`
