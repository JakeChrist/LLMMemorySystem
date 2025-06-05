import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import threading
import time
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cli import memory_cli
from storage.db_interface import Database


def test_cli_flow(tmp_path, capsys, monkeypatch):
    db = Database(tmp_path / "mem.db")

    memory_cli.add_memory(db, "the cat sat", model=None)
    stored = db.load_all()[0]
    assert stored.metadata.get("tags") == ["animal"]
    memory_cli.list_memories(db)
    out = capsys.readouterr().out
    assert "cat" in out

    memory_cli.query_memories(db, "cat", top_k=1, model=None)
    out = capsys.readouterr().out
    assert "cat" in out

    with patch("dreaming.dream_engine.llm_router.get_llm") as mock_get:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "dream"
        mock_get.return_value = mock_llm
        memory_cli.dream_summary(db)
    out = capsys.readouterr().out
    assert "Dream:" in out

    monkeypatch.setattr("builtins.input", lambda *a, **kw: "y")
    memory_cli.reset_database(db)
    out = capsys.readouterr().out
    assert "Database cleared." in out
    memory_cli.list_memories(db)
    out = capsys.readouterr().out
    assert out.strip() == ""


def test_model_argument_passed(tmp_path):
    db = Database(tmp_path / "mem.db")
    called = {}

    def fake_encode(text, model_name=None):
        called["text"] = text
        called["model"] = model_name
        return []

    with patch("cli.memory_cli.encode_text", side_effect=fake_encode):
        memory_cli.add_memory(db, "hello", model="test-model")

    assert called["model"] == "test-model"


def test_edit_and_delete(tmp_path, capsys, monkeypatch):
    db = Database(tmp_path / "mem.db")

    memory_cli.add_memory(db, "hello", model=None)
    ts = db.load_all()[0].timestamp.isoformat()

    monkeypatch.setattr("builtins.input", lambda *a, **kw: "y")
    memory_cli.edit_memory(db, ts, "hello world")
    out = capsys.readouterr().out
    assert "Memory updated." in out
    assert db.load_all()[0].content == "hello world"

    monkeypatch.setattr("builtins.input", lambda *a, **kw: "y")
    memory_cli.delete_memory(db, ts)
    out = capsys.readouterr().out
    assert "Memory deleted." in out
    assert db.load_all() == []


def test_semantic_and_procedural_cli(tmp_path, capsys, monkeypatch):
    db = Database(tmp_path / "mem.db")

    memory_cli.add_sem(db, "Earth is round")
    memory_cli.list_sem(db)
    out = capsys.readouterr().out
    assert "Earth" in out
    ts_sem = db.load_all_semantic()[0].timestamp.isoformat()

    monkeypatch.setattr("builtins.input", lambda *a, **kw: "y")
    memory_cli.edit_sem(db, ts_sem, "Earth orbits sun")
    out = capsys.readouterr().out
    assert "Semantic memory updated." in out
    assert db.load_all_semantic()[0].content == "Earth orbits sun"

    monkeypatch.setattr("builtins.input", lambda *a, **kw: "y")
    memory_cli.delete_sem(db, ts_sem)
    out = capsys.readouterr().out
    assert "Semantic memory deleted." in out
    assert db.load_all_semantic() == []

    memory_cli.add_proc(db, "breathing")
    memory_cli.list_proc(db)
    out = capsys.readouterr().out
    assert "breathing" in out
    ts_proc = db.load_all_procedural()[0].timestamp.isoformat()

    monkeypatch.setattr("builtins.input", lambda *a, **kw: "y")
    memory_cli.edit_proc(db, ts_proc, "walking")
    out = capsys.readouterr().out
    assert "Procedural memory updated." in out
    assert db.load_all_procedural()[0].content == "walking"

    monkeypatch.setattr("builtins.input", lambda *a, **kw: "y")
    memory_cli.delete_proc(db, ts_proc)
    out = capsys.readouterr().out
    assert "Procedural memory deleted." in out
    assert db.load_all_procedural() == []


def test_start_and_stop_dreaming(monkeypatch):
    manager = MagicMock()
    scheduler = MagicMock()
    manager.start_dreaming.return_value = scheduler

    monkeypatch.setattr(memory_cli.time, "sleep", lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    memory_cli.start_dream(manager, interval=5)

    manager.start_dreaming.assert_called_once_with(interval=5, llm_name="local")
    scheduler.stop.assert_called_once()
    memory_cli.stop_dream(manager)
    manager.stop_dreaming.assert_called_once()


def test_start_dream_blocks_until_interrupt(monkeypatch):
    manager = MagicMock()
    scheduler = MagicMock()
    manager.start_dreaming.return_value = scheduler

    stop_event = threading.Event()
    orig_sleep = time.sleep

    def fake_sleep(_):
        if stop_event.is_set():
            raise KeyboardInterrupt()
        orig_sleep(0.01)

    monkeypatch.setattr(memory_cli.time, "sleep", fake_sleep)

    t = threading.Thread(target=memory_cli.start_dream, args=(manager,))
    t.start()
    orig_sleep(0.05)
    assert t.is_alive()
    stop_event.set()
    t.join(timeout=1)
    assert not t.is_alive()

    scheduler.stop.assert_called_once()


def test_reset_database_clears_all_categories(tmp_path):
    db = Database(tmp_path / "mem.db")

    memory_cli.add_memory(db, "a", model=None)
    memory_cli.add_sem(db, "b")
    memory_cli.add_proc(db, "c")

    memory_cli.reset_database(db, assume_yes=True)

    assert db.load_all() == []
    assert db.load_all_semantic() == []
    assert db.load_all_procedural() == []
