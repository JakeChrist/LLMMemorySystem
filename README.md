# LLMemory System

LLMemory is a small demonstration of a local-first memory architecture for language model agents.  
It supports episodic, semantic and procedural memories, retrieval based on embeddings and tags, mood analysis and optional background "dreaming" summaries.  An LLM backend can be swapped out using a pluggable interface.

## Usage

`main.py` is the entry point and exposes three modes:

```
python main.py MODE [--llm NAME] [--db PATH]
```

- **MODE** – `cli`, `gui` or `repl`
- **--llm** – which backend to use (`local`, `openai`, `claude`, `gemini`)
- **--db** – path to the SQLite database used for persistence

### Command line interface

Running `python main.py cli` invokes `cli.memory_cli` which provides a set of subcommands:

```
list                  # list stored memories
add TEXT [--model MODEL]
query TEXT [--top-k N] [--model MODEL]
reset
edit TIMESTAMP TEXT
delete TIMESTAMP
list-sem | add-sem TEXT | edit-sem TIMESTAMP TEXT | delete-sem TIMESTAMP
list-proc | add-proc TEXT | edit-proc TIMESTAMP TEXT | delete-proc TIMESTAMP
start-dream [--interval SECS]
stop-dream
```

`start-dream` runs continuously until interrupted with `Ctrl+C`. The
`stop-dream` command only works when the dreaming scheduler is started
programmatically in the same process.

### REPL and GUI

```
python main.py repl --llm openai
python main.py gui  --llm local
```

The REPL mode starts a simple console conversation loop.  The GUI mode launches the PyQt5 interface defined in `gui/qt_interface.py`.

## Requirements

The project only relies on the Python standard library for basic operation.  The packages below enable optional features:

- `sentence-transformers` – real text embeddings
- `transformers` – sentiment analysis for emotions
- `openai`, `anthropic`, `google-generativeai` – alternative LLM backends
- `PyQt5` – graphical interface
- `numpy`, `faiss` – vector index acceleration
- `pyyaml` – reading YAML config files
- `pytest` – running the unit tests

Install everything using:

```
pip install -r requirements.txt
```

## Running the tests

Unit tests are located in the `tests/` directory and can be executed with:

```
pytest
```
