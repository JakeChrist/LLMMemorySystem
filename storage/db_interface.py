"""SQLite-based persistence for memories."""

from __future__ import annotations

import sqlite3
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
            "CREATE TABLE IF NOT EXISTS memories (content TEXT, timestamp REAL, emotions TEXT)"
        )
        self.conn.commit()

    def save(self, entry: MemoryEntry) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO memories VALUES (?, ?, ?)",
            (
                entry.content,
                entry.timestamp.timestamp(),
                ",".join(entry.emotions),
            ),
        )
        self.conn.commit()

    def load_all(self) -> List[MemoryEntry]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT content, timestamp, emotions FROM memories").fetchall()
        entries: List[MemoryEntry] = []
        for content, ts, emotions in rows:
            entries.append(
                MemoryEntry(content=content, embedding=[], emotions=emotions.split(","))
            )
        return entries
