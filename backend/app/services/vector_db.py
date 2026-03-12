"""Optional Pinecone vector DB service for calendar event knowledge base.

All functions are no-ops when PINECONE_API_KEY is not configured so the rest
of the application works without Pinecone.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_pc = None
_embedder = None
_index = None


def _is_enabled() -> bool:
    return bool(settings.PINECONE_API_KEY)


def _ensure_initialized() -> None:
    global _pc, _embedder, _index
    if _pc is not None:
        return
    if not _is_enabled():
        return

    from pinecone import Pinecone
    from sentence_transformers import SentenceTransformer

    _pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    _embedder = SentenceTransformer("intfloat/e5-large-v2")
    _index = _pc.Index(settings.PINECONE_INDEX_NAME)


def _embed(text: str) -> list[float]:
    _ensure_initialized()
    if _embedder is None:
        return []
    return _embedder.encode(text).tolist()


# ── Public API ────────────────────────────────────────────────────────────────

def upsert_event(namespace: str, event_id: str, text: str, metadata: dict[str, Any]) -> None:
    """Upsert a single event vector into Pinecone under *namespace*."""
    if not _is_enabled():
        return
    try:
        _ensure_initialized()
        vector = _embed(text)
        if _index and vector:
            _index.upsert(
                vectors=[{"id": event_id, "values": vector, "metadata": metadata}],
                namespace=namespace,
            )
    except Exception as exc:
        logger.warning("Vector upsert failed: %s", exc)


def delete_event(namespace: str, event_id: str) -> None:
    """Delete a vector from Pinecone."""
    if not _is_enabled():
        return
    try:
        _ensure_initialized()
        if _index:
            _index.delete(ids=[event_id], namespace=namespace)
    except Exception as exc:
        logger.warning("Vector delete failed: %s", exc)


def query_similar(namespace: str, query_text: str, top_k: int = 10) -> list[str]:
    """Return up to *top_k* similar event texts from the knowledge base.

    Returns a plain list of text strings (empty list if disabled or on error).
    """
    if not _is_enabled():
        return []
    try:
        _ensure_initialized()
        vector = _embed(query_text)
        if not _index or not vector:
            return []
        results = _index.query(
            vector=vector, top_k=top_k, include_metadata=True, namespace=namespace
        )
        texts: list[str] = []
        for match in getattr(results, "matches", []):
            score = getattr(match, "score", 0)
            metadata = getattr(match, "metadata", {})
            if score > 0.5 and metadata.get("text"):
                texts.append(metadata["text"])
        return texts
    except Exception as exc:
        logger.warning("Vector query failed: %s", exc)
        return []
