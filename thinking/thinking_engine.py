"""Autonomous self-reflection engine."""

from __future__ import annotations

import random
import time
from typing import Iterable, List

from retrieval.cue_builder import build_cue
from retrieval.retriever import Retriever
from reconstruction.reconstructor import Reconstructor
from llm import llm_router
from ms_utils import Scheduler


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
        self.prompts = list(prompts) if prompts is not None else self.DEFAULT_PROMPTS

    def _select_prompt(self) -> str:
        return random.choice(self.prompts)

    def think_once(
        self,
        manager,
        mood: str,
        llm_name: str = "local",
    ) -> str:
        """Generate a single reflective thought using the provided manager."""
        prompt = self._select_prompt()
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
        thought = llm.generate(full_prompt).strip()
        entry = manager.add(thought, metadata={"prompt": prompt})
        tags = entry.metadata.get("tags", [])
        if "introspection" not in tags:
            tags.append("introspection")
        entry.metadata["tags"] = tags
        manager.db.update(entry.timestamp, entry)
        return thought

    def run(
        self,
        manager,
        *,
        interval: float = 60.0,
        llm_name: str = "local",
    ) -> Scheduler:
        """Return scheduler that periodically triggers ``think_once``."""

        scheduler = Scheduler()
        manager._next_think_time = time.monotonic() + interval

        def _task() -> None:
            mood = "neutral"
            entries = manager.all()
            if entries and entries[-1].emotion_scores:
                scores = entries[-1].emotion_scores
                mood = max(scores, key=scores.get)
            self.think_once(manager, mood, llm_name=llm_name)
            manager._next_think_time = time.monotonic() + interval

        scheduler.schedule(interval, _task)
        return scheduler
