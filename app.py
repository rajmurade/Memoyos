"""MemoryOS - Streamlit product UI.

Five pages (Ask MemoryOS, Capture Memory, Memory Library, Incident Mode,
Knowledge Map) driven by the existing services in ``src/``. No embedding,
ChromaDB, or LLM logic lives here; app.py only renders and calls those services.
"""

import html
import uuid
from datetime import datetime

import streamlit as st

from src.answer_service import answer_question
from src.conflict_service import analyze_conflicts
from src.incident_service import analyze_incident
from src.llm import is_available
from src.memory_service import Memory, get_service
from src.relationship_service import find_related_memories

APP_NAME = "MemoryOS"
TAGLINE = "Your organization's memory, made actionable."
PAGES = ["Ask MemoryOS", "Capture Memory", "Memory Library", "Incident Mode", "Knowledge Map"]

CATEGORIES = ["Maintenance", "Safety", "Operations", "Troubleshooting", "Equipment", "Process", "Other"]

QUESTION_PLACEHOLDER = (
    "Machine H-204 is overheating after several hours. What should I check first?"
)

INCIDENT_PLACEHOLDER = (
    "H-204 temperature is rapidly increasing during the shift. What does our stored "
    "experience say to do first?"
)

COVERAGE_STYLES = {
    "Strong evidence": ("coverage-strong", "Strong evidence"),
    "Partial evidence": ("coverage-partial", "Partial evidence"),
    "Insufficient evidence": ("coverage-insufficient", "Insufficient evidence"),
}


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

