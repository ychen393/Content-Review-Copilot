"""Regression tests for M1 semantic review isolation and review API compatibility."""
import json

from backend.pipeline import ContentQAPipeline
from backend.policy import SoftRuleEvaluator
from backend.providers import MockLLMProvider, RealLLMProvider
from backend.models import PolicyRule, ReviewPolicy
from api.service import ReviewWorkflowService
from api.store import ReviewStore
from api.models import ReviewCreateRequest


class StrictReviewProvider(MockLLMProvider):
    mode = "live"

    def __init__(self):
        self.review_calls = 0
        self.generate_calls = 0

    def generate(self, prompt: str, **kwargs):
        self.generate_calls += 1
        raise AssertionError("Review must not call generate")

    def semantic_review(self, prompt: str, **kwargs):
        self.review_calls += 1
        data = json.loads(prompt.split("Rules:\\n", 1)[1].split("\\nContent:", 1)[0])
        return [{"rule_id": rule["rule_id"], "passed": True, "evidence": "", "message": "checked"} for rule in data]


def test_review_only_calls_semantic_interface_not_generate():
    provider = StrictReviewProvider()
    result = ContentQAPipeline(provider=provider).run({
        "original_text": "我记录了示例产品的使用感受。",
        "brand": "示例品牌", "product": "示例产品",
        "keyword": "示例产品",
    }, review_only=True)
    assert provider.generate_calls == 0
    assert provider.review_calls >= 1
    assert result.report["mode"] == "review_only"


def test_live_soft_rule_failure_is_not_silently_accepted():
    provider = StrictReviewProvider()
    provider.semantic_review = lambda prompt: []
    rule = PolicyRule(rule_id="SOFT-1", name="Style", source="custom",
        source_name="Custom", description="Check style", type="soft")
    policy = ReviewPolicy(policy_id="p1", created_at="2026-01-01T00:00:00Z",
        soft_rules=[rule])
    try:
        SoftRuleEvaluator(provider).evaluate("text", policy)
    except ValueError as error:
        assert "omitted" in str(error)
    else:
        raise AssertionError("Missing evaluations must not be considered passes")


def test_service_uses_injected_provider_for_review(tmp_path):
    provider = StrictReviewProvider()
    service = ReviewWorkflowService(store=ReviewStore(tmp_path / "m1.sqlite3"), provider=provider)
    session = service.create(ReviewCreateRequest(original_text="我记录了示例产品的体验。", keyword="示例产品"))
    reviewed = service.first_review(session)
    assert reviewed["state"] in ("WAITING_FOR_FIRST_DECISIONS", "FIRST_REVIEW_COMPLETE")
    assert provider.generate_calls == 0
    assert provider.review_calls >= 1
