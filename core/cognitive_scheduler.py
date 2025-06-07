"""Idle-based cognitive state manager."""

from __future__ import annotations

import time
from enum import Enum
from ms_utils.scheduler import Scheduler
from typing import Optional

from core.memory_manager import MemoryManager


class CognitiveState(Enum):
    """Possible cognitive states."""

    ACTIVE = "Active"
    REFLECTIVE = "Reflective"
    ASLEEP = "Asleep"


class CognitiveScheduler:
    """Transition between thinking and dreaming based on idle time."""

    def __init__(
        self,
        manager: MemoryManager,
        *,
        llm_name: str = "local",
        T_think: float = 60.0,
        T_dream: float = 300.0,
        T_alarm: float = 1200.0,
    ) -> None:
        """Create a scheduler for ``manager`` using ``llm_name`` for background tasks.

        Parameters
        ----------
        manager:
            ``MemoryManager`` instance controlling memory operations.
        llm_name:
            LLM backend used by the thinking and dreaming engines.
        T_think:
            Idle time in seconds before entering the reflective state.
        T_dream:
            Idle time in seconds before starting the dreaming engine.
        T_alarm:
            Maximum sleep duration before automatically waking.
        """

        self.manager = manager
        self.llm_name = llm_name
        self.T_think = T_think
        self.T_dream = T_dream
        self.T_alarm = T_alarm
        self.state = CognitiveState.ACTIVE
        self.last_input = time.monotonic()
        self.state_start = self.last_input
        self._think_sched: Optional[Scheduler] = None
        self._dream_sched: Optional[Scheduler] = None

    def notify_input(self) -> None:
        """Record user activity and wake the system if needed."""
        self.last_input = time.monotonic()
        self.state_start = self.last_input
        if self.state != CognitiveState.ACTIVE:
            self._stop_engines()
            self.state = CognitiveState.ACTIVE

    def current_state(self) -> CognitiveState:
        """Return the current cognitive state."""
        return self.state

    def run(self, interval: float = 1.0) -> Scheduler:
        """Start periodic state checks."""
        sched = Scheduler()
        sched.schedule(interval, self.check)
        return sched

    def check(self) -> None:
        """Evaluate idle time and update cognitive state."""
        now = time.monotonic()
        idle = now - self.last_input

        if self.state == CognitiveState.ACTIVE:
            if idle >= self.T_dream:
                self.state = CognitiveState.ASLEEP
                self.state_start = now
                self._dream_sched = self.manager.start_dreaming(
                    interval=self.T_dream,
                    llm_name=self.llm_name,
                )
            elif idle >= self.T_think:
                self.state = CognitiveState.REFLECTIVE
                self.state_start = now
                self._think_sched = self.manager.start_thinking(
                    interval=self.T_think,
                    llm_name=self.llm_name,
                )
        elif self.state == CognitiveState.REFLECTIVE:
            if idle >= self.T_dream:
                if self._think_sched:
                    self.manager.stop_thinking()
                    self._think_sched = None
                self.state = CognitiveState.ASLEEP
                self.state_start = now
                self._dream_sched = self.manager.start_dreaming(
                    interval=self.T_dream,
                    llm_name=self.llm_name,
                )
        elif self.state == CognitiveState.ASLEEP:
            if now - self.state_start >= self.T_alarm:
                if self._dream_sched:
                    self.manager.stop_dreaming()
                    self._dream_sched = None
                self.last_input = now
                self.state = CognitiveState.ACTIVE
                self.state_start = now

    def _stop_engines(self) -> None:
        if self._think_sched:
            self.manager.stop_thinking()
            self._think_sched = None
        if self._dream_sched:
            self.manager.stop_dreaming()
            self._dream_sched = None


__all__ = ["CognitiveScheduler", "CognitiveState"]
