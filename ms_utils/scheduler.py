"""Simple background scheduler for periodic tasks."""

from __future__ import annotations

import threading
import time
from typing import Callable, List


class Scheduler:
    """Run functions at a fixed interval in background threads."""

    def __init__(self) -> None:
        self._threads: List[threading.Thread] = []
        self._stop = threading.Event()

    def schedule(self, interval: float, func: Callable, *args, **kwargs) -> None:
        """Start executing ``func`` every ``interval`` seconds."""

        def loop() -> None:
            while not self._stop.is_set():
                time.sleep(interval)
                func(*args, **kwargs)

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        self._threads.append(t)

    def stop(self) -> None:
        """Stop all scheduled tasks."""
        self._stop.set()
        for t in list(self._threads):
            t.join(timeout=0)


__all__ = ["Scheduler"]
