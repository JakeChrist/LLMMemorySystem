"""Autonomous self-reflection engine."""

from __future__ import annotations

import random
import time
from typing import Iterable, List, TYPE_CHECKING

from retrieval.cue_builder import build_cue
from retrieval.retriever import Retriever
from reconstruction.reconstructor import Reconstructor
from llm import llm_router
from ms_utils import Scheduler
from ms_utils.logger import Logger
from core.emotion_model import analyze_emotions
from reasoning import ReasoningEngine

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from core.memory_manager import MemoryManager


logger = Logger(__name__)


class ThinkingEngine:
    """Generate introspective thoughts based on stored memories."""

    DEFAULT_PROMPTS: List[str] = [
        "What am I feeling right now?",
        "How do my recent experiences relate to my goals?",
        "What can I improve based on recent interactions?",
        "What have I learned recently?",
        "Is there anything I am forgetting to consider?",
    ]

    def __init__(self, prompts: Iterable[str] | None = None) -> None:
        self.prompts = (
            list(prompts) if prompts is not None else self.DEFAULT_PROMPTS
        )

    def _select_prompt(self) -> str:
        return random.choice(self.prompts)

    def _generate_thought(
        self,
        manager: "MemoryManager",
        prompt: str,
        mood: str,
        llm_name: str,
        *,
        use_reasoning: bool = False,
        reasoning_depth: int = 1,
    ) -> str:
        """Internal helper to generate and store a single thought."""

        cue = build_cue(prompt, state={"mood": mood})
        retriever = Retriever(
            manager.all(),
            semantic=manager.semantic.all(),
            procedural=manager.procedural.all(),
        )
        memories = retriever.query(cue, top_k=5, mood=mood)
        reconstructor = Reconstructor()
        context = reconstructor.build_context(memories, mood=mood)
        full_prompt = f"{context}\n{prompt}" if context else prompt
        llm = llm_router.get_llm(llm_name)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are thinking internally. Respond with a single "
                    "first-person thought without addressing anyone as 'you'."
                ),
            },
            {"role": "user", "content": full_prompt},
        ]
        try:
            thought = llm.generate(messages).strip()
        except Exception as exc:  # pragma: no cover - log and continue
            logger.warning(f"LLM generate failed: {exc}")
            return ""
        emotions = analyze_emotions(thought)
        if emotions:
            mood = emotions[0][0]
        manager.add(
            thought,
            emotions=[e[0] for e in emotions],
            emotion_scores={lbl: score for lbl, score in emotions},
            metadata={"prompt": prompt, "tags": ["introspection"]},
        )
        if use_reasoning:
            try:
                ReasoningEngine().reason_once(
                    manager, thought, llm_name=llm_name, depth=reasoning_depth
                )
            except Exception as exc:  # pragma: no cover - log and continue
                logger.warning(f"Reasoning step failed: {exc}")
        return thought

    def think_once(
        self,
        manager: "MemoryManager",
        mood: str,
        llm_name: str = "local",
        use_reasoning: bool = False,
        reasoning_depth: int = 1,
    ) -> str:
        """Generate one introspective thought.

        Parameters
        ----------
        manager:
            Memory manager providing access to memories.
        mood:
            Current emotional state used to bias retrieval.
        llm_name:
            Name of the LLM backend to use.
        use_reasoning:
            If ``True``, generate an additional reasoning step about the
            produced thought.
        reasoning_depth:
            Number of steps to pass to :class:`ReasoningEngine`.

        Returns
        -------
        str
            The generated thought.
        """
        prompt = self._select_prompt()
        return self._generate_thought(
            manager,
            prompt,
            mood,
            llm_name,
            use_reasoning=use_reasoning,
            reasoning_depth=reasoning_depth,
        )

    def think_chain(
        self,
        manager: "MemoryManager",
        mood: str,
        *,
        steps: int = 1,
        llm_name: str = "local",
        reasoning_depth: int = 1,
        use_reasoning: bool = True,
    ) -> str:
        """Generate a chain of thoughts feeding each result as the next prompt."""

        prompt = self._select_prompt()
        thought = ""
        for _ in range(max(1, steps)):
            thought = self._generate_thought(
                manager,
                prompt,
                mood,
                llm_name,
                use_reasoning=use_reasoning,
                reasoning_depth=reasoning_depth,
            )
            prompt = thought
        return thought

    def run(
        self,
        manager: "MemoryManager",
        *,
        think_interval: float = 60.0,
        duration: float | None = None,
        llm_name: str = "local",
        use_reasoning: bool = True,
        reasoning_depth: int = 1,
        chain_steps: int = 1,
    ) -> Scheduler:
        """Start periodic background thinking.

        Parameters
        ----------
        manager:
            Memory manager containing episodic entries.
        think_interval:
            Seconds between each introspection.
        duration:
            Total runtime in seconds before the scheduler automatically stops.
        llm_name:
            Name of the LLM backend to use.
        use_reasoning:
            If ``True``, run :meth:`ReasoningEngine.reason_once` after each
            introspective thought.
        reasoning_depth:
            Number of reasoning steps for ``ReasoningEngine``.
        chain_steps:
            Number of introspective thoughts to chain together per interval.

        Returns
        -------
        Scheduler
            Scheduler instance running the thinking task.
        """

        scheduler = Scheduler()
        now = time.monotonic()
        manager._next_think_time = now + think_interval
        if duration is not None:
            manager._think_end_time = now + duration
        else:
            manager._think_end_time = None

        def _task() -> None:
            mood = "neutral"
            entries = manager.all()
            if entries and entries[-1].emotion_scores:
                scores = entries[-1].emotion_scores
                mood = max(scores, key=scores.get)
            self.think_chain(
                manager,
                mood,
                steps=chain_steps,
                llm_name=llm_name,
                reasoning_depth=reasoning_depth,
                use_reasoning=use_reasoning,
            )
            manager._next_think_time = time.monotonic() + think_interval

        # run once immediately so a thought occurs even if duration == think_interval
        _task()
        scheduler.schedule(think_interval, _task)

        if duration is not None:
            def _stop() -> None:
                scheduler.stop()
                manager._next_think_time = None
                manager._think_end_time = None

            scheduler.schedule(duration, _stop)

        return scheduler
