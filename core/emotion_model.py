"""Minimal sentiment based emotion analyzer."""

from __future__ import annotations

from typing import List

_classifier = None


def _load_classifier():
    """Load sentiment classifier lazily."""
    global _classifier
    if _classifier is None:  # pragma: no cover - heavy dependency may be missing
        try:
            from transformers import pipeline

            _classifier = pipeline("sentiment-analysis")
        except Exception:  # pragma: no cover - optional dependency
            _classifier = None
    return _classifier


def analyze_emotions(text: str) -> List[str]:
    """Return a list of detected emotion labels using a classifier."""
    clf = _load_classifier()
    if clf is None:
        return ["neutral"]

    try:
        result = clf(text)
    except Exception:  # pragma: no cover - runtime issues
        return ["neutral"]

    if not result:
        return ["neutral"]

    label = str(result[0].get("label", "")).lower()
    if "neg" in label:
        return ["negative"]
    if "pos" in label:
        return ["positive"]
    return ["neutral"]
