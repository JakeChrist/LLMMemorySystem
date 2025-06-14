import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_manager import MemoryManager
from dreaming.dream_engine import DreamEngine
from thinking.thinking_engine import ThinkingEngine
from ms_utils.scheduler import Scheduler


def test_dream_run_summarizes_and_prunes(tmp_path):
    path = tmp_path / "mem.db"
    manager = MemoryManager(db_path=path)
    for i in range(7):
        manager.add(f"event {i}")

    def immediate(interval, func, *args, **kwargs):
        func(*args, **kwargs)

    with patch("ms_utils.scheduler.Scheduler.schedule", side_effect=immediate), \
        patch("dreaming.dream_engine.llm_router.get_llm") as mock_get:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "dream summary"
        mock_get.return_value = mock_llm
        engine = DreamEngine()
        engine.run(
            manager,
            interval=0.1,
            duration=0.2,
            summary_size=2,
            max_entries=5,
            store_semantic=True,
        )
    assert mock_get.called

    mems = manager.all()
    assert len(mems) == 5
    assert any("Dream:" in m.content for m in mems)
    assert manager.semantic.all()

    reloaded = MemoryManager(db_path=path)
    sem_entries = [m.content for m in reloaded.semantic.all()]
    assert any("Dream:" in s for s in sem_entries)


def test_dream_run_stops_after_duration(tmp_path):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    engine = DreamEngine()

    def immediate(interval, func, *args, **kwargs):
        func(*args, **kwargs)

    with patch("ms_utils.scheduler.Scheduler.schedule", side_effect=immediate), \
            patch("ms_utils.scheduler.Scheduler.stop") as mock_stop, \
            patch("dreaming.dream_engine.llm_router.get_llm") as mock_get:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "dream"
        mock_get.return_value = mock_llm
        engine.run(manager, interval=0.1, duration=0.2)

    assert mock_stop.called


def test_manager_start_dreaming_uses_engine():
    manager = MemoryManager(db_path=":memory:")

    with patch.object(DreamEngine, "run", return_value=None) as mock_run:
        manager.start_dreaming(interval=1, summary_size=1, max_entries=10, llm_name="openai")
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs.get("llm_name") == "openai"
        assert kwargs.get("duration") is None


def test_start_dreaming_stops_thinking():
    manager = MemoryManager(db_path=":memory:")

    think_sched = MagicMock(spec=Scheduler)
    with patch.object(ThinkingEngine, "run", return_value=think_sched):
        manager.start_thinking(interval=1)

    dream_sched = MagicMock(spec=Scheduler)
    with patch.object(DreamEngine, "run", return_value=dream_sched):
        manager.start_dreaming(interval=1)

    assert think_sched.stop.called

