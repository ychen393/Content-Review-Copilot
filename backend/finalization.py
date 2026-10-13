from __future__ import annotations

from .models import Evaluation, GeneratedContent, PipelineResult


class FinalEvaluator:
    def evaluate(self, text: str, keyword: str, hard_rule_fixes: list, fact_consistency: bool, persona_alignment: bool, latency_ms: float, token_usage: int) -> Evaluation:
        return Evaluation(compliance_pass=not hard_rule_fixes, keyword_pass=not keyword or keyword in text, fact_consistency=fact_consistency, persona_alignment=persona_alignment, image_text_consistency=True, instruction_following=True, structure_quality=bool(text.strip()), latency_ms=latency_ms, token_usage=token_usage, estimated_cost=token_usage * 0.00001)


class ResultAssembler:
    def assemble(self, generated: GeneratedContent, final_text: str, tags: list[str], report: dict, parsed, vision, diagnoses, evaluation, trace, rewrite_validation, review_policy) -> PipelineResult:
        return PipelineResult(final_text=final_text, titles=generated.titles, tags=tags, report=report, preserved_nouns=generated.preserved_nouns, parsed=parsed, vision=vision, diagnoses=diagnoses, evaluation=evaluation, execution_trace=trace, rewrite_validation=rewrite_validation, review_policy=review_policy)
