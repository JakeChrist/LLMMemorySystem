"""Manage creation and storage of memories."""

from __future__ import annotations

from typing import Iterable, List

from pathlib import Path

from core.memory_entry import MemoryEntry
from core.memory_types.episodic import EpisodicMemory
from core.memory_types.semantic import SemanticMemory
from core.memory_types.procedural import ProceduralMemory
from core.working_memory import WorkingMemory
from reconstruction.reconstructor import _load_config
from dreaming.dream_engine import DreamEngine
from ms_utils.scheduler import Scheduler
import time
from storage.db_interface import Database


class MemoryManager:
    """Coordinator for different memory systems."""

    def __init__(self, db_path: str | Path = "memory.db") -> None:
        self.db = Database(db_path)
        cfg = _load_config()
        working_size = cfg.get("memory", {}).get("working_size", 10)
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.working = WorkingMemory(working_size)

        # Load any existing memories from the database into memory stores
        episodic = self.db.load_all()
        self.episodic._entries.extend(episodic)
        semantic = self.db.load_all_semantic()
        self.semantic._entries.extend(semantic)
        procedural = self.db.load_all_procedural()
        self.procedural._entries.extend(procedural)
        if episodic:
            self.working.load(self.episodic.all())

    def add(self, content: str, *, emotions: Iterable[str] | None = None, metadata: dict | None = None) -> MemoryEntry:
        """Add content to episodic memory and update working memory."""
        from encoding.tagging import tag_text

        tags = tag_text(content)
        meta = dict(metadata or {})
        meta["tags"] = tags

        entry = self.episodic.add(content, emotions=emotions, metadata=meta)
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
            from encoding.tagging import tag_text

            entry.embedding = encode_text(new_content)
            entry.metadata["tags"] = tag_text(new_content)
            self.db.update(entry.timestamp, entry)
            self.working.load(self.episodic.all())

    # --- Semantic memory helpers ---
    def add_semantic(
        self, content: str, *, emotions: Iterable[str] | None = None, metadata: dict | None = None
    ) -> MemoryEntry:
        entry = self.semantic.add(content, emotions=emotions, metadata=metadata)
        self.db.save_semantic(entry)
        return entry

    def delete_semantic(self, entry: MemoryEntry) -> None:
        if entry in self.semantic._entries:
            self.semantic._entries.remove(entry)
            self.db.delete_semantic(entry.timestamp)

    def update_semantic(self, entry: MemoryEntry, new_content: str) -> None:
        if entry in self.semantic._entries:
            entry.content = new_content
            from encoding.encoder import encode_text

            entry.embedding = encode_text(new_content)
            self.db.update_semantic(entry.timestamp, entry)

    # --- Procedural memory helpers ---
    def add_procedural(
        self, content: str, *, emotions: Iterable[str] | None = None, metadata: dict | None = None
    ) -> MemoryEntry:
        entry = self.procedural.add(content, emotions=emotions, metadata=metadata)
        self.db.save_procedural(entry)
        return entry

    def delete_procedural(self, entry: MemoryEntry) -> None:
        if entry in self.procedural._entries:
            self.procedural._entries.remove(entry)
            self.db.delete_procedural(entry.timestamp)

    def update_procedural(self, entry: MemoryEntry, new_content: str) -> None:
        if entry in self.procedural._entries:
            entry.content = new_content
            from encoding.encoder import encode_text

            entry.embedding = encode_text(new_content)
            self.db.update_procedural(entry.timestamp, entry)

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
        self._dream_interval = interval
        self._next_dream_time = time.monotonic() + interval
        return self._dream_scheduler

    def stop_dreaming(self) -> None:
        """Stop the background dreaming scheduler if running."""
        sched = getattr(self, "_dream_scheduler", None)
        if isinstance(sched, Scheduler):
            sched.stop()
        self._next_dream_time = None

    def time_until_dream(self) -> float | None:
        """Return seconds until the next scheduled dream or ``None``."""
        next_time = getattr(self, "_next_dream_time", None)
        if next_time is None:
            return None
        return max(0.0, next_time - time.monotonic())
