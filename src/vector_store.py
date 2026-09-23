"""ChromaDB-backed vector store for MemoryOS memories.

Persists under ``data/chroma/`` and uses a single collection. Embeddings are
supplied explicitly (never computed by Chroma) so the embedding model is
consistent and controlled by the application.
"""

import os

import chromadb
from chromadb.config import Settings

DEFAULT_PERSIST_DIR = os.path.join("data", "chroma")
COLLECTION_NAME = "organizational_memories"

_SEARCH_INCLUDE = ["documents", "metadatas", "distances"]


class VectorStore:
    """Small wrapper around a persistent ChromaDB collection."""

    def __init__(self, persist_dir: str | None = None, collection_name: str = COLLECTION_NAME) -> None:
        self.persist_dir = persist_dir or DEFAULT_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.collection_name = collection_name

    def add_memory(self, memory_id: str, embedding: list[float], document: str, metadata: dict) -> None:
        """Upsert a single memory with its precomputed embedding."""
        self._collection.upsert(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
        )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Return the top ``top_k`` memories closest to ``query_embedding``."""
        count = self._collection.count()
        if count == 0:
            return []
        limit = min(max(top_k, 1), count)
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=list(_SEARCH_INCLUDE),
        )
        ids = result.get("ids", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        documents = result.get("documents", [[]])[0]

        items = []
        for memory_id, metadata, distance, document in zip(ids, metadatas, distances, documents):
            metadata = metadata or {}
            items.append(
                {
                    "id": memory_id,
                    "metadata": metadata,
                    "title": metadata.get("title", ""),
                    "distance": distance,
                    "content": document,
                }
            )
        return items

    def count(self) -> int:
        """Return the number of memories stored."""
        return self._collection.count()

    def get_all(self) -> list[dict]:
        """Return every stored memory, without embeddings."""
        result = self._collection.get(include=["documents", "metadatas"])
        items = []
        for memory_id, metadata, document in zip(
            result.get("ids", []),
            result.get("metadatas", []),
            result.get("documents", []),
        ):
            metadata = metadata or {}
            items.append(
                {
                    "id": memory_id,
                    "metadata": metadata,
                    "title": metadata.get("title", ""),
                    "content": document,
                }
            )
        return items

    def clear(self) -> None:
        """Delete all memories from the collection."""
        ids = self._collection.get()["ids"]
        if ids:
            self._collection.delete(ids=ids)