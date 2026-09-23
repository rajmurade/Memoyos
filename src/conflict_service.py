"""Conflict detection service for MemoryOS.

Independent of Streamlit. Detects when two stored organizational experiences
contain potentially conflicting recommendations about the same scenario.

Approach (designed to never fabricate conflicts):

1. Retrieve memories relevant to the topic via the existing vector store.
2. Only consider pairs of memories that are also related to each other
   (semantic distance below a pair threshold) — different scenarios never
   conflict with each other.
3. Cheap filter: pairs whose recommendation texts are almost identical are
   treated as consistent (different wording that says the same thing).
4. Only surviving candidate pairs are sent to the LLM for verification. The LLM
   only reports genuine contradictions; it never picks a winner.
5. When no LLM is available, candidates are presented as "potential conflicts"
   that require human review — never as confirmed facts.

The system never overwrites, merges, or resolves memories. Author, date, and
source information is preserved in the output.
"""

import os
import re

import numpy as np

from src.answer_service import get_memory_distance_threshold
from src.embeddings import embed_text, embed_texts
from src.llm import generate_answer, is_available
from src.memory_service import retrieve_memories

# Max cosine distance between two memories' full texts for them to be considered
# the "same scenario". Higher = more permissive. env-tunable.
DEFAULT_PAIR_DOC_MAX_DISTANCE = 0.55
# Min cosine distance between two recommendation texts to be a candidate pair.
# Below this the recommendations are deemed (near-)identical wording -> consistent.
DEFAULT_RECOMMENDATION_DIFFERENCE_MIN = 0.35

CONFLICT_VERIFY_SYSTEM_PROMPT = """\
You detect genuine disagreements between stored organizational experiences.

A genuine conflict exists ONLY when two stored experiences give directly
contradictory recommendations about the SAME operational scenario — one
instructs an action while the other expressly advises against it, or instructs
the opposite action.

Rules:
- Repeated or paraphrased guidance is NOT a conflict.
- Memories about different equipment or different scenarios are NOT a conflict.
- Use only the memory text provided. Never invent content and never judge which
  recommendation is correct.

Respond with exactly one line per genuine conflict of the form:
CONFLICT: <idA> and <idB> | short reason
If there are no genuine conflicts, respond with exactly:
NO_CONFLICT
"""

_NO_CONFLICT_TOPIC_REASON = "Related memories were found, but their recommendations appear consistent."


def _memory_text(memory: dict) -> str:
    content = memory.get("content")
    if content:
        return content
    meta = memory.get("metadata") or {}
    return "\n".join(
        str(meta.get(k) or "")
        for k in ("title", "situation", "experience", "recommendation", "warnings", "tags")
    )


def _recommendation(memory: dict) -> str:
    meta = memory.get("metadata") or {}
    return str(meta.get("recommendation") or "").strip()


def _brief(memory: dict) -> dict:
    """Preserve source identity + author/date in the structured output."""
    meta = memory.get("metadata") or {}
    return {
        "id": str(memory.get("id") or meta.get("id") or ""),
        "title": str(memory.get("title") or meta.get("title") or "(Untitled)"),
        "author_role": str(meta.get("author_role") or ""),
        "category": str(meta.get("category") or ""),
        "created_at": str(meta.get("created_at") or ""),
        "recommendation": str(meta.get("recommendation") or ""),
        "warnings": str(meta.get("warnings") or ""),
    }


def _distance_matrix(vector_rows: list[list[float]]) -> np.ndarray:
    """Cosine distance matrix (0-2) for a list of normalized vectors."""
    if not vector_rows:
        return np.zeros((0, 0))
    mat = np.asarray(vector_rows, dtype=float)
    similarity = np.clip(mat @ mat.T, -1.0, 1.0)
    return 1.0 - similarity


def _verify_candidates_with_llm(memories: list[dict], pairs: list[tuple[int, int, float]]) -> list[tuple[int, int, str]]:
    """Ask the LLM to confirm which candidate pairs are genuine conflicts.

    Returns a list of ``(i, j, reason)`` indices into ``memories``.
    """
    names = {}
    lines = ["Retrieved organizational memories:", ""]
    for index, memory in enumerate(memories):
        memory_id = str(memory.get("id") or "")
        meta = memory.get("metadata") or {}
        names[index] = memory_id
        lines += [
            f"{index + 1}. id={memory_id}",
            f"   Title: {meta.get('title', '')}",
            f"   Recommendation: {meta.get('recommendation', '')}",
            "",
        ]
    lines.append("Candidate pairs to verify (only these pairs may be genuine conflicts):")
    for i, j, _ in pairs:
        lines.append(f"- {names[i]} and {names[j]}")
    lines += ["", "List the genuine conflicts only, one CONFLICT line each."]
    del names

    text = generate_answer(
        CONFLICT_VERIFY_SYSTEM_PROMPT,
        "\n".join(lines),
        max_tokens=1000,
        temperature=0.0,
    )

    by_id = {str(memory.get("id") or ""): index for index, memory in enumerate(memories)}
    confirmed = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.upper().startswith("CONFLICT:"):
            continue
        pair_part = stripped.split("|", 1)[0]
        reason = stripped.split("|", 1)[1].strip() if "|" in stripped else ""
        pair_ids = {token for token in re.findall(r"[A-Za-z0-9_-]+", pair_part) if token.lower() != "and"}
        for i, j, _ in pairs:
            if by_id.get(str(memories[i].get("id") or "")) == i and {
                str(memories[i].get("id") or ""),
                str(memories[j].get("id") or ""),
            } <= pair_ids:
                confirmed.append((i, j, reason))
                break
    return confirmed


