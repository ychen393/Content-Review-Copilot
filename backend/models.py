from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class CustomReviewRule(BaseModel):
    rule_id: str
    name: str
    description: str
    type: Literal["hard", "soft"] = "soft"
    severity: Literal["low", "medium", "high"] = "medium"
    scope: Literal["full_text", "title", "opening", "core", "ending", "tags"] = "full_text"
    enabled: bool = True


class PolicyRule(CustomReviewRule):
    name_en: str = ""
    description_en: str = ""
    source: str
    source_name: str
    source_version: str = "1.0"
    priority: int = 6
    banned_terms: list[str] = Field(default_factory=list)
    required_terms: list[str] = Field(default_factory=list)
    min_words: int | None = None
    max_words: int | None = None
    evaluation_guidance: str = ""


class ReviewPolicyConflict(BaseModel):
    rule_a: str
    rule_b: str
    conflict: str
    resolution: str = "requires_user_review"


class ReviewPolicy(BaseModel):
    policy_id: str
    created_at: str
    sources: list[dict] = Field(default_factory=list)
    hard_rules: list[PolicyRule] = Field(default_factory=list)
    soft_rules: list[PolicyRule] = Field(default_factory=list)
    conflicts: list[ReviewPolicyConflict] = Field(default_factory=list)


class RuleEvaluationResult(BaseModel):
    rule_id: str
    rule_name: str
    source: str
    passed: bool
    evidence: str = ""
    severity: str = "medium"
    message: str = ""


class ContentInput(BaseModel):
    direction_stage: str = "常规"
    content_type: str = "生活方式"
    sub_direction: str = "日常分享"
    keyword: str = ""
    original_text: str = ""
    images: list[str] = Field(default_factory=list)
    product: str = "示例产品"
    brand: str = "示例品牌"
    target_persona: str = "新手妈妈"
    content_language: str = "auto"
    accepted_suggestions: list[str] = Field(default_factory=list)
    content_goal: str = "品牌认知"
    writing_style: str = "真实自然"
    rewrite_intensity: Literal["light", "standard", "deep"] = "standard"
    custom_rules: list[CustomReviewRule] = Field(default_factory=list)
    review_policy: dict = Field(default_factory=dict)


class ImageAnalysis(BaseModel):
    image_id: str
    scene: str
    image_text: list[str] = Field(default_factory=list)
    other_products: list[str] = Field(default_factory=list)
    style: str = "简约干净"


class ParsedContent(BaseModel):
    title: str = ""
    opening: str = ""
    core_content: str = ""
    ending: str = ""
    tags: list[str] = Field(default_factory=list)
    persona: str = "新手妈妈"
    content_style: str = "真诚分享"
    content_language: str = "auto"


class Rule(BaseModel):
    rule_id: str
    description: str
    banned_words: str = ""
    replace_words: str = ""
    category: str = "general"


class Replacement(BaseModel):
    banned_word: str
    replace_word: str
    count: int


class Issue(BaseModel):
    issue_id: str
    issue_type: str
    severity: Literal["low", "medium", "high"]
    evidence: str
    explanation: str
    suggestion: str
    rule_id: str = ""
    rule_source: str = ""
    rule_description: str = ""


class SuggestionDecision(BaseModel):
    issue_id: str
    decision: Literal["accepted", "ignored", "regenerate"]
    optional_user_instruction: str = ""


class RevisionInstruction(BaseModel):
    instruction: str


class EvaluationResult(BaseModel):
    score: float
    dimensions: dict[str, Any] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    issues: list[Issue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    passed: bool = True


class Evaluation(BaseModel):
    compliance_pass: bool
    keyword_pass: bool
    fact_consistency: bool
    persona_alignment: bool
    image_text_consistency: bool
    instruction_following: bool
    structure_quality: bool
    latency_ms: float = 0
    token_usage: int = 0
    estimated_cost: float = 0
    review_policy_id: str = ""
    rule_results: list[RuleEvaluationResult] = Field(default_factory=list)


class RewriteValidationResult(BaseModel):
    accepted_suggestions_applied: bool = False
    accepted_suggestions_applied_count: int = 0
    accepted_suggestions_total: int = 0
    target_issues_resolved: int = 0
    target_issues_total: int = 0
    fact_preservation_pass: bool = True
    keyword_pass: bool = True
    hard_rule_pass: bool = True
    meaningful_change: bool = False
    new_issues: list[str] = Field(default_factory=list)
    passed: bool = False
    retried: bool = False


class TraceEntry(BaseModel):
    step: str
    input_summary: str
    output_summary: str
    latency_ms: float
    status: Literal["success", "failed", "skipped"]
    error: str | None = None


class GeneratedContent(BaseModel):
    text: str
    titles: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    changes: list[str] = Field(default_factory=list)
    preserved_nouns: list[str] = Field(default_factory=list)
    route: Literal["full", "staged"]


class PipelineResult(BaseModel):
    final_text: str
    titles: list[str]
    tags: list[str]
    report: dict[str, Any]
    preserved_nouns: list[str]
    parsed: ParsedContent
    vision: list[ImageAnalysis]
    diagnoses: dict[str, Diagnosis]
    evaluation: Evaluation
    execution_trace: list[TraceEntry]
    rewrite_validation: RewriteValidationResult | None = None
    review_policy: ReviewPolicy | None = None


class AnalysisVersion(BaseModel):
    version_number: int
    created_time: str
    content: str
    titles: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    applied_suggestions: list[str] = Field(default_factory=list)
    user_instruction: str = ""
    evaluation: EvaluationResult
    execution_trace: list[TraceEntry] = Field(default_factory=list)
    input: dict[str, Any] = Field(default_factory=dict)
    review_policy: ReviewPolicy | None = None
    rewrite_validation: RewriteValidationResult | None = None


class AnalysisSession(BaseModel):
    session_id: str
    created_time: str
    updated_time: str
    source_filename: str = ""
    keyword: str = ""
    content_type: str = ""
    detected_persona: str = ""
    generation_route: str = ""
    issue_count: int = 0
    evaluation_score: float = 0
    provider: str = "mock"
    model: str = "mock-v1"
