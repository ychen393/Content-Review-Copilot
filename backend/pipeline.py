from __future__ import annotations

import time
from pathlib import Path
from .generators import FullRewriteGenerator, StagedRewriteGenerator
from .finalization import FinalEvaluator, ResultAssembler
from .models import ContentInput, Diagnosis, Issue, PipelineResult, ReviewPolicy, TraceEntry
from .policy import PolicyRuleEvaluator, ReviewPolicyBuilder, SoftRuleEvaluator
from .providers import configured_provider
from .repositories import JsonRepository, KnowledgeRetriever, RuleRetriever
from .rules import DeterministicRuleEngine
from .services import (ContentParser, CoreContentEvaluator, ContextResolver, EndingEvaluator, GenerationRouter, InputParser, OpeningEvaluator, PersonaEvaluator, RewritePlanner, VisionAnalyzer)
from .validation import RewriteQualityValidator


class TraceRecorder:
    def __init__(self) -> None:
        self.entries: list[TraceEntry] = []

    def run(self, step: str, value, fn):
        start = time.perf_counter()
        try:
            output = fn(value)
            self.entries.append(TraceEntry(step=step, input_summary=str(value)[:160], output_summary=str(output)[:200], latency_ms=(time.perf_counter() - start) * 1000, status="success"))
            return output
        except Exception as error:
            self.entries.append(TraceEntry(step=step, input_summary=str(value)[:160], output_summary="", latency_ms=(time.perf_counter() - start) * 1000, status="failed", error=str(error)))
            raise


