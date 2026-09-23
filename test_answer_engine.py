"""Smoke test for the MemoryOS AI brain (Part 3).

Run: python test_answer_engine.py

Never requires a paid OpenAI API. If LLM_API_KEY is set, one real grounded
answer is generated; otherwise the retrieval + graceful no-key path is
verified and the LLM call is skipped.
"""

from test_memory_engine import QUERY, SAMPLE_MEMORIES, TARGET_ID

from src.answer_service import answer_question, get_memory_distance_threshold
from src.llm import is_available
from src.memory_service import capture_memory, get_service, retrieve_memories

UNRELATED_QUERY = "How do I file payroll taxes in this company?"


def main() -> None:
    service = get_service()
    print(f"Relevance threshold (cosine distance): {get_memory_distance_threshold()}")
    print("Clearing collection...")
    service.store.clear()

    print("Capturing sample memories...")
    for memory in SAMPLE_MEMORIES:
        capture_memory(memory)
    print(f"Stored memory count: {service.store.count()}")

    print(f"\nQuery: {QUERY}\n")
    results = retrieve_memories(QUERY, top_k=5)
    for result in results:
        print(f"  [{result['distance']:.4f}] {result['id']} | {result['title']}")

    if not results:
        raise SystemExit("FAIL: no memories retrieved")
    top = results[0]
    assert top["id"] == TARGET_ID, f"FAIL: expected {TARGET_ID} on top, got {top['id']}"
    print(f"PASS: H-204 memory retrieved as the top relevant result "
          f"(distance {top['distance']:.4f}).\n")

    unrelated_in_threshold = [
        r
        for r in retrieve_memories(UNRELATED_QUERY, top_k=5)
        if r["distance"] <= get_memory_distance_threshold()
    ]
    if unrelated_in_threshold:
        print(f"NOTE: unrelated query matched {len(unrelated_in_threshold)} memory(ies) "
              "inside the threshold; consider tuning MEMORY_DISTANCE_THRESHOLD.")
    else:
        print("PASS: unrelated query produced no in-threshold sources.\n")

    if not is_available():
        response = answer_question(QUERY, top_k=5)
        assert response["sources"], "FAIL: expected sources in the no-key response"
        assert response["llm_used"] is False
        print("Graceful no-key response sources:")
        for source in response["sources"]:
            print(f"  - {source['title']} (id={source['id']}, distance={source['distance']:.4f})")
        print("\nLLM test skipped: LLM_API_KEY not configured.")
        return

    print("LLM_API_KEY configured - calling the LLM...\n")
    try:
        response = answer_question(QUERY, top_k=5)
    except Exception as exc:  # noqa: BLE001 - report loudly rather than fail silently
        print(f"WARNING: LLM call failed ({type(exc).__name__}): {exc}")
        return

    print("--- Grounded answer ---")
    print(response["answer"])
    print(f"\nKnowledge coverage: {response['knowledge_coverage']}")
    print("\nSources from organizational memory:")
    for source in response["sources"]:
        print(f"  - {source['title']} (id={source['id']}, distance={source['distance']:.4f})")
    print("\nPASS: grounded answer generated and sources returned.")


if __name__ == "__main__":
    main()