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
        cur.execute(
            "CREATE TABLE IF NOT EXISTS semantic_memories (content TEXT, timestamp REAL, embedding TEXT, emotions TEXT, metadata TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS procedural_memories (content TEXT, timestamp REAL, embedding TEXT, emotions TEXT, metadata TEXT)"
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
        cur.execute("DELETE FROM semantic_memories")
        cur.execute("DELETE FROM procedural_memories")
        self.conn.commit()

    def delete(self, timestamp: datetime) -> None:
        """Remove a memory entry by timestamp."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM memories WHERE timestamp=?", (timestamp.timestamp(),))
        self.conn.commit()

    def update(self, timestamp: datetime, entry: MemoryEntry) -> None:
        """Update a memory entry identified by ``timestamp`` with new values."""
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE memories SET content=?, embedding=?, emotions=?, metadata=? WHERE timestamp=?",
            (
                entry.content,
                json.dumps(entry.embedding),
                ",".join(entry.emotions),
                json.dumps(entry.metadata),
                timestamp.timestamp(),
            ),
        )
        self.conn.commit()

    # --- Semantic memory operations ---
    def save_semantic(self, entry: MemoryEntry) -> None:
        self._save_to_table("semantic_memories", entry)

    def load_all_semantic(self) -> List[MemoryEntry]:
        return self._load_from_table("semantic_memories")

    def delete_semantic(self, timestamp: datetime) -> None:
        self._delete_from_table("semantic_memories", timestamp)

    def update_semantic(self, timestamp: datetime, entry: MemoryEntry) -> None:
        self._update_table("semantic_memories", timestamp, entry)

    # --- Procedural memory operations ---
    def save_procedural(self, entry: MemoryEntry) -> None:
        self._save_to_table("procedural_memories", entry)

    def load_all_procedural(self) -> List[MemoryEntry]:
        return self._load_from_table("procedural_memories")

    def delete_procedural(self, timestamp: datetime) -> None:
        self._delete_from_table("procedural_memories", timestamp)

    def update_procedural(self, timestamp: datetime, entry: MemoryEntry) -> None:
        self._update_table("procedural_memories", timestamp, entry)

    # --- Internal helpers ---
    def _save_to_table(self, table: str, entry: MemoryEntry) -> None:
        cur = self.conn.cursor()
        cur.execute(
            f"INSERT INTO {table} VALUES (?, ?, ?, ?, ?)",
            (
                entry.content,
                entry.timestamp.timestamp(),
                json.dumps(entry.embedding),
                ",".join(entry.emotions),
                json.dumps(entry.metadata),
            ),
        )
        self.conn.commit()

    def _load_from_table(self, table: str) -> List[MemoryEntry]:
        cur = self.conn.cursor()
        rows = cur.execute(
            f"SELECT content, timestamp, embedding, emotions, metadata FROM {table}"
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

    def _delete_from_table(self, table: str, timestamp: datetime) -> None:
        cur = self.conn.cursor()
        cur.execute(
            f"DELETE FROM {table} WHERE timestamp=?",
            (timestamp.timestamp(),),
        )
        self.conn.commit()

    def _update_table(self, table: str, timestamp: datetime, entry: MemoryEntry) -> None:
        cur = self.conn.cursor()
        cur.execute(
            f"UPDATE {table} SET content=?, embedding=?, emotions=?, metadata=? WHERE timestamp=?",
            (
                entry.content,
                json.dumps(entry.embedding),
                ",".join(entry.emotions),
                json.dumps(entry.metadata),
                timestamp.timestamp(),
            ),
        )
        self.conn.commit()
