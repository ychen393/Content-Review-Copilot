from __future__ import annotations

from .generators import StagedRewriteGenerator
from .models import ContentInput, GeneratedContent, ParsedContent, RevisionInstruction
from .providers import configured_provider


class SectionRegenerator:
    def __init__(self, provider=None) -> None:
        self.provider = provider or configured_provider()

    def regenerate(self, section: str, content: ContentInput, parsed: ParsedContent, instruction: str = "") -> GeneratedContent:
        generated = StagedRewriteGenerator(self.provider).generate(content, parsed, {}, {}, feedback=instruction)
        sections = {"opening": parsed.opening, "core": parsed.core_content, "ending": parsed.ending}
        if section in sections:
            index = {"opening": 0, "core": 1, "ending": 2}[section]
            sections[section] = f"{generated.text.splitlines()[index]} {instruction}".strip()
        text = "\n".join(value for value in (sections["opening"], sections["core"], sections["ending"]) if value)
        return GeneratedContent(text=text, titles=generated.titles, tags=parsed.tags, changes=[f"Regenerated {section}"], preserved_nouns=generated.preserved_nouns, route="staged")

    def regenerate_titles(self, content: ContentInput, parsed: ParsedContent, instruction: str = "") -> GeneratedContent:
        generated = StagedRewriteGenerator(self.provider).generate(content, parsed, {}, {}, feedback=instruction)
        titles = [f"{title} {instruction}".strip() for title in generated.titles]
        text = "\n".join(value for value in (parsed.opening, parsed.core_content, parsed.ending) if value)
        return GeneratedContent(text=text, titles=titles, tags=parsed.tags, changes=["Regenerated titles"], preserved_nouns=generated.preserved_nouns, route="staged")


class RevisionService:
    def __init__(self, provider=None) -> None:
        self.provider = provider or configured_provider()

    def revise(self, current_content: str, instruction: RevisionInstruction, content: ContentInput) -> str:
        fallback = f"{current_content}\n\n[Revision applied: {instruction.instruction}]"
        prompt = f"Revise the content according to the instruction while preserving facts. Return only the revised content.\nInstruction: {instruction.instruction}\nContent:\n{current_content}"
        return self.provider.generate(prompt, source=current_content, fallback=fallback).strip()
