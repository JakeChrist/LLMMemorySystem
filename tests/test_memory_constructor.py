import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from addons import memory_constructor
from core.memory_manager import MemoryManager


def test_ingest_transcript(monkeypatch):
    manager = MemoryManager(db_path=':memory:')

    def fake_analyze(text):
        return [('neutral', 1.0)]

    monkeypatch.setattr(memory_constructor, 'analyze_emotions', fake_analyze)

    text = 'Alice: Hello.\nBob: Hi there.'
    entries = memory_constructor.ingest_transcript(text, manager)

    assert len(entries) == 2
    assert entries[0].metadata['source'] == 'transcript'
    assert entries[0].metadata['speaker'] == 'Alice'
    assert entries[1].metadata['speaker'] == 'Bob'
    assert entries[0] in manager.all()


def test_ingest_biography(monkeypatch):
    manager = MemoryManager(db_path=':memory:')

    def fake_analyze(text):
        return [('neutral', 1.0)]

    monkeypatch.setattr(memory_constructor, 'analyze_emotions', fake_analyze)

    bio = (
        'John was born in 1990. '
        'He learned to swim at age 5. '
        'He works as a baker.'
    )
    sem, proc = memory_constructor.ingest_biography(bio, manager)

    assert len(sem) == 2
    assert len(proc) == 1
    for entry in sem + proc:
        assert entry.metadata['source'] == 'biography'
    assert proc[0] in manager.procedural.all()
