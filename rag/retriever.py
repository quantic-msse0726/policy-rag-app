"""
Chroma-based retrieval for policy documents.
"""

import os
import re
from pathlib import Path

import chromadb
from openai import OpenAI

# Default paths
DEFAULT_PERSIST_DIR = Path(__file__).resolve().parent.parent / "data" / "index"
COLLECTION_NAME = "policies"

# Snippet length
SNIPPET_CHARS = 300
EMBED_MODEL = "text-embedding-3-small"


def _clean_whitespace(text: str) -> str:
    """Collapse whitespace to single spaces and strip."""
    return re.sub(r"\s+", " ", text).strip()


def _make_snippet(text: str, max_chars: int = SNIPPET_CHARS) -> str:
    """Extract first max_chars of text, cleaned. Truncate at word boundary if possible."""
    cleaned = _clean_whitespace(text)
    if len(cleaned) <= max_chars:
        return cleaned
    trunc = cleaned[:max_chars]
    if " " in trunc:
        return trunc.rsplit(" ", 1)[0] + "..."
    return trunc + "..."


def _embed_query(query: str) -> list[float]:
    """Embed query using OpenAI (matches ingest model)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set for retrieval")
    client = OpenAI()
    resp = client.embeddings.create(model=EMBED_MODEL, input=[query])
    return resp.data[0].embedding


def get_chroma_collection(
    persist_dir: str | Path = DEFAULT_PERSIST_DIR,
    name: str = COLLECTION_NAME,
):
    """Get the Chroma collection for policy documents (no embedding fn; we provide embeddings)."""
    client = chromadb.PersistentClient(path=str(persist_dir))
    return client.get_collection(name=name)


def retrieve(
    query: str,
    k: int = 5,
    persist_dir: str | Path = DEFAULT_PERSIST_DIR,
    collection_name: str = COLLECTION_NAME,
) -> list[dict]:
    """
    Retrieve top-k chunks by similarity.
    Returns list of dicts: doc_id, title, section, chunk_id, snippet, text, distance.
    """
    collection = get_chroma_collection(persist_dir, collection_name)
    query_embedding = _embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    # Chroma returns column-major: ids[0], documents[0], metadatas[0], distances[0]
    ids = results["ids"][0] if results["ids"] else []
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    dists = results["distances"][0] if results["distances"] else []

    out = []
    for i, (id_, text, meta, dist) in enumerate(zip(ids, docs, metas, dists)):
        text = text or ""
        meta = meta or {}
        out.append({
            "doc_id": meta.get("doc_id", ""),
            "title": meta.get("title", ""),
            "section": meta.get("section") or None,
            "chunk_id": meta.get("chunk_id", 0),
            "snippet": _make_snippet(text),
            "text": text,
            "distance": float(dist) if dist is not None else 0.0,
        })
    return out


def should_refuse(results: list[dict]) -> tuple[bool, str]:
    """
    Refuse if retrieval quality is insufficient.
    Returns (True, reason) to refuse, or (False, "").
    """
    if not results:
        return True, "No relevant policy documents found."
    if len(results) < 2:
        return True, "Insufficient context to answer reliably."
    combined_len = sum(len(r.get("text", "")) for r in results)
    if combined_len < 800:
        return True, "Retrieved content too short to answer reliably."
    return False, ""
