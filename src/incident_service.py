"""Incident Mode service for MemoryOS.

Independent of Streamlit. Turns an urgent operational problem description into
structured, grounded decision support based on stored organizational memories.

Guarantees:
- Stored experience, AI-generated synthesis, general reasoning, and warnings are
  kept distinguishable.
- ``relevant_previous_incidents`` and ``relevant_experts`` are always derived
  deterministically from real stored memories (never invented).
- Warning text preserved from source memories, merged with any LLM additions.
- Never claims that any real-world action was performed.
- Insufficient evidence is reported explicitly and gracefully.
"""

import os
import re

from src.answer_service import get_memory_distance_threshold
from src.llm import generate_answer, is_available
from src.memory_service import retrieve_memories

COVERAGE_LEVELS = ("Strong evidence", "Partial evidence", "Insufficient evidence")
# Top-memory distance at/below which coverage can be "Strong evidence".
DEFAULT_STRONG_EVIDENCE_MAX_DISTANCE = 0.55

INCIDENT_DISCLAIMER = (
    "Decision support only. MemoryOS does not operate equipment, stop machines, "
    "contact emergency services, or perform any real-world action. Always follow "
    "site safety procedures and the judgment of qualified personnel."
)

INCIDENT_SYSTEM_PROMPT = """\
You are MemoryOS Incident Support, a decision-support assistant. You do not
control machinery, contact emergency services, or perform any real-world action.

Grounding rules:
1. Base organization-specific statements only on the retrieved organizational
   memories provided below. Never invent procedures, equipment history, or
   previous incidents.
2. Preserve warnings from the stored memories.
3. Clearly distinguish stored organizational experience from general reasoning;
   mark general reasoning with "(general)".
4. Never claim an action was performed by anyone. Frame suggestions as
   "they should consider ...".
5. Do not fabricate confidence numbers.
6. If the memories are insufficient, say so clearly.
"""


def _summarize_source(memory: dict) -> dict:
    """Shape a retrieved memory for return to callers / the UI sources list."""
    metadata = memory.get("metadata") or {}
    return {
        "id": memory.get("id", ""),
        "title": memory.get("title", "") or metadata.get("title", ""),
        "distance": memory.get("distance"),
        "metadata": metadata,
    }


def _coverage_for(relevant: list[dict]) -> str:
    if not relevant:
        return "Insufficient evidence"
    top = float(relevant[0]["distance"])
    strong_max = float(os.getenv("INCIDENT_STRONG_DISTANCE", str(DEFAULT_STRONG_EVIDENCE_MAX_DISTANCE)))
    if top <= strong_max and len(relevant) >= 2:
        return "Strong evidence"
    return "Partial evidence"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value.strip())
    return out


def _section_items(text: str, header: str) -> list[str]:
    """Extract "- " bullet items under a `HEADER:` section of an LLM response."""
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().upper().startswith(header.upper()):
            start = index
            break
    if start is None:
        return []
    items = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[A-Z][A-Z /&-]{2,}:", stripped):
            break
        if stripped.startswith(("-", "•", "*")):
            items.append(stripped.lstrip("-•* ").strip())
    return items


def _analysis_block(text: str) -> str | None:
    """Return the free-text analysis after the ANALYSIS: header."""
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().upper().startswith("ANALYSIS:"):
            start = index + 1
            break
    if start is None:
        return None
    parts = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[A-Z][A-Z /&-]{2,}:", stripped):
            break
        parts.append(stripped.lstrip("-•* ").strip())
    return " ".join(parts) if parts else None


def _coverage_in_text(text: str) -> str | None:
    upper = text.upper()
    for level in COVERAGE_LEVELS:
        if level.upper() in upper:
            return level
    return None


