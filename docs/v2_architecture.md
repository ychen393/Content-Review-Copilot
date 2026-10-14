# M1 — Review/Generation Isolation

## Scope
This increment preserves the current FastAPI, React, SQLite, JSON rules and legacy
`ContentQAPipeline.run()` contract. It does **not** implement M2's Brief-driven creation
or Seed-style batch operations.

## Workflow
- First review: source → deterministic rule checks → content diagnosis → separate
  `semantic_review` call for soft rules (only with a live provider) → human decisions.
- Rewrite: accepted issues → generation → validation/retry.
- Second review: revised copy → deterministic and semantic review → human decisions.
- Finalize: existing finalization route; generating a new final is an explicit action.
- Every review session keeps its frozen policy snapshot.

## Provider contract
`generate()` is for rewritten copy. `semantic_review()` is a distinct
read-only model instruction with temperature 0, JSON array output, and strict
validation of rule IDs and boolean verdicts. Malformed/incomplete live responses
raise an error rather than silently passing rules.

In mock mode there is **no semantic verification**: soft rules are not
asserted passed. Rule results from real models still need independent
evaluation before trusting their accuracy.

## Known limitations
- The review-only path retains the original text for API compatibility and
  continues to construct the existing result schema.
- Existing deterministic cleanup is used internally for inspection; user source
  is returned unchanged in review-only mode.
- The legacy default `run()` pipeline still performs generation and post-generation
  evaluation. API review stages explicitly opt into review-only mode.
- There is no real-model integration benchmark, visual QA, or API cost proof.
- The underlying soft-rule evidence still depends on the provider.
- Do not automatically merge until local Python and frontend regression tests pass.

## Local verification
```bash
python -m pytest -q
cd frontend
npm test
npm run build
```

The upstream CI/VS Code run is required; the GitHub connector alone cannot
execute tests in the user's local environment.
