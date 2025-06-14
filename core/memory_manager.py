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
from thinking.thinking_engine import ThinkingEngine
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

        self._next_think_time: float | None = None
        self._think_end_time: float | None = None
        self._next_dream_time: float | None = None
        self._dream_end_time: float | None = None

        # Load any existing memories from the database into memory stores
        episodic = self.db.load_all()
        self.episodic._entries.extend(episodic)
        semantic = self.db.load_all_semantic()
        self.semantic._entries.extend(semantic)
        procedural = self.db.load_all_procedural()
        self.procedural._entries.extend(procedural)
        if episodic:
            self.working.load(self.episodic.all())

    def add(
        self,
        content: str,
        *,
        emotions: Iterable[str] | None = None,
        emotion_scores: dict[str, float] | None = None,
        metadata: dict | None = None,
    ) -> MemoryEntry:
        """Add content to episodic memory and update working memory."""
        from encoding.tagging import tag_text

        tags = tag_text(content)
        meta = dict(metadata or {})
        meta_tags = list(meta.get("tags", []))
        for tag in tags:
            if tag not in meta_tags:
                meta_tags.append(tag)
        meta["tags"] = meta_tags

        entry = self.episodic.add(
            content,
            emotions=emotions,
            emotion_scores=emotion_scores,
            metadata=meta,
        )
        self.db.save(entry)
        self.working.load(self.episodic.all())
        return entry

    def all(self) -> List[MemoryEntry]:
        return self.episodic.all()

    def all_memories(self) -> List[MemoryEntry]:
        """Return episodic, semantic and procedural memories sorted by timestamp."""
        entries = (
            list(self.episodic.all())
            + list(self.semantic.all())
            + list(self.procedural.all())
        )
        return sorted(entries, key=lambda m: m.timestamp)

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
        self,
        content: str,
        *,
        emotions: Iterable[str] | None = None,
        emotion_scores: dict[str, float] | None = None,
        metadata: dict | None = None,
    ) -> MemoryEntry:
        entry = self.semantic.add(
            content,
            emotions=emotions,
            emotion_scores=emotion_scores,
            metadata=metadata,
        )
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
        self,
        content: str,
        *,
        emotions: Iterable[str] | None = None,
        emotion_scores: dict[str, float] | None = None,
        metadata: dict | None = None,
    ) -> MemoryEntry:
        entry = self.procedural.add(
            content,
            emotions=emotions,
            emotion_scores=emotion_scores,
            metadata=metadata,
        )
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
        duration: float | None = None,
        summary_size: int = 5,
        max_entries: int = 100,
        llm_name: str = "local",
    ) -> Scheduler:
        """Start background dreaming with the :class:`DreamEngine`.

        Any active thinking scheduler will be automatically stopped before
        launching a new dreaming task. The ``duration`` parameter controls how
        long the dreaming loop runs before stopping automatically.
        """

        # Cancel an existing thinking loop if present
        self.stop_thinking()

        engine = DreamEngine()
        self._dream_scheduler = engine.run(
            self,
            interval=interval,
            duration=duration,
            summary_size=summary_size,
            max_entries=max_entries,
            llm_name=llm_name,
        )
        self._dream_interval = interval
        now = time.monotonic()
        self._next_dream_time = now + interval
        self._dream_end_time = now + duration if duration is not None else None
        return self._dream_scheduler

    def stop_dreaming(self) -> None:
        """Stop the background dreaming scheduler if running."""
        sched = getattr(self, "_dream_scheduler", None)
        if isinstance(sched, Scheduler):
            sched.stop()
        self._next_dream_time = None
        self._dream_end_time = None

    def time_until_dream(self) -> float | None:
        """Return seconds until the next scheduled dream or ``None``."""
        next_time = getattr(self, "_next_dream_time", None)
        end_time = getattr(self, "_dream_end_time", None)
        now = time.monotonic()
        if next_time is None or (end_time is not None and now >= end_time):
            return None
        if end_time is not None:
            next_time = min(next_time, end_time)
        return max(0.0, next_time - now)

    def start_thinking(
        self,
        *,
        interval: float = 60.0,
        duration: float | None = None,
        llm_name: str = "local",
        use_reasoning: bool | None = None,
        reasoning_depth: int | None = None,
    ) -> Scheduler:
        """Start periodic introspective thinking via :class:`ThinkingEngine`.

        Any active dreaming scheduler will be automatically cancelled before
        launching a new thinking task. The ``duration`` parameter controls how
        long the thinking loop runs before it automatically stops.
        """

        # Cancel an existing dreaming loop if present
        self.stop_dreaming()

        cfg = _load_config()
        r_cfg = cfg.get("reasoning", {})
        if use_reasoning is None:
            use_reasoning = r_cfg.get("enabled", False)
        if reasoning_depth is None:
            reasoning_depth = r_cfg.get("depth", 1)

        engine = ThinkingEngine()
        self._think_scheduler = engine.run(
            self,
            interval=interval,
            duration=duration,
            llm_name=llm_name,
            use_reasoning=use_reasoning,
            reasoning_depth=reasoning_depth,
        )
        self._think_interval = interval
        now = time.monotonic()
        self._next_think_time = now + interval
        self._think_end_time = now + duration if duration is not None else None
        return self._think_scheduler

    def stop_thinking(self) -> None:
        """Stop the background thinking scheduler if running."""
        sched = getattr(self, "_think_scheduler", None)
        if isinstance(sched, Scheduler):
            sched.stop()
        self._next_think_time = None
        self._think_end_time = None

    def time_until_think(self) -> float | None:
        """Return seconds until the next scheduled thought or ``None``."""
        next_time = getattr(self, "_next_think_time", None)
        end_time = getattr(self, "_think_end_time", None)
        now = time.monotonic()
        if next_time is None or (end_time is not None and now >= end_time):
            return None
        if end_time is not None:
            next_time = min(next_time, end_time)
        return max(0.0, next_time - now)
