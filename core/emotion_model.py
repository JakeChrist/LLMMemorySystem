"""Very small rule-based emotion analyzer."""

from __future__ import annotations

from typing import List

POSITIVE = {"happy", "joy", "love", "great", "awesome", "good"}
NEGATIVE = {"sad", "angry", "bad", "terrible", "awful"}


def analyze_emotions(text: str) -> List[str]:
    """Return a list of detected emotion labels."""
    words = set(text.lower().split())
    emotions: List[str] = []
    if words & POSITIVE:
        emotions.append("positive")
    if words & NEGATIVE:
        emotions.append("negative")
    if not emotions:
        emotions.append("neutral")
    return emotions
