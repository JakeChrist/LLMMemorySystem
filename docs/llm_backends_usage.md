# Running LLMemory with Different LLM Backends

This guide provides step by step instructions for launching the system using each available LLM backend. All entry points share the same command line structure:

```bash
python main.py MODE --llm BACKEND [--db PATH]
```

- `MODE` can be `repl`, `gui` or `cli`.
- `BACKEND` selects the LLM implementation (`local`, `openai`, `claude`, `gemini`, `lmstudio`).
- `PATH` is the SQLite database file (defaults to `memory.db`).

Install the core requirements first:

```bash
pip install -r requirements.txt
```

## Local backend

The local backend requires no additional packages. Run:

```bash
python main.py repl --llm local
```

Use `gui` or `cli` in place of `repl` to start the graphical interface or command line tool.

## OpenAI backend

1. Install the OpenAI package:
   ```bash
   pip install openai
   ```
2. Set your API key:
   ```bash
   export OPENAI_API_KEY=YOUR_KEY
   ```
3. Launch the program:
   ```bash
   python main.py repl --llm openai
   ```

## Claude backend

1. Install the Anthropic client:
   ```bash
   pip install anthropic
   ```
2. Export your key:
   ```bash
   export ANTHROPIC_API_KEY=YOUR_KEY
   ```
3. Run LLMemory:
   ```bash
   python main.py repl --llm claude
   ```

## Gemini backend

1. Install Google's generative AI SDK:
   ```bash
   pip install google-generativeai
   ```
2. Provide your API key:
   ```bash
   export GEMINI_API_KEY=YOUR_KEY
   ```
3. Start the system:
   ```bash
   python main.py repl --llm gemini
   ```

## LMStudio backend

1. Ensure the `requests` library is installed:
   ```bash
   pip install requests
   ```
2. Start the LMStudio server locally and note its URL.
3. Optionally set environment variables to override defaults:
   ```bash
   export LMSTUDIO_URL=http://localhost:1234/v1/chat/completions
   export LMSTUDIO_MODEL=my-model-name
   ```
4. Launch LLMemory:
   ```bash
   python main.py repl --llm lmstudio
   ```

The same `--llm` option works with the GUI or memory CLI modes. For example:

```bash
python main.py gui --llm openai
python main.py cli --llm gemini list
```

