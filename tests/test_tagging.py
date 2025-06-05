import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cli import memory_cli
from storage.db_interface import Database


def test_tagging_with_float_embeddings(tmp_path):
    db = Database(tmp_path / "mem.db")
    with patch("cli.memory_cli.encode_text", return_value=[0.1, 0.2, 0.3]):
        memory_cli.add_memory(db, "hello cat")
    stored = db.load_all()[0]
    assert set(stored.metadata.get("tags")) == {"animal", "greeting"}
