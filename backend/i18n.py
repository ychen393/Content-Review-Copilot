from __future__ import annotations

import json
from pathlib import Path


class Translator:
    def __init__(self, language: str = "zh", directory: str | Path = "translations") -> None:
        self.language = language
        self.directory = Path(directory)
        self.translations = self._load(language)
        self.fallback = self._load("en" if language == "zh" else "zh")

    def _load(self, language: str) -> dict[str, str]:
        path = self.directory / f"{language}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def get(self, key: str, default: str | None = None) -> str:
        return self.translations.get(key, self.fallback.get(key, default or key))

    def __call__(self, key: str, default: str | None = None) -> str:
        return self.get(key, default)


def detect_content_language(text: str) -> str:
    if not text.strip():
        return "unknown"
    chinese = sum("\u4e00" <= char <= "\u9fff" for char in text)
    latin = sum(char.isalpha() and ord(char) < 128 for char in text)
    return "zh" if chinese >= latin else "en"
