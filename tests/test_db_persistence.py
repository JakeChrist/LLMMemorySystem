import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storage.db_interface import Database
from core.memory_entry import MemoryEntry
from core.memory_manager import MemoryManager


def test_round_trip_embedding_and_metadata(tmp_path):
    db = Database(tmp_path / "mem.db")
    entry = MemoryEntry(
        content="hello world",
        embedding=["hello", "world"],
        emotions=["neutral"],
        metadata={"role": "test"},
    )
    db.save(entry)
    loaded = db.load_all()
    assert loaded
    loaded_entry = loaded[0]
    assert loaded_entry.embedding == entry.embedding
    assert loaded_entry.metadata == entry.metadata


def test_memory_manager_loads_existing_entries(tmp_path):
    path = tmp_path / "mem.db"
    mgr1 = MemoryManager(db_path=path)
    mgr1.add("hello world")

    mgr2 = MemoryManager(db_path=path)
    all_entries = [m.content for m in mgr2.all()]
    assert "hello world" in all_entries
