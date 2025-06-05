from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class MemoryEntry:
    """Single piece of stored memory."""

    content: str
    embedding: List[str] | List[float]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    emotions: List[str] = field(default_factory=list)
    emotion_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
