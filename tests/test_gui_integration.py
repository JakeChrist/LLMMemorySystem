import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

PyQt5 = pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QDialog,
    QMenuBar,
    QListWidget,
)
from llm.lmstudio_api import LMStudioBackend

from gui.qt_interface import MemorySystemGUI, MemoryBrowser
import gui.qt_interface as gui_mod
from core.memory_entry import MemoryEntry
from core.memory_manager import MemoryManager
from thinking.thinking_engine import ThinkingEngine
from addons import memory_constructor
import main

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_gui_handle_submit_updates_panels():
    app = QApplication.instance() or QApplication([])

    mock_agent = MagicMock()
    mock_agent.receive.return_value = "reply"
    mock_agent.working_memory.return_value = ["fact1", "fact2"]
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
    bubbles = gui.dialogue_scroll.widget().findChildren(QLabel)
    assert bubbles[-1].text() == "reply"
    mem_bubbles = gui.memory_layout.parentWidget().findChildren(QLabel)
    assert "fact1" in mem_bubbles[-1].text()

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

    dream_bubbles = gui.dream_layout.parentWidget().findChildren(QLabel)
    assert "Dream: second" in dream_bubbles[-1].text()
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

    thought_bubbles = gui.thought_layout.parentWidget().findChildren(QLabel)
    assert "thought2" in thought_bubbles[-1].text()
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

    thought_bubbles = gui.thought_layout.parentWidget().findChildren(QLabel)
    assert "new thought" in thought_bubbles[-1].text()

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
    assert isinstance(gui.menu_bar, QMenuBar)

    class FakeDialog:
        def __init__(self, sched):
            self.sched = sched

        def exec(self):
            return QDialog.Accepted

        def values(self):
            return 1.0, 2.0, 3.0, None, "openai", "new.db"

    monkeypatch.setattr(gui_mod, "SchedulerSettingsDialog", FakeDialog)
    mock_llm = MagicMock()
    monkeypatch.setattr(gui_mod.llm_router, "get_llm", mock_llm)
    monkeypatch.setattr(gui_mod, "MemoryManager", MagicMock(side_effect=AssertionError))

    gui.settings_action.trigger()

    assert scheduler.T_think == 1.0
    assert scheduler.T_dream == 2.0
    assert scheduler.T_alarm == 3.0
    assert scheduler.llm_name == "openai"
    assert scheduler.notify_input.called
    assert not mock_llm.called

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
    scheduler.manager = agent.memory
    scheduler.llm_name = "lmstudio"

    gui = MemorySystemGUI(agent, scheduler=scheduler)
    assert isinstance(gui.menu_bar, QMenuBar)

    class FakeDialog:
        def __init__(self, sched):
            self.sched = sched

        def exec(self):
            return QDialog.Accepted

        def values(self):
            return 1.0, 2.0, 3.0, 42.0, "openai", str(tmp_path / "new.db")

    monkeypatch.setattr(gui_mod, "SchedulerSettingsDialog", FakeDialog)
    new_llm = MagicMock()
    monkeypatch.setattr(gui_mod.llm_router, "get_llm", lambda name: new_llm)
    paths = {}
    def fake_mm(path):
        paths["db"] = path
        return MagicMock(db=MagicMock(path=Path(path)))
    monkeypatch.setattr(gui_mod, "MemoryManager", fake_mm)

    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "15")
    gui.settings_action.trigger()

    assert scheduler.T_think == 1.0
    assert scheduler.T_dream == 2.0
    assert scheduler.T_alarm == 3.0
    assert agent.llm is new_llm
    assert scheduler.llm_name == "openai"
    assert paths["db"] == str(tmp_path / "new.db")
    assert scheduler.manager is agent.memory
    assert agent.llm.timeout == 42.0
    assert scheduler.notify_input.called
    assert os.getenv("LMSTUDIO_TIMEOUT") == "42.0"

    app.quit()

def test_input_box_visible_only_on_dialogue_tab():
    app = QApplication.instance() or QApplication([])

    gui = MemorySystemGUI(None)

    gui.tabs.setCurrentIndex(0)
    assert gui.input_box.isVisible()

    for idx in range(1, gui.tabs.count()):
        gui.tabs.setCurrentIndex(idx)
        assert not gui.input_box.isVisible()

    app.quit()


