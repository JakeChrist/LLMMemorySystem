"""Abstract base interface for LLM backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Base class that all model wrappers must implement."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a completion for the given prompt."""
        raise NotImplementedError


__all__ = ["BaseLLM"]