def inject_styles() -> None:
    """Small, restrained CSS pass to give the app a clean AI-SaaS look."""
    st.markdown(
        """
        <style>
        .block-container { max-width: 1000px; padding-top: 2.2rem; }
        [data-testid="stSidebar"] { border-right: 1px solid #ececf0; }
        [data-testid="stSidebar"] [data-testid="stMetric"] {
            background: #ffffff; border: 1px solid #ececf0; border-radius: 10px;
            padding: 8px 12px;
        }
        .coverage-badge {
            display: inline-block; padding: 2px 12px; border-radius: 999px;
            font-size: 0.8rem; font-weight: 600;
        }
        .coverage-strong      { background: #e7f6ec; color: #0e7a3d; }
        .coverage-partial     { background: #fff4e0; color: #a0660b; }
        .coverage-insufficient{ background: #fdecec; color: #b42318; }

        .conflict-box {
            border: 1px solid #f2c4c4; background: #fdf3f3; border-radius: 10px;
            padding: 12px 16px; margin: 8px 0 12px;
        }
        .conflict-title { font-weight: 700; color: #b42318; font-size: 0.95rem; }
        .conflict-note  { color: #7a4a1f; font-size: 0.82rem; margin-top: 4px; }

        .expert-chip {
            display: inline-block; background: #eef1fa; color: #1f2357;
            border: 1px solid #dde2f5; border-radius: 999px; padding: 2px 12px;
            font-size: 0.8rem; margin: 2px 4px 2px 0;
        }

        .mem-tree { margin: 10px 0 6px; }
        .tree-node {
            display: inline-block; background: #ffffff; border: 1px solid #d6d6e0;
            border-radius: 8px; padding: 4px 10px; font-size: 0.85rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04); max-width: 100%;
        }
        .tree-root { background: #1f2357; color: #ffffff; border-color: #1f2357; font-weight: 600; }
        .tree-stem { width: 2px; height: 14px; background: #d6d6e0; margin: 0 auto; }
        .tree-children { display: flex; justify-content: center; gap: 14px; flex-wrap: wrap; }
        .tree-child  { text-align: center; width: 250px; display: flex; flex-direction: column; align-items: center; }
        .tree-connector { width: 100%; height: 12px; border-top: 2px solid #d6d6e0; }
        .tree-rel { font-size: 0.72rem; color: #1f2357; font-weight: 600; margin-top: 3px; }
        .tree-why { font-size: 0.72rem; color: #6b7280; margin-top: 2px; }
        .tree-sim {
            color: #0e7a3d; font-size: 0.7rem; margin-left: 4px;
            border: 1px solid #cfe8d8; border-radius: 999px; padding: 0 5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Small rendering helpers
# ---------------------------------------------------------------------------

def _render_memory_fields(metadata: dict, created: bool = False) -> None:
    """Render a memory's structured fields as labeled lines."""
    fields = [
        ("Author role", "author_role"),
        ("Category", "category"),
        ("Situation / Context", "situation"),
        ("Experience / Observation", "experience"),
        ("Recommended action", "recommendation"),
        ("Warnings / Things to avoid", "warnings"),
        ("Tags", "tags"),
    ]
    for label, key in fields:
        value = str(metadata.get(key) or "").strip()
        if value:
            st.markdown(f"**{label}:** {value}")
    if created:
        created_value = str(metadata.get("created_at") or "").strip()
        if created_value:
            st.caption(f"Created: {format_date(created_value)}")


def format_date(value: str) -> str:
    """Format an ISO timestamp for display, degrading gracefully."""
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M")
    except (TypeError, ValueError):
        return str(value)[:16] or "—"


def _coverage_badge(label: str) -> None:
    css_class, text = COVERAGE_STYLES.get(label, ("", label or ""))
    if css_class:
        st.markdown(f'<span class="coverage-badge {css_class}">{text}</span>', unsafe_allow_html=True)
    else:
        st.caption(text)


def _render_coverage_badge(coverage: str | None, llm_used: bool) -> None:
    st.markdown("#### Knowledge Coverage")
    if coverage in COVERAGE_STYLES:
        _coverage_badge(coverage)
    elif not llm_used:
        st.caption("Not available — AI answering is not configured.")
    else:
        st.caption("The model did not state a Knowledge Coverage level.")


def _render_sources(sources: list[dict]) -> None:
    st.markdown("#### Sources from organizational memory")
    if not sources:
        st.info("I don't have enough relevant organizational memory to answer this reliably.")
        return
    for source in sources:
        metadata = source.get("metadata") or {}
        title = str(source.get("title") or metadata.get("title") or "(Untitled)")
        with st.expander(title):
            _render_memory_fields(metadata)
            distance = source.get("distance")
            if distance is not None:
                st.caption(f"Semantic distance: {distance:.4f}")


def render_related_tree(related_result: dict) -> None:
    """Render a connected-card 'tree' for a ``find_related_memories`` result."""
    related = related_result.get("related_memories") or []
    st.markdown("### Related Organizational Experience")
    if not related:
        st.info(related_result.get("note") or "No related organizational memory found yet.")
        return

    root = str(related_result.get("memory_title") or "(Untitled)")
    parts = ['<div class="mem-tree">']
    parts.append(f'<div class="tree-node tree-root">{html.escape(root)}</div>')
    parts.append('<div class="tree-stem"></div>')
    parts.append('<div class="tree-children">')
    for item in related:
        parts.append('<div class="tree-child">')
        parts.append('<div class="tree-connector"></div>')
        parts.append(
            f'<div class="tree-node">{html.escape(str(item.get("title") or "(Untitled)"))}'
            f'<span class="tree-sim">{item.get("similarity", 0.0):.2f}</span></div>'
        )
        parts.append(f'<div class="tree-rel">{html.escape(item.get("relationship") or "")}</div>')
        parts.append(f'<div class="tree-why">{html.escape(item.get("reason") or "")}</div>')
        parts.append("</div>")
    parts.append("</div></div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
    st.caption(
        "Similarity is cosine similarity (1.0 = identical). Relationship labels come from "
        "shared data in the memories (equipment codes, symptoms, tags), not from assumptions."
    )
    for item in related:
        with st.expander(f"Open: {item.get('title') or '(Untitled)'}", expanded=False):
            _render_memory_fields(item.get("metadata") or {})


def render_conflict_result(result: dict, show_clear: bool = False) -> None:
    """Render a conflict-analysis result (``src.conflict_service.analyze_conflicts``)."""
    pairs = result.get("pairs") or []
    if not pairs:
        if show_clear:
            st.caption("No potential recommendation conflicts among related memories.")
        return

    st.markdown("### ⚠️ Potential Knowledge Conflict")
    st.markdown(result.get("summary") or "")
    if result.get("evidence") == "confirmed":
        st.caption("AI-verified against the stored experience — yet MemoryOS does not decide which is correct.")
    else:
        st.caption("Candidate detected locally — human verification recommended.")

    for index, pair in enumerate(pairs, start=1):
        a = pair.get("memory_a") or {}
        b = pair.get("memory_b") or {}
        with st.container(border=True):
            st.markdown(f"**Memory {index * 2 - 1}:** {a.get('title') or '(Untitled)'}")
            st.markdown(f"_Recommendation:_ {a.get('recommendation') or '—'}")
            st.caption(
                f"{a.get('author_role') or 'Unknown role'} · {format_date(a.get('created_at') or '')}"
            )
            st.markdown("**vs.**")
            st.markdown(f"**Memory {index * 2}:** {b.get('title') or '(Untitled)'}")
            st.markdown(f"_Recommendation:_ {b.get('recommendation') or '—'}")
            st.caption(
                f"{b.get('author_role') or 'Unknown role'} · {format_date(b.get('created_at') or '')}"
            )
            if pair.get("reason"):
                st.caption(f"→ {pair['reason']}")
    st.markdown(
        "**Human verification recommended.** The system will not pick a winner, overwrite, "
        "or merge these memories — it only surfaces the disagreement."
    )


# ---------------------------------------------------------------------------
# Cached service wrappers (results are stable within a session unless the store changes)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, max_entries=64)
def _cached_conflicts(topic: str, store_count: int) -> dict:
    return analyze_conflicts(topic)


@st.cache_data(show_spinner=False, max_entries=128)
def _cached_related(memory_id: str, store_count: int, memory_title: str) -> dict:
    memories = get_service().list_memories()
    memory = next(
        (m for m in memories if str((m.get("metadata") or {}).get("id")) == memory_id),
        None,
    )
    if memory is None:
        return {
            "memory_id": memory_id,
            "memory_title": memory_title,
            "related_memories": [],
            "note": "This memory could not be found.",
        }
    return find_related_memories(memory)


@st.cache_data(show_spinner=False, max_entries=32)
def _cached_incident(incident: str, store_count: int) -> dict:
    return analyze_incident(incident)


def _store_count() -> int:
    return get_service().store.count()


def _memory_options() -> dict:
    memories = get_service().list_memories()
    return {
        f"{str((m.get('metadata') or {}).get('title') or m.get('id'))} · {(m.get('metadata') or {}).get('id')}": m
        for m in memories
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> str:
    """Render navigation + live library statistics, return the chosen page."""
    service = get_service()
    memories = service.list_memories()

    total = len(memories)
    categories = {str((m.get("metadata") or {}).get("category") or "").strip() for m in memories}
    categories.discard("")
    created_values = [str((m.get("metadata") or {}).get("created_at") or "") for m in memories]
    last_added = max(created_values) if created_values else ""

    with st.sidebar:
        st.markdown(f"# {APP_NAME}")
        st.caption(TAGLINE)
        st.divider()
        page = st.radio("Navigate", PAGES, key="current_page")
        st.divider()
        st.markdown("### Library")
        st.metric("Total Memories", total)
        st.metric("Categories", len(categories))
        st.metric("Last Added", format_date(last_added) if last_added else "—")
        st.divider()
        if not is_available():
            st.caption("AI answering is not configured (add `LLM_API_KEY` to `.env`). "
                       "The local memory engine is working.")
    return page


# ---------------------------------------------------------------------------
# Page 1 - Ask MemoryOS
# ---------------------------------------------------------------------------

def render_ask_page() -> None:
    st.header("Ask MemoryOS")
    st.subheader("Ask what your organization already knows.")

    if not is_available():
        st.info(
            "AI answering is not configured yet. The local memory engine is working — "
            "ask a question to test semantic retrieval. Add `LLM_API_KEY` to `.env` to "
            "enable full AI answers."
        )

    question = st.text_area(
        "What would you like to know?",
        placeholder=QUESTION_PLACEHOLDER,
        height=110,
        key="ask_question",
    )

    if st.button("Ask MemoryOS", type="primary", width="stretch"):
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            try:
                result = answer_question(question.strip())
                st.session_state["last_result"] = result
                st.session_state["last_question"] = question.strip()
            except Exception as exc:  # noqa: BLE001 - details go to the terminal only
                print(f"[MemoryOS] failed to generate an answer: {exc!r}")
                st.error("Memory retrieval worked, but the AI response could not be generated.")
                st.session_state.pop("last_result", None)

    result = st.session_state.get("last_result")
    if not result:
        return

    with st.container(border=True):
        st.markdown("### Result")
        st.markdown(result.get("answer", ""))

    _render_coverage_badge(result.get("knowledge_coverage"), bool(result.get("llm_used")))
    st.divider()
    _render_sources(result.get("sources") or [])

    question_used = st.session_state.get("last_question", "")
    if result.get("sources") and question_used:
        st.divider()
        try:
            conflict = _cached_conflicts(question_used, _store_count())
        except Exception as exc:  # noqa: BLE001
            print(f"[MemoryOS] conflict check failed: {exc!r}")
            st.caption("Conflict check could not be completed.")
        else:
            render_conflict_result(conflict, show_clear=True)


# ---------------------------------------------------------------------------
# Page 2 - Capture Memory
# ---------------------------------------------------------------------------

def render_capture_page() -> None:
    st.header("Capture Organizational Memory")
    st.caption("Preserve practical knowledge before it gets lost.")

    form_key = st.session_state.get("capture_form_key", "capture_form_0")
    with st.form(form_key):
        title = st.text_input("Title", placeholder="e.g. Hydraulic Press H-204 Overheating")
        left, right = st.columns(2)
        with left:
            author_role = st.text_input("Author role", placeholder="e.g. Senior Maintenance Technician")
        with right:
            category = st.selectbox("Category", CATEGORIES)
        situation = st.text_area("Situation / Context", placeholder="When and where does this knowledge apply?")
        experience = st.text_area("Experience / Observation", placeholder="What did you learn in practice?")
        recommendation = st.text_area("Recommended action", placeholder="What should someone do?")
        warnings = st.text_area("Warnings / Things to avoid", placeholder="Anything risky to watch out for?")
        tags = st.text_input("Tags (comma-separated)", placeholder="hydraulics, troubleshooting, h-204")
        submitted = st.form_submit_button("Save Memory", type="primary", width="stretch")

    if submitted:
        if not title.strip():
            st.error("A memory needs a title before it can be saved.")
        else:
            memory = Memory(
                title=title.strip(),
                author_role=author_role.strip(),
                category=category,
                situation=situation.strip(),
                experience=experience.strip(),
                recommendation=recommendation.strip(),
                warnings=warnings.strip(),
                tags=[t.strip() for t in tags.split(",") if t.strip()],
            )
            try:
                captured = get_service().capture_memory(memory)
            except Exception as exc:  # noqa: BLE001 - details go to the terminal only
                print(f"[MemoryOS] failed to save memory: {exc!r}")
                st.error("Could not save this memory. Please try again.")
            else:
                st.session_state["capture_success"] = f"Memory saved: {captured.title}"
                st.session_state["capture_form_key"] = f"capture_form_{uuid.uuid4().hex}"
                st.rerun()

    if st.session_state.get("capture_success"):
        st.success(st.session_state["capture_success"])
        st.session_state["capture_success"] = ""


# ---------------------------------------------------------------------------
# Page 3 - Memory Library
# ---------------------------------------------------------------------------

def render_library_page() -> None:
    st.header("Organizational Memory")
    st.caption("Structured human experience, not generic documents.")

    memories = get_service().list_memories()
    if not memories:
        st.info(
            "No memories stored yet. Head to **Capture Memory** in the sidebar to "
            "save the first piece of organizational knowledge."
        )
        return

    categories = sorted(
        {str((m.get("metadata") or {}).get("category") or "").strip() for m in memories},
    )
    categories = [c for c in categories if c]
    selected = st.selectbox("Filter by category", ["All"] + categories)

    shown = [
        m for m in memories
        if selected == "All" or str((m.get("metadata") or {}).get("category") or "") == selected
    ]
    st.caption(f"Showing {len(shown)} of {len(memories)} memories")

    for memory in shown:
        metadata = memory.get("metadata") or {}
        title = str(metadata.get("title") or memory.get("id") or "(Untitled)")
        with st.expander(title):
            _render_memory_fields(metadata, created=True)

    st.divider()
    st.markdown("### Inspect a memory")
    st.caption("See the connected experience and any conflicts for one selected memory.")
    options = _memory_options()
    if options:
        choice = st.selectbox("Choose a memory to inspect", list(options), key="inspect_memory")
        memory = options[choice]
        metadata = memory.get("metadata") or {}
        memory_id = str(metadata.get("id") or "")
        title = str(metadata.get("title") or "(Untitled)")

        with st.container(border=True):
            st.markdown(f"#### {title}")
            _render_memory_fields(metadata, created=True)

        try:
            related = _cached_related(memory_id, _store_count(), title)
        except Exception as exc:  # noqa: BLE001
            print(f"[MemoryOS] related-memory lookup failed: {exc!r}")
            st.caption("Related-memory lookup could not be completed.")
        else:
            render_related_tree(related)

        try:
            conflict = _cached_conflicts(title, _store_count())
        except Exception as exc:  # noqa: BLE001
            print(f"[MemoryOS] conflict check failed: {exc!r}")
            st.caption("Conflict check could not be completed.")
        else:
            render_conflict_result(conflict, show_clear=True)


# ---------------------------------------------------------------------------
# Page 4 - Incident Mode
# ---------------------------------------------------------------------------

def render_incident_page() -> None:
    st.header("🚨 Incident Mode")
    st.caption("Decision support for urgent operational problems, grounded in organizational memory.")
    st.markdown(
        "_Decision support only — MemoryOS does not operate equipment, stop machines, or "
        "contact anyone. Follow site safety procedures and the judgment of qualified personnel._"
    )

    incident = st.text_area(
        "Describe the incident",
        placeholder=INCIDENT_PLACEHOLDER,
        height=120,
        key="incident_input",
    )

    if st.button("Analyze Incident", type="primary", width="stretch"):
        if not incident.strip():
            st.warning("Describe the incident first, e.g. 'H-204 temperature is rapidly increasing.'")
        else:
            try:
                st.session_state["incident_result"] = _cached_incident(incident.strip(), _store_count())
            except Exception as exc:  # noqa: BLE001
                print(f"[MemoryOS] incident analysis failed: {exc!r}")
                st.error("Incident analysis could not be generated.")
                st.session_state.pop("incident_result", None)

    result = st.session_state.get("incident_result")
    if not result:
        if is_available():
            st.caption("Example: **H-204 temperature is rapidly increasing.** ")
        return

    if result.get("insufficient"):
        st.info(
            "The organization's stored memory does **not** contain relevant experience for this "
            "incident yet. See the coverage badge below — capture a memory on this topic after "
            "the event so future incidents get grounded support."
        )

    with st.container(border=True):
        st.markdown("### INCIDENT")
        st.markdown(result.get("incident", ""))

    with st.container(border=True):
        st.markdown("### Immediate Considerations")
        considerations = result.get("immediate_considerations") or []
        if considerations:
            for index, item in enumerate(considerations, start=1):
                st.markdown(f"**{index}.** {item}")
        else:
            st.caption("None — no stored recommendations matched this incident.")

    with st.container(border=True):
        st.markdown("### Relevant Previous Incidents")
        incidents = result.get("relevant_previous_incidents") or []
        if incidents:
            for item in incidents:
                st.markdown(f"- {item.get('title') or '(Untitled)'}")
        else:
            st.caption("None — no stored incidents matched.")

    with st.container(border=True):
        st.markdown("### ⚠️ Warnings")
        warnings = result.get("warnings") or []
        if warnings:
            for item in warnings:
                st.markdown(f"- {item}")
        else:
            st.caption("None recorded in the retrieved memories.")

    st.markdown("### Relevant Experts")
    experts = result.get("relevant_experts") or []
    if experts:
        chips = " ".join(f'<span class="expert-chip">{html.escape(e)}</span>' for e in experts)
        st.markdown(chips, unsafe_allow_html=True)
    else:
        st.caption("Unknown — no author roles in the retrieved memories.")

    st.divider()
    _render_coverage_badge(result.get("knowledge_coverage"), bool(result.get("llm_used")))
    st.divider()

    with st.container(border=True):
        label = "AI-Generated Synthesis (grounded in stored experience)" if result.get("llm_used") else "Local Synthesis (AI not used)"
        st.markdown(f"### {label}")
        st.markdown(result.get("summary", ""))

    st.divider()
    _render_sources(result.get("sources") or [])
    st.caption(result.get("disclaimer") or "")


# ---------------------------------------------------------------------------
# Page 5 - Knowledge Map / Related Memories
# ---------------------------------------------------------------------------

def render_knowledge_map_page() -> None:
    st.header("Knowledge Map")
    st.caption("Stored memories connected by semantic similarity — an organizational memory graph.")

    memories = get_service().list_memories()
    if not memories:
        st.info("No memories stored yet. Capture or seed memories to build the map.")
        return

    options = _memory_options()
    choice = st.selectbox("Start the map from this memory", list(options), key="map_root")
    memory = options[choice]
    metadata = memory.get("metadata") or {}
    memory_id = str(metadata.get("id") or "")
    title = str(metadata.get("title") or "(Untitled)")

    st.caption(
        f"{len(memories)} memories stored. Each node below is a real stored memory; "
        "links are drawn when the semantic distance stays under the related-memory threshold."
    )

    try:
        related = _cached_related(memory_id, _store_count(), title)
    except Exception as exc:  # noqa: BLE001
        print(f"[MemoryOS] related-memory lookup failed: {exc!r}")
        st.error("Could not build the map for this memory.")
        return

    render_related_tree(related)

    st.divider()
    st.markdown("### Explore second-level connections")
    children = (related.get("related_memories") or [])[:5]
    if not children:
        st.caption("No related memories to expand.")
    for child in children:
        child_id = str(child.get("id") or "")
        child_title = str(child.get("title") or "(Untitled)")
        with st.expander(f"Explore further: {child_title}", expanded=False):
            try:
                inner = _cached_related(child_id, _store_count(), child_title)
            except Exception as exc:  # noqa: BLE001
                print(f"[MemoryOS] related-memory lookup failed: {exc!r}")
                st.caption("Lookup failed.")
            else:
                render_related_tree(inner)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title=APP_NAME,
        page_icon=":brain:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    page = render_sidebar()
    if page == "Capture Memory":
        render_capture_page()
    elif page == "Memory Library":
        render_library_page()
    elif page == "Incident Mode":
        render_incident_page()
    elif page == "Knowledge Map":
        render_knowledge_map_page()
    else:
        render_ask_page()


main()