def test_memory_table_double_click_opens_browser(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])

    manager = MemoryManager(db_path=tmp_path / "mem.db")
    manager.add("hello")

    agent = MagicMock()
    agent.memory = manager

    gui = MemorySystemGUI(agent)

    class FakeBrowser:
        def __init__(self, mgr):
            self.manager = mgr
            self.list = QListWidget()

        def display_memory(self, row):
            pass

        def exec(self):
            self.manager.update(self.manager.all()[0], "hello world")

    monkeypatch.setattr(gui_mod, "MemoryBrowser", FakeBrowser)

    gui.table.cellDoubleClicked.emit(0, 0)

    assert gui.table.item(0, 4).text() == "hello world"

    app.quit()


def test_import_tab_present():
    app = QApplication.instance() or QApplication([])

    gui = MemorySystemGUI(None)

    labels = [gui.tabs.tabText(i) for i in range(gui.tabs.count())]
    assert "Import" in labels

    app.quit()


def test_import_calls_constructor(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])

    agent = MagicMock()
    agent.memory = MemoryManager(db_path=tmp_path / "mem.db")

    conv = tmp_path / "conv.txt"
    conv.write_text("Alice: Hi")

    monkeypatch.setattr(
        gui_mod.QFileDialog,
        "getOpenFileName",
        lambda *a, **k: (str(conv), ""),
    )

    called = {}

    def fake_ingest(text, manager):
        called["text"] = text
        called["manager"] = manager
        return []

    monkeypatch.setattr(memory_constructor, "ingest_transcript", fake_ingest)

    gui = MemorySystemGUI(agent)
    gui.transcript_btn.click()
    gui.import_btn.click()

    assert called["text"] == conv.read_text()
    assert called["manager"] is agent.memory

    app.quit()


def test_import_biography_calls_constructor(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])

    agent = MagicMock()
    agent.memory = MemoryManager(db_path=tmp_path / "bio.db")

    bio = tmp_path / "bio.txt"
    bio.write_text("Born 1990. Learned to swim.")

    monkeypatch.setattr(
        gui_mod.QFileDialog,
        "getOpenFileName",
        lambda *a, **k: (str(bio), ""),
    )

    called = {}

    def fake_ingest(text, manager):
        called["text"] = text
        called["manager"] = manager
        return [], [], []

    monkeypatch.setattr(memory_constructor, "ingest_biography", fake_ingest)

    gui = MemorySystemGUI(agent)
    gui.bio_btn.click()
    gui.import_btn.click()

    assert called["text"] == bio.read_text()
    assert called["manager"] is agent.memory

    app.quit()


def test_import_preview_shows(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])

    bio = tmp_path / "bio.txt"
    bio.write_text("Born 1990. Learned to swim.")

    monkeypatch.setattr(
        gui_mod.QFileDialog,
        "getOpenFileName",
        lambda *a, **k: (str(bio), ""),
    )

    gui = MemorySystemGUI(None)
    gui.bio_btn.click()

    assert "Born 1990" in gui.preview.toPlainText()

    app.quit()


def test_memory_table_shows_all_memory_types(tmp_path):
    app = QApplication.instance() or QApplication([])

    manager = MemoryManager(db_path=tmp_path / "mem.db")
    manager.add_semantic("fact")
    manager.add_procedural("skill")

    agent = MagicMock()
    agent.memory = manager

    gui = MemorySystemGUI(agent)
    gui.refresh_memory_table()

    assert gui.table.rowCount() == len(manager.all_memories())
    types = {gui.table.item(i, 1).text() for i in range(gui.table.rowCount())}
    assert {"semantic", "procedural"} <= types

    app.quit()


def test_memory_browser_edits_and_deletes_non_episodic(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])

    manager = MemoryManager(db_path=tmp_path / "mem.db")
    sem = manager.add_semantic("fact")
    proc = manager.add_procedural("skill")

    agent = MagicMock()
    agent.memory = manager

    gui = MemorySystemGUI(agent)

    class FakeBrowser:
        def __init__(self, mgr):
            self.manager = mgr
            self.list = QListWidget()
            self.row = None

        def display_memory(self, row):
            self.row = row

        def exec(self):
            if self.row == 0:
                self.manager.update_semantic(sem, "better fact")
            else:
                self.manager.delete_procedural(proc)

    monkeypatch.setattr(gui_mod, "MemoryBrowser", FakeBrowser)

    gui.open_memory_dialog(0, 0)
    assert gui.table.item(0, 4).text() == "better fact"

    gui.open_memory_dialog(1, 0)
    assert gui.table.rowCount() == 1

    app.quit()
