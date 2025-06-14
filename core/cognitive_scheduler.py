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
        think_interval: float | None = None,
        T_delay: float = 1.0,
    ) -> None:
        """Create a scheduler for ``manager`` using ``llm_name`` for background tasks.

        Parameters
        ----------
        manager:
            ``MemoryManager`` instance controlling memory operations.
        llm_name:
            LLM backend used by the thinking and dreaming engines.
        T_think:
            Duration in seconds to remain in the reflective state.
        T_dream:
            Duration in seconds to remain asleep and dreaming.
        T_alarm:
            Maximum sleep duration before automatically waking.
        think_interval:
            Seconds between reflective thoughts while in the reflective state.
        T_delay:
            Minimum seconds to wait between consecutive state transitions.
        """

        self.manager = manager
        self.llm_name = llm_name
        self.T_think = T_think
        self.T_dream = T_dream
        self.T_alarm = T_alarm
        self.think_interval = think_interval if think_interval is not None else T_think
        self.T_delay = T_delay
        self.state = CognitiveState.ACTIVE
        self.last_input = time.monotonic()
        self.state_start = self.last_input
        self._last_transition = self.last_input
        self._think_sched: Optional[Scheduler] = None
        self._dream_sched: Optional[Scheduler] = None

    def notify_input(self) -> None:
        """Record user activity and wake the system if needed."""
        self.last_input = time.monotonic()
        self.state_start = self.last_input
        if self.state != CognitiveState.ACTIVE:
            self._stop_engines()
            self.state = CognitiveState.ACTIVE
        self._last_transition = self.last_input

    def current_state(self) -> CognitiveState:
        """Return the current cognitive state."""
        return self.state

    def run(self, interval: float = 1.0) -> Scheduler:
        """Start periodic state checks."""
        sched = Scheduler()
        sched.schedule(interval, self.check)
        return sched

    def check(self) -> None:
        """Evaluate idle time and update cognitive state.

        When waking automatically from sleep, ``last_input`` is adjusted so the
        next invocation transitions into the reflective state after ``T_think``.
        """
        now = time.monotonic()
        if now - self._last_transition < self.T_delay:
            return
        idle = now - self.last_input

        if self.state == CognitiveState.ACTIVE:
            if idle >= self.T_think:
                self.state = CognitiveState.REFLECTIVE
                self.state_start = now
                self._last_transition = now
                self._think_sched = self.manager.start_thinking(
                    think_interval=self.think_interval,
                    duration=self.T_think,
                    llm_name=self.llm_name,
                )
        elif self.state == CognitiveState.REFLECTIVE:
            if now - self.state_start >= self.T_think:
                if self._think_sched:
                    self.manager.stop_thinking()
                    self._think_sched = None
                self.state = CognitiveState.ASLEEP
                self.state_start = now
                self._last_transition = now
                self._dream_sched = self.manager.start_dreaming(
                    interval=self.T_dream,
                    duration=self.T_dream,
                    llm_name=self.llm_name,
                )
        elif self.state == CognitiveState.ASLEEP:
            elapsed = now - self.state_start
            if elapsed >= self.T_dream or elapsed >= self.T_alarm:
                if self._dream_sched:
                    self.manager.stop_dreaming()
                    self._dream_sched = None
                # Automatically queue the next reflective phase
                self.last_input = now - self.T_think
                self.state = CognitiveState.ACTIVE
                self.state_start = now
                self._last_transition = now

    def _stop_engines(self) -> None:
        if self._think_sched:
            self.manager.stop_thinking()
            self._think_sched = None
        if self._dream_sched:
            self.manager.stop_dreaming()
            self._dream_sched = None


__all__ = ["CognitiveScheduler", "CognitiveState"]
