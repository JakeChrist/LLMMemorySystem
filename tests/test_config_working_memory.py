import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_manager import MemoryManager


def test_memory_manager_uses_config(monkeypatch):
    monkeypatch.setattr(
        "core.memory_manager._load_config",
        lambda: {"memory": {"working_size": 3}},
    )
    manager = MemoryManager(db_path=":memory:")
    assert manager.working.max_size == 3
