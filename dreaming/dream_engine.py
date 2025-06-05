"""Background dreaming process for summarizing episodic memory."""

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

from ms_utils import format_context, Scheduler
import time
from llm import llm_router
from ms_utils.logger import Logger

logger = Logger(__name__)
from core.memory_types.semantic import SemanticMemory

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from core.memory_manager import MemoryManager
from core.memory_entry import MemoryEntry


class DreamEngine:
    """Generate dream summaries from episodic memories."""

    def summarize(
        self,
        memories: Iterable[MemoryEntry],
        *,
        llm_name: str = "local",
        semantic: SemanticMemory | None = None,
    ) -> str:
        """Return a concise dream summary using the configured LLM.

        Parameters
        ----------
        memories:
            Iterable of episodic memories to summarize.
        llm_name:
            Identifier of the LLM backend to use.
        semantic:
            Optional semantic memory store to persist the summary.
        """

        lines = [m.content for m in memories]
        prompt = (
            "Summarize the following memories in 1-2 sentences or as a concise schema:\n"
            + format_context(lines)
        )
        llm = llm_router.get_llm(llm_name)
        summary = llm.generate(prompt).strip()
        summary = "Dream: " + summary
        if semantic is not None:
            semantic.add(summary)
        logger.info(summary)
        return summary

    def run(
        self,
        manager: MemoryManager,
        *,
        interval: float = 60.0,
        summary_size: int = 5,
        max_entries: int = 100,
        llm_name: str = "local",
        store_semantic: bool = False,
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
        manager._next_dream_time = time.monotonic() + interval

        def _task() -> None:
            recent = manager.all()[-summary_size:]
            if recent:
                summary = self.summarize(
                    recent,
                    llm_name=llm_name,
                    semantic=manager.semantic if store_semantic else None,
                )
                manager.add(summary)
            manager.prune(max_entries)
            manager._next_dream_time = time.monotonic() + interval

        scheduler.schedule(interval, _task)
        return scheduler
