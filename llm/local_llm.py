"""Extremely small local LLM stub."""

from __future__ import annotations

from llm.base_interface import BaseLLM


class LocalLLM(BaseLLM):
    def generate(self, prompt: str | list[dict[str, str]]) -> str:
        return "Local backend unavailable."
