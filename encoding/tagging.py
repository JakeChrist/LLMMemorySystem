"""Keyword-based tagging pipeline."""

from __future__ import annotations

from typing import List

from encoding.encoder import encode_text

# Simple mapping of categories to keyword sets
_TAG_VOCAB = {
    "animal": {"cat", "dog", "bird", "fish"},
    "greeting": {"hello", "hi", "hey"},
    "food": {"pizza", "apple", "bread", "cake"},
}


def tag_text(text: str) -> List[str]:
    """Return list of tags detected in text based on keyword matches."""
    tokens = set(encode_text(text))
    tags = [name for name, words in _TAG_VOCAB.items() if tokens & words]
    if not tags:
        tags.append("misc")
    return tags
