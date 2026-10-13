# Original Workflow Analysis

## Original pipeline

The source workflow is a multimodal content review and rewriting pipeline for branded social content:

1. Normalize the three direction fields and keyword input.
2. Retrieve direction, sub-direction, keyword, issue, compliance, RTB, persona, and reference context.
3. Convert each supplied image into structured visual evidence.
4. Apply deterministic compliance substitutions to the source text.
5. Assemble stage-specific context and parse the cleaned content into title, opening, RTB/core, ending, and tags.
6. Match one configured persona and retrieve its style DNA.
7. Diagnose opening, RTB/core, and ending independently using checklists and image evidence.
8. Aggregate diagnoses into a rewrite plan.
9. Route `纯路人` to a full rewrite; route other content types to staged generation.
10. Merge generated content, normalize tags, run an independent final hard-rule review, and return a report.

## Node groups

| Business group | Source responsibilities | Rebuilt responsibility |
| --- | --- | --- |
| Input and mapping | Start fields, stage mapping, RTB type construction | `InputParser`, `ContextResolver` |
| Retrieval | Keyword, direction, sub-direction, issue, compliance, RTB, persona, knowledge, references | Repository-backed retrieval services |
| Evidence and cleaning | Image understanding and hard-rule replacement | `VisionAnalyzer`, `DeterministicRuleEngine` |
| Understanding | Content split and persona matching | `ContentParser`, `PersonaEvaluator` |
| Diagnosis | Opening, RTB, ending soft checks | `OpeningEvaluator`, `CoreContentEvaluator`, `EndingEvaluator` |
| Planning and routing | Diagnosis aggregation and selector | `RewritePlanner`, `GenerationRouter` |
| Generation | Full rewrite or sequential opening/core/ending generation | `FullRewriteGenerator`, `StagedRewriteGenerator` |
| Finalization | Merge, final scan, report, optional persistence | `FinalEvaluator`, `ResultAssembler` |

## Dependencies

The original graph depends on normalized input, repository lookups, visual evidence, and the cleaned source text. Diagnosis depends on parsed sections and assembled issue rules. Generation depends on the aggregated plan, persona DNA, retrieved knowledge/reference material, and prior generated sections in the staged branch. Finalization depends on generated output and the complete compliance rule set.

The standalone application replaces Feishu and private APIs with JSON repositories behind provider-like interfaces. An `LLMProvider` abstraction owns semantic generation, structured generation, and vision calls. `MockLLMProvider` makes the pipeline deterministic and testable without credentials.

## Branch logic

The router checks `content_type` after normalization:

- `纯路人` selects the full rewrite route. One generator receives the full plan and optional reference material.
- Any other value selects staged generation. Opening is generated first, then core content receives the generated opening, and ending/titles/tags receive both previous generated sections.

Both routes converge on the same final evaluator and result assembler. The original persistence side effect is intentionally optional in the standalone version.

## Input and output contracts

Input is normalized to direction stage, content type, sub-direction, keyword, original text, and zero or more images. Image input may be a path, URL, or descriptive string for the mock provider.

The parsed content contract contains `title`, `opening`, `core_content`, `ending`, `tags`, `persona`, and `content_style`. Each diagnosis returns `issues`, `suggestions`, and `passed`; issues carry an ID, type, severity, evidence, explanation, and suggestion.

The final contract preserves `final_text`, `report`, and `preserved_nouns`, and adds title/tag variants, evaluation scores, route, and an execution trace. Final evaluation covers compliance, keywords, factual consistency, persona alignment, image-text consistency, instruction following, and structure quality, plus latency, token usage, and estimated cost.
