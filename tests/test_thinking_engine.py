import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ms_utils.scheduler import Scheduler

from core.memory_manager import MemoryManager
from thinking.thinking_engine import ThinkingEngine
from dreaming.dream_engine import DreamEngine


def test_think_once_stores_introspection():
    manager = MemoryManager(db_path=":memory:")
    engine = ThinkingEngine(prompts=["reflect"])
    with patch("thinking.thinking_engine.llm_router.get_llm") as mock_get, \
            patch.object(manager.db, "update") as mock_update:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "thought"
        mock_get.return_value = mock_llm
        thought = engine.think_once(manager, "neutral")
    assert thought == "thought"
    entry = manager.all()[-1]
    assert entry.content == "thought"
    assert "introspection" in entry.metadata.get("tags", [])
    assert entry.metadata.get("prompt") == "reflect"
    mock_update.assert_not_called()


def test_think_chain_uses_previous_thought(tmp_path):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    engine = ThinkingEngine(prompts=["reflect"])

    with patch("thinking.thinking_engine.llm_router.get_llm") as mock_get, \
            patch("retrieval.cue_builder.build_cue", return_value="cue"), \
            patch("retrieval.retriever.Retriever.query", return_value=[]), \
            patch("reconstruction.reconstructor.Reconstructor.build_context", return_value=""), \
            patch("reasoning.reasoning_engine.ReasoningEngine.reason_once", return_value="a"):
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = ["thought1", "thought2"]
        mock_get.return_value = mock_llm
        result = engine.think_chain(manager, "neutral", steps=2)

    assert result == "thought2"
    entries = manager.all()[-2:]
    assert entries[0].metadata.get("prompt") == "reflect"
    assert entries[1].metadata.get("prompt") == "thought1"


def test_run_invokes_think_chain(tmp_path):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    engine = ThinkingEngine(prompts=["reflect"])

    def immediate(interval, func, *args, **kwargs):
        func(*args, **kwargs)

    with patch("ms_utils.scheduler.Scheduler.schedule", side_effect=immediate):
        with patch.object(engine, "think_chain", return_value="x") as mock_chain:
            sched = engine.run(manager, think_interval=0.1, duration=0.2)
            call_count = mock_chain.call_count
    assert isinstance(sched, Scheduler)
    assert call_count > 1


def test_run_executes_without_scheduler(tmp_path):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    engine = ThinkingEngine(prompts=["reflect"])

    with patch("ms_utils.scheduler.Scheduler.schedule", lambda *a, **k: None):
        with patch.object(engine, "think_chain", return_value="x") as mock_chain:
            engine.run(manager, think_interval=0.1, duration=0.1)
    assert mock_chain.called


def test_run_stops_after_duration(tmp_path):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    engine = ThinkingEngine(prompts=["reflect"])

    def immediate(interval, func, *args, **kwargs):
        func(*args, **kwargs)

    with patch("ms_utils.scheduler.Scheduler.schedule", side_effect=immediate), \
            patch("ms_utils.scheduler.Scheduler.stop") as mock_stop:
        engine.run(manager, think_interval=0.1, duration=0.2)
    assert mock_stop.called


def test_manager_start_thinking_uses_engine():
    manager = MemoryManager(db_path=":memory:")

    with patch.object(ThinkingEngine, "run", return_value=None) as mock_run:
        manager.start_thinking(think_interval=1, llm_name="openai")
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs.get("llm_name") == "openai"
        assert kwargs.get("duration") is None


def test_start_thinking_stops_dreaming():
    manager = MemoryManager(db_path=":memory:")

    dream_sched = MagicMock(spec=Scheduler)
    with patch.object(DreamEngine, "run", return_value=dream_sched):
        manager.start_dreaming(interval=1)

    think_sched = MagicMock(spec=Scheduler)
    with patch.object(ThinkingEngine, "run", return_value=think_sched):
        manager.start_thinking(think_interval=1)

    assert dream_sched.stop.called


def test_llm_exception_does_not_stop_scheduler(tmp_path, monkeypatch):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    engine = ThinkingEngine(prompts=["reflect"])

    def immediate(interval, func, *args, **kwargs):
        func(*args, **kwargs)

    with patch("ms_utils.scheduler.Scheduler.schedule", side_effect=immediate), \
            patch("retrieval.cue_builder.build_cue", return_value="cue"), \
            patch("retrieval.retriever.Retriever.query", return_value=[]), \
            patch("reconstruction.reconstructor.Reconstructor.build_context", return_value=""), \
            patch("reasoning.reasoning_engine.ReasoningEngine.reason_once", return_value="a"):
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = [Exception("fail"), "thought"]
        with patch("thinking.thinking_engine.llm_router.get_llm", return_value=mock_llm):
            logger_mock = MagicMock()
            monkeypatch.setattr("thinking.thinking_engine.logger", logger_mock)
            engine.run(manager, think_interval=0.1, duration=0.2)

    mems = manager.all()
    assert len(mems) >= 1
    assert logger_mock.warning.call_count >= 1


def test_reasoning_exception_does_not_stop_scheduler(tmp_path, monkeypatch):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    engine = ThinkingEngine(prompts=["reflect"])

    def immediate(interval, func, *args, **kwargs):
        func(*args, **kwargs)

    with patch("ms_utils.scheduler.Scheduler.schedule", side_effect=immediate), \
            patch("retrieval.cue_builder.build_cue", return_value="cue"), \
            patch("retrieval.retriever.Retriever.query", return_value=[]), \
            patch("reconstruction.reconstructor.Reconstructor.build_context", return_value=""), \
            patch("thinking.thinking_engine.llm_router.get_llm") as mock_get:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "thought"
        mock_get.return_value = mock_llm
        logger_mock = MagicMock()
        monkeypatch.setattr("thinking.thinking_engine.logger", logger_mock)
        with patch(
            "reasoning.reasoning_engine.ReasoningEngine.reason_once",
            side_effect=Exception("fail"),
        ):
            engine.run(manager, think_interval=0.1, duration=0.2)

    mems = manager.all()
    assert len(mems) >= 1
    assert logger_mock.warning.call_count >= 1
