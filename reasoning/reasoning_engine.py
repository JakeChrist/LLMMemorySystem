"""Reasoning and planning utilities."""

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

from retrieval.cue_builder import build_cue
from retrieval.retriever import Retriever
from reconstruction.reconstructor import Reconstructor
from llm import llm_router
from ms_utils.logger import Logger

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from core.memory_manager import MemoryManager
    from core.memory_entry import MemoryEntry


logger = Logger(__name__)


class ReasoningEngine:
    """Perform multi-step reasoning and planning using stored memories."""

    def reason_once(
        self,
        manager: "MemoryManager",
        topic: str,
        llm_name: str = "local",
    ) -> str:
        """Generate a reasoning chain about ``topic``.

        Parameters
        ----------
        manager:
            Memory manager providing access to memories.
        topic:
            Topic or question to reason about.
        llm_name:
            Name of the LLM backend to use.

        Returns
        -------
        str
            The reasoning output from the LLM.
        """
        cue = build_cue(topic)
        retriever = Retriever(
            manager.all(),
            semantic=manager.semantic.all(),
            procedural=manager.procedural.all(),
        )
        memories = retriever.query(cue, top_k=5)
        logger.info("Retrieved: " + ", ".join(str(m.timestamp) for m in memories))
        reconstructor = Reconstructor()
        context = reconstructor.build_context(memories)
        prompt = (
            f"{context}\nReason step by step about: {topic}" if context else f"Reason step by step about: {topic}"
        )
        llm = llm_router.get_llm(llm_name)
        messages = [
            {
                "role": "system",
                "content": (
                    "You reason about your experiences. Respond with a concise multi-step analysis."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        logger.info("Prompt: " + prompt)
        output = llm.generate(messages).strip()
        logger.info("Output: " + output)
        entry = manager.add(
            output,
            metadata={"topic": topic, "tags": ["reasoning", "inference"]},
        )
        logger.info(f"Stored reasoning memory {entry.timestamp.isoformat()}")
        return output

    def plan(
        self,
        goal: str,
        manager: "MemoryManager",
        llm_name: str = "local",
    ) -> str:
        """Create a step-by-step plan to achieve ``goal``.

        The resulting plan is stored in procedural memory tagged ``plan``.
        """
        cue = build_cue(goal)
        retriever = Retriever(
            manager.all(),
            semantic=manager.semantic.all(),
            procedural=manager.procedural.all(),
        )
        memories = retriever.query(cue, top_k=5)
        reconstructor = Reconstructor()
        context = reconstructor.build_context(memories)
        prompt = (
            f"{context}\nCreate a plan to accomplish: {goal}" if context else f"Create a plan to accomplish: {goal}"
        )
        llm = llm_router.get_llm(llm_name)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a planner. Provide a short numbered plan to achieve the goal."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        logger.info("Plan prompt: " + prompt)
        plan_text = llm.generate(messages).strip()
        logger.info("Plan output: " + plan_text)
        entry = manager.add_procedural(
            plan_text,
            metadata={"goal": goal, "tags": ["reasoning", "plan"]},
        )
        logger.info(f"Stored plan memory {entry.timestamp.isoformat()}")
        return plan_text

    def analyze_contradictions(self, text: str) -> dict[str, float]:
        """Placeholder for contradiction analysis of ``text``."""
        # Future work: implement real contradiction detection
        return {}


__all__ = ["ReasoningEngine"]
