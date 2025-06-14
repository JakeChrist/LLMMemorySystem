import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm import llm_router
from llm.local_llm import LocalLLM
from llm.openai_api import OpenAIBackend
from llm.claude_api import ClaudeBackend
from llm.gemini_api import GeminiBackend
from llm.lmstudio_api import LMStudioBackend
import llm.lmstudio_api as lmstudio_api
from core.agent import Agent
from retrieval.retriever import Retriever
from reconstruction.reconstructor import Reconstructor
from cli import memory_cli
from storage.db_interface import Database


def test_get_llm_variants():
    assert isinstance(llm_router.get_llm("local"), LocalLLM)
    assert isinstance(llm_router.get_llm("openai"), OpenAIBackend)
    assert isinstance(llm_router.get_llm("claude"), ClaudeBackend)
    assert isinstance(llm_router.get_llm("gemini"), GeminiBackend)
    assert isinstance(llm_router.get_llm("lmstudio"), LMStudioBackend)
    assert isinstance(llm_router.get_llm(), LocalLLM)


def test_get_llm_unknown():
    try:
        llm_router.get_llm("bogus")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_agent_uses_llm_router():
    with patch("core.agent.llm_router.get_llm") as mock_get:
        fake_llm = LocalLLM()
        mock_get.return_value = fake_llm
        agent = Agent("local")
        assert agent.llm is fake_llm
        mock_get.assert_called_once_with("local")


def test_agent_and_cli_end_to_end(tmp_path, capsys):
    agent = Agent("local")
    agent.memory.add_semantic("the sky is blue")
    agent.memory.add_procedural("open the door by turning the knob")
    resp = agent.receive("cats like milk")
    assert isinstance(resp, str) and resp

    retriever = Retriever(
        agent.memory.all(),
        semantic=agent.memory.semantic.all(),
        procedural=agent.memory.procedural.all(),
    )
    results = retriever.query("cats", top_k=2)
    reconstructor = Reconstructor()
    context = reconstructor.build_context(results)
    assert "cats" in context

    sem_result = retriever.query("sky", top_k=1)
    assert sem_result and sem_result[0].content == "the sky is blue"

    proc_result = retriever.query("turning the knob", top_k=1)
    assert proc_result and proc_result[0].content.startswith("open the door")

    db = Database(tmp_path / "mem.db")
    for entry in agent.memory.all():
        memory_cli.add_memory(db, entry.content)

    memory_cli.list_memories(db)
    out = capsys.readouterr().out
    assert "cats" in out

    memory_cli.query_memories(db, "cats", top_k=1)
    out = capsys.readouterr().out
    assert "cats" in out

    with patch("dreaming.dream_engine.llm_router.get_llm") as mock_get:
        mock_llm = LocalLLM()
        mock_get.return_value = mock_llm
        memory_cli.dream_summary(db)
    out = capsys.readouterr().out
    assert "Dream:" in out
    db.close()


def test_lmstudio_timeout_env(monkeypatch):
    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "99")
    backend = LMStudioBackend()
    assert backend.timeout == 99.0


def test_lmstudio_timeout_argument(monkeypatch):
    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "33")
    backend = LMStudioBackend(timeout=44)
    assert backend.timeout == 44


def test_lmstudio_timeout_none_argument(monkeypatch):
    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "22")
    backend = LMStudioBackend(timeout=None)
    assert backend.timeout is None


def test_lmstudio_timeout_env_none(monkeypatch):
    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "none")
    backend = LMStudioBackend()
    assert backend.timeout is None


def test_lmstudio_auto_model(monkeypatch):
    monkeypatch.delenv("LMSTUDIO_MODEL", raising=False)

    class FakeResp:
        def json(self):
            return {"data": [{"id": "auto-model"}]}

    class FakeRequests:
        def get(self, url, timeout=None):
            return FakeResp()

    monkeypatch.setattr(lmstudio_api, "requests", FakeRequests())
    backend = LMStudioBackend()
    assert backend.model == "auto-model"
