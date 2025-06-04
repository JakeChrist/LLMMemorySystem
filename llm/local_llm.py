"""Extremely small local LLM stub."""

from __future__ import annotations

from llm.base_interface import BaseLLM


class LocalLLM(BaseLLM):
    def generate(self, prompt: str) -> str:
        return f"Echo: {prompt}"
