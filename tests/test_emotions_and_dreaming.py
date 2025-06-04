import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.emotion_model import analyze_emotions
from dreaming.dream_engine import DreamEngine
from core.memory_entry import MemoryEntry
from datetime import datetime


def test_analyze_emotions_positive():
    assert "positive" in analyze_emotions("I am happy today")


def test_dream_engine_summarize():
    engine = DreamEngine()
    mems = [MemoryEntry(content="a cat", embedding=[], timestamp=datetime.utcnow())]
    summary = engine.summarize(mems)
    assert "Dream:" in summary
