# GUI Tabbed Interface

The Qt GUI groups output into four tabs using a ``QTabWidget``:

- **Dialogue** – the main conversation view. New user and agent messages appear here. The text input box and **Send** button are only visible on this tab.
- **Dreaming** – shows bubbles for background dream summaries when the DreamEngine triggers.
- **Thoughts** – displays introspection results from the ThinkingEngine.
- **Memories** – lists the agent's current working memory and retrieved context after each user submission.

Each tab uses a scrolling list of chat bubbles similar to the conversation view. Background entries are appended automatically when they are generated. You can browse all stored memories using the **Browse Memories** button which is still located on the right side panel.
