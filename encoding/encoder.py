"""Simple text encoder used across the project."""

from __future__ import annotations

import re
from typing import List

_TOKEN_RE = re.compile(r"\w+")

_model = None
_model_failed = False
_model_name = "all-MiniLM-L6-v2"


def set_model_name(name: str) -> None:
    """Specify which sentence-transformers model to use."""
    global _model, _model_failed, _model_name
    if name != _model_name:
        _model_name = name
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
    _model = SentenceTransformer(_model_name)
    return _model


def encode_text(text: str, model_name: str | None = None) -> List[str] | List[float]:
    """Return an embedding for text.

    If ``sentence_transformers`` is installed, this returns a vector from a
    small pretrained model. Otherwise a simple token list is returned for use
    in tests.
    """

    if model_name is not None:
        set_model_name(model_name)

    model = _load_model()
    if model is not None:
        vec = model.encode(text)
        return [float(x) for x in vec]
    return _TOKEN_RE.findall(text.lower())
