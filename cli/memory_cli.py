"""Command line interface for inspecting stored memories."""

from __future__ import annotations

import argparse
from datetime import datetime

from ms_utils.logger import Logger
import time

logger = Logger(__name__)

from core.emotion_model import analyze_emotions
from core.memory_entry import MemoryEntry
from encoding.encoder import encode_text, set_model_name
from encoding.tagging import tag_text
from dreaming.dream_engine import DreamEngine
from core.memory_manager import MemoryManager
from retrieval.retriever import Retriever
from storage.db_interface import Database


def list_memories(db: Database) -> None:
    """Print all memories stored in the database."""
    memories = db.load_all()
    for i, mem in enumerate(memories, 1):
        ts = mem.timestamp.isoformat()
        logger.info(f"{i}. {ts} - {mem.content}")


def add_memory(db: Database, text: str, model: str | None = None) -> None:
    """Add a new memory entry to the database."""
    emotions = analyze_emotions(text)
    labels = [e[0] for e in emotions]
    scores = {label: score for label, score in emotions}
    tags = tag_text(text)
    entry = MemoryEntry(
        content=text,
        embedding=encode_text(text, model_name=model),
        emotions=labels,
        emotion_scores=scores,
        metadata={"tags": tags},
    )
    db.save(entry)
    logger.info("Memory added.")


def query_memories(
    db: Database, text: str, top_k: int = 5, model: str | None = None
) -> None:
    """Query stored memories using vector similarity."""
    memories = db.load_all()
    sem = db.load_all_semantic()
    proc = db.load_all_procedural()
    if model is not None:
        set_model_name(model)
    retriever = Retriever(memories, semantic=sem, procedural=proc)
    results = retriever.query(text, top_k=top_k)
    for mem in results:
        logger.info(f"{mem.timestamp.isoformat()} - {mem.content}")


def dream_summary(db: Database) -> None:
    """Generate a dream summary from all memories."""
    memories = db.load_all()
    engine = DreamEngine()
    summary = engine.summarize(memories, log=False)
    logger.info(summary)


def reset_database(db: Database, *, assume_yes: bool = False) -> None:
    """Delete all memories after user confirmation."""
    if not assume_yes:
        ans = input("Delete all memories? [y/N] ").strip().lower()
        if ans not in {"y", "yes"}:
            logger.warning("Aborted.")
            return
    db.clear()
    logger.info("Database cleared.")


def edit_memory(
    db: Database,
    timestamp: str,
    text: str,
    *,
    assume_yes: bool = False,
) -> None:
    """Edit an existing memory identified by ``timestamp``."""
    ts = datetime.fromisoformat(timestamp)
    entries = [m for m in db.load_all() if m.timestamp.isoformat() == timestamp]
    if not entries:
        logger.warning("Entry not found.")
        return
    if not assume_yes:
        ans = input(f"Edit memory at {timestamp}? [y/N] ").strip().lower()
        if ans not in {"y", "yes"}:
            logger.warning("Aborted.")
            return
    emotions = analyze_emotions(text)
    tags = tag_text(text)
    labels = [e[0] for e in emotions]
    scores = {label: score for label, score in emotions}
    updated = MemoryEntry(
        content=text,
        embedding=encode_text(text),
        timestamp=ts,
        emotions=labels,
        emotion_scores=scores,
        metadata={"tags": tags},
    )
    db.update(ts, updated)
    logger.info("Memory updated.")


def delete_memory(db: Database, timestamp: str, *, assume_yes: bool = False) -> None:
    """Remove a memory entry by ``timestamp``."""
    ts = datetime.fromisoformat(timestamp)
    entries = [m for m in db.load_all() if m.timestamp.isoformat() == timestamp]
    if not entries:
        logger.warning("Entry not found.")
        return
    if not assume_yes:
        ans = input(f"Delete memory at {timestamp}? [y/N] ").strip().lower()
        if ans not in {"y", "yes"}:
            logger.warning("Aborted.")
            return
    db.delete(ts)
    logger.info("Memory deleted.")


def list_sem(db: Database) -> None:
    """List all semantic memories."""
    memories = db.load_all_semantic()
    for i, mem in enumerate(memories, 1):
        ts = mem.timestamp.isoformat()
        logger.info(f"{i}. {ts} - {mem.content}")


