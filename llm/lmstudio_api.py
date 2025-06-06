"""Simple LMStudio REST API wrapper."""

from __future__ import annotations

import os
from typing import Any

_DEFAULT = object()

from llm.base_interface import BaseLLM

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - graceful fallback when package missing
    requests = None


class LMStudioBackend(BaseLLM):
    """HTTP client for the LMStudio local server."""

    def __init__(
        self,
        url: str | None = None,
        model: str | None = None,
        timeout: int | float | None | object = _DEFAULT,
    ) -> None:
        """Create a new LMStudio backend instance.

        Parameters
        ----------
        url:
            Endpoint for the LMStudio chat completion API.
        model:
            Model name to use for requests.
        timeout:
            Request timeout in seconds. Pass ``None`` to disable. Defaults to
            the ``LMSTUDIO_TIMEOUT`` environment variable or ``30`` seconds.
        """

        self.url = url or os.getenv("LMSTUDIO_URL", "http://localhost:1234/v1/chat/completions")
        self.model = model or os.getenv("LMSTUDIO_MODEL", "local")
        env_timeout = os.getenv("LMSTUDIO_TIMEOUT")
        if env_timeout is not None:
            env_timeout = env_timeout.strip().lower()
            if env_timeout == "none":
                env_timeout_val = None
            else:
                env_timeout_val = float(env_timeout)
        else:
            env_timeout_val = None

        if timeout is _DEFAULT:
            if env_timeout is not None:
                self.timeout = env_timeout_val
            else:
                self.timeout = 30.0
        else:
            self.timeout = timeout

    def generate(self, prompt: str) -> str:
        """Generate a completion for ``prompt`` using the LMStudio server."""

        if requests is None:
            return "LMStudio backend unavailable."
        try:
            resp = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=self.timeout,
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
