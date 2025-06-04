import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ms_utils import format_context


def test_format_context_joins_with_newlines():
    assert format_context(["a", "b"]) == "a\nb"
