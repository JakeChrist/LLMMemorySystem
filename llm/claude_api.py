"""Minimal Anthropic Claude API wrapper."""

from __future__ import annotations

import os
from typing import Any

from llm.base_interface import BaseLLM

try:  # pragma: no cover - optional dependency
    import anthropic
except Exception:  # pragma: no cover - fallback when package missing
    anthropic = None


class ClaudeBackend(BaseLLM):
    """Wrapper around the ``anthropic`` package."""

    def __init__(self, model: str = "claude-3-opus-20240229", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if anthropic is not None and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:  # pragma: no cover - degrade gracefully
            self.client = None

    def generate(self, prompt: str | list[dict[str, str]]) -> str:
        """Return a completion for ``prompt`` using Anthropic's API."""

        if self.client is None:
            return "Claude backend unavailable."

        if isinstance(prompt, list):
            messages = prompt
        else:
            messages = [{"role": "user", "content": prompt}]

        resp: Any = self.client.messages.create(
            model=self.model,
            messages=messages,
            max_tokens=512,
        )
        # anthropic 0.24 returns resp.content[0].text
        content = getattr(resp, "content", None)
        if isinstance(content, list) and content:
            return getattr(content[0], "text", "").strip()
        return getattr(resp, "completion", "").strip()


__all__ = ["ClaudeBackend"]
