from __future__ import annotations

import json
from .models import ContentInput, GeneratedContent, ParsedContent
from .providers import LLMProvider, extract_nouns


def _rewrite(content: ContentInput, parsed: ParsedContent, deep: bool = False) -> str:
    keyword = content.keyword or content.product or ("this experience" if parsed.content_language == "en" else "这次体验")
    original = " ".join(part for part in (parsed.opening, parsed.core_content, parsed.ending) if part).strip()
    english = parsed.content_language == "en"
    if content.rewrite_intensity == "light" and not deep:
        opening = parsed.opening or original
        core = parsed.core_content or original
        ending = parsed.ending or ("I recommend choosing based on your actual needs." if english else "推荐按自己的实际需要选择。")
        if keyword:
            opening = opening if keyword in opening else (f"A note on {keyword}: {opening}" if english else f"关于{keyword}，{opening}")
            core = core if keyword in core else (f"{core} This is what matters most to me when considering {keyword}." if english else f"{core} 这也是我关注{keyword}时最看重的一点。")
            ending = ending if keyword in ending else (f"{ending} I still recommend evaluating {keyword} rationally." if english else f"{ending} 对{keyword}仍推荐理性选择。")
        return "\n".join((opening.replace("推荐", "更建议"), core, ending))
    if english:
        tone = {"真实自然": "in a natural, honest way", "专业可信": "with clear and credible detail", "轻松活泼": "in a light, lively voice", "简洁直接": "clearly and directly", "温暖生活化": "with a warm, everyday feel"}.get(content.writing_style, "naturally")
        opening = f"I recently took a closer look at {keyword} and wanted to share the experience {tone}."
        facts = original or (f"I tried {content.product} in a real-life setting." if content.product else "I recorded the experience in a real-life setting.")
        core = (f"For {keyword}, the bottom line is that personal needs matter most. The original experience was: {facts}" if deep else f"The key point worth keeping about {keyword} is: {facts}")
        ending = f"If you are also considering {keyword}, I recommend weighing it against your own needs rather than following a trend."
        return "\n".join((opening, core, ending))
    tone = {"真实自然": "真实自然地", "专业可信": "清晰可信地", "轻松活泼": "轻松地", "简洁直接": "简洁直接地", "温暖生活化": "温暖生活化地"}.get(content.writing_style, "自然地")
    opening = f"最近整理日常记录时，我又想起了这次{keyword}的体验，索性把感受说得更完整一些。"
    facts = original or (f"我结合实际场景体验了{content.product}。" if content.product else "我结合实际场景记录了这次体验。")
    facts = facts.replace("。 ", "。").replace(". ", ". ").rstrip("。.!！")
    if deep:
        core = f"先说结论：{keyword}是否适合自己，还是要看具体需求。原来的真实体验是：{facts}。"
    else:
        core = f"说回实际感受，{facts}。这些细节比笼统的推荐更能说明{keyword}是否适合自己。"
    ending = f"如果你也在关注{keyword}，推荐结合自己的情况理性判断，不必盲目跟随。"
    return "\n".join((opening, core, ending))


class FullRewriteGenerator:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def generate(self, content: ContentInput, parsed: ParsedContent, plan: dict, context: dict, feedback: str = "") -> GeneratedContent:
        fallback = _rewrite(content, parsed, deep=content.rewrite_intensity == "deep" or bool(feedback))
        text = self.provider.generate(_prompt(content, parsed, plan, context, feedback, "full"), source=content.original_text, fallback=fallback).strip()
        if not text:
            text = fallback
        return GeneratedContent(text=text, titles=[f"{content.keyword}的真实体验", f"给{content.target_persona}的实用分享", f"这份{content.product}体验值得收藏"], tags=[f"#{content.keyword}"] if content.keyword else [], changes=["根据诊断计划重组内容结构"], preserved_nouns=extract_nouns(text, [content.brand, content.product, content.keyword]), route="full")


class StagedRewriteGenerator:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def generate(self, content: ContentInput, parsed: ParsedContent, plan: dict, context: dict, feedback: str = "") -> GeneratedContent:
        fallback = _rewrite(content, parsed, deep=content.rewrite_intensity == "deep" or bool(feedback))
        text = self.provider.generate(_prompt(content, parsed, plan, context, feedback, "staged"), source=content.original_text, fallback=fallback).strip()
        return GeneratedContent(text=text, titles=[f"{content.keyword or content.product}体验记录", "一份更清楚的日常分享", "适合谁？我的真实感受"], tags=[f"#{content.keyword}"] if content.keyword else [], changes=["按 opening -> core -> ending 顺序连续生成"], preserved_nouns=extract_nouns(text, [content.brand, content.product, content.keyword]), route="staged")


def _prompt(content: ContentInput, parsed: ParsedContent, plan: dict, context: dict, feedback: str, route: str) -> str:
    payload = {"original_content": content.original_text, "accepted_suggestions": plan.get("accepted_suggestions", []),
        "effective_review_policy": content.review_policy, "detected_persona": parsed.persona,
        "content_type": content.sub_direction or content.content_type, "content_goal": content.content_goal,
        "writing_style": content.writing_style, "rewrite_intensity": content.rewrite_intensity,
        "keyword": content.keyword, "product_knowledge": context.get("knowledge", []),
        "image_context": context.get("images", []),
        "previous_sections": {"opening": parsed.opening, "core": parsed.core_content, "ending": parsed.ending} if route == "staged" else {},
        "validation_feedback": feedback}
    return "Rewrite using this complete context. Preserve verified facts, apply accepted suggestions, and return only polished content.\n" + json.dumps(payload, ensure_ascii=False)
