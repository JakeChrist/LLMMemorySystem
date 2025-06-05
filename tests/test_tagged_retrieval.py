import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import emotion_model
from core.agent import Agent


def test_agent_passes_tags_to_cue_builder():
    fake_clf = MagicMock(return_value=[{"label": "POSITIVE"}])
    with patch.object(emotion_model, "_load_classifier", return_value=fake_clf):
        emotion_model._classifier = None
        with patch("core.agent.build_cue", return_value="cue") as mock_cue:
            with patch("retrieval.retriever.Retriever.query", return_value=[]):
                agent = Agent("local")
                agent.receive("hello cat")
                _, kwargs = mock_cue.call_args
                assert kwargs.get("tags") == ["animal", "greeting"]
