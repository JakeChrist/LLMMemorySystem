"""Optional vector index using FAISS if available."""

from __future__ import annotations

from typing import Iterable, List

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - numpy may not be installed
    np = None

from core.memory_entry import MemoryEntry

try:  # pragma: no cover - optional dependency
    import faiss  # type: ignore
except Exception:  # pragma: no cover - faiss may not be installed
    faiss = None


class FaissIndex:
    """Wrapper around a FAISS index for memory retrieval."""

    def __init__(self, memories: Iterable[MemoryEntry]):
        self._memories = list(memories)
        self._index = None
        if faiss is None or np is None or not self._memories:
            return
        first = self._memories[0].embedding
        if not first or not isinstance(first[0], (float, int)):
            return
        dim = len(first)
        vectors = np.array([m.embedding for m in self._memories], dtype="float32")
        self._index = faiss.IndexFlatL2(dim)
        self._index.add(vectors)

    @property
    def available(self) -> bool:
        return self._index is not None

    def query(self, vector: List[float], top_k: int = 5) -> List[int]:
        if self._index is None or np is None:
            return []
        vec = np.array([vector], dtype="float32")
        _, indices = self._index.search(vec, top_k)
        return [int(i) for i in indices[0]]
