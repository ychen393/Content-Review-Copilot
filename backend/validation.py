from __future__ import annotations

from difflib import SequenceMatcher

from .models import ContentInput, RewriteValidationResult


class RewriteQualityValidator:
    """Deterministic post-generation gate; it never relies on a self-reported score."""

    def validate(self, content: ContentInput, rewritten: str, target_issue_ids: list[str],
                 remaining_issue_ids: list[str], hard_rule_fixes: list, new_issue_ids: list[str]) -> RewriteValidationResult:
        original = content.original_text.strip()
        rewritten = rewritten.strip()
        remaining = set(remaining_issue_ids)
        resolved = [issue_id for issue_id in target_issue_ids if issue_id not in remaining]
        required_facts = [value for value in (content.brand, content.product) if value and value in original]
        fact_pass = all(value in rewritten for value in required_facts)
        similarity = SequenceMatcher(None, original, rewritten).ratio() if original and rewritten else 0.0
        change_limit = {"light": 0.995, "standard": 0.92, "deep": 0.82}[content.rewrite_intensity]
        meaningful = bool(rewritten) and similarity < change_limit
        keyword_pass = not content.keyword or content.keyword in rewritten
        hard_pass = not hard_rule_fixes
        new_issues = sorted(set(new_issue_ids))
        passed = (len(resolved) == len(target_issue_ids) and fact_pass and keyword_pass and hard_pass
                  and meaningful and not new_issues and bool(rewritten))
        return RewriteValidationResult(
            accepted_suggestions_applied=len(resolved) == len(target_issue_ids), accepted_suggestions_applied_count=len(resolved), accepted_suggestions_total=len(target_issue_ids),
            target_issues_resolved=len(resolved), target_issues_total=len(target_issue_ids),
            fact_preservation_pass=fact_pass, keyword_pass=keyword_pass, hard_rule_pass=hard_pass,
            meaningful_change=meaningful, new_issues=new_issues, passed=passed,
        )
