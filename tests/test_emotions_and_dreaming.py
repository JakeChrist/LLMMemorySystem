import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unittest.mock import MagicMock, patch

from core import emotion_model
from dreaming.dream_engine import DreamEngine
from core.memory_entry import MemoryEntry
from core.memory_manager import MemoryManager
from datetime import datetime


def test_analyze_emotions_positive():
    fake_clf = MagicMock(return_value=[[{"label": "joy", "score": 0.9}]])
    with patch.object(emotion_model, "_load_classifier", return_value=fake_clf):
        # reset cached classifier
        emotion_model._classifier = None
        result = emotion_model.analyze_emotions("I am happy today")
        assert result[0][0] == "happy"
        assert isinstance(result[0][1], float)


def test_dream_engine_summarize(tmp_path):
    engine = DreamEngine()
    mems = [MemoryEntry(content="a cat", embedding=[], timestamp=datetime.utcnow())]

    with patch("dreaming.dream_engine.llm_router.get_llm") as mock_get:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "summary"
        mock_get.return_value = mock_llm
        manager = MemoryManager(db_path=tmp_path / "mem.db")
        summary, labels, scores = engine.summarize(
            mems, semantic=manager.semantic, manager=manager
        )

    mock_get.assert_called_once_with("local")
    assert summary == "Dream: summary"
    assert labels and scores
    assert manager.semantic.all()[0].content == summary

    reloaded = MemoryManager(db_path=tmp_path / "mem.db")
    assert any(m.content == summary for m in reloaded.semantic.all())
