# MemoryOS

**MemoryOS** is an AI-powered institutional memory system that captures valuable
knowledge from experienced people and makes it searchable and actionable for
other team members.

## Project status

**Current status — Part 1 (foundation), Part 2 (memory engine), Part 3 (AI
brain), Part 4 (connected memory: conflicts, related memories, incident mode)
done:**

- A Streamlit app shell that displays the project name, description, and a
  "Foundation setup complete" status (including whether an LLM API key is
  configured).
- A small `src/config.py` module that loads `.env` and exposes the LLM API
  configuration with sensible defaults.
- A local semantic memory engine:
  - `src/embeddings.py` — lazy local embeddings via sentence-transformers.
  - `src/vector_store.py` — persistent ChromaDB wrapper (single collection).
  - `src/memory_service.py` — capture/retrieval service layer, independent
    of Streamlit.
- An AI reasoning layer that grounds answers on retrieved memories:
  - `src/llm.py` — lazy OpenAI-compatible client wrapper (OpenRouter-ready),
    with automatic retry on empty free-tier responses.
  - `src/answer_service.py` — retrieves relevant memories, applies a cosine
    distance relevance cutoff, and returns a grounded answer plus the source
    memories for display.
- A connected-memory layer built on the same embeddings / ChromaDB:
  - `src/conflict_service.py` — detects potentially conflicting
    recommendations between stored experiences; asks for human verification
    instead of picking a winner.
  - `src/relationship_service.py` — finds related memories (no graph DB) and
    labels the relationship only when shared data supports it.
  - `src/incident_service.py` — grounded, structured decision support for
    urgent operational problems (Incident Mode).
- A Streamlit product UI (`app.py`) with five pages:
  - **Ask MemoryOS** — semantic retrieval + grounded AI answers with source
    transparency, Knowledge Coverage, and conflict checks on the result.
  - **Capture Memory** — form that stores structured experience.
  - **Memory Library** — browse stored memories by category, then inspect one
    memory to see its related experience and any conflicts.
  - **Incident Mode** — enter an urgent problem, get structured immediate
    considerations, relevant previous incidents, warnings, relevant experts,
    coverage, and grounded synthesis.
  - **Knowledge Map** — pick a memory and see its connected experience as a
    lightweight tree (second-level exploration included).

LLM-backed answers require an API key; the local retrieval engine works without it.

## Getting started

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate it:

   - Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - Windows (cmd):
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
   - macOS / Linux:
     ```bash
     source .venv/bin/activate
     ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure the environment:

   - Copy `.env.example` to `.env`:
     - Windows (PowerShell): `Copy-Item .env.example .env`
     - macOS / Linux: `cp .env.example .env`
   - The intended LLM provider is **OpenRouter**, which is OpenAI-compatible.
     Set `LLM_BASE_URL=https://openrouter.ai/api/v1` (this is already the
     example default), put your OpenRouter API key in `LLM_API_KEY`, and set
     `LLM_MODEL` to a model such as `gpt-4o-mini`.
- The API key is **optional** for the local memory-engine test but
      **required** for AI answering. `MEMORY_DISTANCE_THRESHOLD` is an optional
      cosine-distance cutoff (defaults to `0.75`) for memories passed to the LLM.
   - Optional tuning for the newer features (see `.env.example`):
     `RELATED_DISTANCE_THRESHOLD` (default `0.80`) controls related-memory
     suggestions; `CONFLICT_PAIR_DISTANCE` (default `0.55`) and
     `CONFLICT_REC_DIFF` (default `0.35`) tune conflict-candidate detection.

5. Run the app:

   ```bash
   streamlit run app.py
   ```

6. Smoke-test the memory engine (no API key needed):

   ```bash
   python test_memory_engine.py
   ```

7. Smoke-test the AI answering layer (skips the LLM call if no API key):

   ```bash
   python test_answer_engine.py
   ```

8. Test the connected-memory features (conflicts, related memories, incident
   mode) against an isolated store (no API key needed):

   ```bash
   python test_new_features.py
   ```

9. Smoke-test the full Streamlit UI with AppTest (all five pages render):

   ```bash
   python test_app.py
   ```

## Demo

The demo memories are **fictional manufacturing examples** — all organizations,
machine IDs, and incidents are made up for demonstration only.

1. Activate the virtual environment (see Getting started).
2. Seed the demo memories (from the project root):

   ```bash
   .\.venv\Scripts\python.exe seed/demo_memories.py
   ```

   Re-running is safe (stable IDs, no duplicates). Pass `--reset` to clear the
   store back to exactly the demo memories. Seeding is never automatic.
3. Start Streamlit:

   ```bash
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```
4. Open the browser URL shown in the terminal.
5. On **Ask MemoryOS**, try one of the example questions:

   - "Machine H-204 is overheating after several hours. What should I check first?"
   - "The conveyor is vibrating more than usual. What should maintenance inspect?"
   - "The compressor keeps losing pressure during operation. What should we investigate?"
   - "A motor has started making unusual bearing noise. What does our previous experience suggest?"
   - "H-204 just tripped on high oil temperature. Should we restart it right away?"

   The relevant memory appears under **Sources from organizational memory**,
   and a grounded AI answer is generated when `LLM_API_KEY` is configured.
6. On **Memory Library** → **Inspect a memory**, select
   *Inspect Cooling Before Restarting H-204* to see the **Potential Knowledge
   Conflict** — *Quick Restart After H-204 Overheating* recommends an immediate
   restart while this memory says "do not restart; inspect first". The system
   asks for human verification and does not pick a winner.
7. On **Incident Mode**, enter:
   "H-204 temperature is rapidly increasing." — and see immediate
   considerations, relevant previous incidents, warnings, relevant experts,
   knowledge coverage, and grounded synthesis.
8. On **Knowledge Map**, start from *Hydraulic Press H-204 Overheating* to see
   it connected to the other H-204, overheating, and sensor memories.

## Project structure

```text
MemoryOS/
├── app.py            # Streamlit product UI (Ask / Capture / Library / Incident / Map)
├── test_memory_engine.py   # Smoke test for the memory engine
├── test_answer_engine.py   # Smoke test for the AI answering layer
├── test_new_features.py    # Tests for conflicts, related memories, incident mode
├── test_app.py             # Streamlit AppTest smoke test for all pages
├── requirements.txt
├── .env.example      # Environment variable template (no real secrets)
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py     # Loads .env and exposes LLM API configuration
│   ├── embeddings.py # Local lazy embeddings (sentence-transformers, incl. batch)
│   ├── vector_store.py  # Persistent ChromaDB wrapper (single collection)
│   ├── memory_service.py # Memory domain model + capture/retrieve service
│   ├── llm.py        # Lazy OpenAI-compatible client wrapper (retry on empty)
│   ├── answer_service.py # Grounded Q&A on retrieved memories
│   ├── conflict_service.py # Detects conflicting recommendations (human review)
│   ├── relationship_service.py # Related memories via embeddings (no graph DB)
│   └── incident_service.py    # Structured decision support for incidents
├── data/
│   └── chroma/       # Local ChromaDB persistence
└── seed/
    └── demo_memories.py  # Seeds 14 fictional demo memories (run manually)
```