def _build_incident_prompt(incident: str, relevant: list[dict]) -> str:
    lines = [f"Incident described by the user:\n{incident}", "", "Retrieved organizational memories:", ""]
    for index, memory in enumerate(relevant, start=1):
        meta = memory.get("metadata") or {}
        lines += [
            f"Memory {index} (id={memory.get('id', '')}):",
            f"Title: {meta.get('title', '')}",
            f"Experience: {meta.get('experience', '')}",
            f"Recommendation: {meta.get('recommendation', '')}",
            f"Warnings: {meta.get('warnings', '')}",
            "",
        ]
    lines += [
        "Respond using ONLY this structure:",
        "",
        "ANALYSIS:",
        "(2-4 sentences grounded in the memories; tag general reasoning with (general))",
        "IMMEDIATE CONSIDERATIONS:",
        "- <item>",
        "RELEVANT PREVIOUS INCIDENTS:",
        "- <title from the memories only>",
        "WARNINGS:",
        "- <item>",
        "RELEVANT EXPERTS:",
        "- <role from the memories only>",
        "KNOWLEDGE COVERAGE: Strong evidence",
    ]
    return "\n".join(lines)


def analyze_incident(incident: str, top_k: int = 6, use_llm: bool | None = None) -> dict:
    """Analyze a described incident and return structured decision support.

    Returns a dict with keys: ``incident``, ``summary``, ``immediate_considerations``,
    ``relevant_previous_incidents``, ``warnings``, ``relevant_experts``,
    ``knowledge_coverage``, ``sources``, ``llm_used``, ``insufficient``, and
    ``disclaimer``.
    """
    incident = (incident or "").strip()
    if not incident:
        raise ValueError("Incident description must not be empty")

    memories = retrieve_memories(incident, top_k=top_k)
    threshold = get_memory_distance_threshold()
    relevant = [
        m for m in memories
        if isinstance(m.get("distance"), (int, float)) and m["distance"] <= threshold
    ]

    sources = [_summarize_source(m) for m in relevant]
    coverage = _coverage_for(relevant)

    incidents = [
        {"id": m.get("id", ""), "title": (m.get("title") or ""), "distance": float(m["distance"])}
        for m in relevant
    ]
    experts = _unique([str((m.get("metadata") or {}).get("author_role") or "") for m in relevant])
    local_warnings = _unique(
        [str((m.get("metadata") or {}).get("warnings") or "") for m in relevant]
    )
    local_considerations = _unique(
        [str((m.get("metadata") or {}).get("recommendation") or "") for m in relevant]
    )

    local_summary = (
        "Local synthesis from stored organizational experience. "
        + (("Consider: " + " # ".join(local_considerations[:3]) + ". ") if local_considerations else
           "No stored recommendations retrieved.")
        + f"Knowledge coverage: {coverage}."
    )

    if use_llm is None:
        use_llm = is_available()

    llm_used = False
    analysis = local_summary
    considerations = local_considerations
    warnings = local_warnings

    if use_llm and relevant:
        try:
            text = generate_answer(
                INCIDENT_SYSTEM_PROMPT,
                _build_incident_prompt(incident, relevant),
                max_tokens=1200,
            )
            llm_used = True
            analysis = _analysis_block(text) or local_summary
            llm_considerations = _section_items(text, "IMMEDIATE CONSIDERATIONS:")
            llm_warnings = _section_items(text, "WARNINGS:")
            if llm_considerations:
                considerations = _unique(llm_considerations + local_considerations)
            if llm_warnings:
                warnings = _unique(local_warnings + llm_warnings)
            llm_coverage = _coverage_in_text(text)
            if llm_coverage:
                coverage = llm_coverage
        except Exception as exc:  # noqa: BLE001 - details go to the terminal only
            print(f"[MemoryOS] incident LLM call failed: {exc!r}")

    return {
        "incident": incident,
        "summary": analysis,
        "immediate_considerations": considerations,
        "relevant_previous_incidents": incidents,
        "warnings": warnings,
        "relevant_experts": experts,
        "knowledge_coverage": coverage,
        "sources": sources,
        "llm_used": llm_used,
        "insufficient": not bool(relevant),
        "disclaimer": INCIDENT_DISCLAIMER,
    }