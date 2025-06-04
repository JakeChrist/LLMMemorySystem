"""Command line interface for inspecting stored memories."""

from __future__ import annotations

import argparse

from core.emotion_model import analyze_emotions
from core.memory_entry import MemoryEntry
from encoding.encoder import encode_text
from dreaming.dream_engine import DreamEngine
from retrieval.retriever import Retriever
from storage.db_interface import Database


def list_memories(db: Database) -> None:
    """Print all memories stored in the database."""
    memories = db.load_all()
    for i, mem in enumerate(memories, 1):
        ts = mem.timestamp.isoformat()
        print(f"{i}. {ts} - {mem.content}")


def add_memory(db: Database, text: str) -> None:
    """Add a new memory entry to the database."""
    emotions = analyze_emotions(text)
    entry = MemoryEntry(
        content=text,
        embedding=encode_text(text),
        emotions=emotions,
        metadata={},
    )
    db.save(entry)
    print("Memory added.")


def query_memories(db: Database, text: str, top_k: int = 5) -> None:
    """Query stored memories using vector similarity."""
    memories = db.load_all()
    retriever = Retriever(memories)
    results = retriever.query(text, top_k=top_k)
    for mem in results:
        print(f"{mem.timestamp.isoformat()} - {mem.content}")


def dream_summary(db: Database) -> None:
    """Generate a dream summary from all memories."""
    memories = db.load_all()
    engine = DreamEngine()
    summary = engine.summarize(memories)
    print(summary)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Memory management CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List stored memories")

    add_p = sub.add_parser("add", help="Add a new memory")
    add_p.add_argument("text", help="Memory text")

    query_p = sub.add_parser("query", help="Query memories")
    query_p.add_argument("text", help="Query text")
    query_p.add_argument("--top-k", type=int, default=5, help="Number of results")

    sub.add_parser("dream", help="Generate dream summary")

    args = parser.parse_args(argv)

    db = Database()

    if args.cmd == "list":
        list_memories(db)
    elif args.cmd == "add":
        add_memory(db, args.text)
    elif args.cmd == "query":
        query_memories(db, args.text, top_k=args.top_k)
    elif args.cmd == "dream":
        dream_summary(db)


if __name__ == "__main__":
    main()
