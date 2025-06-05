# System architecture

The LLMemory project is organized around a small set of cooperating modules. An
``Agent`` receives user text, stores it via the ``MemoryManager`` and generates a
response using a pluggable LLM backend. The main subsystems are shown below.

```
+-------+  add/query  +---------------+
| Agent |-----------> | MemoryManager |
+-------+             +---------------+
     |                       |
     |               episodic / semantic / procedural
     |                       v
     |                +-------------+
     |   cue/tags --> | Retriever   |
     |                +-------------+
     |                       |
     |                +--------------+
     |<-------------- | Reconstructor|
     |  context       +--------------+
     |                       |
     |              prompt/context
     v                       v
 +---------+ <-------  +-----------+
 | LLM via |           | DreamEngine|
 | router  |---summar- +-----------+
 +---------+
```

1. **Agent** – orchestrates the conversation loop. It tags incoming text,
   builds a cue, and retrieves relevant memories before calling the LLM.
2. **MemoryManager** – coordinates three memory stores:
   - **episodic**: chronological events, loaded into working memory and
     pruned over time.
   - **semantic**: factual summaries and schemas.
   - **procedural**: skills or instructions.
   The manager persists entries via ``Database`` and exposes helpers for
   adding, deleting and updating all types.
3. **Retriever** – given a cue from ``cue_builder`` and optional mood or tags,
   ranks episodic, semantic and procedural memories using embeddings and
   recency weighting.
4. **Reconstructor** – merges retrieved memories into a context window for the
   next prompt.
5. **DreamEngine** – background summarization. It periodically summarizes
   recent episodic memories using an LLM and can store the result back into
   semantic memory while pruning old entries.
6. **LLM router** – ``llm_router.get_llm()`` selects the backend. Supported
   names are ``local``, ``openai``, ``claude`` and ``gemini``. The ``Agent``
   chooses one at construction or via the command line.

Episodic experiences feed into semantic summaries during dreaming and may form
procedural memories manually. Retrieval queries all stores so that facts,
procedures and recent events together influence the generated reply.
