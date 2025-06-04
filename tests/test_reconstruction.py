import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_entry import MemoryEntry
from reconstruction.reconstructor import Reconstructor


def test_build_context_orders_by_timestamp():
    now = datetime(2023, 1, 1, 12, 0, 0)
    older = MemoryEntry(content="old", embedding=[], timestamp=now)
    newer = MemoryEntry(content="new", embedding=[], timestamp=now + timedelta(minutes=1))
    reconstructor = Reconstructor(max_context_length=100)
    context = reconstructor.build_context([newer, older])
    assert context.splitlines() == ["old", "new"]


def test_build_context_respects_max_length():
    reconstructor = Reconstructor(max_context_length=15)
    entries = [
        MemoryEntry(content="1234567890", embedding=[], timestamp=datetime.utcnow()),
        MemoryEntry(content="abcdefghij", embedding=[], timestamp=datetime.utcnow() + timedelta(seconds=1)),
    ]
    context = reconstructor.build_context(entries)
    assert len(context) <= 15
    assert context.endswith("abcdefghij")


def test_build_context_includes_mood_and_metadata():
    entry = MemoryEntry(content="hello", embedding=[], timestamp=datetime.utcnow())
    context = Reconstructor(max_context_length=100).build_context(
        [entry], mood="happy", metadata={"loc": "home"}
    )
    lines = context.splitlines()
    assert lines[0] == "Mood: happy; loc: home"
    assert lines[1] == "hello"

