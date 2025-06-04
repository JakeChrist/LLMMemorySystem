"""Short-term working memory manager."""

from __future__ import annotations

from typing import Iterable, List

from core.memory_entry import MemoryEntry


class WorkingMemory:
    """Maintain a limited-size list of active memories."""

    def __init__(self, max_size: int = 10) -> None:
        self.max_size = max_size
        self._entries: List[MemoryEntry] = []

    def load(self, memories: Iterable[MemoryEntry]) -> None:
        self._entries = list(memories)[-self.max_size :]

    def contents(self) -> List[MemoryEntry]:
        return list(self._entries)
