# Migration notes

- `app.py` is retained as a deprecated internal/diagnostic Streamlit client. Product development moves to `frontend/`.
- Working Python domain modules were not rewritten in TypeScript.
- A thin FastAPI adapter in `api/` owns workflow state, UI mappings, persistence and export.
- Product responses use dedicated view models; raw `PipelineResult`, provider details and traces are returned only by the developer endpoint.
- The five requested Figma image assets are not present in the repository. Add them under `docs/figma/` for pixel-level visual comparison.

