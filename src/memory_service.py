"""Service layer for capturing and retrieving organizational memories.

Independent of Streamlit. Pure Python domain objects plus local embeddings
and ChromaDB persistence.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.embeddings import embed_text
from src.vector_store import VectorStore

REQUIRED_FIELDS = ("title", "situation")


@dataclass
class Memory:
    """A single piece of structured organizational knowledge."""

    title: str = ""
    situation: str = ""
    experience: str = ""
    recommendation: str = ""
    warnings: str = ""
    author_role: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    id: str = ""
    created_at: str = ""


class MemoryService:
    """Wraps capture + semantic retrieval of memories."""

    def __init__(self, store: VectorStore | None = None) -> None:
        self.store = store or VectorStore()

    def capture_memory(self, memory: Memory) -> Memory:
        """Validate, key, embed, and store a memory. Mutates and returns it."""
        self._validate(memory)
        if not memory.id:
            memory.id = uuid.uuid4().hex
        if not memory.created_at:
            memory.created_at = datetime.now(timezone.utc).isoformat()
        searchable_text = self._searchable_text(memory)
        embedding = embed_text(searchable_text)
        self.store.add_memory(
            memory_id=memory.id,
            embedding=embedding,
            document=searchable_text,
            metadata=self._metadata(memory),
        )
        return memory

    def retrieve_memories(self, query: str, top_k: int = 5) -> list[dict]:
        """Embed ``query`` and return the most semantically similar memories."""
        if not query or not query.strip():
            raise ValueError("Query must not be empty")
        query_embedding = embed_text(query)
        return self.store.search(query_embedding, top_k=top_k)

    def list_memories(self) -> list[dict]:
        """Return all stored memories, most recently created first."""
        memories = self.store.get_all()
        memories.sort(
            key=lambda m: (m.get("metadata") or {}).get("created_at", ""),
            reverse=True,
        )
        return memories

    @staticmethod
    def _validate(memory: Memory) -> None:
        missing = [f for f in REQUIRED_FIELDS if not str(getattr(memory, f) or "").strip()]
        if missing:
            raise ValueError(f"Memory missing required fields: {', '.join(missing)}")

    @staticmethod
    def _searchable_text(memory: Memory) -> str:
        parts = [
            memory.title,
            memory.situation,
            memory.experience,
            memory.recommendation,
            memory.warnings,
            " ".join(memory.tags),
        ]
        return "\n".join(p for p in parts if p and str(p).strip())

    @staticmethod
    def _metadata(memory: Memory) -> dict:
        return {
            "id": memory.id,
            "title": memory.title or "",
            "author_role": memory.author_role or "",
            "category": memory.category or "",
            "situation": memory.situation or "",
            "experience": memory.experience or "",
            "recommendation": memory.recommendation or "",
            "warnings": memory.warnings or "",
            "tags": ", ".join(memory.tags or []),
            "created_at": memory.created_at or "",
        }


_service: MemoryService | None = None


def get_service() -> MemoryService:
    """Return a lazily created default MemoryService singleton."""
    global _service
    if _service is None:
        _service = MemoryService()
    return _service


def capture_memory(memory: Memory) -> Memory:
    """Capture a memory via the default service."""
    return get_service().capture_memory(memory)


def retrieve_memories(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve memories semantically similar to ``query``."""
    return get_service().retrieve_memories(query, top_k=top_k)