class ContentQAPipeline:
    def __init__(self, data_dir: str | Path = "data", provider=None) -> None:
        repository = JsonRepository(data_dir)
        self.provider = provider or configured_provider()
        self.rules = RuleRetriever(repository)
        self.knowledge = KnowledgeRetriever(repository)
        self.input_parser = InputParser()
        self.context = ContextResolver()
        self.cleaner = DeterministicRuleEngine()

    def run(self, raw: dict | ContentInput, accepted_issue_ids: list[str] | None = None) -> PipelineResult:
        trace = TraceRecorder()
        content = trace.run("Input Parsed", raw, lambda value: value if isinstance(value, ContentInput) else self.input_parser.parse(value))
        policy = trace.run("Review Policy Built", content, lambda value: ReviewPolicy.model_validate(value.review_policy) if value.review_policy else ReviewPolicyBuilder(self.rules.repository.data_dir).build(value))
        content.review_policy = policy.model_dump()
        resolved = trace.run("Context Resolved", content, lambda value: self.context.resolve(value))
        vision = trace.run("Vision Analysis", content.images, lambda value: VisionAnalyzer(self.provider).analyze(value))
        rules = trace.run("Rule Retrieval", content, lambda _: self.rules.compliance_rules())
        cleaned, replacements = trace.run("Hard Rule Check", content.original_text, lambda value: self.cleaner.clean(value, rules))
        parsed = trace.run("Content Parsing", cleaned, lambda value: ContentParser().parse(value, content.target_persona, content.content_language))
        diagnoses = {
            "opening": trace.run("Opening Evaluation", parsed.opening, lambda value: OpeningEvaluator(self.rules).evaluate(value, content.keyword, vision)),
            "core": trace.run("Core Evaluation", parsed.core_content, lambda value: CoreContentEvaluator(self.rules).evaluate(value, content.keyword, vision)),
            "ending": trace.run("Ending Evaluation", parsed.ending, lambda value: EndingEvaluator(self.rules).evaluate(value, content.keyword, vision)),
            "persona": trace.run("Persona Evaluation", parsed.persona, lambda _: PersonaEvaluator().evaluate(parsed, content.target_persona)),
        }
        policy_by_id = {rule.rule_id: rule for rule in policy.hard_rules + policy.soft_rules}
        linkage = {"keyword": "TR-KEYWORD-01", "structure": "QR-002", "persona": "QR-003", "product_fact": "PF-001", "image_text": "QR-006"}
        for diagnosis in diagnoses.values():
            for issue in diagnosis.issues:
                rule = policy_by_id.get(linkage.get(issue.issue_type, ""))
                if rule:
                    issue.rule_id, issue.rule_source, issue.rule_description = rule.rule_id, rule.source_name, rule.description
        initial_policy_results = trace.run("Policy Hard Rule Evaluation", cleaned, lambda value: PolicyRuleEvaluator().evaluate_hard(value, policy))
        policy_issues = []
        for item in initial_policy_results:
            if not item.passed and item.rule_id != "TR-KEYWORD-01":
                policy_issues.append(Issue(issue_id=f"policy_{item.rule_id}", issue_type="compliance", severity=item.severity, evidence=item.evidence, explanation=item.message, suggestion="Remove or correct the expression that violates this rule.", rule_id=item.rule_id, rule_source=item.source, rule_description=item.message))
        diagnoses["policy"] = Diagnosis(issues=policy_issues, suggestions=[x.suggestion for x in policy_issues], passed=not policy_issues)
        plan = trace.run("Rewrite Planning", diagnoses, lambda value: RewritePlanner().build(value, content, replacements, accepted_issue_ids))
        route = trace.run("Generation Routing", content.content_type, lambda value: GenerationRouter().route(value))
        context = self.knowledge.context(content.content_type, content.sub_direction)
        context["images"] = [item.model_dump() for item in vision]
        generator = FullRewriteGenerator(self.provider) if route == "full" else StagedRewriteGenerator(self.provider)
        generated = trace.run("Content Generation", route, lambda _: generator.generate(content, parsed, plan, context))
        final_text, final_fixes = self.cleaner.clean(generated.text, rules)
        for policy_rule in policy.hard_rules:
            for banned_term in policy_rule.banned_terms:
                final_text = final_text.replace(banned_term, "")
        original_issue_ids = [issue.issue_id for diagnosis in diagnoses.values() for issue in diagnosis.issues]
        target_issue_ids = accepted_issue_ids if accepted_issue_ids is not None else original_issue_ids

        def validate_rewrite(text: str):
            rewritten = ContentParser().parse(text, content.target_persona, content.content_language)
            after = {
                "opening": OpeningEvaluator(self.rules).evaluate(rewritten.opening, content.keyword, vision),
                "core": CoreContentEvaluator(self.rules).evaluate(rewritten.core_content, content.keyword, vision),
                "ending": EndingEvaluator(self.rules).evaluate(rewritten.ending, content.keyword, vision),
                "persona": PersonaEvaluator().evaluate(rewritten, content.target_persona),
            }
            remaining = [issue.issue_id for diagnosis in after.values() for issue in diagnosis.issues]
            final_policy_results = PolicyRuleEvaluator().evaluate_hard(text, policy)
            remaining.extend(f"policy_{item.rule_id}" for item in final_policy_results if not item.passed and item.rule_id != "TR-KEYWORD-01")
            introduced = [issue_id for issue_id in remaining if issue_id not in original_issue_ids]
            return RewriteQualityValidator().validate(content, text, target_issue_ids, remaining, final_fixes, introduced)

        validation = trace.run("Rewrite Validation", final_text, validate_rewrite)
        if not validation.passed:
            failures = []
            if not validation.accepted_suggestions_applied: failures.append("accepted suggestions were not fully applied")
            if validation.target_issues_resolved < validation.target_issues_total: failures.append("target issues remain unresolved")
            if not validation.keyword_pass: failures.append("the required keyword is missing")
            if not validation.hard_rule_pass: failures.append("a hard rule failed")
            if not validation.fact_preservation_pass: failures.append("verified facts were not preserved")
            if not validation.meaningful_change: failures.append("the rewrite remained too similar to the source")
            if validation.new_issues: failures.append("new issues were introduced: " + ", ".join(validation.new_issues))
            feedback = "The previous rewrite failed because " + "; ".join(failures) + ". Rewrite once more while preserving factual meaning."
            generated = trace.run("Content Generation Retry", route, lambda _: generator.generate(content, parsed, plan, context, feedback=feedback))
            final_text, final_fixes = self.cleaner.clean(generated.text, rules)
            for policy_rule in policy.hard_rules:
                for banned_term in policy_rule.banned_terms:
                    final_text = final_text.replace(banned_term, "")
            validation = trace.run("Rewrite Validation Retry", final_text, validate_rewrite)
            validation.retried = True
        evaluation = FinalEvaluator().evaluate(final_text, content.keyword, final_fixes, not diagnoses["core"].issues, diagnoses["persona"].passed, sum(item.latency_ms for item in trace.entries), len(final_text.split()))
        evaluation.review_policy_id = policy.policy_id
        evaluation.rule_results = PolicyRuleEvaluator().evaluate_hard(final_text, policy) + SoftRuleEvaluator(self.provider).evaluate(final_text, policy)
        trace.entries.append(TraceEntry(step="Final Evaluation", input_summary=generated.text[:160], output_summary=str(evaluation.model_dump())[:200], latency_ms=0, status="success"))
        tags = list(dict.fromkeys(tag if tag.startswith("#") else f"#{tag}" for tag in generated.tags))
        report = {"route": generated.route, "issues_found": [issue.model_dump() for diagnosis in diagnoses.values() for issue in diagnosis.issues], "hard_rule_fixes": [item.model_dump() for item in replacements + final_fixes], "generation_changes": generated.changes}
        report["rewrite_validation"] = validation.model_dump()
        report["review_policy_id"] = policy.policy_id
        report["provider"] = {"name": self.provider.provider_name, "model": self.provider.model, "mode": self.provider.mode}
        return ResultAssembler().assemble(generated, final_text, tags, report, parsed, vision, diagnoses, evaluation, trace.entries, validation, policy)
