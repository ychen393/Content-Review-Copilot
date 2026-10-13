from __future__ import annotations

import re
from .models import ContentInput, Diagnosis, ImageAnalysis, Issue, ParsedContent
from .repositories import KnowledgeRetriever, RuleRetriever


class InputParser:
    def parse(self, raw: dict) -> ContentInput:
        return ContentInput.model_validate(raw)


class ContextResolver:
    def normalize_stage(self, stage: str) -> str:
        return {"一段": "早阶", "二段": "早阶", "孕晚": "早阶"}.get(stage, "常规")

    def resolve(self, content: ContentInput) -> dict:
        mapped = self.normalize_stage(content.direction_stage)
        return {"direction_stage": mapped, "rtb_type": mapped + content.content_type}


class VisionAnalyzer:
    def __init__(self, provider) -> None:
        self.provider = provider

    def analyze(self, images: list[str]) -> list[ImageAnalysis]:
        return self.provider.vision(images)


class ContentParser:
    def parse(self, text: str, target_persona: str = "新手妈妈", content_language: str = "auto") -> ParsedContent:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        title = lines[0].lstrip("# ") if lines and lines[0].startswith("#") else ""
        body = lines[1:] if title else lines
        tags = re.findall(r"#[\w\u4e00-\u9fff-]+", "\n".join(body))
        body = [re.sub(r"#[\w\u4e00-\u9fff-]+", "", line).strip() for line in body]
        core_index = next((i for i, line in enumerate(body) if any(word.lower() in line.lower() for word in ("配方", "成分", "产品", "含有", "适合", "product", "ingredient", "key point"))), max(1, len(body) // 2) if body else 0)
        ending_index = next((i for i, line in enumerate(body[core_index + 1:], core_index + 1) if any(word.lower() in line.lower() for word in ("所以", "推荐", "欢迎", "希望", "记得", "recommend", "finally", "in summary", "if you"))), len(body))
        detected_language = content_language if content_language != "auto" else ("zh" if any("\u4e00" <= char <= "\u9fff" for char in text) else "en")
        return ParsedContent(title=title, opening="\n".join(body[:core_index]), core_content="\n".join(body[core_index:ending_index]), ending="\n".join(body[ending_index:]), tags=tags, persona=target_persona, content_style="真诚分享", content_language=detected_language)


class _BaseEvaluator:
    area = "general"

    def __init__(self, rules: RuleRetriever) -> None:
        self.rules = rules

    def evaluate(self, text: str, keyword: str, images: list[ImageAnalysis]) -> Diagnosis:
        issues: list[Issue] = []
        if not text:
            issues.append(Issue(issue_id=f"{self.area}_missing", issue_type="structure", severity="high", evidence="空内容", explanation=f"{self.area} section is missing", suggestion="补充可验证、具体的内容。"))
        if keyword and text and keyword not in text:
            issues.append(Issue(issue_id=f"{self.area}_keyword", issue_type="keyword", severity="medium", evidence=text[:80], explanation="关键词未出现在该内容段", suggestion=f"自然加入关键词“{keyword}”。"))
        return Diagnosis(issues=issues, suggestions=[issue.suggestion for issue in issues], passed=not issues)


class OpeningEvaluator(_BaseEvaluator):
    area = "opening"


class CoreContentEvaluator(_BaseEvaluator):
    area = "core"

    def evaluate(self, text: str, keyword: str, images: list[ImageAnalysis]) -> Diagnosis:
        result = super().evaluate(text, keyword, images)
        if text and images and any(product and product not in text for image in images for product in image.other_products):
            result.issues.append(Issue(issue_id="core_product_fact", issue_type="product_fact", severity="high", evidence=text[:80], explanation="正文与图片中的产品证据不一致", suggestion="核对品牌、产品和规格后再生成。"))
            result.passed = False
        return result


class EndingEvaluator(_BaseEvaluator):
    area = "ending"


class PersonaEvaluator:
    def evaluate(self, parsed: ParsedContent, target: str) -> Diagnosis:
        if parsed.persona == target:
            return Diagnosis()
        issue = Issue(issue_id="persona_alignment", issue_type="persona", severity="medium", evidence=parsed.persona, explanation="识别的人设与目标人设不一致", suggestion=f"调整为{target}的语气和经验视角。")
        return Diagnosis(issues=[issue], suggestions=[issue.suggestion], passed=False)


class RewritePlanner:
    def build(self, diagnoses: dict[str, Diagnosis], content: ContentInput, replacements: list, decisions: list | None = None) -> dict:
        accepted = set(decisions or [])
        suggestions = [issue.suggestion for diagnosis in diagnoses.values() for issue in diagnosis.issues if not accepted or issue.issue_id in accepted]
        return {"route": "full" if content.content_type == "纯路人" else "staged", "keyword": content.keyword, "persona": content.target_persona, "diagnoses": diagnoses, "replacements": replacements, "direction": content.sub_direction, "accepted_suggestions": suggestions}


class GenerationRouter:
    def route(self, content_type: str) -> str:
        return "full" if content_type == "纯路人" else "staged"
