"""Background dreaming process for summarizing episodic memory."""

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

from ms_utils import format_context, Scheduler
import time
from llm import llm_router
from ms_utils.logger import Logger
from core.emotion_model import analyze_emotions

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
        manager: "MemoryManager" | None = None,
        log: bool = False,
    ) -> tuple[str, list[str], dict[str, float]]:
        """Return a concise dream summary using the configured LLM.

        Parameters
        ----------
        memories:
            Iterable of episodic memories to summarize.
        llm_name:
            Identifier of the LLM backend to use.
        semantic:
            Optional semantic memory store to persist the summary.
        manager:
            If provided along with ``semantic``, ``manager.add_semantic`` will be
            called so the summary is saved to persistent storage.
        log:
            If ``True``, log the produced summary using :class:`ms_utils.logger.Logger`.
        """

        lines = [m.content for m in memories]
        prompt = (
            "Summarize the following memories in 1-2 sentences or as a concise schema:\n"
            + format_context(lines)
        )
        llm = llm_router.get_llm(llm_name)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the agent's subconscious summarizing experiences."
                    " Respond in the first person as a brief dream narrative."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        summary = llm.generate(messages).strip()
        summary = "Dream: " + summary
        emotions = analyze_emotions(summary)
        labels = [e[0] for e in emotions]
        scores = {lbl: score for lbl, score in emotions}
        if semantic is not None:
            if manager is not None:
                manager.add_semantic(
                    summary, emotions=labels, emotion_scores=scores
                )
            else:
                semantic.add(summary, emotions=labels, emotion_scores=scores)
        if log:
            logger.info(summary)
        return summary, labels, scores

    def run(
        self,
        manager: MemoryManager,
        *,
        interval: float = 60.0,
        duration: float | None = None,
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
        duration:
            Total runtime in seconds before the scheduler stops automatically.
        summary_size:
            Number of most recent memories to summarize.
        max_entries:
            Maximum number of episodic memories to keep after pruning.
        """

        scheduler = Scheduler()
        now = time.monotonic()
        manager._next_dream_time = now + interval
        if duration is not None:
            manager._dream_end_time = now + duration
        else:
            manager._dream_end_time = None

        def _task() -> None:
            recent = manager.all()[-summary_size:]
            if recent:
                summary, labels, scores = self.summarize(
                    recent,
                    llm_name=llm_name,
                    semantic=manager.semantic if store_semantic else None,
                    manager=manager if store_semantic else None,
                    log=False,
                )
                manager.add(
                    summary, emotions=labels, emotion_scores=scores
                )
            manager.prune(max_entries)
            manager._next_dream_time = time.monotonic() + interval

        # ensure the first summary occurs even when duration == interval
        _task()
        scheduler.schedule(interval, _task)

        if duration is not None:
            def _stop() -> None:
                scheduler.stop()
                manager._next_dream_time = None
                manager._dream_end_time = None

            scheduler.schedule(duration, _stop)

        return scheduler
