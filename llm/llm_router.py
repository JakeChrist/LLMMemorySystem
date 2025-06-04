"""Simple LLM router selecting between available backends."""

from __future__ import annotations

from typing import Literal

from llm.local_llm import LocalLLM


def get_llm(name: Literal["local"] = "local") -> LocalLLM:
    if name == "local":
        return LocalLLM()
    raise ValueError(f"Unknown LLM: {name}")
