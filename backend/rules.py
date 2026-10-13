from __future__ import annotations

import re
from .models import Replacement, Rule


class DeterministicRuleEngine:
    def clean(self, text: str, rules: list[Rule]) -> tuple[str, list[Replacement]]:
        replacements: list[tuple[str, str]] = []
        for rule in rules:
            banned = re.split(r"[,，、]", rule.banned_words) if rule.banned_words else []
            replacement = re.split(r"[,，、]", rule.replace_words) if rule.replace_words else []
            replacements.extend((word.strip(), replacement[index].strip() if index < len(replacement) else "") for index, word in enumerate(banned) if word.strip())
        result = text
        log: list[Replacement] = []
        for banned, replacement in sorted(replacements, key=lambda pair: len(pair[0]), reverse=True):
            if banned == replacement or banned not in result:
                continue
            count = result.count(banned)
            result = result.replace(banned, replacement)
            log.append(Replacement(banned_word=banned, replace_word=replacement, count=count))
        return result, log
