"""Memory retrieval using simple vector similarity."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Sequence

from core.memory_entry import MemoryEntry
from encoding.encoder import encode_text

try:  # pragma: no cover - optional dependency
    from storage.faiss_index import FaissIndex
except Exception:  # pragma: no cover - faiss may not be available
    FaissIndex = None


class Retriever:
    """In-memory retriever using cosine similarity and recency bias."""

    def __init__(self, memories: Iterable[MemoryEntry]):
        self._memories = list(memories)
        self._index = None
        self._dense_vectors: List[List[float]] = []
        self._vocab: Dict[str, int] = {}
        self._vectors: List[Dict[int, int]] = []

        if self._memories and self._memories[0].embedding and isinstance(
            self._memories[0].embedding[0], (float, int)
        ):
            # numeric embeddings
            self._dense_vectors = [list(map(float, m.embedding)) for m in self._memories]
            if FaissIndex is not None:
                idx = FaissIndex(self._memories)
                if idx.available:
                    self._index = idx
        else:
            # token-based embeddings
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

    def _cosine_dense(self, a: Sequence[float], b: Sequence[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a and norm_b:
            return dot / (norm_a * norm_b)
        return 0.0

    def query(self, text: str, top_k: int = 5) -> List[MemoryEntry]:
        embedding = encode_text(text)
        now = datetime.utcnow()

        if (
            self._index is not None
            and embedding
            and isinstance(embedding[0], (float, int))
        ):
            idxs = self._index.query(embedding, top_k)
            return [self._memories[i] for i in idxs]

        if self._dense_vectors and embedding and isinstance(embedding[0], (float, int)):
            scored = []
            for memory, vec in zip(self._memories, self._dense_vectors):
                sim = self._cosine_dense(embedding, vec)
                recency = 1 / ((now - memory.timestamp).total_seconds() + 1)
                scored.append((sim + 0.1 * recency, memory))
            scored.sort(key=lambda item: item[0], reverse=True)
            return [m for _, m in scored[:top_k]]

        tokens = embedding  # type: ignore[assignment]
        q_vec: Dict[int, int] = {}
        for t in tokens:
            idx = self._vocab.get(t)
            if idx is not None:
                q_vec[idx] = q_vec.get(idx, 0) + 1
        scored = []
        for memory, vec in zip(self._memories, self._vectors):
            sim = self._cosine(q_vec, vec)
            recency = 1 / ((now - memory.timestamp).total_seconds() + 1)
            scored.append((sim + 0.1 * recency, memory))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [m for _, m in scored[:top_k]]
