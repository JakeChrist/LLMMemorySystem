import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

PyQt5 = pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import QApplication, QLabel

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
    bubbles = gui.chat_widget.findChildren(QLabel)
    assert bubbles[-1].text() == "reply"
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


def test_update_countdown_refreshes_dream_box():
    app = QApplication.instance() or QApplication([])

    entries = [
        MemoryEntry(content="Dream: first", embedding=[], timestamp=datetime.utcnow())
    ]

    mock_agent = MagicMock()
    mock_agent.memory.all.return_value = entries
    mock_agent.memory.time_until_dream.return_value = 10

    gui = MemorySystemGUI(mock_agent)

    # Simulate new dream added to memory
    entries.append(MemoryEntry(content="Dream: second", embedding=[], timestamp=datetime.utcnow()))

    gui.update_countdown()

    assert "Dream: second" in gui.dream_box.toPlainText()
    assert gui.countdown_label.text() == "10s"


    app.quit()


def test_update_countdown_refreshes_think_box():
    app = QApplication.instance() or QApplication([])

    entries = [
        MemoryEntry(
            content="thought1",
            embedding=[],
            timestamp=datetime.utcnow(),
            metadata={"tags": ["introspection"]},
        )
    ]

    mock_agent = MagicMock()
    mock_agent.memory.all.return_value = entries
    mock_agent.memory.time_until_dream.return_value = None

    gui = MemorySystemGUI(mock_agent)

    # New introspection entry added
    entries.append(
        MemoryEntry(
            content="thought2",
            embedding=[],
            timestamp=datetime.utcnow(),
            metadata={"tags": ["introspection"]},
        )
    )

    gui.update_countdown()

    assert "thought2" in gui.think_box.toPlainText()

    app.quit()
