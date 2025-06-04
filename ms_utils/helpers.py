"""Utility helper functions."""

from typing import Iterable


def format_context(context: Iterable[str]) -> str:
    """Return newline-joined string from iterable of context lines."""
    return "\n".join(context)
