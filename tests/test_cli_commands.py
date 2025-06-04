import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cli import memory_cli
from storage.db_interface import Database


def test_cli_flow(tmp_path, capsys, monkeypatch):
    db = Database(tmp_path / "mem.db")

    memory_cli.add_memory(db, "the cat sat", model=None)
    memory_cli.list_memories(db)
    out = capsys.readouterr().out
    assert "cat" in out

    memory_cli.query_memories(db, "cat", top_k=1, model=None)
    out = capsys.readouterr().out
    assert "cat" in out

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
