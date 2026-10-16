# M2.1 Preview deployment acceptance

## Target
- Git branch: `feature/m2-unified-content-tasks`
- Vercel project: `content-review-copilot-preview`
- Keep `main` unchanged; PR #2 remains a draft until product acceptance.

## Verify every pushed revision
1. Record the full Git commit SHA and GitHub Actions result.
2. In Vercel Deployments, filter by `content-review-copilot-preview`
   and verify the deployment metadata contains that SHA and this exact branch.
3. Wait for READY; BUILDING/QUEUED or a successful build check alone is not acceptance.
4. Open the deployment URL and verify that the React workspace renders.
5. Call `GET /api/health` and require HTTP 200 + `{"status":"ok"}`.
6. Exercise project/task/item/version creation and read-back through the API.
7. Reload and repeat the read-back after a fresh invocation. **Do not claim SQLite
   persistence on Vercel** unless storage is on a persistent shared database.
8. Review Vercel runtime logs and ensure APIs and frontend use the same origin.

## Storage blocker
Existing `ReviewStore` and `WorkspaceRepository` use
`data/history.sqlite3`. A packaged SQLite file on Vercel Functions is not a
shared, durable, writable database. Do not write into the deployment bundle or
use `/tmp` as if it survived a new invocation or redeployment.
A persistent managed database or durable hosted backend is required for
multi-request project and review-session acceptance.

## Scope and access
The project may use Vercel Authentication/SSO deployment protection. A READY
deployment is not by itself a publicly reachable acceptance URL. Validate both
authenticated browser access and requested API paths.

## Release gates
- GitHub Actions: Python + frontend all green.
- Vercel deployment metadata matches intended commit/branch.
- Browser page and API health verified.
- Durable create/read/reload tested on an external persistent store.
- No PR merges into `main` until acceptance.
