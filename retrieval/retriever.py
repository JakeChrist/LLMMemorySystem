"""Simple memory retrieval using token overlap."""

from typing import Iterable, List, Set

from core.memory_entry import MemoryEntry
from encoding.encoder import encode_text


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class Retriever:
    """Naïve in-memory retriever using Jaccard similarity."""

    def __init__(self, memories: Iterable[MemoryEntry]):
        self._memories = list(memories)

    def query(self, text: str, top_k: int = 5) -> List[MemoryEntry]:
        query_tokens = set(encode_text(text))
        scored = [(_jaccard(query_tokens, set(m.embedding)), m) for m in self._memories]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [m for _, m in scored[:top_k]]
