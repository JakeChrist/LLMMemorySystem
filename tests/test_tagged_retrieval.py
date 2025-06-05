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
            with patch("retrieval.retriever.Retriever.query", return_value=[]) as mock_query:
                agent = Agent("local")
                agent.receive("hello cat")
                _, kwargs = mock_cue.call_args
                assert kwargs.get("tags") == ["animal", "greeting"]
                _, q_kwargs = mock_query.call_args
                assert q_kwargs.get("tags") == ["animal", "greeting"]

from datetime import datetime
from core.memory_entry import MemoryEntry
from retrieval.retriever import Retriever


def test_retriever_ranks_matching_tags_higher():
    m1 = MemoryEntry(
        content="cats are great",
        embedding=["cats", "are", "great"],
        timestamp=datetime(2020, 1, 1),
        metadata={"tags": ["animal"]},
    )
    m2 = MemoryEntry(
        content="hello there",
        embedding=["hello", "there"],
        timestamp=datetime(2020, 1, 1),
        metadata={"tags": ["greeting"]},
    )
    retriever = Retriever([m1, m2])
    results = retriever.query("unrelated", top_k=2, tags=["greeting"])
    assert results[0] is m2
