"""Brief-driven content drafting, deliberately separate from the rewrite pipeline."""
from __future__ import annotations
from pydantic import BaseModel, Field
from backend.providers import LLMProvider, configured_provider
from .workspace import WorkspaceRepository, ItemCreate, VersionCreate


class GenerateRequest(BaseModel):
    instruction: str = Field(default="", max_length=3000)


class DraftGenerationService:
    def __init__(self, workspace: WorkspaceRepository, provider: LLMProvider | None = None):
        self.workspace = workspace
        self.provider = provider or configured_provider()

    def generate_one(self, task_id: str, instruction: str = "") -> dict:
        task = self.workspace.get_task(task_id)
        if not task:
            raise LookupError("Task not found")
        if task["mode"] != "generate":
            raise ValueError("Only generate-mode tasks can create drafts")
        project = self.workspace.get_project(task["project_id"])
        if not task.get("brief", "").strip():
            raise ValueError("A non-empty Brief is required")
        if not project:
            raise LookupError("Project not found")
        # Demo output is deliberately not passed off as live model output.
        provider = self.provider
        is_demo = getattr(provider, "mode", "") != "live"
        prompt = (
            "Create ONE original, clearly identified brand marketing draft, not a fabricated "
            "first-person testimonial or undisclosed consumer endorsement. Only use "
            "verified facts explicitly provided below; do not invent usage claims, "
            "statistics, certifications, guarantees or personal experience. "
            "Output only the draft text.\n"
            f"Platform: {project.get('platform', '')}\n"
            f"Brand: {project.get('brand', '')}\n"
            f"Product: {project.get('product', '')}\n"
            f"Project notes: {project.get('description', '')}\n"
            f"Brief: {task['brief']}\n"
            f"Additional instructions: {instruction}\n"
        )
        # Generate before persistence, preventing failed model calls from creating an item.
        text = provider.generate(prompt).strip()
        if not text:
            raise ValueError("Model returned an empty draft")
        item = self.workspace.create_item(task_id, ItemCreate(title="AI 生成初稿", body=text))
        # Persist actual provenance as part of the item payload without replacing version history.
        return {**item, "generation": {
            "provider": provider.provider_name, "model": provider.model,
            "mode": "demo" if is_demo else "live",
            "note": "Mock 示例，不代表真实 AI 生成" if is_demo else "待人工审核",
        }}
