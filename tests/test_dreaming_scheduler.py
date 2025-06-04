import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_manager import MemoryManager
from dreaming.dream_engine import DreamEngine


def test_dream_run_summarizes_and_prunes():
    manager = MemoryManager()
    for i in range(7):
        manager.add(f"event {i}")

    def immediate(interval, func, *args, **kwargs):
        func(*args, **kwargs)

    with patch("ms_utils.scheduler.Scheduler.schedule", side_effect=immediate):
        engine = DreamEngine()
        engine.run(manager, interval=0.1, summary_size=2, max_entries=5)

    mems = manager.all()
    assert len(mems) == 5
    assert any("Dream:" in m.content for m in mems)


def test_manager_start_dreaming_uses_engine():
    manager = MemoryManager()

    with patch.object(DreamEngine, "run", return_value=None) as mock_run:
        manager.start_dreaming(interval=1, summary_size=1, max_entries=10)
        mock_run.assert_called_once()

