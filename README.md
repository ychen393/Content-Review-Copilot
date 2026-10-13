# Multimodal Content QA & Optimization Agent

A standalone Python 3.11+ portfolio application for multimodal content diagnosis and optimization. It preserves the source workflow's business logic while replacing private data services with synthetic JSON repositories.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
python -m benchmark.runner
streamlit run app.py
```

The default provider is `MockLLMProvider`, so no API key is needed. The provider contract exposes `generate`, `structured_generate`, and `vision` for a future hosted-model adapter.

## Architecture

Typed Pydantic contracts connect `InputParser`, `VisionAnalyzer`, `ContextResolver`, `RuleRetriever`, `KnowledgeRetriever`, `DeterministicRuleEngine`, `ContentParser`, independent evaluators, `RewritePlanner`, `GenerationRouter`, full/staged generators, `FinalEvaluator`, and `ResultAssembler`. Hard constraints remain deterministic; semantic checks are isolated behind evaluator/provider boundaries.

The staged route passes generated opening into core generation and both prior sections into ending generation. Every pipeline step records a trace entry. The Streamlit app exposes Overview, Diagnosis, Vision Analysis, Rewrite Plan, Final Content, Evaluation, and Execution Trace tabs.

See [docs/original_workflow_analysis.md](docs/original_workflow_analysis.md) and [docs/new_architecture.md](docs/new_architecture.md) for the source graph and redesign mapping.
