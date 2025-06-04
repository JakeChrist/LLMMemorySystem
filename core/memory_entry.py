from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict


@dataclass
class MemoryEntry:
    """Single piece of stored memory."""

    content: str
    embedding: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    emotions: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
