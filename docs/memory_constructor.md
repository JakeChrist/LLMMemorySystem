# Memory Construction Helpers

The `addons.memory_constructor` module parses raw text sources and stores them
via a `MemoryManager`. Two workflows are provided for importing transcripts and
biographies.

## Transcript workflow

1. Split the text into lines and detect optional ``speaker:`` prefixes.
2. Create episodic `MemoryEntry` objects with emotion labels.
3. Optionally run the `DreamEngine` to generate a semantic summary.

```python
from addons.memory_constructor import ingest_transcript
```

### CLI usage

```bash
python main.py cli add-conversation transcript.txt --agent Thorne
```

### GUI

Open the **Import** tab, click **Choose Transcript** to select a file,
preview the lines and press **Import** to ingest them.

## Biography workflow

1. Split the biography into sentences.
2. Sentences describing a skill are stored in procedural memory.
3. Sentences mentioning specific events or dates are saved as episodic memories.
4. All remaining sentences become semantic entries.

```python
from addons.memory_constructor import ingest_biography
```

### CLI usage

```bash
python main.py cli add-biography bio.txt --agent Thorne
```

### GUI

In the **Import** tab choose **Choose Biography**, review the preview and use
**Import** to load the sentences.
