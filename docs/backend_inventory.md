# Backend inventory

| Capability | Existing module | Reusable | Required change |
| --- | --- | --- | --- |
| Input and pipeline contracts | `backend/models.py` | Yes | Add API/session view models without leaking backend enums to React. |
| Review policy snapshot | `backend/policy.py` | Yes | Freeze the built policy when a review session is created. |
| Deterministic hard rules | `backend/rules.py`, `backend/policy.py` | Yes | Expose mandatory issue semantics through API view models. |
| Semantic diagnosis | `backend/services.py` | Yes | Invoke through stage-specific API operations. |
| Rewrite generation | `backend/generators.py` | Yes | Call only from rewrite/finalize operations. |
| Rewrite quality gate | `backend/validation.py` | Yes | Extend with unsupported-claim checks and title/tag validation. |
| LLM abstraction | `backend/providers.py` | Yes | Mock remains default; real OpenAI-compatible provider is environment-driven. |
| Document parsing | `backend/documents.py` | Yes | API upload accepts txt, md, docx and pdf only. |
| Image handling | `backend/services.py` (`VisionAnalyzer`) | Partly | API currently records filenames; binary image persistence is a later hardening item. |
| Result assembly/evaluation | `backend/finalization.py` | Yes | Map to product-facing response objects. |
| Suggestion decisions | `backend/models.py` | Yes | Persist first- and second-review decisions per session. |
| History/version persistence | `backend/history.py` | Yes | Add workflow snapshot storage so old sessions reopen with their frozen policy. |
| Word export | Existing Streamlit implementation | Partly | Move DOCX creation behind an API endpoint. |
| Benchmark and execution trace | `benchmark/`, `PipelineResult.execution_trace` | Yes | Developer mode only. |
| Automated tests | `tests/` | Yes | Add API, workflow, unsupported-fact and export coverage. |

## Current constraints

- The existing `ContentQAPipeline.run()` performs diagnosis and generation in one call. The API isolates product stages and does not return generated copy from first review, but a deeper backend split is still desirable so first review performs no generation work at all.
- No approved Figma PNG files were present in `docs/figma/` when implementation began. The React screens follow the supplied F01–F05 written specification.

