"""Simple token encoder for tests."""

import re
from typing import List

_TOKEN_RE = re.compile(r"\w+")


def encode_text(text: str) -> List[str]:
    """Tokenize text into lowercase word tokens."""
    return _TOKEN_RE.findall(text.lower())
