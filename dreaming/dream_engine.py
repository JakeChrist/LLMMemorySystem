"""Background dreaming process for summarizing episodic memory."""

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

from ms_utils import format_context, Scheduler

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from core.memory_manager import MemoryManager
from core.memory_entry import MemoryEntry


class DreamEngine:
    """Generate dream summaries from episodic memories."""

    def summarize(self, memories: Iterable[MemoryEntry]) -> str:
        lines = [m.content for m in memories]
        return "Dream:" + " " + format_context(lines)

    def run(
        self,
        manager: MemoryManager,
        *,
        interval: float = 60.0,
        summary_size: int = 5,
        max_entries: int = 100,
    ) -> Scheduler:
        """Periodically summarize recent memories and prune old ones.

        Parameters
        ----------
        manager:
            Memory manager providing episodic entries.
        interval:
            Seconds between summarization runs.
        summary_size:
            Number of most recent memories to summarize.
        max_entries:
            Maximum number of episodic memories to keep after pruning.
        """

        scheduler = Scheduler()

        def _task() -> None:
            recent = manager.all()[-summary_size:]
            if recent:
                manager.add(self.summarize(recent))
            manager.prune(max_entries)

        scheduler.schedule(interval, _task)
        return scheduler
