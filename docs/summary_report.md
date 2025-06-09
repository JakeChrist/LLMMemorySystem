# 🧠 LLMemory Implementation Plan — Summary Report

## 🔹 Introduction

The **LLMemory system** is a local-first, reconstructive memory architecture for AI agents inspired by human cognition. It supports episodic, semantic, and procedural memory with emotion modeling and background dreaming for schema formation and long-term context reconstruction. It is pluggable, LLM-agnostic, and designed to help agents evolve their behavior over time.

---

## Dependencies

- Python 3.10+
- [sentence-transformers](https://www.sbert.net/) *(optional)* — used by `encoding/encoder.py` for generating real embeddings when installed.

---

## 📁 Project Directory Structure

```
llmemory/
├── main.py                    # Entry point
├── config/                    # Configuration files
├── core/                      # Core logic including memory types and agent
│   └── memory_types/          # Episodic, semantic, procedural memory
├── encoding/                  # Text-to-vector encoding and tagging
├── retrieval/                 # Cue construction and memory retrieval
├── reconstruction/            # Reconstruct working memory context
├── dreaming/                  # Background summarization and pruning
├── storage/                   # Persistent storage and vector indexing
├── llm/                       # Pluggable LLM backends (OpenAI, Claude, LMStudio, etc.)
├── utils/                     # Logging and background task management
├── cli/                       # Command-line interface
├── tests/                     # Unit tests
├── docs/                      # Documentation
└── gui/                       # Optional PyQt GUI with conversation view
```

---

## ✅ Features Implemented So Far

- 🧱 Modular folder structure scaffolded and zipped for immediate development.
- 🔌 Pluggable LLM interface design for OpenAI, Claude, Gemini, LMStudio, etc.
- 🧠 Placeholder files for all core systems: encoding, retrieval, reconstruction, dreaming.
- 🪟 **Optional PyQt5 GUI**:
  - Three-panel layout: left (user inputs), center (LLM responses), right (agent state).
  - Dummy placeholders for memory, mood, and dreaming.
- 📦 Downloadable project ZIP with code templates and GUI included.

### 🚀 Launching the GUI

Create an ``Agent`` instance and pass it to ``run_gui``:

```python
from core.agent import Agent
from gui.qt_interface import run_gui

agent = Agent("local")
run_gui(agent)
```

---

## 🔜 Next Steps

### 🔧 Core Memory System
- [ ] Implement `MemoryEntry` data structures with metadata, embeddings, emotion tags.
- [ ] Connect `encoder.py` to real embedding models (e.g., `sentence-transformers`).
- [ ] Develop `retriever.py` to return top-K relevant memories using FAISS or Chroma.
- [ ] Implement `reconstructor.py` to merge memory fragments into coherent prompts.

### 🧠 Emotion & Mood
- [ ] Add `emotion_model.py` logic using sentiment classifier.
- [ ] Use mood to bias retrieval and context generation.

### 🌙 Dreaming Subsystem
- [ ] Add `dream_engine.py` to run in background or on schedule.
- [ ] Summarize related memories, generate schemas, prune redundancies.

### 🤖 LLM Integration
- [ ] Implement each LLM backend wrapper (`openai_api.py`, `local_llm.py`, etc.).
- [ ] Use `llm_router.py` to dynamically select backend.
- [ ] Route agent output to selected LLM using reconstructed prompt.

### 🖥️ GUI Polishing (Optional)
- [ ] Make PyQt GUI reactive to real memory data.
- [ ] Add mood/dreaming visualization (e.g., color-coded or icon-based).
- [ ] Enable editing or exploration of stored memories from the GUI.

### 🧪 Testing & CLI
- [ ] Build `test_memory_workflow.py` to simulate full memory loop.
- [ ] Add CLI commands to query memory, trigger dreams, or reset state.

### CLI Usage

```
python -m cli.memory_cli list
python -m cli.memory_cli add "remember this" --model all-MiniLM-L6-v2
python -m cli.memory_cli query "cats" --top-k 3 --model all-MiniLM-L6-v2
python -m cli.memory_cli dream
python -m cli.memory_cli reset
python -m cli.memory_cli add-conversation chat.txt --agent bob
python -m cli.memory_cli add-biography bio.txt --agent bob
```

Use `--model` to select a sentence-transformers embedding model and `--top-k`
to control query result count.

### Launching with custom backends

You can run the main entry point with a specific LLM backend and database path:

```
python main.py repl --llm openai --db ./my.db
python main.py gui --llm openai --db ./my.db
python main.py cli --db ./my.db list
```

## License

This documentation is licensed under the [MIT License](../LICENSE). Copyright (c) 2024 Jacob Christ.