def add_sem(db: Database, text: str) -> None:
    """Add a semantic memory entry."""
    entry = MemoryEntry(content=text, embedding=encode_text(text), emotions=[], metadata={})
    db.save_semantic(entry)
    logger.info("Semantic memory added.")


def edit_sem(db: Database, timestamp: str, text: str, *, assume_yes: bool = False) -> None:
    """Edit a semantic memory entry by timestamp."""
    ts = datetime.fromisoformat(timestamp)
    entries = [m for m in db.load_all_semantic() if m.timestamp.isoformat() == timestamp]
    if not entries:
        logger.warning("Entry not found.")
        return
    if not assume_yes:
        ans = input(f"Edit semantic memory at {timestamp}? [y/N] ").strip().lower()
        if ans not in {"y", "yes"}:
            logger.warning("Aborted.")
            return
    existing = entries[0]
    updated = MemoryEntry(
        content=text,
        embedding=encode_text(text),
        timestamp=ts,
        emotions=existing.emotions,
        emotion_scores=existing.emotion_scores,
        metadata=existing.metadata,
    )
    db.update_semantic(ts, updated)
    logger.info("Semantic memory updated.")


def delete_sem(db: Database, timestamp: str, *, assume_yes: bool = False) -> None:
    """Delete a semantic memory entry by timestamp."""
    ts = datetime.fromisoformat(timestamp)
    entries = [m for m in db.load_all_semantic() if m.timestamp.isoformat() == timestamp]
    if not entries:
        logger.warning("Entry not found.")
        return
    if not assume_yes:
        ans = input(f"Delete semantic memory at {timestamp}? [y/N] ").strip().lower()
        if ans not in {"y", "yes"}:
            logger.warning("Aborted.")
            return
    db.delete_semantic(ts)
    logger.info("Semantic memory deleted.")


def list_proc(db: Database) -> None:
    """List all procedural memories."""
    memories = db.load_all_procedural()
    for i, mem in enumerate(memories, 1):
        ts = mem.timestamp.isoformat()
        logger.info(f"{i}. {ts} - {mem.content}")


def add_proc(db: Database, text: str) -> None:
    """Add a procedural memory entry."""
    entry = MemoryEntry(content=text, embedding=encode_text(text), emotions=[], metadata={})
    db.save_procedural(entry)
    logger.info("Procedural memory added.")


def edit_proc(db: Database, timestamp: str, text: str, *, assume_yes: bool = False) -> None:
    """Edit a procedural memory entry by timestamp."""
    ts = datetime.fromisoformat(timestamp)
    entries = [m for m in db.load_all_procedural() if m.timestamp.isoformat() == timestamp]
    if not entries:
        logger.warning("Entry not found.")
        return
    if not assume_yes:
        ans = input(f"Edit procedural memory at {timestamp}? [y/N] ").strip().lower()
        if ans not in {"y", "yes"}:
            logger.warning("Aborted.")
            return
    existing = entries[0]
    updated = MemoryEntry(
        content=text,
        embedding=encode_text(text),
        timestamp=ts,
        emotions=existing.emotions,
        emotion_scores=existing.emotion_scores,
        metadata=existing.metadata,
    )
    db.update_procedural(ts, updated)
    logger.info("Procedural memory updated.")


def delete_proc(db: Database, timestamp: str, *, assume_yes: bool = False) -> None:
    """Delete a procedural memory entry by timestamp."""
    ts = datetime.fromisoformat(timestamp)
    entries = [m for m in db.load_all_procedural() if m.timestamp.isoformat() == timestamp]
    if not entries:
        logger.warning("Entry not found.")
        return
    if not assume_yes:
        ans = input(f"Delete procedural memory at {timestamp}? [y/N] ").strip().lower()
        if ans not in {"y", "yes"}:
            logger.warning("Aborted.")
            return
    db.delete_procedural(ts)
    logger.info("Procedural memory deleted.")


