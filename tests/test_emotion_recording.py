import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.agent import Agent
from thinking.thinking_engine import ThinkingEngine
from dreaming.dream_engine import DreamEngine
from core.memory_manager import MemoryManager
from core import emotion_model


def test_agent_records_emotion_for_response():
    agent = Agent("local")
    with patch.object(emotion_model, "analyze_emotions", return_value=[("happy", 0.9)]), \
            patch("retrieval.cue_builder.build_cue", return_value="cue"), \
            patch("retrieval.retriever.Retriever.query", return_value=[]), \
            patch("reconstruction.reconstructor.Reconstructor.build_context", return_value=""), \
            patch("llm.llm_router.get_llm") as mock_get, \
            patch.object(agent.memory, "add") as mock_add:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "reply"
        mock_get.return_value = mock_llm
        agent.receive("hello")
        _, kwargs = mock_add.call_args_list[1]
        assert kwargs["emotions"]
        assert kwargs["emotion_scores"]


def test_think_once_records_emotion(tmp_path):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    engine = ThinkingEngine(prompts=["reflect"])
    with patch("thinking.thinking_engine.llm_router.get_llm") as mock_get, \
            patch("thinking.thinking_engine.analyze_emotions", return_value=[("sad", 0.8)]), \
            patch("retrieval.cue_builder.build_cue", return_value="cue"), \
            patch("retrieval.retriever.Retriever.query", return_value=[]), \
            patch("reconstruction.reconstructor.Reconstructor.build_context", return_value=""), \
            patch.object(manager, "add") as mock_add:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "thought"
        mock_get.return_value = mock_llm
        engine.think_once(manager, "neutral")
        _, kwargs = mock_add.call_args
        assert kwargs["emotions"]
        assert kwargs["emotion_scores"]


def test_dream_run_records_emotion(tmp_path):
    manager = MemoryManager(db_path=tmp_path / "mem.db")
    manager.add("event 1")
    engine = DreamEngine()

    def immediate(interval, func, *args, **kwargs):
        func(*args, **kwargs)

    with patch("ms_utils.scheduler.Scheduler.schedule", side_effect=immediate), \
            patch("dreaming.dream_engine.llm_router.get_llm") as mock_get, \
            patch("dreaming.dream_engine.analyze_emotions", return_value=[("happy", 0.5)]), \
            patch.object(manager, "add") as mock_add:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "summary"
        mock_get.return_value = mock_llm
        engine.run(manager, interval=0.1, summary_size=1, max_entries=5)
    _, kwargs = mock_add.call_args
    assert kwargs["emotions"]
    assert kwargs["emotion_scores"]
