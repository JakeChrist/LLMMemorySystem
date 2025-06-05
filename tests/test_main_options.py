import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main


def test_main_cli_db_option(tmp_path):
    db_path = tmp_path / "cli.db"
    with patch("cli.memory_cli.Database") as MockDB, patch("cli.memory_cli.list_memories"):
        MockDB.return_value = MagicMock(load_all=lambda: [])
        main.main(["cli", "list", "--db", str(db_path)])
        MockDB.assert_called_once_with(str(db_path))


def test_main_calls_run_repl_with_options(tmp_path):
    db_path = tmp_path / "mem.db"
    with patch("main.run_repl") as mock_repl:
        main.main(["repl", "--llm", "claude", "--db", str(db_path)])
        mock_repl.assert_called_once_with("claude", str(db_path))


def test_run_repl_creates_agent(tmp_path):
    db_path = tmp_path / "mem.db"
    with patch("core.agent.Agent") as MockAgent:
        agent = MockAgent.return_value
        agent.receive.side_effect = ["hi"]
        with patch("builtins.input", side_effect=EOFError):
            main.run_repl("openai", str(db_path))
        MockAgent.assert_called_once_with("openai", db_path=str(db_path))

