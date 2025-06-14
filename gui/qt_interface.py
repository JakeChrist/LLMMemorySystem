import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QScrollArea,
    QSplitter,
    QSizePolicy,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QListWidget,
    QMenuBar,
    QAction,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QComboBox,
    QLineEdit,
)
from PyQt5.QtCore import Qt, QTimer
import sys
import re

from ms_utils import format_context
from encoding.tagging import tag_text
from core.memory_entry import MemoryEntry
from llm.lmstudio_api import LMStudioBackend
from llm import llm_router
from core.memory_manager import MemoryManager
from pathlib import Path
from addons import memory_constructor
from . import settings_store


class MemoryBrowser(QDialog):
    """Dialog for inspecting and editing stored memories."""

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.current: object | None = None
        self.setWindowTitle("Stored Memories")

        main = QHBoxLayout()
        self.list = QListWidget()
        self.list.currentRowChanged.connect(self.display_memory)
        main.addWidget(self.list)

        detail_layout = QVBoxLayout()
        self.detail = QTextEdit()
        detail_layout.addWidget(self.detail)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.del_btn = QPushButton("Delete")
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.del_btn)
        detail_layout.addLayout(btn_row)
        main.addLayout(detail_layout)

        self.setLayout(main)

        self.save_btn.clicked.connect(self.save_current)
        self.del_btn.clicked.connect(self.delete_current)

        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for mem in self.manager.all_memories():
            text = f"{mem.timestamp.isoformat()} - {mem.content[:30]}"
            self.list.addItem(text)

    def display_memory(self, row: int) -> None:
        entries = self.manager.all_memories()
        if 0 <= row < len(entries):
            self.current = entries[row]
            self.detail.setPlainText(entries[row].content)
        else:
            self.current = None
            self.detail.clear()

    def save_current(self) -> None:
        if self.current is None:
            return
        new_text = self.detail.toPlainText()
        if new_text != self.current.content:
            if self.current in self.manager.semantic._entries:
                self.manager.update_semantic(self.current, new_text)
            elif self.current in self.manager.procedural._entries:
                self.manager.update_procedural(self.current, new_text)
            else:
                self.manager.update(self.current, new_text)
            self.refresh()

    def delete_current(self) -> None:
        if self.current is None:
            return
        if self.current in self.manager.semantic._entries:
            self.manager.delete_semantic(self.current)
        elif self.current in self.manager.procedural._entries:
            self.manager.delete_procedural(self.current)
        else:
            self.manager.delete(self.current)
        self.current = None
        self.refresh()


