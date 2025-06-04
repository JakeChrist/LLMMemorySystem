"""Reconstruct working memory context from retrieved entries."""

from __future__ import annotations

from typing import Iterable, Dict, Any
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency may not exist
    yaml = None

from core.memory_entry import MemoryEntry
from ms_utils import format_context


def _load_config() -> Dict[str, Any]:
    """Load YAML config with a minimal parser fallback."""
    path = Path(__file__).resolve().parents[1] / "config/default_config.yaml"
    if yaml is not None:  # pragma: no cover - dependency may not be present
        with path.open() as fh:
            return yaml.safe_load(fh) or {}

    config: Dict[str, Any] = {}
    current = None
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith(":"):
                current = line[:-1]
                config[current] = {}
            else:
                key, val = [p.strip() for p in line.split(":", 1)]
                val = int(val) if val.isdigit() else val
                if current is None:
                    config[key] = val
                else:
                    config[current][key] = val
    return config


class Reconstructor:
    """Combine memory fragments into a context string."""

    def __init__(self, max_context_length: int | None = None) -> None:
        if max_context_length is None:
            cfg = _load_config()
            max_context_length = cfg.get("reconstruction", {}).get(
                "max_context_length", 1000
            )
        self.max_context_length = max_context_length

    def build_context(
        self,
        memories: Iterable[MemoryEntry],
        *,
        mood: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        """Return single prompt string from memory fragments and metadata."""

        ordered = sorted(memories, key=lambda m: m.timestamp)

        lines = []
        if mood or metadata:
            meta_parts = []
            if mood:
                meta_parts.append(f"Mood: {mood}")
            if metadata:
                meta_parts.extend(f"{k}: {v}" for k, v in metadata.items())
            lines.append("; ".join(meta_parts))

        lines.extend(m.content for m in ordered)

        context = format_context(lines)
        if len(context) > self.max_context_length:
            context = context[-self.max_context_length :]
        return context
