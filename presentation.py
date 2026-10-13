from __future__ import annotations

from typing import Any


DISPLAY = {
    "zh": {
        "severity": {"low": "低风险", "medium": "中等风险", "high": "高风险"},
        "issue_type": {"keyword": "关键词缺失", "compliance": "合规问题", "persona": "人设匹配", "product_fact": "产品事实", "image_text": "图文一致性", "structure": "结构问题"},
        "route": {"staged": "分段优化", "full": "整篇改写"},
        "language": {"auto": "自动识别", "zh": "中文", "en": "英文", "unknown": "未识别"},
        "content_type": {"生活方式": "日常分享", "纯路人": "自然分享"},
        "content_direction": {"日常分享": "日常分享", "产品体验": "产品体验", "知识科普": "知识科普", "场景种草": "场景种草", "产品测评": "产品测评", "对比推荐": "对比推荐", "问题解决": "问题解决", "新品介绍": "新品介绍", "活动内容": "活动内容", "FAQ / 答疑": "FAQ / 答疑"},
        "content_goal": {"品牌认知": "品牌认知", "产品介绍": "产品介绍", "知识教育": "知识教育", "种草": "种草", "转化": "转化", "用户互动": "用户互动"},
        "writing_style": {"真实自然": "真实自然", "专业可信": "专业可信", "轻松活泼": "轻松活泼", "简洁直接": "简洁直接", "温暖生活化": "温暖生活化"},
        "intensity": {"light": "轻度润色", "standard": "正常优化", "deep": "深度改写"},
        "rule_type": {"hard": "硬性规则", "soft": "软性规则"},
        "rule_source": {"task": "本次任务要求", "brand": "品牌规则", "product": "产品知识", "platform": "平台示例规则", "rubric": "内容质量标准", "custom": "自定义规则"},
        "area": {"opening": "开头", "core": "核心内容", "ending": "结尾", "persona": "人设", "multimodal": "多模态"},
        "decision": {"accepted": "已接受", "ignored": "已忽略", "regenerate": "待重新生成"},
        "status": {"success": "成功", "failed": "失败", "skipped": "已跳过"},
        "trace_step": {"Input Parsed": "输入解析", "Context Resolved": "上下文识别", "Vision Analysis": "图片理解", "Rule Retrieval": "规则检索", "Hard Rule Check": "硬性规则检查", "Content Parsing": "内容解析", "Opening Evaluation": "开头诊断", "Core Evaluation": "核心内容诊断", "Ending Evaluation": "结尾诊断", "Persona Evaluation": "人设诊断", "Rewrite Planning": "改写规划", "Generation Routing": "生成方式选择", "Content Generation": "改写生成", "Final Evaluation": "最终评估"},
    },
    "en": {
        "severity": {"low": "Low", "medium": "Medium", "high": "High"},
        "issue_type": {"keyword": "Missing keyword", "compliance": "Compliance", "persona": "Persona alignment", "product_fact": "Product fact", "image_text": "Image-text consistency", "structure": "Structure"},
        "route": {"staged": "Staged optimization", "full": "Full rewrite"},
        "language": {"auto": "Auto-detected", "zh": "Chinese", "en": "English", "unknown": "Not detected"},
        "content_type": {"生活方式": "Lifestyle sharing", "纯路人": "Natural sharing"},
        "content_direction": {"日常分享": "Daily sharing", "产品体验": "Product experience", "知识科普": "Educational content", "场景种草": "Scenario recommendation", "产品测评": "Product review", "对比推荐": "Comparison", "问题解决": "Problem solving", "新品介绍": "Product launch", "活动内容": "Campaign content", "FAQ / 答疑": "FAQ"},
        "content_goal": {"品牌认知": "Brand awareness", "产品介绍": "Product introduction", "知识教育": "Education", "种草": "Recommendation", "转化": "Conversion", "用户互动": "Engagement"},
        "writing_style": {"真实自然": "Authentic", "专业可信": "Professional", "轻松活泼": "Lighthearted", "简洁直接": "Concise", "温暖生活化": "Warm lifestyle"},
        "intensity": {"light": "Light", "standard": "Standard", "deep": "Deep"},
        "rule_type": {"hard": "Hard rule", "soft": "Soft rule"},
        "rule_source": {"task": "Task requirements", "brand": "Brand rules", "product": "Product knowledge", "platform": "Demo platform rules", "rubric": "Content quality rubric", "custom": "Custom rules"},
        "area": {"opening": "Opening", "core": "Core content", "ending": "Ending", "persona": "Persona", "multimodal": "Multimodal"},
        "decision": {"accepted": "Accepted", "ignored": "Ignored", "regenerate": "Needs regeneration"},
        "status": {"success": "Succeeded", "failed": "Failed", "skipped": "Skipped"},
        "trace_step": {"Input Parsed": "Input parsing", "Context Resolved": "Context resolution", "Vision Analysis": "Vision analysis", "Rule Retrieval": "Rule retrieval", "Hard Rule Check": "Hard-rule check", "Content Parsing": "Content parsing", "Opening Evaluation": "Opening diagnosis", "Core Evaluation": "Core-content diagnosis", "Ending Evaluation": "Ending diagnosis", "Persona Evaluation": "Persona diagnosis", "Rewrite Planning": "Rewrite planning", "Generation Routing": "Generation routing", "Content Generation": "Content generation", "Final Evaluation": "Final evaluation"},
    },
}


def label(group: str, value: Any, language: str, default: str | None = None) -> str:
    return DISPLAY.get(language, DISPLAY["en"]).get(group, {}).get(str(value), default or str(value))


def content_language_label(selected: str, detected: str, language: str) -> str:
    selected_label = label("language", selected, language)
    detected_label = label("language", detected, language)
    return selected_label if selected != "auto" else f"{selected_label} · {detected_label}"
