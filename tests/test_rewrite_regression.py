from backend.models import PipelineResult
from backend.pipeline import ContentQAPipeline
from backend.providers import MockLLMProvider, RealLLMProvider, configured_provider


ORIGINAL = "#早餐\n今天分享一个日常场景。\n轻盈奶粉体验不错。\n推荐按需选择。"


def test_standard_chinese_rewrite_regression():
    result = ContentQAPipeline("data", provider=MockLLMProvider()).run({"original_text": ORIGINAL, "keyword": "轻盈奶粉", "rewrite_intensity": "standard"})
    assert result.final_text.strip()
    assert "轻盈奶粉" in result.final_text
    assert "的使用感受" not in result.final_text
    assert "轻盈奶粉体验不错" in result.final_text
    assert result.final_text != ORIGINAL
    assert result.rewrite_validation is not None
    assert result.rewrite_validation.meaningful_change
    assert result.rewrite_validation.keyword_pass
    assert result.rewrite_validation.accepted_suggestions_applied


def test_missing_optional_metadata_never_creates_broken_fragment():
    result = ContentQAPipeline("data", provider=MockLLMProvider()).run({"brand": "", "product": "", "keyword": "", "original_text": "今天记录一段真实体验。", "rewrite_intensity": "standard"})
    assert result.final_text.strip()
    assert "的使用感受" not in result.final_text
    assert not result.final_text.startswith("的")


def test_retry_receives_explicit_validation_feedback_once():
    class RetryProvider(MockLLMProvider):
        def __init__(self): self.prompts = []
        def generate(self, prompt, **kwargs):
            self.prompts.append(prompt)
            return kwargs["source"] if len(self.prompts) == 1 else kwargs["fallback"]

    provider = RetryProvider()
    result = ContentQAPipeline("data", provider=provider).run({"original_text": ORIGINAL, "keyword": "轻盈奶粉"})
    assert len(provider.prompts) == 2
    assert "previous rewrite failed" in provider.prompts[1]
    assert result.rewrite_validation.retried
    assert result.rewrite_validation.passed


def test_old_pipeline_result_without_validation_deserializes_safely():
    fields = {"final_text": "old", "titles": [], "tags": [], "report": {}, "preserved_nouns": [], "parsed": {}, "vision": [], "diagnoses": {}, "evaluation": {"compliance_pass": True, "keyword_pass": True, "fact_consistency": True, "persona_alignment": True, "image_text_consistency": True, "instruction_following": True, "structure_quality": True}, "execution_trace": []}
    result = PipelineResult.model_validate(fields)
    assert result.rewrite_validation is None


def test_provider_defaults_to_explicit_demo_mode(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False); monkeypatch.delenv("LLM_MODEL", raising=False); monkeypatch.delenv("LLM_API_KEY", raising=False)
    provider = configured_provider()
    assert provider.mode == "demo"
    assert provider.provider_name == "Mock"


def test_real_provider_is_selected_only_with_complete_environment(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai"); monkeypatch.setenv("LLM_MODEL", "configured-model"); monkeypatch.setenv("LLM_API_KEY", "test-key")
    provider = configured_provider()
    assert isinstance(provider, RealLLMProvider)
    assert provider.model == "configured-model"
    assert provider.mode == "live"
