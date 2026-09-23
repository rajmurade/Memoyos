"""Related memories / memory graph service for MemoryOS.

Independent of Streamlit. Uses the existing embedding + ChromaDB retrieval to
find semantically related organizational memories for a chosen memory. No graph
database is introduced; relationships are derived from embedding similarity and
shared structured fields (tags, equipment codes, symptom keywords).

The relationship labels are only claims that the data actually supports:
shared equipment codes, shared symptom keywords, or shared tags.
"""

import os
import re

from src.memory_service import retrieve_memories

DEFAULT_RELATED_MEMORY_DISTANCE_THRESHOLD = 0.80

# Lower = more permissive. env-friendly.
_EQUIPMENT_CODE_RE = re.compile(r"\b[A-Za-z]{1,3}-\d{2,}\b")

_SYMPTOM_KEYWORDS = (
    "overheating",
    "overheat",
    "vibration",
    "vibrat",
    "noise",
    "bearing",
    "pressure",
    "leak",
    "calibration",
    "calibrat",
    "drift",
    "contamination",
    "contaminat",
    "coolant",
    "alarm",
    "sensor",
    "wear",
    "seized",
    "failure",
    "tolerance",
)


def get_related_memory_threshold() -> float:
    """Return the cosine-distance cutoff for related memory suggestions."""
    raw = os.getenv("RELATED_DISTANCE_THRESHOLD", "").strip()
    if raw:
        try:
            value = float(raw)
        except ValueError:
            return DEFAULT_RELATED_MEMORY_DISTANCE_THRESHOLD
        if 0.0 <= value <= 2.0:
            return value
    return DEFAULT_RELATED_MEMORY_DISTANCE_THRESHOLD


def _query_text(memory: dict) -> str:
    """Best text to use as the similarity query for a stored memory."""
    if memory.get("content"):
        return memory["content"]
    meta = memory.get("metadata") or {}
    return "\n".join(
        str(meta.get(k) or "")
        for k in ("title", "situation", "experience", "recommendation", "warnings", "tags")
    )


def _tags(meta: dict) -> set[str]:
    return {t.strip().lower() for t in str(meta.get("tags") or "").split(",") if t.strip()}


def _symptom_set(meta: dict) -> set[str]:
    hay = " ".join(
        str(meta.get(k) or "")
        for k in ("title", "situation", "experience", "warnings", "tags")
    ).lower()
    return {kw for kw in _SYMPTOM_KEYWORDS if kw in hay}


def _equipment_set(meta: dict) -> set[str]:
    hay = " ".join(
        str(meta.get(k) or "") for k in ("title", "situation", "tags")
    )
    return {match.upper() for match in _EQUIPMENT_CODE_RE.findall(hay)}


def _describe_relationship(memory_meta: dict, other_meta: dict) -> tuple[str, str]:
    """Return (relationship_label, reason) supported by the actual data."""
    shared_equipment = _equipment_set(memory_meta) & _equipment_set(other_meta)
    if shared_equipment:
        items = ", ".join(sorted(shared_equipment))
        return "Similar equipment", f"Both experiences reference equipment code(s): {items}."

    shared_symptoms = _symptom_set(memory_meta) & _symptom_set(other_meta)
    if shared_symptoms:
        items = ", ".join(sorted(shared_symptoms))
        return "Similar failure symptom", f"Both experiences involve: {items}."

    shared_tags = _tags(memory_meta) & _tags(other_meta)
    if shared_tags:
        items = ", ".join(sorted(shared_tags))
        return "Related maintenance topic", f"Shared topic tags: {items}."

    return "Related experience", "Semantically close within the stored organizational memory."


def find_related_memories(memory: dict, top_k: int = 8) -> dict:
    """Return the memories most related to ``memory`` (excluding itself).

    Returns a dict with keys: ``memory_id``, ``related_memories`` (each entry has
    ``id``, ``title``, ``similarity``, ``distance``, ``relationship``, ``reason``)
    and ``note`` when nothing meaningful was found.
    """
    memory_id = str(memory.get("id") or "").strip()
    meta = memory.get("metadata") or {}
    title = str(memory.get("title") or meta.get("title") or "(Untitled)")
    query = _query_text(memory)
    if not query.strip():
        return {
            "memory_id": memory_id,
            "memory_title": title,
            "related_memories": [],
            "note": "This memory doesn't have enough text to compare.",
        }

    threshold = get_related_memory_threshold()
    results = retrieve_memories(query, top_k=top_k)

    related = []
    for candidate in results:
        candidate_id = str(candidate.get("id") or "")
        if memory_id and candidate_id == memory_id:
            continue
        distance = candidate.get("distance")
        if distance is None or not isinstance(distance, (int, float)) or distance > threshold:
            continue
        candidate_meta = candidate.get("metadata") or {}
        relationship, reason = _describe_relationship(meta, candidate_meta)
        related.append(
            {
                "id": candidate_id,
                "title": str(candidate.get("title") or candidate_meta.get("title") or "(Untitled)"),
                "similarity": round(max(0.0, 1.0 - float(distance)), 4),
                "distance": round(float(distance), 4),
                "relationship": relationship,
                "reason": reason,
                "metadata": candidate_meta,
            }
        )

    related.sort(key=lambda r: r["distance"])
    note = ""
    if not related:
        note = (
            f"No closely related organizational memories found for this one "
            f"(cosine-distance threshold {threshold:.2f})."
        )
    return {
        "memory_id": memory_id,
        "memory_title": title,
        "related_memories": related,
        "threshold": threshold,
        "note": note,
    }