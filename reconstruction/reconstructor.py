"""Reconstruct working memory context from retrieved entries."""

from __future__ import annotations

from typing import Iterable

from core.memory_entry import MemoryEntry
from ms_utils import format_context


class Reconstructor:
    """Combine memory fragments into a context string."""

    def build_context(self, memories: Iterable[MemoryEntry]) -> str:
        # sort by timestamp so recent memories come last
        ordered = sorted(memories, key=lambda m: m.timestamp)
        lines = [m.content for m in ordered]
        return format_context(lines)