def _no_conflict(topic: str, note: str, evidence: str = "insufficient") -> dict:
    return {
        "topic": topic,
        "has_conflict": False,
        "confirmed": False,
        "evidence": evidence,
        "summary": note,
        "pairs": [],
        "memories": [],
        "recommendations": [],
        "requires_human_review": False,
        "llm_used": False,
        "note": note,
    }


def analyze_conflicts(topic: str, top_k: int = 10, use_llm: bool | None = None) -> dict:
    """Analyze ``topic`` for conflicting recommendations in stored memories.

    Returns a dict with keys: ``has_conflict``, ``confirmed``, ``evidence``,
    ``summary``, ``pairs``, ``memories``, ``recommendations``,
    ``requires_human_review``, ``llm_used``, and ``note``.
    """
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("Topic must not be empty")

    memories = retrieve_memories(topic, top_k=top_k)
    threshold = get_memory_distance_threshold()
    relevant = [
        m for m in memories
        if isinstance(m.get("distance"), (int, float)) and m["distance"] <= threshold
    ]

    if len(relevant) < 2:
        return _no_conflict(
            topic,
            f"Not enough relevant memories to compare (found {len(relevant)}); "
            "evidence is insufficient. Capture or seed more memories on this topic.",
        )

    docs = [_memory_text(m) for m in relevant]
    doc_matrix = _distance_matrix(embed_texts(docs))

    rec_vectors: dict[int, np.ndarray] = {}
    for index, memory in enumerate(relevant):
        rec = _recommendation(memory)
        if rec:
            rec_vectors[index] = np.asarray(embed_text(rec), dtype=float)

    max_pair_distance = float(os.getenv("CONFLICT_PAIR_DISTANCE", str(DEFAULT_PAIR_DOC_MAX_DISTANCE)))
    min_rec_difference = float(os.getenv("CONFLICT_REC_DIFF", str(DEFAULT_RECOMMENDATION_DIFFERENCE_MIN)))

    candidates: list[tuple[int, int, float]] = []
    for i in range(len(relevant)):
        for j in range(i + 1, len(relevant)):
            if float(doc_matrix[i][j]) > max_pair_distance:
                continue
            if i not in rec_vectors or j not in rec_vectors:
                continue
            difference = float(1.0 - np.clip(float(rec_vectors[i] @ rec_vectors[j]), -1.0, 1.0))
            if difference < min_rec_difference:
                continue
            candidates.append((i, j, round(difference, 4)))

    if not candidates:
        return _no_conflict(topic, _NO_CONFLICT_TOPIC_REASON, evidence="consistent")

    if use_llm is None:
        use_llm = is_available()

    candidate_reason = (
        "The two stored recommendations point to different actions for the same scenario."
    )
    llm_outcome = "none"  # "verified" | "errored"
    verified_pairs: list[tuple[int, int, str]] = []
    if use_llm:
        try:
            verified_pairs = _verify_candidates_with_llm(relevant, candidates)
            llm_outcome = "verified"
        except Exception as exc:  # noqa: BLE001 - details go to the terminal only
            print(f"[MemoryOS] conflict LLM verification failed: {exc!r}")
            llm_outcome = "errored"

    if llm_outcome == "verified" and not verified_pairs:
        # The LLM explicitly evaluated the candidates and found no contradiction.
        return _no_conflict(topic, _NO_CONFLICT_TOPIC_REASON, evidence="consistent")

    if llm_outcome == "verified":
        evidence = "confirmed"
        summary = (
            "Two stored experiences contain conflicting recommendations for the same scenario. "
            "MemoryOS does not decide which is correct — human verification is required."
        )
        report_pairs = verified_pairs
    else:
        # Candidate evidence only (LLM unavailable or errored). Never over-claims.
        evidence = "candidate"
        summary = (
            "Two stored experiences give different recommendations for the same scenario. "
            "Human verification is recommended before relying on either one."
        )
        if use_llm:
            summary += " LLM verification could not be completed; this is a candidate, not a confirmed conflict."
        else:
            summary += " LLM verification was not available; this is a candidate, not a confirmed conflict."
        report_pairs = [(i, j, candidate_reason) for i, j, _ in candidates]

    pair_entries = []
    for i, j, reason in report_pairs:
        pair_entries.append(
            {
                "memory_a": _brief(relevant[i]),
                "memory_b": _brief(relevant[j]),
                "rec_distance": round(
                    max(0.0, 1.0 - float(np.clip(rec_vectors[i] @ rec_vectors[j], -1.0, 1.0))), 4
                ),
                "related_distance": round(float(doc_matrix[i][j]), 4),
                "reason": reason,
            }
        )

    recommendations = []
    seen_ids: set[str] = set()
    for i, j, _ in candidates:
        for idx in (i, j):
            mem_id = str(relevant[idx].get("id") or "")
            if mem_id in seen_ids:
                continue
            seen_ids.add(mem_id)
            recommendations.append(_brief(relevant[idx]))

    return {
        "topic": topic,
        "has_conflict": True,
        "confirmed": evidence == "confirmed",
        "evidence": evidence,
        "summary": summary,
        "pairs": pair_entries,
        "memories": [_brief(m) for m in relevant],
        "recommendations": recommendations,
        "requires_human_review": True,
        "llm_used": llm_outcome == "verified",
        "note": summary,
    }