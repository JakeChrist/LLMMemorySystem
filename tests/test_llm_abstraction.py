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
