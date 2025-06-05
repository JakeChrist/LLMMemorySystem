from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QListWidget, QScrollArea, QListWidgetItem,
    QSplitter, QFrame, QSizePolicy, QDialog
)
from PyQt5.QtCore import Qt
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
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LLMemory Agent Interface")
        self.resize(1200, 700)

        # Left Panel: User prompts
        self.user_list = QListWidget()
        self.user_list.setStyleSheet("background-color: #f7f7f7;")
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("User Prompts"))
        left_panel.addWidget(self.user_list)

        # Middle Panel: LLM responses
        self.response_list = QListWidget()
        self.response_list.setStyleSheet("background-color: #ffffff;")
        middle_panel = QVBoxLayout()
        middle_panel.addWidget(QLabel("LLM Responses"))
        middle_panel.addWidget(self.response_list)

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
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        middle_widget = QWidget()
        middle_widget.setLayout(middle_panel)
        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(middle_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400, 400])
        splitter.setStretchFactor(1, 1)

        main_column = QVBoxLayout()
        main_column.addWidget(splitter)
        main_column.addLayout(input_layout)

        self.setLayout(main_column)

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

        # Add user input to left panel
        user_item = QListWidgetItem(user_input)
        self.user_list.addItem(user_item)

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
            retriever = Retriever(self.agent.memory.all())
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

        # Add response to middle panel
        response_item = QListWidgetItem(response)
        self.response_list.addItem(response_item)

        # Update right panel
        mem_text = format_context(working)
        if context:
            mem_text += "\n\nRetrieved:\n" + format_context(context)
        self.memory_box.setPlainText(mem_text)
        self.mood_box.setPlainText(mood)
        self.dream_box.setPlainText(dreaming)

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
