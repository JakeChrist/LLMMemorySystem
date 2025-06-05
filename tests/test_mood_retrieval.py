import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import emotion_model
from core.agent import Agent


def test_agent_passes_mood_to_retriever():
    fake_clf = MagicMock(return_value=[{"label": "POSITIVE"}])
    with patch.object(emotion_model, "_load_classifier", return_value=fake_clf):
        emotion_model._classifier = None
        with patch("retrieval.retriever.Retriever.query", return_value=[]) as mock_q:
            agent = Agent("local")
            agent.receive("I am thrilled")
            _, kwargs = mock_q.call_args
            assert kwargs.get("mood") == "positive"
