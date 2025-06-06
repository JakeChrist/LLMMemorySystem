# Memory Construction Helpers

The `addons.memory_constructor` module provides helper functions for loading
external text data into the memory system.

## `ingest_transcript`

```python
from addons.memory_constructor import ingest_transcript
```

Parses a dialogue transcript and stores each line as an episodic memory. The
speaker name, when present, and the source of the data are recorded in the
metadata. Optionally a short semantic summary can be generated.

## `ingest_biography`

```python
from addons.memory_constructor import ingest_biography
```

Splits biographical text into sentences and stores them as semantic or
procedural memories depending on whether the line describes a skill. All
entries include metadata noting that the source was a biography.
