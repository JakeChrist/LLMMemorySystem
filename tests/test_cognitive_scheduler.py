import sys
from pathlib import Path
from unittest.mock import MagicMock
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory_manager import MemoryManager
from core.cognitive_scheduler import CognitiveScheduler, CognitiveState


def test_state_transitions(monkeypatch):
    mm = MemoryManager(db_path=":memory:")
    times = iter([0, 11, 21, 25, 26])
    monkeypatch.setattr(time, "monotonic", lambda: next(times))
    sched = CognitiveScheduler(mm, T_think=10, T_dream=20, T_alarm=60)

    start_think = MagicMock()
    start_dream = MagicMock()
    stop_think = MagicMock()
    stop_dream = MagicMock()
    monkeypatch.setattr(mm, "start_thinking", start_think)
    monkeypatch.setattr(mm, "start_dreaming", start_dream)
    monkeypatch.setattr(mm, "stop_thinking", stop_think)
    monkeypatch.setattr(mm, "stop_dreaming", stop_dream)

    sched.check()
    assert sched.current_state() is CognitiveState.REFLECTIVE
    assert start_think.called

    sched.check()
    assert sched.current_state() is CognitiveState.ASLEEP
    assert start_dream.called
    assert stop_think.called

    sched.notify_input()
    assert stop_dream.called
    assert sched.current_state() is CognitiveState.ACTIVE

    sched.check()
    assert sched.current_state() is CognitiveState.ACTIVE


def test_alarm_wakes(monkeypatch):
    mm = MemoryManager(db_path=":memory:")
    times = iter([0, 5, 11, 12])
    monkeypatch.setattr(time, "monotonic", lambda: next(times))
    sched = CognitiveScheduler(mm, T_think=2, T_dream=4, T_alarm=6)

    monkeypatch.setattr(mm, "start_dreaming", MagicMock())
    stop_dream = MagicMock()
    monkeypatch.setattr(mm, "stop_dreaming", stop_dream)
    monkeypatch.setattr(mm, "start_thinking", MagicMock())
    monkeypatch.setattr(mm, "stop_thinking", MagicMock())

    sched.check()
    assert sched.current_state() is CognitiveState.ASLEEP

    sched.check()
    assert sched.current_state() is CognitiveState.ACTIVE
    assert stop_dream.called

    sched.check()
    assert sched.current_state() is CognitiveState.ACTIVE
