"""Manage creation and storage of memories."""

from __future__ import annotations

from typing import Iterable, List

from pathlib import Path

from core.memory_entry import MemoryEntry
from core.memory_types.episodic import EpisodicMemory
from core.memory_types.semantic import SemanticMemory
from core.memory_types.procedural import ProceduralMemory
from core.working_memory import WorkingMemory
from dreaming.dream_engine import DreamEngine
from ms_utils.scheduler import Scheduler
from storage.db_interface import Database


class MemoryManager:
    """Coordinator for different memory systems."""

    def __init__(self, db_path: str | Path = "memory.db") -> None:
        self.db = Database(db_path)
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.working = WorkingMemory()

        # Load any existing memories from the database into episodic memory
        existing = self.db.load_all()
        self.episodic._entries.extend(existing)
        if existing:
            self.working.load(self.episodic.all())

    def add(self, content: str, *, emotions: Iterable[str] | None = None, metadata: dict | None = None) -> MemoryEntry:
        """Add content to episodic memory and update working memory."""
        entry = self.episodic.add(content, emotions=emotions, metadata=metadata)
        self.db.save(entry)
        self.working.load(self.episodic.all())
        return entry

    def all(self) -> List[MemoryEntry]:
        return self.episodic.all()

    def prune(self, max_entries: int) -> None:
        """Remove oldest episodic memories beyond ``max_entries``."""
        self.episodic.prune(max_entries)
        self.working.load(self.episodic.all())

    def delete(self, entry: MemoryEntry) -> None:
        """Remove ``entry`` from memory and persistent storage."""
        if entry in self.episodic._entries:
            self.episodic._entries.remove(entry)
            self.db.delete(entry.timestamp)
            self.working.load(self.episodic.all())

    def update(self, entry: MemoryEntry, new_content: str) -> None:
        """Modify the content of ``entry`` and persist the change."""
        if entry in self.episodic._entries:
            entry.content = new_content
            from encoding.encoder import encode_text

            entry.embedding = encode_text(new_content)
            self.db.update(entry.timestamp, entry)
            self.working.load(self.episodic.all())

    def start_dreaming(
        self,
        *,
        interval: float = 60.0,
        summary_size: int = 5,
        max_entries: int = 100,
    ) -> Scheduler:
        """Start background dreaming with the :class:`DreamEngine`."""

        engine = DreamEngine()
        self._dream_scheduler = engine.run(
            self,
            interval=interval,
            summary_size=summary_size,
            max_entries=max_entries,
        )
        return self._dream_scheduler

    def stop_dreaming(self) -> None:
        """Stop the background dreaming scheduler if running."""
        sched = getattr(self, "_dream_scheduler", None)
        if isinstance(sched, Scheduler):
            sched.stop()
