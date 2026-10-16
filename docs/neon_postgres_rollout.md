# Neon PostgreSQL rollout (M2.1.2)

## Configuration
Local dev and CI use SQLite if no `DATABASE_URL` is set.
The production/preview FastAPI service chooses PostgreSQL when `DATABASE_URL`
is set; never put connection strings in GitHub or frontend Vite env variables.

1. Create a Neon project in the preferred region.
2. Create a dedicated **preview database or Neon database branch** for
   `feature/m2-neon-persistence`; do not share production data.
3. In the Vercel project's **Preview** environment, set
   `DATABASE_URL` to the server-side Neon Postgres connection string.
   Prefer the pooling connection string suitable for serverless workload,
   with TLS enabled as Neon specifies.
4. Redeploy the feature branch after saving the environment variable.
5. Check `GET /api/health`, create a Project/Task/Item, then load them
   in a new browser session and after a fresh deployment.
6. Check `POST /api/items/{id}/review`, save review decisions, and
   inspect version history after reload.

## Architecture
- `api/database.py` adapts existing parameterized SQL calls for PostgreSQL.
- `api/workspace.py` persists projects/tasks/items/versions.
- `api/store.py` persists API review sessions.
- Local SQLite stays available to keep development and regression tests fast.
- The older standalone Streamlit `backend/history.py` still uses SQLite;
  it is not part of the Vercel FastAPI workspace storage guarantee.

## Migration and safety
Existing SQLite records are **not automatically copied** to Neon.
Do not cut over production data without an explicit backup and import plan.
Avoid connecting production and preview to the same database.
Database schema is created idempotently on repository initialization for MVP;
for later production use, introduce versioned migrations (e.g. Alembic).
Set Vercel variables only in the Vercel dashboard or authorized integration.
Do not log connection strings or put secrets in documentation.

## Unverified
Without an actual Neon `DATABASE_URL`, CI only verifies SQLite compatibility
and mocked PostgreSQL adapter behavior. Live Neon read/write, serverless cold
starts, Vercel route reachability, and cross-deployment persistence remain
acceptance gates, not completed facts.
