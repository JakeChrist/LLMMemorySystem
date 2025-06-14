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
            Model name to use for requests. If omitted and ``LMSTUDIO_MODEL`` is
            not set, the backend attempts to detect the loaded model from the
            LMStudio server.
        timeout:
            Request timeout in seconds. Pass ``None`` to disable. Defaults to
            the ``LMSTUDIO_TIMEOUT`` environment variable or ``30`` seconds.
        """

        self.url = url or os.getenv(
            "LMSTUDIO_URL", "http://localhost:1234/v1/chat/completions"
        )
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

        if model is not None:
            self.model = model
        else:
            env_model = os.getenv("LMSTUDIO_MODEL")
            if env_model:
                self.model = env_model
            else:
                detected = self._detect_model()
                self.model = detected or "local"

    def _detect_model(self) -> str | None:
        """Attempt to detect the active model from the LMStudio server."""

        if requests is None:
            return None
        try:
            models_url = self.url.replace("chat/completions", "models")
            resp = requests.get(models_url, timeout=self.timeout or 5)
            data: Any = resp.json()
            models = data.get("data") or data.get("models")
            if isinstance(models, list) and models:
                first = models[0]
                if isinstance(first, dict):
                    return str(first.get("id"))
                return str(first)
        except Exception:
            return None
        return None

    def generate(self, prompt: str | list[dict[str, str]]) -> str:
        """Generate a completion for ``prompt`` using the LMStudio server."""

        if requests is None:
            return "LMStudio backend unavailable."

        if isinstance(prompt, list):
            messages = prompt
        else:
            messages = [{"role": "user", "content": prompt}]

        try:
            resp = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "messages": messages,
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
