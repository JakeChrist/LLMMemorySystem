"""Minimal logger used across the project."""

from __future__ import annotations

from datetime import datetime


class Logger:
    """Very small logger printing timestamped messages."""

    def __init__(self, name: str = "LLM") -> None:
        self.name = name

    def _log(self, level: str, message: str) -> None:
        ts = datetime.utcnow().isoformat()
        print(f"[{ts}] {self.name} {level}: {message}")

    def info(self, message: str) -> None:
        self._log("INFO", message)

    def warning(self, message: str) -> None:
        self._log("WARN", message)

    def error(self, message: str) -> None:
        self._log("ERROR", message)


__all__ = ["Logger"]
