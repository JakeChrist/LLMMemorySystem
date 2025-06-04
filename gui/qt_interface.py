from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QListWidget, QScrollArea, QListWidgetItem,
    QSplitter, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
import sys

from ms_utils import format_context

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

        # Layout setup
        main_layout = QHBoxLayout(self)

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

    def handle_submit(self):
        user_input = self.input_box.toPlainText().strip()
        if not user_input:
            return
        self.input_box.clear()

        # Add user input to left panel
        user_item = QListWidgetItem(user_input)
        self.user_list.addItem(user_item)

        # Dummy logic (replace with actual agent call)
        context = ["Agent met a dragon.", "Agent learned fire magic."]
        response = "The agent recalls using fire magic to defeat the dragon."
        mood = "Curious, determined"
        dreaming = "Summarizing recent battle experiences into schema..."

        # Add response to middle panel
        response_item = QListWidgetItem(response)
        self.response_list.addItem(response_item)

        # Update right panel
        self.memory_box.setPlainText(format_context(context))
        self.mood_box.setPlainText(mood)
        self.dream_box.setPlainText(dreaming)

def run_gui(agent=None):
    app = QApplication(sys.argv)
    gui = MemorySystemGUI(agent)
    gui.show()
    sys.exit(app.exec_())

# Usage:
# from gui.qt_interface import run_gui
# run_gui(agent)