def start_dream(manager: MemoryManager, *, interval: float = 60.0) -> None:
    """Begin periodic dreaming using ``MemoryManager`` and block until interrupted."""
    scheduler = manager.start_dreaming(interval=interval)
    logger.info("Dreaming started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        logger.info("Dreaming stopped.")


def stop_dream(manager: MemoryManager) -> None:
    """Stop any active dreaming scheduler."""
    manager.stop_dreaming()
    logger.info("Dreaming stopped.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Memory management CLI for stored agent memories"
    )
    parser.add_argument(
        "--db",
        default="memory.db",
        help="Path to SQLite database",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List stored memories")

    add_p = sub.add_parser("add", help="Add a new memory")
    add_p.add_argument("text", help="Memory text")
    add_p.add_argument(
        "--model",
        default=None,
        help="SentenceTransformer model for embedding",
    )

    query_p = sub.add_parser("query", help="Query memories")
    query_p.add_argument("text", help="Query text")
    query_p.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results",
    )
    query_p.add_argument(
        "--model",
        default=None,
        help="SentenceTransformer model for query",
    )

    sub.add_parser("reset", help="Delete all memories")

    sub.add_parser("dream", help="Generate dream summary")
    start_p = sub.add_parser(
        "start-dream",
        help="Start periodic dreaming (background summarization)",
    )
    start_p.add_argument(
        "--interval",
        type=float,
        default=60.0,
        help="Seconds between dream summaries",
    )
    sub.add_parser("stop-dream", help="Stop periodic dreaming")

    edit_p = sub.add_parser("edit", help="Edit a memory entry")
    edit_p.add_argument("timestamp", help="Timestamp of memory to edit")
    edit_p.add_argument("text", help="New memory text")

    del_p = sub.add_parser("delete", help="Delete a memory entry")
    del_p.add_argument("timestamp", help="Timestamp of memory to delete")

    sub.add_parser("list-sem", help="List semantic memories")
    add_sem_p = sub.add_parser("add-sem", help="Add a semantic memory")
    add_sem_p.add_argument("text", help="Semantic memory text")
    edit_sem_p = sub.add_parser(
        "edit-sem", help="Edit a semantic memory entry"
    )
    edit_sem_p.add_argument("timestamp", help="Timestamp of semantic memory to edit")
    edit_sem_p.add_argument("text", help="New memory text")
    del_sem_p = sub.add_parser(
        "delete-sem", help="Delete a semantic memory entry"
    )
    del_sem_p.add_argument("timestamp", help="Timestamp of semantic memory to delete")

    sub.add_parser("list-proc", help="List procedural memories")
    add_proc_p = sub.add_parser("add-proc", help="Add a procedural memory")
    add_proc_p.add_argument("text", help="Procedural memory text")
    edit_proc_p = sub.add_parser(
        "edit-proc", help="Edit a procedural memory entry"
    )
    edit_proc_p.add_argument("timestamp", help="Timestamp of procedural memory to edit")
    edit_proc_p.add_argument("text", help="New memory text")
    del_proc_p = sub.add_parser(
        "delete-proc", help="Delete a procedural memory entry"
    )
    del_proc_p.add_argument(
        "timestamp", help="Timestamp of procedural memory to delete"
    )

    args = parser.parse_args(argv)

    db = Database(args.db)

    if args.cmd == "list":
        list_memories(db)
    elif args.cmd == "add":
        add_memory(db, args.text, model=args.model)
    elif args.cmd == "query":
        query_memories(db, args.text, top_k=args.top_k, model=args.model)
    elif args.cmd == "dream":
        dream_summary(db)
    elif args.cmd == "start-dream":
        manager = MemoryManager(args.db)
        start_dream(manager, interval=args.interval)
    elif args.cmd == "stop-dream":
        manager = MemoryManager(args.db)
        stop_dream(manager)
    elif args.cmd == "reset":
        reset_database(db)
    elif args.cmd == "edit":
        edit_memory(db, args.timestamp, args.text)
    elif args.cmd == "delete":
        delete_memory(db, args.timestamp)
    elif args.cmd == "list-sem":
        list_sem(db)
    elif args.cmd == "add-sem":
        add_sem(db, args.text)
    elif args.cmd == "edit-sem":
        edit_sem(db, args.timestamp, args.text)
    elif args.cmd == "delete-sem":
        delete_sem(db, args.timestamp)
    elif args.cmd == "list-proc":
        list_proc(db)
    elif args.cmd == "add-proc":
        add_proc(db, args.text)
    elif args.cmd == "edit-proc":
        edit_proc(db, args.timestamp, args.text)
    elif args.cmd == "delete-proc":
        delete_proc(db, args.timestamp)


if __name__ == "__main__":
    main()
