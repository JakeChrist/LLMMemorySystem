"""Simple text encoder used across the project."""

from __future__ import annotations

import re
from typing import List, Sequence

_TOKEN_RE = re.compile(r"\w+")

_model = None
_model_failed = False


def _load_model():
    """Lazily load a sentence-transformers model if available."""
    global _model, _model_failed
    if _model is not None or _model_failed:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:  # pragma: no cover - optional dependency may not exist
        _model_failed = True
        return None
    _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def encode_text(text: str) -> List[str] | List[float]:
    """Return an embedding for text.

    If ``sentence_transformers`` is installed, this returns a vector from a
    small pretrained model. Otherwise a simple token list is returned for use
    in tests.
    """

    model = _load_model()
    if model is not None:
        vec: Sequence[float] = model.encode(text)
        return list(vec)
    return _TOKEN_RE.findall(text.lower())
