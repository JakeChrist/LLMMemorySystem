"""In-memory vector index built on top of Retriever."""

from __future__ import annotations

from typing import Iterable

from core.memory_entry import MemoryEntry
from retrieval.retriever import Retriever


class VectorIndexer:
    def __init__(self, memories: Iterable[MemoryEntry]):
        self._retriever = Retriever(memories)

    def query(self, text: str, top_k: int = 5):
        return self._retriever.query(text, top_k=top_k)
