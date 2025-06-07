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
    start_think.assert_called_once()
    assert start_think.call_args.kwargs.get("interval") == 10

    sched.check()
    assert sched.current_state() is CognitiveState.ASLEEP
    start_dream.assert_called_once()
    assert start_dream.call_args.kwargs.get("interval") == 20
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

def test_idle_period_transitions(monkeypatch):
    mm = MemoryManager(db_path=":memory:")
    times = iter([0, 6, 11, 12, 13])
    monkeypatch.setattr(time, "monotonic", lambda: next(times))
    scheduler = CognitiveScheduler(mm, T_think=5, T_dream=10, T_alarm=60)

    start_think = MagicMock()
    start_dream = MagicMock()
    stop_think = MagicMock()
    stop_dream = MagicMock()
    monkeypatch.setattr(mm, "start_thinking", start_think)
    monkeypatch.setattr(mm, "start_dreaming", start_dream)
    monkeypatch.setattr(mm, "stop_thinking", stop_think)
    monkeypatch.setattr(mm, "stop_dreaming", stop_dream)

    scheduler.check()
    assert scheduler.current_state() is CognitiveState.REFLECTIVE
    start_think.assert_called_once()
    assert start_think.call_args.kwargs.get("interval") == 5

    scheduler.check()
    assert scheduler.current_state() is CognitiveState.ASLEEP
    start_dream.assert_called_once()
    assert start_dream.call_args.kwargs.get("interval") == 10
    stop_think.assert_called_once()

    scheduler.notify_input()
    assert scheduler.current_state() is CognitiveState.ACTIVE
    stop_dream.assert_called_once()

    scheduler.check()
    assert scheduler.current_state() is CognitiveState.ACTIVE
