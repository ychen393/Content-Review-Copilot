from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .models import (ContentInput, CustomReviewRule, PolicyRule, ReviewPolicy,
                     ReviewPolicyConflict, RuleEvaluationResult)


SOURCE_PRIORITY = {"task": 1, "brand": 2, "product": 3, "platform": 4, "custom": 5, "rubric": 6}


class ReviewPolicyBuilder:
    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)

    def _read(self, name: str) -> dict:
        path = self.data_dir / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def build(self, content: ContentInput) -> ReviewPolicy:
        brand = self._read("brand_rules.json"); product = self._read("product_knowledge.json")
        platform = self._read("platform_rules.json"); rubric = self._read("quality_rubric.json")
        rules: list[PolicyRule] = [
            PolicyRule(rule_id="TR-KEYWORD-01", name="指定关键词", name_en="Required keyword", description=f"正文必须自然包含关键词“{content.keyword}”。", description_en=f"Content must naturally include “{content.keyword}”.", type="hard", severity="medium", scope="full_text", source="task", source_name="Task requirements", priority=1, required_terms=[content.keyword] if content.keyword else []),
            PolicyRule(rule_id="TR-STYLE-01", name="表达风格", name_en="Writing style", description=f"表达应符合所选风格：{content.writing_style}。", description_en=f"Writing should follow the selected style: {content.writing_style}.", type="soft", severity="medium", scope="full_text", source="task", source_name="Task requirements", priority=1),
        ]
        for row in brand.get("rules", []): rules.append(self._rule(row, "brand", f"{brand.get('brand_name', 'Demo brand')} rules", brand.get("version", "1.0")))
        for fact in product.get("facts", []):
            rules.append(PolicyRule(rule_id=fact["fact_id"], name=f"产品事实：{fact['field']}", name_en=f"Product fact: {fact.get('field_en', fact['field'])}", description=f"{fact['field']}: {fact['value']}", description_en=f"{fact.get('field_en', fact['field'])}: {fact.get('value_en', fact['value'])}", type="hard", severity="high", scope="full_text", source="product", source_name=f"{product.get('product_name', 'Demo product')} knowledge", source_version=product.get("version", "1.0"), priority=3))
        for row in platform.get("rules", []): rules.append(self._rule(row, "platform", platform.get("source_name", "Demo Rule Pack"), platform.get("version", "1.0")))
        for row in rubric.get("rules", []):
            normalized = {**row, "rule_id": row.get("rubric_id")}
            rules.append(self._rule(normalized, "rubric", rubric.get("name", "Content Quality Rubric"), rubric.get("version", "1.0")))
        for custom in content.custom_rules:
            if custom.enabled: rules.append(self._custom(custom))
        conflicts = self._conflicts(rules)
        stable = json.dumps([rule.model_dump() for rule in rules], ensure_ascii=False, sort_keys=True)
        policy_id = "RP-" + hashlib.sha256(stable.encode()).hexdigest()[:12].upper()
        sources = [
            {"source": "task", "name": "Task requirements", "version": "1.0"},
            {"source": "brand", "name": brand.get("brand_name", "Demo brand"), "version": brand.get("version", "1.0")},
            {"source": "product", "name": product.get("product_name", "Demo product"), "version": product.get("version", "1.0")},
            {"source": "platform", "name": platform.get("source_name", "Demo Rule Pack"), "version": platform.get("version", "1.0"), "source_type": platform.get("source_type", "demo"), "reference_note": platform.get("reference_note", "")},
            {"source": "rubric", "name": rubric.get("name", "Content Quality Rubric"), "version": rubric.get("version", "1.0")},
            {"source": "custom", "name": "Custom rules", "version": "task", "count": len(content.custom_rules)},
        ]
        return ReviewPolicy(policy_id=policy_id, created_at=datetime.now(timezone.utc).isoformat(), sources=sources,
                            hard_rules=sorted([r for r in rules if r.type == "hard"], key=lambda r: r.priority),
                            soft_rules=sorted([r for r in rules if r.type == "soft"], key=lambda r: r.priority), conflicts=conflicts)

    def _rule(self, row: dict, source: str, source_name: str, version: str) -> PolicyRule:
        return PolicyRule(rule_id=row["rule_id"], name=row.get("name", row["rule_id"]), name_en=row.get("name_en", ""), description=row.get("description", ""), description_en=row.get("description_en", ""), type=row.get("type", "soft"), severity=row.get("severity", "medium"), scope=row.get("scope", "full_text"), source=source, source_name=source_name, source_version=version, priority=SOURCE_PRIORITY[source], banned_terms=row.get("banned_terms", []), required_terms=row.get("required_terms", []), evaluation_guidance=row.get("evaluation_guidance", ""))

    def _custom(self, rule: CustomReviewRule) -> PolicyRule:
        quoted = re.findall(r"[‘'\"]([^’'\"]+)[’'\"]", rule.description)
        maximum = re.search(r"(?:不超过|maximum|max)\s*(\d+)", rule.description, re.I)
        return PolicyRule(**rule.model_dump(), source="custom", source_name="Custom rule", source_version="task", priority=5,
                          banned_terms=quoted if rule.type == "hard" and any(x in rule.description.lower() for x in ("不要", "禁止", "avoid")) else [],
                          max_words=int(maximum.group(1)) if maximum else None)

    def _conflicts(self, rules: list[PolicyRule]) -> list[ReviewPolicyConflict]:
        conflicts = []
        for index, a in enumerate(rules):
            for b in rules[index + 1:]:
                overlap = (set(a.required_terms) & set(b.banned_terms)) | (set(b.required_terms) & set(a.banned_terms))
                if overlap:
                    conflicts.append(ReviewPolicyConflict(rule_a=a.rule_id, rule_b=b.rule_id, conflict=f"Terms are both required and prohibited: {', '.join(overlap)}"))
        return conflicts


