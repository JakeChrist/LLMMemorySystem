"""Manage creation and storage of memories."""

from __future__ import annotations

from typing import Iterable, List

from core.memory_entry import MemoryEntry
from core.memory_types.episodic import EpisodicMemory
from core.memory_types.semantic import SemanticMemory
from core.memory_types.procedural import ProceduralMemory
from core.working_memory import WorkingMemory


class MemoryManager:
    """Coordinator for different memory systems."""

    def __init__(self) -> None:
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.working = WorkingMemory()

    def add(self, content: str, *, emotions: Iterable[str] | None = None, metadata: dict | None = None) -> MemoryEntry:
        """Add content to episodic memory and update working memory."""
        entry = self.episodic.add(content, emotions=emotions, metadata=metadata)
        self.working.load(self.episodic.all())
        return entry

    def all(self) -> List[MemoryEntry]:
        return self.episodic.all()