class SchedulerSettingsDialog(QDialog):
    """Dialog for configuring :class:`CognitiveScheduler` timers."""

    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler
        self.setWindowTitle("Scheduler Settings")

        layout = QVBoxLayout()
        form = QFormLayout()

        self.think_spin = QDoubleSpinBox()
        self.think_spin.setRange(1.0, 3600.0)
        self.think_spin.setValue(scheduler.T_think)
        form.addRow("T_think (s)", self.think_spin)

        self.dream_spin = QDoubleSpinBox()
        self.dream_spin.setRange(1.0, 7200.0)
        self.dream_spin.setValue(scheduler.T_dream)
        form.addRow("T_dream (s)", self.dream_spin)


        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.0, 60.0)
        self.delay_spin.setValue(scheduler.T_delay)
        form.addRow("T_delay (s)", self.delay_spin)

        agent = getattr(scheduler, "agent", None)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["local", "openai", "claude", "gemini", "lmstudio"])
        if getattr(scheduler, "llm_name", None):
            self.model_combo.setCurrentText(scheduler.llm_name)
        form.addRow("LLM backend", self.model_combo)

        self.db_edit = QLineEdit()
        if agent and getattr(agent, "memory", None):
            self.db_edit.setText(str(agent.memory.db.path))
        db_row = QHBoxLayout()
        db_row.addWidget(self.db_edit)
        browse = QPushButton("Browse")
        browse.clicked.connect(self._choose_db)
        db_row.addWidget(browse)
        form.addRow("Database file", db_row)

        self.lmstudio_timeout_spin = None
        if agent and isinstance(getattr(agent, "llm", None), LMStudioBackend):
            self.lmstudio_timeout_spin = QDoubleSpinBox()
            self.lmstudio_timeout_spin.setRange(0.0, 600.0)
            value = agent.llm.timeout if agent.llm.timeout is not None else 0.0
            self.lmstudio_timeout_spin.setValue(value)
            form.addRow("LMStudio timeout (s)", self.lmstudio_timeout_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def values(self):
        if self.lmstudio_timeout_spin is not None:
            val = self.lmstudio_timeout_spin.value()
            timeout = None if val == 0 else val
        else:
            timeout = None

        return (
            self.think_spin.value(),
            self.dream_spin.value(),
            self.delay_spin.value(),
            timeout,
            self.model_combo.currentText(),
            self.db_edit.text(),
        )

    def _choose_db(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Database")
        if path:
            self.db_edit.setText(path)

class ChatBubble(QLabel):
    """Simple word-wrapped label styled as a chat message bubble."""

    def __init__(self, text, is_user=True):
        super().__init__(text)
        self.setWordWrap(True)
        self.setMargin(10)
        self.setStyleSheet(
            "background-color: %s; border-radius: 10px;" %
            ("#d0f0c0" if is_user else "#f0d0d0")
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

class MemorySystemGUI(QWidget):
    """Qt interface for interacting with an :class:`Agent` and its memories."""

    def __init__(self, agent, scheduler=None):
        super().__init__()
        self.agent = agent
        self.scheduler = scheduler
        if self.scheduler is not None and not hasattr(self.scheduler, "agent"):
            self.scheduler.agent = self.agent
        self._last_dream = None
        self._last_think = None
        self._mem_count = 0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LLMemory Agent Interface")
        self.resize(900, 600)

        # Menu bar with application actions
        self.menu_bar = QMenuBar(self)
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.show_settings)
        self.menu_bar.addAction(self.settings_action)

        # Tabbed conversation area
        self.tabs = QTabWidget()

        # Dialogue tab
        self.dialogue_layout = QVBoxLayout()
        self.dialogue_layout.addStretch()
        dialogue_container = QWidget()
        dialogue_container.setLayout(self.dialogue_layout)
        self.dialogue_scroll = QScrollArea()
        self.dialogue_scroll.setWidgetResizable(True)
        self.dialogue_scroll.setWidget(dialogue_container)

        self.input_box = QTextEdit()
        self.input_box.setMaximumHeight(80)
        self.submit_button = QPushButton("Send")
        self.submit_button.clicked.connect(self.handle_submit)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.submit_button)

        dialogue_tab = QWidget()
        d_layout = QVBoxLayout()
        d_layout.addWidget(self.dialogue_scroll)
        d_layout.addLayout(input_layout)
        dialogue_tab.setLayout(d_layout)
        self.tabs.addTab(dialogue_tab, "Dialogue")

        # Dreaming tab
        self.dream_layout = QVBoxLayout()
        self.dream_layout.addStretch()
        dream_container = QWidget()
        dream_container.setLayout(self.dream_layout)
        self.dream_scroll = QScrollArea()
        self.dream_scroll.setWidgetResizable(True)
        self.dream_scroll.setWidget(dream_container)
        dream_tab = QWidget()
        dream_layout = QVBoxLayout()
        dream_layout.addWidget(self.dream_scroll)
        dream_tab.setLayout(dream_layout)
        self.tabs.addTab(dream_tab, "Dreaming")

        # Thoughts tab
        self.thought_layout = QVBoxLayout()
        self.thought_layout.addStretch()
        thought_container = QWidget()
        thought_container.setLayout(self.thought_layout)
        self.thought_scroll = QScrollArea()
        self.thought_scroll.setWidgetResizable(True)
        self.thought_scroll.setWidget(thought_container)
        thought_tab = QWidget()
        t_layout = QVBoxLayout()
        t_layout.addWidget(self.thought_scroll)
        thought_tab.setLayout(t_layout)
        self.tabs.addTab(thought_tab, "Thoughts")

        # Memories tab
        self.memory_layout = QVBoxLayout()
        self.memory_layout.addStretch()
        memory_container = QWidget()
        memory_container.setLayout(self.memory_layout)
        self.memory_scroll = QScrollArea()
        self.memory_scroll.setWidgetResizable(True)
        self.memory_scroll.setWidget(memory_container)
        memory_tab = QWidget()
        m_layout = QVBoxLayout()
        m_layout.addWidget(self.memory_scroll)
        memory_tab.setLayout(m_layout)
        self.tabs.addTab(memory_tab, "Memories")

        # Browse tab - table of stored memories
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Timestamp", "Type", "Emotion", "Strength", "Memory"]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_memory_dialog)
        browse_tab = QWidget()
        b_layout = QVBoxLayout()
        b_layout.addWidget(self.table)
        browse_tab.setLayout(b_layout)
        self.tabs.addTab(browse_tab, "Browse")

        # Import tab
        import_tab = QWidget()
        i_layout = QVBoxLayout()
        choose_layout = QHBoxLayout()
        self.transcript_btn = QPushButton("Choose Transcript")
        self.bio_btn = QPushButton("Choose Biography")
        choose_layout.addWidget(self.transcript_btn)
        choose_layout.addWidget(self.bio_btn)
        i_layout.addLayout(choose_layout)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        i_layout.addWidget(self.preview)

        action_layout = QHBoxLayout()
        self.import_btn = QPushButton("Import")
        self.cancel_import_btn = QPushButton("Cancel")
        action_layout.addWidget(self.import_btn)
        action_layout.addWidget(self.cancel_import_btn)
        i_layout.addLayout(action_layout)

        import_tab.setLayout(i_layout)
        self.tabs.addTab(import_tab, "Import")

        # Import handlers
        self.transcript_btn.clicked.connect(self.choose_transcript)
        self.bio_btn.clicked.connect(self.choose_biography)
        self.import_btn.clicked.connect(self.import_data)
        self.cancel_import_btn.clicked.connect(self.clear_import)

        self._import_text = ""
        self._import_type = None

        # Right Panel: controls
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Next Dream"))
        self.countdown_label = QLabel("")
        right_panel.addWidget(self.countdown_label)

        right_panel.addStretch()

        # Assemble into layout
        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tabs)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        main_column = QVBoxLayout()
        main_column.setMenuBar(self.menu_bar)
        main_column.addWidget(splitter)

        self.setLayout(main_column)

        # Timer to update dream countdown
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

        self.refresh_memory_table()

    def _scroll_to_bottom(self, scroll: QScrollArea) -> None:
        bar = scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def add_message(self, text: str, *, is_user: bool = True) -> None:
        bubble = ChatBubble(text, is_user=is_user)
        row = QHBoxLayout()
        if is_user:
            row.addStretch()
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch()
        container = QWidget()
        container.setLayout(row)
        self.dialogue_layout.insertWidget(
            self.dialogue_layout.count() - 1, container
        )
        QTimer.singleShot(0, lambda: self._scroll_to_bottom(self.dialogue_scroll))

    def add_dream_message(self, text: str) -> None:
        bubble = ChatBubble(text, is_user=False)
        row = QHBoxLayout()
        row.addWidget(bubble)
        row.addStretch()
        container = QWidget()
        container.setLayout(row)
        self.dream_layout.insertWidget(
            self.dream_layout.count() - 1, container
        )
        QTimer.singleShot(0, lambda: self._scroll_to_bottom(self.dream_scroll))

    def add_thought_message(self, text: str) -> None:
        bubble = ChatBubble(text, is_user=False)
        row = QHBoxLayout()
        row.addWidget(bubble)
        row.addStretch()
        container = QWidget()
        container.setLayout(row)
        self.thought_layout.insertWidget(
            self.thought_layout.count() - 1, container
        )
        QTimer.singleShot(0, lambda: self._scroll_to_bottom(self.thought_scroll))

    def add_memory_message(self, text: str) -> None:
        bubble = ChatBubble(text, is_user=False)
        row = QHBoxLayout()
        row.addWidget(bubble)
        row.addStretch()
        container = QWidget()
        container.setLayout(row)
        self.memory_layout.insertWidget(
            self.memory_layout.count() - 1, container
        )
        QTimer.singleShot(0, lambda: self._scroll_to_bottom(self.memory_scroll))

    def _memory_type(self, mem: MemoryEntry) -> str:
        if mem in self.agent.memory.semantic._entries:
            return "semantic"
        if mem in self.agent.memory.procedural._entries:
            return "procedural"
        if "introspection" in mem.metadata.get("tags", []):
            return "thought"
        if mem.content.startswith("Dream:"):
            return "dream"
        if mem.metadata.get("role") == "assistant":
            return "response"
        return "user"

    def refresh_memory_table(self) -> None:
        if not self.agent:
            self.table.setRowCount(0)
            return
        entries = self.agent.memory.all_memories()
        self.table.setRowCount(len(entries))
        for row, mem in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(mem.timestamp.isoformat()))
            self.table.setItem(row, 1, QTableWidgetItem(self._memory_type(mem)))
            emotion = mem.emotions[0] if mem.emotions else ""
            strength = mem.emotion_scores.get(emotion, 0.0) if emotion else 0.0
            self.table.setItem(row, 2, QTableWidgetItem(emotion))
            self.table.setItem(row, 3, QTableWidgetItem(f"{strength:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(mem.content))

    def update_countdown(self) -> None:
        if not self.agent:
            self.countdown_label.setText("")
            return
        dream = self.agent.memory.time_until_dream()
        think = self.agent.memory.time_until_think()
        if dream is None and think is None:
            self.countdown_label.setText("")
        else:
            parts = []
            if dream is not None:
                parts.append(f"D:{int(dream)}s")
            if think is not None:
                parts.append(f"T:{int(think)}s")
            self.countdown_label.setText(" | ".join(parts))

        dream_entries = [
            m for m in self.agent.memory.all_memories()
            if m.content.startswith("Dream:")
        ]
        if dream_entries:
            latest = dream_entries[-1]
            if latest is not self._last_dream:
                self.add_dream_message(latest.content)
                self._last_dream = latest

        think_entries = [
            m
            for m in self.agent.memory.all_memories()
            if "introspection" in m.metadata.get("tags", [])
        ]
        if think_entries:
            latest_think = think_entries[-1]
            if latest_think is not self._last_think:
                self.add_thought_message(latest_think.content)
                self._last_think = latest_think

        entries = self.agent.memory.all_memories()
        if len(entries) != self._mem_count:
            self._mem_count = len(entries)
            self.refresh_memory_table()

    def show_settings(self):
        if not self.scheduler:
            return
        dlg = SchedulerSettingsDialog(self.scheduler)
        if dlg.exec() == QDialog.Accepted:
            think, dream, delay, timeout, llm_name, db_path = dlg.values()
            self.scheduler.T_think = think
            self.scheduler.T_dream = dream
            self.scheduler.T_delay = delay
            self.scheduler.llm_name = llm_name
            self.scheduler.notify_input()

            if self.agent:
                if self.agent.llm_name != llm_name:
                    self.agent.llm_name = llm_name
                    self.agent.llm = llm_router.get_llm(llm_name)

                if str(self.agent.memory.db.path) != db_path:
                    self.agent.memory = MemoryManager(db_path=db_path)
                    self.scheduler.manager = self.agent.memory

                if isinstance(self.agent.llm, LMStudioBackend):
                    self.agent.llm.timeout = timeout
                    if timeout is None:
                        os.environ["LMSTUDIO_TIMEOUT"] = "none"
                    else:
                        os.environ["LMSTUDIO_TIMEOUT"] = str(timeout)

            data = {
                "T_think": self.scheduler.T_think,
                "T_dream": self.scheduler.T_dream,
                "T_delay": self.scheduler.T_delay,
                "llm_name": self.scheduler.llm_name,
                "db_path": str(self.agent.memory.db.path) if self.agent else "",
                "lmstudio_timeout": (
                    self.agent.llm.timeout
                    if self.agent and isinstance(self.agent.llm, LMStudioBackend)
                    else None
                ),
            }
            settings_store.save_settings(data)

    def show_memories(self):
        if not self.agent:
            return
        dlg = MemoryBrowser(self.agent.memory)
        dlg.exec()

    def open_memory_dialog(self, row: int | None = None, column: int | None = None) -> None:
        """Open a :class:`MemoryBrowser` and refresh the table when closed."""
        if not self.agent:
            return
        dlg = MemoryBrowser(self.agent.memory)
        if row is not None:
            dlg.list.setCurrentRow(row)
            dlg.display_memory(row)
        dlg.exec()
        self.refresh_memory_table()

    def choose_transcript(self) -> None:
        """Prompt user to select a transcript file and show a preview."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Transcript")
        if path:
            with open(path, "r", encoding="utf-8") as fh:
                self._import_text = fh.read()
            self._import_type = "transcript"
            lines = [ln.strip() for ln in self._import_text.splitlines() if ln.strip()]
            self.preview.setPlainText("\n".join(lines))

    def choose_biography(self) -> None:
        """Prompt user to select a biography file and show a preview."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Biography")
        if path:
            with open(path, "r", encoding="utf-8") as fh:
                self._import_text = fh.read()
            self._import_type = "biography"
            parts = re.split(r"[.!?]+\s*", self._import_text)
            lines = [p.strip() for p in parts if p.strip()]
            self.preview.setPlainText("\n".join(lines))

    def import_data(self) -> None:
        """Import previewed data into memory and clear the preview."""
        if not self.agent or not self._import_text:
            return
        if self._import_type == "transcript":
            memory_constructor.ingest_transcript(self._import_text, self.agent.memory)
        elif self._import_type == "biography":
            memory_constructor.ingest_biography(self._import_text, self.agent.memory)
        self.refresh_memory_table()
        self.clear_import()

    def clear_import(self) -> None:
        """Reset import state and clear preview text."""
        self._import_text = ""
        self._import_type = None
        self.preview.clear()

    def handle_submit(self):
        user_input = self.input_box.toPlainText().strip()
        if not user_input:
            return
        self.input_box.clear()

        if self.scheduler is not None:
            self.scheduler.notify_input()

        # Add user message to chat
        self.add_message(user_input, is_user=True)

        # Query the agent and update debug panels
        response = self.agent.receive(user_input) if self.agent else ""

        # Working memory context used by the agent
        context = []
        working = []
        if self.agent:
            from retrieval.cue_builder import build_cue
            from retrieval.retriever import Retriever

            tags = tag_text(user_input)
            cue = build_cue(user_input, tags=tags, state={"mood": self.agent.mood})
            retriever = Retriever(
                self.agent.memory.all(),
                semantic=self.agent.memory.semantic.all(),
                procedural=self.agent.memory.procedural.all(),
            )
            retrieved = retriever.query(cue, top_k=5, mood=self.agent.mood, tags=tags)
            context = [m.content for m in retrieved]
            working = self.agent.working_memory()

        # Add response bubble
        self.add_message(response, is_user=False)

        # Update right panel
        mem_text = format_context(working)
        if context:
            mem_text += "\n\nRetrieved:\n" + format_context(context)
        self.add_memory_message(mem_text)
        self._mem_count = (
            len(self.agent.memory.all_memories()) if self.agent else 0
        )
        self.refresh_memory_table()


def run_gui(agent=None, scheduler=None):
    """Launch the Qt GUI and return when the window is closed.

    Parameters
    ----------
    agent:
        Optional :class:`~core.agent.Agent` controlling the conversation.
    scheduler:
        Optional :class:`~core.cognitive_scheduler.CognitiveScheduler` used to
        report user input events.
    """
    # QApplication should be instantiated once in a process.  Creating
    # a new instance when one already exists raises a runtime error,
    # which can easily happen in interactive sessions (e.g. Jupyter).
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    if agent and scheduler:
        cfg = settings_store.load_settings()
        scheduler.T_think = cfg.get("T_think", scheduler.T_think)
        scheduler.T_dream = cfg.get("T_dream", scheduler.T_dream)
        scheduler.T_delay = cfg.get("T_delay", scheduler.T_delay)
        scheduler.llm_name = cfg.get("llm_name", scheduler.llm_name)

        if agent.llm_name != scheduler.llm_name:
            agent.llm_name = scheduler.llm_name
            agent.llm = llm_router.get_llm(agent.llm_name)

        db_path = cfg.get("db_path")
        if db_path and str(agent.memory.db.path) != db_path:
            agent.memory = MemoryManager(db_path=db_path)
            scheduler.manager = agent.memory

        if isinstance(agent.llm, LMStudioBackend):
            timeout = cfg.get("lmstudio_timeout")
            if timeout is not None:
                agent.llm.timeout = timeout
                os.environ["LMSTUDIO_TIMEOUT"] = (
                    "none" if timeout is None else str(timeout)
                )

    gui = MemorySystemGUI(agent, scheduler)
    gui.show()
    # exec_() is deprecated in modern PyQt5 versions but still supported.
    # Using exec() keeps compatibility with both newer and older releases.
    sys.exit(app.exec())

# Usage:
# from gui.qt_interface import run_gui
# run_gui(agent)
