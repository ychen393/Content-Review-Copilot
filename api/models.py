from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowState(StrEnum):
    NEW_REVIEW = "NEW_REVIEW"
    REVIEWING = "REVIEWING"
    FIRST_REVIEW_COMPLETE = "FIRST_REVIEW_COMPLETE"
    WAITING_FOR_FIRST_DECISIONS = "WAITING_FOR_FIRST_DECISIONS"
    GENERATING_OPTIMIZED_DRAFT = "GENERATING_OPTIMIZED_DRAFT"
    OPTIMIZED_DRAFT_READY = "OPTIMIZED_DRAFT_READY"
    SECOND_REVIEWING = "SECOND_REVIEWING"
    SECOND_REVIEW_COMPLETE = "SECOND_REVIEW_COMPLETE"
    WAITING_FOR_SECOND_DECISIONS = "WAITING_FOR_SECOND_DECISIONS"
    GENERATING_FINAL = "GENERATING_FINAL"
    READY_TO_DELIVER = "READY_TO_DELIVER"
    FAILED = "FAILED"


class ReviewIssueViewModel(BaseModel):
    id: str
    priorityLabel: str
    categoryLabel: str
    title: str
    description: str
    originalText: str
    suggestedText: str
    ruleReference: str
    decision: Literal["accepted", "ignored", "regenerate"] | None = None
    isMandatory: bool = False


class ReviewSummaryViewModel(BaseModel):
    autoFixedCount: int = 0
    pendingCount: int = 0
    acceptedCount: int = 0
    ignoredCount: int = 0
    complianceStatus: str = "待审核"


class ReviewCreateRequest(BaseModel):
    original_text: str
    source_filename: str = ""
    images: list[str] = Field(default_factory=list, max_length=15)
    content_type: str = "生活方式"
    sub_direction: str = "日常分享"
    content_goal: str = "品牌认知"
    writing_style: str = "真实自然"
    keyword: str = ""
    brand: str = "示例品牌"
    product: str = "示例产品"
    target_persona: str = "AI 自动识别"
    rewrite_intensity: Literal["light", "standard", "deep"] = "standard"
    content_language: str = "auto"
    custom_rules: list[dict[str, Any]] = Field(default_factory=list)


class DecisionRequest(BaseModel):
    stage: Literal["first", "second"] = "first"
    decisions: dict[str, Literal["accepted", "ignored", "regenerate"]]


class ReviewSessionViewModel(BaseModel):
    id: str
    state: WorkflowState
    createdAt: str
    updatedAt: str
    sourceFilename: str = ""
    taskSummary: str
    reviewFocus: list[str]
    reviewBasis: list[dict[str, Any]]
    summary: ReviewSummaryViewModel = Field(default_factory=ReviewSummaryViewModel)
    firstReview: list[ReviewIssueViewModel] = Field(default_factory=list)
    optimizedDraft: dict[str, Any] | None = None
    secondReview: list[ReviewIssueViewModel] = Field(default_factory=list)
    finalVersion: dict[str, Any] | None = None
    error: str | None = None

