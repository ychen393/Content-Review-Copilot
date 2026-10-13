from __future__ import annotations

import re
import json
import os
import urllib.request
from abc import ABC, abstractmethod
from typing import Any
from dotenv import load_dotenv
from .models import ImageAnalysis


class LLMProvider(ABC):
    provider_name = "Unknown"
    model = ""
    mode = "unknown"
    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str: ...

    @abstractmethod
    def structured_generate(self, prompt: str, schema: type[Any], **kwargs: Any) -> Any: ...

    @abstractmethod
    def vision(self, images: list[str], **kwargs: Any) -> list[ImageAnalysis]: ...


class MockLLMProvider(LLMProvider):
    """Deterministic local provider used by tests and the demo."""
    provider_name = "Mock"
    model = "mock-v1"
    mode = "demo"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return kwargs.get("fallback", "") or kwargs.get("source", "") or "把真实体验整理成清晰、可信、易读的分享。"

    def structured_generate(self, prompt: str, schema: type[Any], **kwargs: Any) -> Any:
        return schema.model_validate(kwargs.get("value", {}))

    def vision(self, images: list[str], **kwargs: Any) -> list[ImageAnalysis]:
        results = []
        for index, image in enumerate(images, 1):
            label = image.split("|") if "|" in image else [image]
            results.append(ImageAnalysis(image_id=f"图{index}", scene=label[0], image_text=label[1:2], other_products=[], style="简约干净"))
        return results


def extract_nouns(text: str, candidates: list[str]) -> list[str]:
    return [candidate for candidate in candidates if candidate and candidate in text]


class RealLLMProvider(LLMProvider):
    """OpenAI-compatible provider configured exclusively through environment variables."""
    provider_name = "Real LLM Provider"
    mode = "live"

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1") -> None:
        self.model, self.api_key, self.base_url = model, api_key, base_url.rstrip("/")

    def generate(self, prompt: str, **kwargs: Any) -> str:
        payload = json.dumps({"model": self.model, "messages": [{"role": "system", "content": "You are a careful content editor. Return only the rewritten content."}, {"role": "user", "content": prompt}], "temperature": 0.4}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(f"{self.base_url}/chat/completions", data=payload, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def structured_generate(self, prompt: str, schema: type[Any], **kwargs: Any) -> Any:
        return schema.model_validate_json(self.generate(prompt + "\nReturn valid JSON only.", **kwargs))

    def vision(self, images: list[str], **kwargs: Any) -> list[ImageAnalysis]:
        return []


def configured_provider() -> LLMProvider:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    model = os.getenv("LLM_MODEL", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if provider not in {"", "mock", "demo"} and model and api_key:
        return RealLLMProvider(model, api_key, os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))
    return MockLLMProvider()
