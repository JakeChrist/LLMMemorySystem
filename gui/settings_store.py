import json
from pathlib import Path
from typing import Any, Dict

"""Persistence helpers for GUI settings."""

SETTINGS_FILE = Path.home() / ".llmemory_gui.json"


def load_settings() -> Dict[str, Any]:
    """Return saved settings or an empty dict."""
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_settings(data: Dict[str, Any]) -> None:
    """Write ``data`` to :data:`SETTINGS_FILE`. Errors are ignored."""
    try:
        with SETTINGS_FILE.open("w", encoding="utf-8") as fh:
            json.dump(data, fh)
    except Exception:
        pass