class PolicyRuleEvaluator:
    def evaluate_hard(self, text: str, policy: ReviewPolicy) -> list[RuleEvaluationResult]:
        results = []
        for rule in policy.hard_rules:
            banned = [term for term in rule.banned_terms if term and term in text]
            missing = [term for term in rule.required_terms if term and term not in text]
            words = len(text.split())
            length_failed = (rule.min_words is not None and words < rule.min_words) or (rule.max_words is not None and words > rule.max_words)
            passed = not banned and not missing and not length_failed
            evidence = ", ".join(banned or missing) or (str(words) if length_failed else "")
            results.append(RuleEvaluationResult(rule_id=rule.rule_id, rule_name=rule.name, source=rule.source_name, passed=passed, evidence=evidence, severity=rule.severity, message=rule.description))
        return results


class SoftRuleEvaluator:
    def __init__(self, provider=None) -> None:
        self.provider = provider

    def evaluate(self, text: str, policy: ReviewPolicy) -> list[RuleEvaluationResult]:
        if not policy.soft_rules:
            return []
        if self.provider is None or getattr(self.provider, "mode", "demo") != "live":
            # Mock mode is not evidence of semantic compliance.
            return []
        prompt = ("Evaluate every rule independently. Return a JSON array with rule_id, "
                  "passed (boolean), evidence, and message.\\nRules:\\n"
                  + json.dumps([r.model_dump() for r in policy.soft_rules], ensure_ascii=False)
                  + "\\nContent:\\n" + text)
        rows = self.provider.semantic_review(prompt)
        by_id = {rule.rule_id: rule for rule in policy.soft_rules}
        results = {}
        for row in rows:
            if not isinstance(row, dict) or row.get("rule_id") not in by_id:
                continue
            if not isinstance(row.get("passed"), bool):
                raise ValueError("Semantic review must supply a boolean passed field")
            rule = by_id[row["rule_id"]]
            results[rule.rule_id] = RuleEvaluationResult(
                rule_id=rule.rule_id, rule_name=rule.name, source=rule.source_name,
                passed=row["passed"], evidence=str(row.get("evidence", "")),
                severity=rule.severity, message=str(row.get("message", rule.description)),
            )
        if len(results) != len(by_id):
            raise ValueError("Semantic review omitted one or more soft rules")
        return list(results.values())
