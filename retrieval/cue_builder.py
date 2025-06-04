"""Construct retrieval cues from user text and agent state."""

from __future__ import annotations

from typing import Dict, Iterable


def build_cue(text: str, *, tags: Iterable[str] | None = None, state: Dict[str, str] | None = None) -> str:
    parts = [text]
    if state:
        parts.extend(f"{k}:{v}" for k, v in state.items())
    if tags:
        parts.extend(tags)
    return " ".join(parts)
