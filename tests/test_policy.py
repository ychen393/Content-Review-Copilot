from backend.history import HistoryRepository
from backend.models import ContentInput, CustomReviewRule
from backend.pipeline import ContentQAPipeline
from backend.policy import ReviewPolicyBuilder
from presentation import label


def test_policy_builder_separates_sources_types_and_priority():
    policy = ReviewPolicyBuilder("data").build(ContentInput(keyword="demo"))
    assert policy.hard_rules and policy.soft_rules
    assert policy.hard_rules[0].source == "task"
    assert {source["source"] for source in policy.sources} == {"task", "brand", "product", "platform", "rubric", "custom"}


def test_custom_rule_creation_and_conflict_detection():
    custom = CustomReviewRule(rule_id="CR-001", name="Ban keyword", description="不要出现‘demo’", type="hard", severity="high")
    policy = ReviewPolicyBuilder("data").build(ContentInput(keyword="demo", custom_rules=[custom]))
    assert any(rule.rule_id == "CR-001" for rule in policy.hard_rules)
    assert policy.conflicts
    assert policy.conflicts[0].resolution == "requires_user_review"


def test_diagnosis_links_rule_and_evaluation_uses_frozen_policy():
    result = ContentQAPipeline("data").run({"keyword": "轻盈奶粉", "original_text": "普通开头。\n产品体验。\n推荐理性选择。"})
    issues = [issue for diagnosis in result.diagnoses.values() for issue in diagnosis.issues]
    assert any(issue.rule_id == "TR-KEYWORD-01" for issue in issues)
    assert result.evaluation.review_policy_id == result.review_policy.policy_id
    assert result.evaluation.rule_results


def test_policy_snapshot_persists_exactly(tmp_path):
    repository = HistoryRepository(tmp_path / "history.sqlite3")
    policy = ReviewPolicyBuilder("data").build(ContentInput(keyword="snapshot"))
    session = repository.create_session({"keyword": "snapshot"})
    repository.save_version(session, {"content": "text", "evaluation": {"score": 1}, "review_policy": policy.model_dump()})
    loaded = repository.get_versions(session)[0]
    assert loaded.review_policy.model_dump() == policy.model_dump()


def test_policy_i18n_labels():
    assert label("rule_type", "hard", "zh") == "硬性规则"
    assert label("rule_source", "product", "en") == "Product knowledge"
