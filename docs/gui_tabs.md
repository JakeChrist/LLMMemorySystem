# GUI Tabbed Interface

The Qt GUI groups output into six tabs using a ``QTabWidget``:

- **Dialogue** – the main conversation view. New user and agent messages appear here. The text input box and **Send** button are only visible on this tab.
- **Dreaming** – shows bubbles for background dream summaries when the DreamEngine triggers.
- **Thoughts** – displays introspection results from the ThinkingEngine.
- **Memories** – lists the agent's current working memory and retrieved context after each user submission.
- **Browse** – shows all stored memories in a table view.
- **Import** – preview and load transcript or biography files into memory.

The Import tab offers **Choose Transcript** and **Choose Biography** buttons
for selecting a text file. The contents are shown in a read-only preview before
pressing **Import** to ingest the data or **Cancel** to discard it.

Each tab uses a scrolling list of chat bubbles similar to the conversation view. Background entries are appended automatically when they are generated. The "Browse" tab replaces the old **Browse Memories** button and presents every stored memory in a sortable table.
