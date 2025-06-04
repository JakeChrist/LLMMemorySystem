"""Reconstruct working memory context from retrieved entries."""

from typing import Iterable

from core.memory_entry import MemoryEntry
from ms_utils import format_context


class Reconstructor:
    """Simple reconstructor that joins memory contents."""

    def build_context(self, memories: Iterable[MemoryEntry]) -> str:
        lines = [m.content for m in memories]
        return format_context(lines)
