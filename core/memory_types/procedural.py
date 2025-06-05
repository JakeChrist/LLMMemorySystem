"""Procedural memory store."""

from __future__ import annotations

from typing import Iterable, List

from core.memory_entry import MemoryEntry
from encoding.encoder import encode_text


class ProceduralMemory:
    """Skills and procedures."""

    def __init__(self) -> None:
        self._entries: List[MemoryEntry] = []

    def add(
        self,
        content: str,
        *,
        emotions: Iterable[str] | None = None,
        emotion_scores: dict[str, float] | None = None,
        metadata: dict | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            embedding=encode_text(content),
            emotions=list(emotions or []),
            emotion_scores=emotion_scores or {},
            metadata=metadata or {},
        )
        self._entries.append(entry)
        return entry

    def all(self) -> List[MemoryEntry]:
        return list(self._entries)
