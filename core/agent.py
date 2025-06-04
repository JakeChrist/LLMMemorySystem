"""Basic interactive agent tying memory and LLM together."""

from __future__ import annotations

from typing import List

from core.emotion_model import analyze_emotions
from core.memory_manager import MemoryManager
from llm import llm_router


class Agent:
    """Minimal conversational agent."""

    def __init__(self, llm_name: str = "local") -> None:
        self.memory = MemoryManager()
        self.llm = llm_router.get_llm(llm_name)
        self.mood = "neutral"

    def working_memory(self) -> List[str]:
        """Return contents of working memory as plain strings."""
        return [m.content for m in self.memory.working.contents()]

    def receive(self, text: str) -> str:
        """Process user input and return LLM response."""
        emotions = analyze_emotions(text)
        if emotions:
            self.mood = emotions[0]
        self.memory.add(text, emotions=emotions, metadata={"role": "user"})
        context = "\n".join(self.working_memory())
        prompt = f"{context}\nUser: {text}" if context else text
        response = self.llm.generate(prompt)
        self.memory.add(response, metadata={"role": "assistant"})
        return response
