"""Simple LLM router selecting between available backends."""

from __future__ import annotations

from typing import Literal

from llm.base_interface import BaseLLM
from llm.local_llm import LocalLLM
from llm.openai_api import OpenAIBackend
from llm.claude_api import ClaudeBackend
from llm.gemini_api import GeminiBackend
from llm.lmstudio_api import LMStudioBackend


def get_llm(name: Literal["local", "openai", "claude", "gemini", "lmstudio"] = "local") -> BaseLLM:
    if name == "local":
        return LocalLLM()
    if name == "openai":
        return OpenAIBackend()
    if name == "claude":
        return ClaudeBackend()
    if name == "gemini":
        return GeminiBackend()
    if name == "lmstudio":
        return LMStudioBackend()
    raise ValueError(f"Unknown LLM: {name}")
