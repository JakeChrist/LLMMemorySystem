import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unittest.mock import MagicMock, patch

from core import emotion_model
from dreaming.dream_engine import DreamEngine
from core.memory_entry import MemoryEntry
from core.memory_types.semantic import SemanticMemory
from datetime import datetime


def test_analyze_emotions_positive():
    fake_clf = MagicMock(return_value=[{"label": "POSITIVE"}])
    with patch.object(emotion_model, "_load_classifier", return_value=fake_clf):
        # reset cached classifier
        emotion_model._classifier = None
        assert "positive" in emotion_model.analyze_emotions("I am happy today")


def test_dream_engine_summarize():
    engine = DreamEngine()
    mems = [MemoryEntry(content="a cat", embedding=[], timestamp=datetime.utcnow())]

    with patch("dreaming.dream_engine.llm_router.get_llm") as mock_get:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "summary"
        mock_get.return_value = mock_llm
        sem = SemanticMemory()
        summary = engine.summarize(mems, semantic=sem)

    mock_get.assert_called_once_with("local")
    assert summary == "Dream: summary"
    assert sem.all()[0].content == summary
