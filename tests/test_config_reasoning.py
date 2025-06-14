import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_manager import MemoryManager
from thinking.thinking_engine import ThinkingEngine


def test_start_thinking_uses_reasoning_config(monkeypatch):
    monkeypatch.setattr(
        "core.memory_manager._load_config",
        lambda: {
            "memory": {"working_size": 10},
            "reasoning": {"enabled": True, "depth": 2},
        },
    )

    manager = MemoryManager(db_path=":memory:")
    with patch.object(ThinkingEngine, "run", return_value=None) as mock_run:
        manager.start_thinking(think_interval=1)
        _, kwargs = mock_run.call_args
        assert kwargs.get("use_reasoning") is True
        assert kwargs.get("reasoning_depth") == 2

