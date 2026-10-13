from backend.pipeline import ContentQAPipeline


def test_pipeline_produces_trace_and_result():
    original = "#早餐\n今天分享一个日常场景。\n轻盈奶粉体验不错。\n推荐按需选择。"
    result = ContentQAPipeline("data").run({"content_type": "生活方式", "keyword": "轻盈奶粉", "original_text": original})
    assert result.final_text
    assert result.final_text != original
    assert result.execution_trace
    assert result.evaluation.keyword_pass
    assert result.rewrite_validation.passed
    assert result.rewrite_validation.meaningful_change


def test_full_route_is_selected_for_pure_bystander():
    result = ContentQAPipeline("data").run({"content_type": "纯路人", "keyword": "轻盈奶粉", "original_text": "真实体验轻盈奶粉。"})
    assert result.report["route"] == "full"


def test_light_rewrite_still_resolves_keyword_issues():
    result = ContentQAPipeline("data").run({"content_type": "生活方式", "keyword": "轻盈奶粉", "rewrite_intensity": "light", "original_text": "今天记录一个日常片段。\n使用感受比较自然。\n建议按需选择。"})
    assert result.rewrite_validation.keyword_pass
    assert result.rewrite_validation.target_issues_resolved == result.rewrite_validation.target_issues_total


def test_english_standard_rewrite_is_valid_and_stays_english():
    result = ContentQAPipeline("data").run({"content_type": "生活方式", "keyword": "light formula", "content_language": "en", "original_text": "A simple breakfast moment.\nThe product felt easy to use.\nI recommend choosing based on your needs."})
    assert result.rewrite_validation.passed
    assert "I recently" in result.final_text
