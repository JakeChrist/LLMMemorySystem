"""Minimal Google Gemini API wrapper."""

from __future__ import annotations

import os
from typing import Any

from llm.base_interface import BaseLLM

try:  # pragma: no cover - optional dependency
    import google.generativeai as genai
except Exception:  # pragma: no cover - fallback when package missing
    genai = None


class GeminiBackend(BaseLLM):
    """Wrapper around ``google.generativeai`` package."""

    def __init__(self, model: str = "gemini-pro", api_key: str | None = None) -> None:
        self.model_name = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if genai is not None and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model)
        else:  # pragma: no cover - degrade gracefully
            self.model = None

    def generate(self, prompt: str) -> str:
        if self.model is None:
            return "Gemini backend unavailable."
        resp: Any = self.model.generate_content(prompt)
        return getattr(resp, "text", str(resp)).strip()


__all__ = ["GeminiBackend"]
