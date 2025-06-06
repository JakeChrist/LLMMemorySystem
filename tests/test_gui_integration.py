import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

PyQt5 = pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import QApplication, QLabel, QDialog
from llm.lmstudio_api import LMStudioBackend

from gui.qt_interface import MemorySystemGUI, MemoryBrowser
import gui.qt_interface as gui_mod
from core.memory_entry import MemoryEntry
from core.memory_manager import MemoryManager
from thinking.thinking_engine import ThinkingEngine
import main

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
    mock_agent.memory.time_until_think.return_value = 5

    gui = MemorySystemGUI(mock_agent)

    # Simulate new dream added to memory
    entries.append(MemoryEntry(content="Dream: second", embedding=[], timestamp=datetime.utcnow()))

    gui.update_countdown()

    assert "Dream: second" in gui.dream_box.toPlainText()
    label = gui.countdown_label.text()
    assert "D:10s" in label
    assert "T:5s" in label


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
    mock_agent.memory.time_until_think.return_value = 7

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
    label = gui.countdown_label.text()
    assert "T:7s" in label

    app.quit()


def test_think_once_updates_gui(tmp_path):
    pytest.importorskip("PyQt5")
    app = QApplication.instance() or QApplication([])

    manager = MemoryManager(db_path=tmp_path / "mem.db")
    agent = MagicMock()
    agent.memory = manager

    gui = MemorySystemGUI(agent)

    engine = ThinkingEngine(prompts=["reflect"])
    with patch("thinking.thinking_engine.llm_router.get_llm") as mock_get, \
            patch("retrieval.cue_builder.build_cue", return_value="cue"), \
            patch("retrieval.retriever.Retriever.query", return_value=[]), \
            patch("reconstruction.reconstructor.Reconstructor.build_context", return_value=""):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "new thought"
        mock_get.return_value = mock_llm
        engine.think_once(manager, "neutral")

    gui.update_countdown()

    assert "new thought" in gui.think_box.toPlainText()

    app.quit()


def test_main_gui_initializes_scheduler(tmp_path):
    db = tmp_path / "mem.db"
    with patch("main.run_gui") as mock_gui, \
            patch("core.agent.Agent") as MockAgent, \
            patch("core.cognitive_scheduler.CognitiveScheduler") as MockSched:
        mock_instance = MockSched.return_value
        runner = MagicMock()
        mock_instance.run.return_value = runner

        main.main(["gui", "--db", str(db), "--llm", "local"])

        MockAgent.assert_called_once_with("local", db_path=str(db))
        MockSched.assert_called_once_with(
            MockAgent.return_value.memory, llm_name="local"
        )
        mock_instance.run.assert_called_once()
        runner.stop.assert_called_once()


def test_settings_dialog_updates_scheduler(monkeypatch):
    app = QApplication.instance() or QApplication([])

    scheduler = MagicMock()
    scheduler.T_think = 5.0
    scheduler.T_dream = 10.0
    scheduler.T_alarm = 20.0
    scheduler.notify_input = MagicMock()

    gui = MemorySystemGUI(None, scheduler=scheduler)

    class FakeDialog:
        def __init__(self, sched):
            self.sched = sched

        def exec(self):
            return QDialog.Accepted

        def values(self):
            return 1.0, 2.0, 3.0

    monkeypatch.setattr(gui_mod, "SchedulerSettingsDialog", FakeDialog)

    gui.show_settings()

    assert scheduler.T_think == 1.0
    assert scheduler.T_dream == 2.0
    assert scheduler.T_alarm == 3.0
    assert scheduler.notify_input.called

    app.quit()


def test_settings_dialog_updates_lmstudio_timeout(monkeypatch):
    app = QApplication.instance() or QApplication([])

    agent = MagicMock()
    agent.llm = LMStudioBackend(timeout=30)

    scheduler = MagicMock()
    scheduler.T_think = 5.0
    scheduler.T_dream = 10.0
    scheduler.T_alarm = 20.0
    scheduler.notify_input = MagicMock()
    scheduler.agent = agent

    gui = MemorySystemGUI(agent, scheduler=scheduler)

    class FakeDialog:
        def __init__(self, sched):
            self.sched = sched

        def exec(self):
            return QDialog.Accepted

        def values(self):
            return 1.0, 2.0, 3.0, 42.0

    monkeypatch.setattr(gui_mod, "SchedulerSettingsDialog", FakeDialog)

    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "15")
    gui.show_settings()

    assert scheduler.T_think == 1.0
    assert scheduler.T_dream == 2.0
    assert scheduler.T_alarm == 3.0
    assert agent.llm.timeout == 42.0
    assert scheduler.notify_input.called
    assert os.getenv("LMSTUDIO_TIMEOUT") == "42.0"

    app.quit()
