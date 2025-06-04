"""SQLite-based persistence for memories."""

from __future__ import annotations

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from core.memory_entry import MemoryEntry


class Database:
    def __init__(self, path: str | Path = "memory.db") -> None:
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self._setup()

    def _setup(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS memories (content TEXT, timestamp REAL, embedding TEXT, emotions TEXT, metadata TEXT)"
        )
        self.conn.commit()

    def save(self, entry: MemoryEntry) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO memories VALUES (?, ?, ?, ?, ?)",
            (
                entry.content,
                entry.timestamp.timestamp(),
                json.dumps(entry.embedding),
                ",".join(entry.emotions),
                json.dumps(entry.metadata),
            ),
        )
        self.conn.commit()

    def load_all(self) -> List[MemoryEntry]:
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT content, timestamp, embedding, emotions, metadata FROM memories"
        ).fetchall()
        entries: List[MemoryEntry] = []
        for content, ts, emb, emotions, metadata in rows:
            entries.append(
                MemoryEntry(
                    content=content,
                    embedding=json.loads(emb) if emb else [],
                    timestamp=datetime.utcfromtimestamp(ts),
                    emotions=emotions.split(",") if emotions else [],
                    metadata=json.loads(metadata) if metadata else {},
                )
            )
        return entries

    def clear(self) -> None:
        """Delete all stored memories."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM memories")
        self.conn.commit()
