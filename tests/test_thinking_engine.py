import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ms_utils.scheduler import Scheduler

from core.memory_manager import MemoryManager
from thinking.thinking_engine import ThinkingEngine


def test_think_once_stores_introspection():
    manager = MemoryManager(db_path=":memory:")
    engine = ThinkingEngine(prompts=["reflect"])
    with patch("thinking.thinking_engine.llm_router.get_llm") as mock_get:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "thought"
        mock_get.return_value = mock_llm
        thought = engine.think_once(manager, "neutral")
    assert thought == "thought"
    entry = manager.all()[-1]
    assert entry.content == "thought"
    assert "introspection" in entry.metadata.get("tags", [])
    assert entry.metadata.get("prompt") == "reflect"


def test_run_invokes_think_once(tmp_path):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    engine = ThinkingEngine(prompts=["reflect"])

    def immediate(interval, func, *args, **kwargs):
        func(*args, **kwargs)

    with patch("ms_utils.scheduler.Scheduler.schedule", side_effect=immediate):
        with patch.object(engine, "think_once", return_value="x") as mock_once:
            sched = engine.run(manager, interval=0.1)
    assert isinstance(sched, Scheduler)
    assert mock_once.called
