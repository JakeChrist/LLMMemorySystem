import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

PyQt5 = pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import QApplication

from gui.qt_interface import MemorySystemGUI, MemoryBrowser
from core.memory_entry import MemoryEntry
from core.memory_manager import MemoryManager

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_gui_handle_submit_updates_panels():
    app = QApplication.instance() or QApplication([])

    mock_agent = MagicMock()
    mock_agent.receive.return_value = "reply"
    mock_agent.working_memory.return_value = ["fact1", "fact2"]
    mock_agent.mood = "happy"
    mock_agent.memory.all.return_value = [
        MemoryEntry(content="Dream: something", embedding=[], timestamp=datetime.utcnow())
    ]

    gui = MemorySystemGUI(mock_agent)
    gui.input_box.setPlainText("hello")
    with patch("retrieval.cue_builder.build_cue", return_value="cue") as mock_cue:
        with patch("retrieval.retriever.Retriever.query", return_value=[] ) as mock_query:
            gui.handle_submit()
            _, kwargs = mock_cue.call_args
            assert kwargs.get("tags") == ["greeting"]
            _, q_kwargs = mock_query.call_args
            assert q_kwargs.get("tags") == ["greeting"]

    assert mock_agent.receive.called
    assert gui.response_list.item(0).text() == "reply"
    assert "fact1" in gui.memory_box.toPlainText()
    assert "happy" in gui.mood_box.toPlainText()
    assert "Dream:" in gui.dream_box.toPlainText()

    app.quit()


def test_memory_browser_edit_refreshes_tags(tmp_path):
    app = QApplication.instance() or QApplication([])

    manager = MemoryManager(db_path=tmp_path / "mem.db")
    entry = manager.add("hello")

    browser = MemoryBrowser(manager)
    browser.display_memory(0)
    browser.detail.setPlainText("the cat sat")
    browser.save_current()

    assert entry.metadata.get("tags") == ["animal"]
    stored = manager.db.load_all()[0]
    assert stored.metadata.get("tags") == ["animal"]
    assert manager.working.contents()[0].metadata.get("tags") == ["animal"]

    app.quit()
