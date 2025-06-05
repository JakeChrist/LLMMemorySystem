"""Minimal emotion analyzer using a transformer model."""

from __future__ import annotations

from typing import List, Tuple

_classifier = None


def _load_classifier():
    """Load emotion classifier lazily."""
    global _classifier
    if _classifier is None:  # pragma: no cover - heavy dependency may be missing
        try:
            from transformers import pipeline

            _classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True,
            )
        except Exception:  # pragma: no cover - optional dependency
            _classifier = None
    return _classifier


_LABEL_MAP = {
    "joy": "happy",
    "happiness": "happy",
    "optimism": "happy",
    "amusement": "happy",
    "excitement": "happy",
    "sadness": "sad",
    "grief": "sad",
    "disappointment": "sad",
    "anger": "angry",
    "annoyance": "angry",
    "disgust": "disgust",
    "fear": "fear",
    "nervousness": "fear",
    "love": "love",
    "caring": "love",
    "surprise": "surprise",
    "embarrassment": "embarrassed",
    "approval": "pleasure",
    "admiration": "pleasure",
    "desire": "pleasure",
    "neutral": "neutral",
}


def _canonical(label: str) -> str:
    return _LABEL_MAP.get(label.lower(), label.lower())


def analyze_emotions(text: str) -> List[Tuple[str, float]]:
    """Return a list of detected emotion ``(label, score)`` pairs."""
    clf = _load_classifier()
    if clf is None:
        return [("neutral", 0.0)]

    try:
        result = clf(text)
    except Exception:  # pragma: no cover - runtime issues
        return [("neutral", 0.0)]

    if not result:
        return [("neutral", 0.0)]

    preds = result[0] if isinstance(result[0], list) else result
    pairs = []
    for item in preds:
        label = _canonical(str(item.get("label", "")))
        score = float(item.get("score", 0.0))
        pairs.append((label, score))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs
