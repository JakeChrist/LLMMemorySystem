import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_manager import MemoryManager
from reasoning.reasoning_engine import ReasoningEngine


def test_reason_once_stores_reasoning_memory():
    manager = MemoryManager(db_path=":memory:")
    engine = ReasoningEngine()
    with patch("reasoning.reasoning_engine.llm_router.get_llm") as mock_get, \
            patch("retrieval.cue_builder.build_cue", return_value="cue"), \
            patch("retrieval.retriever.Retriever.query", return_value=[]), \
            patch("reconstruction.reconstructor.Reconstructor.build_context", return_value=""):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "analysis"
        mock_get.return_value = mock_llm
        result = engine.reason_once(manager, "topic")
    assert result == "analysis"
    entry = manager.all()[-1]
    assert entry.content == "analysis"
    assert "reasoning" in entry.metadata.get("tags", [])


def test_plan_generates_procedural_memory():
    manager = MemoryManager(db_path=":memory:")
    engine = ReasoningEngine()
    with patch("reasoning.reasoning_engine.llm_router.get_llm") as mock_get, \
            patch("retrieval.cue_builder.build_cue", return_value="cue"), \
            patch("retrieval.retriever.Retriever.query", return_value=[]), \
            patch("reconstruction.reconstructor.Reconstructor.build_context", return_value=""), \
            patch.object(manager, "add_procedural") as mock_add:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "steps"
        mock_get.return_value = mock_llm
        plan = engine.plan("goal", manager)
        mock_add.assert_called_once()
        args, kwargs = mock_add.call_args
        assert "plan" in kwargs.get("metadata", {}).get("tags", [])
    assert plan == "steps"
