# New Architecture

## Design

The application is a small layered Python service rather than a node-for-node workflow port. Pydantic schemas define boundaries; repositories provide local data; services orchestrate business behavior; the provider abstraction isolates model calls; Streamlit is only a presentation layer.

```text
InputParser -> ContextResolver -> retrieval services
                                  |\
                                  v \
VisionAnalyzer -> DeterministicRuleEngine -> ContentParser -> evaluators
                                                        -> RewritePlanner
                                                        -> GenerationRouter
                                             full ------> FullRewriteGenerator
                                             staged ----> StagedRewriteGenerator
                                                        -> FinalEvaluator
                                                        -> ResultAssembler
```

## Module mapping

- `InputParser` validates and normalizes user input.
- `VisionAnalyzer` turns images into explicit evidence through `LLMProvider.vision`.
- `ContextResolver` maps business stages, builds the RTB key, and assembles prompts.
- `RuleRetriever` reads issue and compliance data without exposing storage details.
- `KnowledgeRetriever` supplies RTB, knowledge, and reference material.
- `DeterministicRuleEngine` performs positional, longest-first banned-term replacement and logs every change.
- `ContentParser` segments source text without rewriting and identifies persona/style.
- `OpeningEvaluator`, `CoreContentEvaluator`, `EndingEvaluator`, and `PersonaEvaluator` perform independent semantic checks. Their output uses one structured diagnosis schema.
- `RewritePlanner` aggregates diagnoses, style DNA, retrieval context, and hard-rule changes into explicit plans.
- `GenerationRouter` selects full or staged generation from content type.
- `FullRewriteGenerator` creates one coherent article; `StagedRewriteGenerator` passes generated opening into core and both into ending/titles/tags.
- `FinalEvaluator` independently checks the generated result and tracks operational metrics.
- `ResultAssembler` merges route output, normalizes tags, preserves nouns, and exposes the report and execution trace.

## Data and extension points

Synthetic JSON files in `data/` replace internal tables. Repository classes accept a data directory and can later be replaced by database, API, or vector-store implementations without changing pipeline contracts. The provider interface similarly allows a hosted model adapter while tests use `MockLLMProvider`.

## Deterministic versus semantic checks

Required fields, required keywords, formatting, banned terms, and explicit product constraints are deterministic and run in `DeterministicRuleEngine` or `FinalEvaluator`. Persona alignment, style, image-text consistency, and writing quality are semantic evaluator concerns. The boundary is intentional: model output cannot bypass compliance.

## Observability and benchmark

`TraceRecorder` wraps each pipeline stage with input/output summaries, latency, status, and errors. The Streamlit UI renders the trace as a dedicated tab. The offline benchmark loads 30 synthetic JSONL cases and computes precision, recall, F1, pass rate, average latency, and estimated cost against issue IDs and expected pass flags.
