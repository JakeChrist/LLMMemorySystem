import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime
from core.memory_entry import MemoryEntry
from retrieval.retriever import Retriever


def test_retriever_ranks_emotion_weighted_results():
    m1 = MemoryEntry(
        content="happy memory",
        embedding=["a"],
        timestamp=datetime(2020, 1, 1),
        emotions=["happy"],
        emotion_scores={"happy": 0.9},
    )
    m2 = MemoryEntry(
        content="less happy memory",
        embedding=["a"],
        timestamp=datetime(2020, 1, 1),
        emotions=["happy"],
        emotion_scores={"happy": 0.1},
    )
    retriever = Retriever([m1, m2])
    results = retriever.query("a", top_k=2, mood="happy")
    assert results[0] is m1
