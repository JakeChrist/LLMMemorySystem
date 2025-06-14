"""Minimal OpenAI API wrapper."""

from __future__ import annotations

import os
from typing import Any

from llm.base_interface import BaseLLM

try:  # pragma: no cover - optional dependency
    import openai
except Exception:  # pragma: no cover - fallback when package missing
    openai = None


class OpenAIBackend(BaseLLM):
    """Wrapper around ``openai`` package."""

    def __init__(self, model: str = "gpt-3.5-turbo", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if openai is not None and self.api_key:
            openai.api_key = self.api_key

    def generate(self, prompt: str | list[dict[str, str]]) -> str:
        """Return a completion for ``prompt`` using the OpenAI API."""

        if openai is None:
            return "OpenAI backend unavailable."

        if isinstance(prompt, list):
            messages = prompt
        else:
            messages = [{"role": "user", "content": prompt}]

        if hasattr(openai, "chat"):
            resp: Any = openai.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return resp.choices[0].message.content.strip()

        resp: Any = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
        )
        return resp["choices"][0]["message"]["content"].strip()


__all__ = ["OpenAIBackend"]
