import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_manager import MemoryManager
from retrieval.retriever import Retriever
from reconstruction.reconstructor import Reconstructor


def test_memory_add_and_retrieve():
    manager = MemoryManager(db_path=":memory:")
    manager.add("the cat sat on the mat")
    manager.add("dogs are wonderful companions")

    retriever = Retriever(manager.all())
    results = retriever.query("cat", top_k=1)
    assert results
    assert "cat" in results[0].content

    reconstructor = Reconstructor()
    context = reconstructor.build_context(results)
    assert "cat" in context
