import json

from streamlit.testing.v1 import AppTest

from backend.history import HistoryRepository
from backend.models import (AnalysisVersion, Evaluation, EvaluationResult,
                            ParsedContent, PipelineResult,
                            RewriteValidationResult)
from backend.pipeline import ContentQAPipeline
from backend.providers import MockLLMProvider


def minimal_result(validation=None):
    return PipelineResult(final_text="old content", titles=[], tags=[], report={}, preserved_nouns=[],
        parsed=ParsedContent(), vision=[], diagnoses={}, evaluation=Evaluation(compliance_pass=True,
        keyword_pass=True, fact_consistency=True, persona_alignment=True, image_text_consistency=True,
        instruction_following=True, structure_quality=True), execution_trace=[], rewrite_validation=validation)


def test_canonical_validation_model_import_and_defaults():
    validation = RewriteValidationResult()
    assert validation.accepted_suggestions_applied is False
    assert validation.meaningful_change is False


def test_pipeline_result_contract_with_and_without_validation():
    assert minimal_result().rewrite_validation is None
    validation = RewriteValidationResult(keyword_pass=True)
    assert minimal_result(validation).rewrite_validation == validation


def test_ui_renders_old_result_without_validation():
    at = AppTest.from_file("../app.py", default_timeout=20)
    at.session_state["result"] = minimal_result()
    at.session_state["input"] = {"original_text": "old content"}
    at.session_state["result_view"] = "result"
    at.run()
    assert not at.exception
    assert any("尚未执行改写质量验证" in item.value for item in at.warning)


def test_old_history_payload_without_validation_loads(tmp_path):
    repository = HistoryRepository(tmp_path / "history.sqlite3")
    session = repository.create_session({"keyword": "old"})
    repository.save_version(session, {"content": "old", "evaluation": {"score": 1}})
    loaded = repository.get_versions(session)[0]
    assert loaded.rewrite_validation is None


def test_mock_and_live_provider_paths_return_same_schema():
    class LiveContractProvider(MockLLMProvider):
        provider_name = "Contract live provider"; model = "test-model"; mode = "live"
        def generate(self, prompt, **kwargs):
            return kwargs.get("fallback", "")
        def semantic_review(self, prompt, **kwargs):
            rules = json.loads(prompt.split("Rules:\\n", 1)[1].split("\\nContent:", 1)[0])
            return [{"rule_id": r["rule_id"], "passed": True, "evidence": "", "message": "contract test"} for r in rules]

    raw = {"original_text": "开头。\n产品体验自然。\n推荐按需选择。", "keyword": "产品"}
    mock_result = ContentQAPipeline("data", provider=MockLLMProvider()).run(raw)
    live_result = ContentQAPipeline("data", provider=LiveContractProvider()).run(raw)
    assert isinstance(mock_result.rewrite_validation, RewriteValidationResult)
    assert isinstance(live_result.rewrite_validation, RewriteValidationResult)
