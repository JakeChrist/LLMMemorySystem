"""Utilities for constructing memories from raw text."""

from __future__ import annotations

from typing import List, Tuple
import re

from core.emotion_model import analyze_emotions
from core.memory_manager import MemoryManager
from core.memory_entry import MemoryEntry
from dreaming.dream_engine import DreamEngine


_PROCEDURE_PAT = re.compile(
    r"\b(how to|learn(?:ed|s|ing)? to|steps? to|procedure|method|practice|skill)\b",
    re.IGNORECASE,
)

# Match sentences describing personal events or dates
_EVENT_PAT = re.compile(
    r"\b(\d{4}|at age \d+|\d+ years? old|born|graduat|married|divorc|died|moved|met|visited|travel|hired|fired)\b",
    re.IGNORECASE,
)


def ingest_transcript(
    text: str, manager: MemoryManager, *, summarize: bool = False
) -> List[MemoryEntry]:
    """Store dialogue transcript lines as episodic memories.

    Each non-empty line is treated as a dialogue turn. If a ``speaker:`` prefix
    is present, it will be recorded in the memory metadata.

    Parameters
    ----------
    text:
        Multiline transcript text to process.
    manager:
        :class:`MemoryManager` used for storing entries.
    summarize:
        When ``True``, generate a semantic summary using
        :class:`~dreaming.dream_engine.DreamEngine` after ingesting the lines.

    Returns
    -------
    list[MemoryEntry]
        List of the created episodic entries.
    """

    entries: List[MemoryEntry] = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines:
        speaker = None
        content = line
        if ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                speaker, content = parts[0].strip(), parts[1].strip()
        emotions = analyze_emotions(content)
        labels = [e[0] for e in emotions]
        scores = {lbl: score for lbl, score in emotions}
        metadata = {"source": "transcript"}
        if speaker:
            metadata["speaker"] = speaker
        entry = manager.add(
            content,
            emotions=labels,
            emotion_scores=scores,
            metadata=metadata,
        )
        entries.append(entry)

    if summarize and entries:
        engine = DreamEngine()
        engine.summarize(entries, semantic=manager.semantic, manager=manager)

    return entries


def ingest_biography(
    text: str, manager: MemoryManager
) -> Tuple[List[MemoryEntry], List[MemoryEntry], List[MemoryEntry]]:
    """Parse biography text into semantic, episodic and procedural memories.

    Sentences describing skills or procedures are stored in procedural memory,
    sentences containing event-related cues are stored in episodic memory,
    and all remaining sentences become semantic memories.

    Parameters
    ----------
    text:
        Biography text to ingest.
    manager:
        :class:`MemoryManager` that receives the new entries.

    Returns
    -------
    tuple[list[MemoryEntry], list[MemoryEntry], list[MemoryEntry]]
        ``(semantic_entries, episodic_entries, procedural_entries)`` created from the biography.
    """

    semantic_entries: List[MemoryEntry] = []
    episodic_entries: List[MemoryEntry] = []
    procedural_entries: List[MemoryEntry] = []
    sentences = re.split(r"[.!?]+\s*", text)
    for sent in sentences:
        sentence = sent.strip()
        if not sentence:
            continue
        emotions = analyze_emotions(sentence)
        labels = [e[0] for e in emotions]
        scores = {lbl: score for lbl, score in emotions}
        metadata = {"source": "biography"}
        if _PROCEDURE_PAT.search(sentence):
            entry = manager.add_procedural(
                sentence,
                emotions=labels,
                emotion_scores=scores,
                metadata=metadata,
            )
            procedural_entries.append(entry)
        elif _EVENT_PAT.search(sentence):
            entry = manager.add(
                sentence,
                emotions=labels,
                emotion_scores=scores,
                metadata=metadata,
            )
            episodic_entries.append(entry)
        else:
            entry = manager.add_semantic(
                sentence,
                emotions=labels,
                emotion_scores=scores,
                metadata=metadata,
            )
            semantic_entries.append(entry)

    return semantic_entries, episodic_entries, procedural_entries
