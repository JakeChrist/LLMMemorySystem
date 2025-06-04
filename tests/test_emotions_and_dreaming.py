import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unittest.mock import MagicMock, patch

from core import emotion_model
from dreaming.dream_engine import DreamEngine
from core.memory_entry import MemoryEntry
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
    summary = engine.summarize(mems)
    assert "Dream:" in summary
