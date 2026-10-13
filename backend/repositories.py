from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from .models import Rule


class JsonRepository:
    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)

    def read(self, name: str) -> Any:
        path = self.data_dir / name
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))


class RuleRetriever:
    def __init__(self, repository: JsonRepository) -> None:
        self.repository = repository

    def compliance_rules(self) -> list[Rule]:
        payload = self.repository.read("brand_rules.json")
        rows = payload.get("rules", []) if isinstance(payload, dict) else payload
        normalized = []
        for item in rows:
            if "banned_terms" in item:
                item = {**item, "description": item.get("description", item.get("name", "")),
                        "banned_words": ",".join(item.get("banned_terms", [])),
                        "replace_words": ",".join(item.get("replace_terms", [])), "category": "compliance"}
            normalized.append(Rule.model_validate(item))
        return normalized

    def issue_rules(self) -> list[dict[str, Any]]:
        return self.repository.read("issue_rules.json")

    def keyword_rules(self, keyword: str, stage: str = "") -> list[dict[str, Any]]:
        return [row for row in self.repository.read("keyword_rules.json") if not keyword or row["keyword"] == keyword]


class KnowledgeRetriever:
    def __init__(self, repository: JsonRepository) -> None:
        self.repository = repository

    def context(self, content_type: str, sub_direction: str) -> dict[str, Any]:
        rows = self.repository.read("knowledge.json")
        refs = self.repository.read("reference_articles.json")
        return {"knowledge": [r for r in rows if r.get("sub_direction") in (sub_direction, "通用")], "references": [r for r in refs if r.get("direction") == sub_direction]}

    def direction(self, content_type: str, sub_direction: str) -> dict[str, Any]:
        directions = self.repository.read("content_directions.json")
        personas = self.repository.read("personas.json")
        return {"direction": next((r for r in directions if r.get("content_type") == content_type), directions[0] if directions else {}), "persona": next((r for r in personas if r.get("name") == "新手妈妈"), {})}
