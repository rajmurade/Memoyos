"""Local semantic embeddings for MemoryOS.

Uses sentence-transformers with a lightweight model that runs fully on the
local machine. The model is loaded lazily on first use so importing this
module does not trigger a model download or load.
"""

import os
import threading

from sentence_transformers import SentenceTransformer

DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def get_embedding_model_name() -> str:
    """Return the name of the embedding model in use."""
    return DEFAULT_EMBEDDING_MODEL


def get_model() -> SentenceTransformer:
    """Return the shared embedding model, loading it once on first use."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a piece of text into a normalized vector of floats."""
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")
    encoding = get_model().encode(text.strip(), normalize_embeddings=True)
    return encoding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts into a list of normalized float vectors."""
    if not texts:
        raise ValueError("Cannot embed an empty list of texts")
    stripped = [t.strip() if t else "" for t in texts]
    if any(not t for t in stripped):
        raise ValueError("Cannot embed empty text in a batch")
    encoding = get_model().encode(stripped, normalize_embeddings=True)
    return [vec.tolist() for vec in encoding]