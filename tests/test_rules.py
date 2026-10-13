from backend.models import Rule
from backend.rules import DeterministicRuleEngine


def test_rules_replace_longest_and_delete_empty_replacement():
    text, log = DeterministicRuleEngine().clean("百分百有效，最强体验", [Rule(rule_id="x", description="x", banned_words="百分百有效,最强", replace_words="体验较好,")])
    assert text == "体验较好，体验"
    assert [item.banned_word for item in log] == ["百分百有效", "最强"]
