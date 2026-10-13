from backend.repositories import JsonRepository, KnowledgeRetriever, RuleRetriever
from backend.services import ContextResolver, ContentParser


def test_context_and_parser():
    assert ContextResolver().normalize_stage("孕晚") == "早阶"
    parsed = ContentParser().parse("#标题\n开头场景\n产品成分说明\n推荐按需选择\n#轻盈奶粉")
    assert parsed.title == "标题"
    assert parsed.core_content
    assert parsed.tags == ["#轻盈奶粉"]


def test_repositories_load_local_data():
    repository = JsonRepository("data")
    assert RuleRetriever(repository).compliance_rules()
    assert KnowledgeRetriever(repository).context("生活方式", "日常分享")["knowledge"]
