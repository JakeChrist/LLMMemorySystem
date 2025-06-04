"""Memory retrieval using simple vector similarity."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List

from core.memory_entry import MemoryEntry
from encoding.encoder import encode_text


class Retriever:
    """In-memory retriever using cosine similarity and recency bias."""

    def __init__(self, memories: Iterable[MemoryEntry]):
        self._memories = list(memories)
        self._vocab: Dict[str, int] = {}
        self._vectors: List[Dict[int, int]] = []
        for m in self._memories:
            vec = {}
            for token in m.embedding:
                idx = self._vocab.setdefault(token, len(self._vocab))
                vec[idx] = vec.get(idx, 0) + 1
            self._vectors.append(vec)

    def _cosine(self, vec: Dict[int, int], other: Dict[int, int]) -> float:
        dot = sum(vec.get(i, 0) * other.get(i, 0) for i in set(vec) | set(other))
        norm_a = sum(v * v for v in vec.values()) ** 0.5
        norm_b = sum(v * v for v in other.values()) ** 0.5
        if norm_a and norm_b:
            return dot / (norm_a * norm_b)
        return 0.0

    def query(self, text: str, top_k: int = 5) -> List[MemoryEntry]:
        tokens = encode_text(text)
        q_vec: Dict[int, int] = {}
        for t in tokens:
            idx = self._vocab.get(t)
            if idx is not None:
                q_vec[idx] = q_vec.get(idx, 0) + 1
        scored = []
        now = datetime.utcnow()
        for memory, vec in zip(self._memories, self._vectors):
            sim = self._cosine(q_vec, vec)
            recency = 1 / ((now - memory.timestamp).total_seconds() + 1)
            scored.append((sim + 0.1 * recency, memory))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [m for _, m in scored[:top_k]]
