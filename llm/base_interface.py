"""Abstract base interface for LLM backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Base class that all model wrappers must implement."""

    @abstractmethod
    def generate(self, prompt: str | list[dict[str, str]]) -> str:
        """Generate a completion for ``prompt``.

        ``prompt`` may be a plain string or a list of role/content
        dictionaries following the OpenAI chat format.
        """
        raise NotImplementedError


__all__ = ["BaseLLM"]
