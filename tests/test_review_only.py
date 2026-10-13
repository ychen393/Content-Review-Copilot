"""M1 regression: analysis operations must not invoke a rewrite generator."""
from backend.pipeline import ContentQAPipeline
from backend.providers import MockLLMProvider


class FailIfGenerating(MockLLMProvider):
    def generate(self, prompt: str, **kwargs):
        raise AssertionError("Review-only mode invoked content generation")


def test_review_only_does_not_generate_or_retry():
    pipeline = ContentQAPipeline(provider=FailIfGenerating())
    result = pipeline.run({
        "original_text": "这是一篇关于示例产品的真实体验。",
        "keyword": "示例产品",
        "brand": "示例品牌",
        "product": "示例产品",
    }, review_only=True)
    assert result.report["mode"] == "review_only"
    assert result.final_text == "这是一篇关于示例产品的真实体验。"
    assert result.rewrite_validation is None
    assert not any("Generation" in entry.step or "Rewrite Validation" in entry.step for entry in result.execution_trace)


def test_default_pipeline_still_supports_generation():
    pipeline = ContentQAPipeline(provider=MockLLMProvider())
    result = pipeline.run({"original_text": "我试用了示例产品。", "keyword": "示例产品"})
    assert result.final_text
    assert any(entry.step == "Content Generation" for entry in result.execution_trace)
