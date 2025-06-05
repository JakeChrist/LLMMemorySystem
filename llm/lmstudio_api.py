"""Simple LMStudio REST API wrapper."""

from __future__ import annotations

import os
from typing import Any

from llm.base_interface import BaseLLM

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - graceful fallback when package missing
    requests = None


class LMStudioBackend(BaseLLM):
    """HTTP client for the LMStudio local server."""

    def __init__(self, url: str | None = None, model: str | None = None) -> None:
        self.url = url or os.getenv("LMSTUDIO_URL", "http://localhost:1234/v1/chat/completions")
        self.model = model or os.getenv("LMSTUDIO_MODEL", "local")

    def generate(self, prompt: str) -> str:
        if requests is None:
            return "LMStudio backend unavailable."
        try:
            resp = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            data: Any = resp.json()
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                return msg.get("content", "").strip()
            return str(data)
        except Exception as exc:  # pragma: no cover - network failure path
            return str(exc)


__all__ = ["LMStudioBackend"]
