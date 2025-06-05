import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_manager import MemoryManager
from retrieval.retriever import Retriever
from reconstruction.reconstructor import Reconstructor


def test_memory_add_and_retrieve():
    manager = MemoryManager(db_path=":memory:")
    entry = manager.add("the cat sat on the mat")
    assert entry.metadata.get("tags") == ["animal"]
    manager.add("dogs are wonderful companions")

    retriever = Retriever(
        manager.all(),
        semantic=manager.semantic.all(),
        procedural=manager.procedural.all(),
    )
    results = retriever.query("cat", top_k=1)
    assert results
    assert "cat" in results[0].content

    reconstructor = Reconstructor()
    context = reconstructor.build_context(results)
    assert "cat" in context


def test_semantic_and_procedural_retrieval():
    manager = MemoryManager(db_path=":memory:")
    sem = manager.add_semantic("Paris is in France")
    proc = manager.add_procedural("tie a knot by looping twice")

    retriever = Retriever(
        manager.all(),
        semantic=manager.semantic.all(),
        procedural=manager.procedural.all(),
    )

    res_sem = retriever.query("France", top_k=1)
    assert res_sem and res_sem[0] is sem

    res_proc = retriever.query("knot", top_k=1)
    assert res_proc and res_proc[0] is proc
