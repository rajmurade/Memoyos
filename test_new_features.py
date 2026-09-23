"""Tests / demo for the three new MemoryOS features.

Run: python test_new_features.py

Offline by default: conflict detection is exercised with ``use_llm=False``
(candidate-evidence path) and with the same-wording consistency guard. The
incident and relationship services never require the LLM for their structured
output. Uses an isolated temporary ChromaDB store so the demo data is untouched.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import src.memory_service as ms  # noqa: E402
from src.conflict_service import analyze_conflicts  # noqa: E402
from src.incident_service import analyze_incident, INCIDENT_DISCLAIMER  # noqa: E402
from src.memory_service import Memory  # noqa: E402
from src.relationship_service import find_related_memories  # noqa: E402
from src.vector_store import VectorStore  # noqa: E402


CONFLICT_A = Memory(
    id="test-conf-a",
    title="Cool Down and Restart H-204",
    author_role="Shift Operator",
    category="Operations",
    situation=(
        "Press H-204 trips on high oil temperature; the alarm clears once the oil cools."
    ),
    experience=(
        "Restarting after the cooldown has kept production moving without further checks."
    ),
    recommendation=(
        "After H-204 overheats and the alarm clears, restart the press as soon as the oil "
        "temperature drops below the alarm threshold. Production should continue."
    ),
    warnings="Do not attempt a restart while the temperature is still climbing.",
    tags=["hydraulics", "h-204", "restart"],
    created_at="2026-03-01T08:00:00+00:00",
)

CONFLICT_B = Memory(
    id="test-conf-b",
    title="Inspect Cooling Before Restarting H-204",
    author_role="Senior Maintenance Technician",
    category="Maintenance",
    situation=(
        "Press H-204 re-trips shortly after immediate restarts, and pump seals fail within weeks."
    ),
    experience=(
        "Recurrences were traced to a clogged cooling filter and restricted hydraulic circulation."
    ),
    recommendation=(
        "Do NOT restart H-204 immediately after an overheating trip. Inspect the cooling filter and "
        "hydraulic fluid circulation first, and only restart once flow is confirmed and temperature "
        "is stable."
    ),
    warnings=(
        "Never restart the press immediately after a high-temperature shutdown without confirming "
        "circulation."
    ),
    tags=["hydraulics", "h-204", "restart", "inspection"],
    created_at="2026-03-02T09:30:00+00:00",
)

CONSISTENT = Memory(
    id="test-cons",
    title="Cool Down and Restart H-204 (second account)",
    author_role="Maintenance Technician",
    category="Operations",
    situation=(
        "Press H-204 trips on high oil temperature; the alarm clears once the oil cools."
    ),
    experience="Same lesson recorded by another technician.",
    recommendation=(
        "After H-204 overheats and the alarm clears, restart the press as soon as the oil "
        "temperature drops below the alarm threshold. Production should continue."
    ),
    warnings="Do not attempt a restart while the temperature is still climbing.",
    tags=["hydraulics", "h-204", "restart"],
    created_at="2026-03-03T10:00:00+00:00",
)

RELATED = Memory(
    id="test-rel",
    title="Hydraulic Filter Change Cycle for H-204",
    author_role="Maintenance Technician II",
    category="Maintenance",
    situation="H-204 hydraulic filter bypass trips early between oil changes.",
    experience="Early filter replacement reduces heat-related trips on the press.",
    recommendation="Replace the H-204 hydraulic filter quarterly or when the bypass indicator trips.",
    warnings="Do not wait for a full oil change to replace a clogged filter.",
    tags=["hydraulics", "h-204", "filter", "preventive"],
    created_at="2026-03-04T11:00:00+00:00",
)

UNRELATED = Memory(
    id="test-unrelated",
    title="Onboarding Checklist for New Hires",
    author_role="Team Lead",
    category="People",
    situation="New employees need accounts and a team walkthrough.",
    experience="First-day access setup prevents most onboarding blockers.",
    recommendation="Provision accounts, add repository access, and schedule a pair partner.",
    warnings="Do not grant production access until the review is completed.",
    tags=["onboarding", "access", "people"],
    created_at="2026-03-05T12:00:00+00:00",
)


def fresh_service(*memories: Memory) -> ms.MemoryService:
    """Point the singleton at a fresh temp store and capture the given memories."""
    tmp = tempfile.mkdtemp(prefix="memoryos_tests_")
    service = ms.MemoryService(store=VectorStore(persist_dir=tmp))
    ms._service = service
    for memory in memories:
        service.capture_memory(memory)
    return service


def by_id(memories: list[dict], memory_id: str) -> dict:
    return next(m for m in memories if str((m.get("metadata") or {}).get("id")) == memory_id)


def main() -> None:
    failures: list[str] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}" + (f" | {detail}" if detail else ""))
        if not condition:
            failures.append(f"{name}: {detail}")

    # -- Feature 1: conflict detection --------------------------------------
    print("\nFeature 1: Conflict detection")

    fresh_service(CONFLICT_A, CONFLICT_B, UNRELATED)
    res = analyze_conflicts("H-204 restart after overheating", use_llm=False)
    check("conflict detected (has_conflict)", res["has_conflict"] is True)
    check("requires human review", res["requires_human_review"] is True)
    check("evidence is candidate", res["evidence"] == "candidate")
    check("context memories returned", len(res["memories"]) >= 2)
    pair_found = any(
        {p["memory_a"]["id"], p["memory_b"]["id"]} == {"test-conf-a", "test-conf-b"}
        for p in res["pairs"]
    )
    check("conflicting pair surfaced", pair_found)
    pair = next(p for p in res["pairs"] if {p["memory_a"]["id"], p["memory_b"]["id"]} == {"test-conf-a", "test-conf-b"})
    side_a = next(s for s in (pair["memory_a"], pair["memory_b"]) if s["id"] == "test-conf-a")
    side_b = next(s for s in (pair["memory_a"], pair["memory_b"]) if s["id"] == "test-conf-b")
    check(
        "author/date preserved",
        side_a["author_role"] == "Shift Operator"
        and side_a["created_at"] == "2026-03-01T08:00:00+00:00"
        and side_b["author_role"] == "Senior Maintenance Technician",
    )
    check("recommendations list populated", any(r["id"] == "test-conf-a" for r in res["recommendations"]))
    check("unrelated memory excluded from pairs", all(
        p["memory_a"]["id"] != "test-unrelated" and p["memory_b"]["id"] != "test-unrelated"
        for p in res["pairs"]
    ))

    fresh_service(CONFLICT_A, CONSISTENT)
    res = analyze_conflicts("H-204 restart after overheating", use_llm=False)
    check("same-wording pair NOT conflicting", res["has_conflict"] is False)

    fresh_service()
    res = analyze_conflicts("completely unknown topic xyz", use_llm=False)
    check("insufficient evidence handled", res["has_conflict"] is False and "insufficient" in res["note"].lower())

    # -- Feature 2: related memories ----------------------------------------
    print("\nFeature 2: Related memories / memory graph")

    service = fresh_service(CONFLICT_A, CONFLICT_B, RELATED, UNRELATED)
    root = by_id(service.list_memories(), "test-conf-a")
    rel = find_related_memories(root)
    related_ids = {r["id"] for r in rel["related_memories"]}
    check("excludes the memory itself", "test-conf-a" not in related_ids)
    check("finds conflicting memory (close pair)", "test-conf-b" in related_ids)
    check("finds shared-equipment memory", "test-rel" in related_ids)
    check("unrelated memory below threshold", "test-unrelated" not in related_ids)
    check(
        "all similarities in (0,1]",
        all(0.0 < r["similarity"] <= 1.0 for r in rel["related_memories"]),
    )
    check(
        "relationship label data-supported",
        all(r["relationship"] in {"Similar equipment", "Similar failure symptom", "Related maintenance topic", "Related experience"} for r in rel["related_memories"]),
    )
    check("reason text present", all(r.get("reason") for r in rel["related_memories"]))
    b_entry = next(r for r in rel["related_memories"] if r["id"] == "test-conf-b")
    check("equipment relationship labelled", b_entry["relationship"] == "Similar equipment")

    loner = fresh_service(UNRELATED).list_memories()
    rel = find_related_memories(loner[0])
    check("no related memories -> empty + note", not rel["related_memories"] and bool(rel["note"]))

    # -- Feature 3: incident mode -------------------------------------------
    print("\nFeature 3: Incident mode")

    service = fresh_service(CONFLICT_A, CONFLICT_B, RELATED, UNRELATED)
    res = analyze_incident("H-204 temperature is rapidly increasing.", use_llm=False)
    check("structured keys present", all(
        k in res for k in (
            "incident", "summary", "immediate_considerations", "relevant_previous_incidents",
            "warnings", "relevant_experts", "knowledge_coverage", "sources", "llm_used",
            "insufficient", "disclaimer",
        )
    ))
    check("not marked insufficient", res["insufficient"] is False)
    check("findings grounded in memories", bool(res["sources"]) and len(res["immediate_considerations"]) >= 2)
    check("previous incidents from memory titles", any("H-204" in i["title"] for i in res["relevant_previous_incidents"]))
    check("warnings preserved", any("restart" in w.lower() for w in res["warnings"]))
    check("experts derived from sources", "Shift Operator" in res["relevant_experts"])
    check("disclaimer present", res["disclaimer"] == INCIDENT_DISCLAIMER)

    fresh_service()
    res = analyze_incident("quarterly corporate tax filing deadline", use_llm=False)
    check("insufficient evidence graceful", res["insufficient"] is True and res["knowledge_coverage"] == "Insufficient evidence")
    check("no fabricated sources on insufficient", not res["sources"])

    # -- summary --------------------------------------------------------------
    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s) failed")
        for f in failures:
            print(f"  - {f}")
        raise SystemExit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()