from io import BytesIO

from backend.comparison import compare_versions
from backend.documents import DefaultDocumentParser
from backend.history import HistoryRepository
from backend.i18n import Translator, detect_content_language
from backend.models import AnalysisVersion, ContentInput, EvaluationResult, ParsedContent, RevisionInstruction, TraceEntry
from backend.revision import SectionRegenerator, RevisionService
from backend.services import RewritePlanner


def version(number: int, content: str, issues: list[str] | None = None) -> AnalysisVersion:
    return AnalysisVersion(version_number=number, created_time="now", content=content, applied_suggestions=issues or [], evaluation=EvaluationResult(score=float(number * 10)), execution_trace=[])


def test_document_parser_supports_text_and_rejects_unknown():
    parser = DefaultDocumentParser()
    assert parser.parse("note.txt", b"hello").text == "hello"
    assert parser.parse("note.md", "标题".encode("utf-8")).text == "标题"
    assert parser.parse("note.exe", b"x").status == "failed"


def test_history_persists_incrementing_versions(tmp_path):
    repository = HistoryRepository(tmp_path / "history.sqlite3")
    session_id = repository.create_session({"keyword": "demo", "content_type": "生活方式"})
    first = repository.save_version(session_id, {"content": "one", "evaluation": {"score": 50}, "titles": [], "tags": [], "applied_suggestions": [], "execution_trace": []})
    second = repository.save_version(session_id, {"content": "two", "evaluation": {"score": 80}, "titles": [], "tags": [], "applied_suggestions": ["issue-1"], "execution_trace": []})
    assert [item.version_number for item in repository.get_versions(session_id)] == [1, 2]
    assert second.content == "two"
    assert repository.list_sessions()[0].keyword == "demo"


def test_version_comparison_reports_diff_and_score_change():
    result = compare_versions(version(1, "old", ["issue-1"]), version(2, "new", []))
    assert "old" in result["diff"]
    assert result["evaluation_difference"] == 10
    assert result["issues_fixed"] == ["issue-1"]


def test_suggestion_acceptance_and_section_regeneration():
    plan = RewritePlanner().build({}, ContentInput(keyword="demo"), [], ["issue-1"])
    assert plan["accepted_suggestions"] == []
    parsed = ParsedContent(opening="old opening", core_content="old core", ending="old ending")
    regenerated = SectionRegenerator().regenerate("opening", ContentInput(product="Product"), parsed)
    assert "old core" in regenerated.text
    assert "old ending" in regenerated.text
    assert "revision applied" in RevisionService().revise("content", RevisionInstruction(instruction="be natural"), ContentInput()).lower()


def test_i18n_fallback_and_content_language():
    assert Translator("en")("missing.key") == "missing.key"
    assert Translator("zh")("app.title")
    assert detect_content_language("这是中文") == "zh"
    assert detect_content_language("This is English") == "en"


def test_content_parser_preserves_selected_language_and_title_regeneration():
    parsed = ParsedContent(opening="opening", core_content="core", ending="ending")
    regenerated = SectionRegenerator().regenerate_titles(ContentInput(product="Product", content_language="en"), parsed, "natural")
    assert regenerated.text == "opening\ncore\nending"
    assert all("natural" in title for title in regenerated.titles)