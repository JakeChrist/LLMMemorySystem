"""Simple LLM router selecting between available backends."""

from __future__ import annotations

from typing import Literal

from llm.base_interface import BaseLLM
from llm.local_llm import LocalLLM
from llm.openai_api import OpenAIBackend
from llm.claude_api import ClaudeBackend
from llm.gemini_api import GeminiBackend


def get_llm(name: Literal["local", "openai", "claude", "gemini"] = "local") -> BaseLLM:
    if name == "local":
        return LocalLLM()
    if name == "openai":
        return OpenAIBackend()
    if name == "claude":
        return ClaudeBackend()
    if name == "gemini":
        return GeminiBackend()
    raise ValueError(f"Unknown LLM: {name}")
