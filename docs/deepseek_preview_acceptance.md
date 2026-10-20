# DeepSeek Preview acceptance

Configuration (Vercel Preview secrets only): LLM_PROVIDER=deepseek, LLM_MODEL=deepseek-chat, LLM_BASE_URL=https://api.deepseek.com, LLM_API_KEY=<secret>, DATABASE_URL=<secret>.

## Checks
1. GET /api/models/status reports mode=live and model=deepseek-chat. This confirms *configuration presence only*.
2. POST /api/projects; POST /api/tasks (mode=generate, Brief required).
3. POST /api/tasks/{id}/generate-one with request_key UUID and auto_review=true. Verify non-Mock provider, saved text, version=1, and linked first review.
4. Reload project/task/items, ensure same IDs and review records still exist.
5. Repeat the same request_key and ensure the exact same item ID returns. Do not test a new key unless intending a new billable call.
6. Redeploy Preview and re-read the same project/item/session; verify durability.

Never put actual API keys in requests, screenshots or issue reports. Avoid using real client briefs until authorization and access controls are completed. CI and Vercel READY alone do not prove live inference or data durability.
