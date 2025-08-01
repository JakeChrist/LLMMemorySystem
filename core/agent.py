"""Basic interactive agent tying memory and LLM together."""

from __future__ import annotations

from typing import List

from core.emotion_model import analyze_emotions
from core.memory_manager import MemoryManager
from retrieval.cue_builder import build_cue
from encoding.tagging import tag_text
from retrieval.retriever import Retriever
from reconstruction.reconstructor import Reconstructor
from llm import llm_router


class Agent:
    """Minimal conversational agent."""

    def __init__(self, llm_name: str = "local", db_path: str | None = None) -> None:
        self.llm_name = llm_name
        self.memory = MemoryManager(db_path=db_path or "memory.db")
        self.llm = llm_router.get_llm(llm_name)
        self.mood = "neutral"

    def working_memory(self) -> List[str]:
        """Return contents of working memory as plain strings."""
        return [m.content for m in self.memory.working.contents()]

    def receive(self, text: str) -> str:
        """Process user input and return LLM response."""
        emotions = analyze_emotions(text)
        if emotions:
            self.mood = emotions[0][0]

        self.memory.add(
            text,
            emotions=[e[0] for e in emotions],
            emotion_scores={lbl: score for lbl, score in emotions},
            metadata={"role": "user"},
        )

        tags = tag_text(text)
        cue = build_cue(text, tags=tags, state={"mood": self.mood})
        retriever = Retriever(
            self.memory.all(),
            semantic=self.memory.semantic.all(),
            procedural=self.memory.procedural.all(),
        )
        retrieved = retriever.query(cue, top_k=5, mood=self.mood, tags=tags)
        reconstructor = Reconstructor()
        context = reconstructor.build_context(retrieved, mood=self.mood)

        prompt = f"{context}\nUser: {text}" if context else text
        response = self.llm.generate(prompt)
        resp_emotions = analyze_emotions(response)
        if resp_emotions:
            self.mood = resp_emotions[0][0]

        resp_tags = tag_text(response)
        self.memory.add(
            response,
            emotions=[e[0] for e in resp_emotions],
            emotion_scores={lbl: score for lbl, score in resp_emotions},
            metadata={"role": "assistant", "tags": resp_tags},
        )
        return response
