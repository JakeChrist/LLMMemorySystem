"""Background dreaming process for summarizing episodic memory."""

from __future__ import annotations

from typing import Iterable

from core.memory_entry import MemoryEntry
from ms_utils import format_context


class DreamEngine:
    """Generate dream summaries from episodic memories."""

    def summarize(self, memories: Iterable[MemoryEntry]) -> str:
        lines = [m.content for m in memories]
        return "Dream:" + " " + format_context(lines)
