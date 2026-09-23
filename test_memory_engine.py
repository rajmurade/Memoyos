"""Smoke test / demo for the MemoryOS local semantic memory engine (Part 2).

Run: python test_memory_engine.py
"""

from src.embeddings import get_embedding_model_name
from src.memory_service import Memory, capture_memory, get_service, retrieve_memories

TARGET_ID = "mem-h204-001"

SAMPLE_MEMORIES = [
    Memory(
        id=TARGET_ID,
        title="Hydraulic Press H-204 Overheating",
        situation="Hydraulic press H-204 begins overheating after several hours of continuous operation.",
        experience="Experienced technicians observed that restricted hydraulic fluid flow and clogged cooling filters were common causes.",
        recommendation="Check hydraulic fluid level, cooling filter condition, and circulation before replacing components.",
        warnings="Do not immediately restart the machine if temperature continues rising.",
        author_role="Senior Maintenance Technician",
        category="Maintenance",
        tags=["hydraulics", "h-204", "maintenance", "overheating"],
    ),
    Memory(
        id="mem-api-001",
        title="API Rate Limit Spikes During Release",
        situation="Production API returns 429 rate limit errors during the weekly release window.",
        experience="The spike is usually caused by retry storms from misconfigured clients, not by the new code itself.",
        recommendation="Enable retries with exponential backoff and jitter on the client side before scaling the gateway.",
        warnings="Do not restart the gateway first; that makes the retry storm worse.",
        author_role="Platform Engineer",
        category="Software",
        tags=["api", "rate-limit", "release", "incident"],
    ),
    Memory(
        id="mem-onb-001",
        title="First Week Onboarding Checklist",
        situation="New joiners need accounts, repository access, and a walkthrough of the team playbook.",
        experience="Spending the first day on access setup pays off; most blockers happen on day one.",
        recommendation="Provision accounts, add to GitHub, grant read-only staging access, and schedule a pair on call.",
        warnings="Do not grant production access until the onboarding review is completed.",
        author_role="Team Lead",
        category="People",
        tags=["onboarding", "access", "new-joiner"],
    ),
    Memory(
        id="mem-net-001",
        title="VLAN 40 Intermittent Packet Loss",
        situation="Devices on VLAN 40 drop packets intermittently, especially near peak camera streaming.",
        experience="The uplink port was negotiating half-duplex under load; the switch config was never verified.",
        recommendation="Verify the uplink duplex mode and check for CRC errors on the trunk port.",
        warnings="Do not rewrite the whole network config while diagnosing; change one switchport at a time.",
        author_role="Network Administrator",
        category="Infrastructure",
        tags=["network", "vlan", "switching", "packet-loss"],
    ),
]

QUERY = "Machine H-204 is overheating after several hours. What should I check first?"


def main() -> None:
    print(f"Embedding model: {get_embedding_model_name()}")
    service = get_service()
    print("Clearing collection...")
    service.store.clear()

    print("Capturing sample memories...")
    for memory in SAMPLE_MEMORIES:
        captured = capture_memory(memory)
        print(f"  stored {captured.id} | {captured.title}")

    print(f"\nStored memory count: {service.store.count()}")
    print(f"\nQuery: {QUERY}\n")

    results = retrieve_memories(QUERY, top_k=3)
    for result in results:
        print(
            f"  [{result['distance']:.4f}] {result['id']} | {result['title']}"
            f" | tags={result['metadata'].get('tags')}"
        )

    if not results:
        raise SystemExit("FAIL: no results returned")

    top = results[0]
    expected_title = next(m.title for m in SAMPLE_MEMORIES if m.id == TARGET_ID)
    assert top["id"] == TARGET_ID, f"FAIL: expected {TARGET_ID} on top, got {top['id']}"
    assert top["title"] == expected_title, f"FAIL: unexpected top title {top['title']}"
    assert top["content"], "FAIL: expected document/content in result"
    assert top["metadata"].get("category") == "Maintenance", "FAIL: metadata missing category"

    print("\nPASS: H-204 memory retrieved as the top relevant result.")


if __name__ == "__main__":
    main()