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
    QListWidget,
)
from PyQt5.QtCore import Qt, QTimer
import sys

from ms_utils import format_context
from encoding.tagging import tag_text


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
        for mem in self.manager.all():
            text = f"{mem.timestamp.isoformat()} - {mem.content[:30]}"
            self.list.addItem(text)

    def display_memory(self, row: int) -> None:
        entries = self.manager.all()
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
            self.manager.update(self.current, new_text)
            self.refresh()

    def delete_current(self) -> None:
        if self.current is None:
            return
        self.manager.delete(self.current)
        self.current = None
        self.refresh()

class ChatBubble(QLabel):
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
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self._last_dream: str | None = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LLMemory Agent Interface")
        self.resize(900, 600)

        # Conversation area
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.addStretch()
        self.chat_widget.setLayout(self.chat_layout)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setWidget(self.chat_widget)

        # Right Panel: State debug panel
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Working Memory"))
        self.memory_box = QTextEdit()
        self.memory_box.setReadOnly(True)
        right_panel.addWidget(self.memory_box)

        right_panel.addWidget(QLabel("Current Mood"))
        self.mood_box = QTextEdit()
        self.mood_box.setReadOnly(True)
        right_panel.addWidget(self.mood_box)

        right_panel.addWidget(QLabel("Dreaming Output"))
        self.dream_box = QTextEdit()
        self.dream_box.setReadOnly(True)
        right_panel.addWidget(self.dream_box)
        if self.agent:
            dream_entries = [
                m.content
                for m in self.agent.memory.all()
                if m.content.startswith("Dream:")
            ]
            if dream_entries:
                self._last_dream = dream_entries[-1]
                self.dream_box.setPlainText(self._last_dream)

        right_panel.addWidget(QLabel("Next Dream"))
        self.countdown_label = QLabel("")
        right_panel.addWidget(self.countdown_label)

        self.mem_button = QPushButton("Browse Memories")
        self.mem_button.clicked.connect(self.show_memories)
        right_panel.addWidget(self.mem_button)

        # Input bar
        self.input_box = QTextEdit()
        self.input_box.setMaximumHeight(80)
        self.submit_button = QPushButton("Send")
        self.submit_button.clicked.connect(self.handle_submit)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.submit_button)

        # Assemble into layout
        chat_container = QWidget()
        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.chat_scroll)
        chat_container.setLayout(chat_layout)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(chat_container)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        main_column = QVBoxLayout()
        main_column.addWidget(splitter)
        main_column.addLayout(input_layout)

        self.setLayout(main_column)

        # Timer to update dream countdown
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

    def scroll_to_bottom(self):
        bar = self.chat_scroll.verticalScrollBar()
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
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
        QTimer.singleShot(0, self.scroll_to_bottom)

    def update_countdown(self) -> None:
        if not self.agent:
            self.countdown_label.setText("")
            return
        remaining = self.agent.memory.time_until_dream()
        if remaining is None:
            self.countdown_label.setText("")
        else:
            self.countdown_label.setText(f"{int(remaining)}s")

        dream_entries = [
            m.content
            for m in self.agent.memory.all()
            if m.content.startswith("Dream:")
        ]
        if dream_entries:
            latest = dream_entries[-1]
            if latest != self._last_dream:
                self._last_dream = latest
                self.dream_box.setPlainText(latest)

    def show_memories(self):
        if not self.agent:
            return
        dlg = MemoryBrowser(self.agent.memory)
        dlg.exec()

    def handle_submit(self):
        user_input = self.input_box.toPlainText().strip()
        if not user_input:
            return
        self.input_box.clear()

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
            dream_entries = [
                m.content
                for m in self.agent.memory.all()
                if m.content.startswith("Dream:")
            ]
            dreaming = dream_entries[-1] if dream_entries else ""
            mood = self.agent.mood
        else:
            mood = ""
            dreaming = ""

        # Add response bubble
        self.add_message(response, is_user=False)

        # Update right panel
        mem_text = format_context(working)
        if context:
            mem_text += "\n\nRetrieved:\n" + format_context(context)
        self.memory_box.setPlainText(mem_text)
        self.mood_box.setPlainText(mood)
        self.dream_box.setPlainText(dreaming)
        if dreaming:
            self._last_dream = dreaming

def run_gui(agent=None):
    """Launch the Qt GUI and return when the window is closed."""
    # QApplication should be instantiated once in a process.  Creating
    # a new instance when one already exists raises a runtime error,
    # which can easily happen in interactive sessions (e.g. Jupyter).
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    gui = MemorySystemGUI(agent)
    gui.show()
    # exec_() is deprecated in modern PyQt5 versions but still supported.
    # Using exec() keeps compatibility with both newer and older releases.
    sys.exit(app.exec())

# Usage:
# from gui.qt_interface import run_gui
# run_gui(agent)
