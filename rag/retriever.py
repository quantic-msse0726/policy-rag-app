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

# Retrieval
DEFAULT_K = 6
EVIDENCE_MAX_CHARS = 350
EVIDENCE_MAX_SENTENCES = 2
EMBED_MODEL = "text-embedding-3-small"

# Refusal threshold: best (lowest) distance above this = weak evidence, refuse
DISTANCE_REFUSE_THRESHOLD = 1.2

# Lightweight stopwords for keyword extraction
STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can", "what", "which", "who", "whom",
    "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "and", "or", "but", "if", "then", "else", "when", "at", "by", "for", "with",
    "about", "into", "through", "during", "from", "to", "of", "in", "on",
})


def _clean_whitespace(text: str) -> str:
    """Collapse whitespace to single spaces and strip."""
    return re.sub(r"\s+", " ", text).strip()


def _extract_keywords(question: str) -> set[str]:
    """Extract keywords: lowercase, length >= 4, not stopwords."""
    words = re.findall(r"\b\w+\b", question.lower())
    return {w for w in words if len(w) >= 4 and w not in STOPWORDS}


def _keyword_score(text: str, keywords: set[str]) -> int:
    """Count keyword hits in text (case-insensitive)."""
    if not keywords:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


# Rule-like terms for quote scoring (policy language)
QUOTE_RULE_TERMS = ("must", "required", "prohibited", "up to", "within", "days", "approval")


RULE_TERMS = ("up to", "within", "must", "required", "prohibited",
              "may", "cannot", "days", "hours", "approval")


def _rule_bonus(text: str) -> int:
    """Bonus points for digits and rule-like keywords (policy language)."""
    text_lower = text.lower()
    bonus = 1 if re.search(r"\d", text) else 0
    bonus += sum(1 for term in RULE_TERMS if term in text_lower)
    return bonus


def split_sentences(text: str) -> list[str]:
    """Split on [.!?] followed by space, or any newline. Strip, filter out short (< 20 chars)."""
    if not text:
        return []
    # Use lookbehind to keep punctuation and split on whitespace following it
    # Also split on any newlines
    raw = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences = [s.strip() for s in raw if s.strip()]
    return [s for s in sentences if len(s) >= 20]


def _quote_span_score(span: str) -> int:
    """Score a span for digits/policy keywords (used to prefer certain spans)."""
    score = 1 if re.search(r"\d", span) else 0
    span_lower = span.lower()
    score += sum(1 for t in QUOTE_RULE_TERMS if t in span_lower)
    return score


def extract_evidence_sentences(
    chunk_text: str,
    question: str,
    max_sentences: int = EVIDENCE_MAX_SENTENCES,
    max_chars: int = EVIDENCE_MAX_CHARS,
) -> str:
    """
    Extract evidence sentences: choose sentences with highest keyword hit count.
    Return joined sentences as snippet (<= max_chars).
    """
    keywords = _extract_keywords(question)
    # Better split: same as split_sentences but keep punctuation
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", chunk_text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    if not sentences:
        return _clean_whitespace(chunk_text)[:max_chars]

    # Score each sentence by keyword hits + rule bonus (digits, policy keywords)
    scored = [(s, _keyword_score(s, keywords) + _rule_bonus(s)) for s in sentences]
    # Sort by score desc, then by length (prefer shorter for diversity)
    scored.sort(key=lambda x: (-x[1], len(x[0])))

    # Take top max_sentences
    chosen = [s for s, _ in scored[:max_sentences]]
    joined = ". ".join(chosen)
    if not joined.endswith(".") and not joined.endswith("!") and not joined.endswith("?"):
        joined += "."
    if len(joined) > max_chars:
        trunc = joined[:max_chars]
        joined = (trunc.rsplit(" ", 1)[0] + "...") if " " in trunc else trunc + "..."
    return joined


def pick_verbatim_quote(
    text: str,
    question_keywords: set[str] | None = None,
    min_words: int = 5,
    max_words: int = 15,
) -> str:
    """
    Pick a verbatim quote from text. Returns "" if nothing suitable.
    Ensures the returned string is a literal substring of the input text.
    """
    if not text or not text.strip():
        return ""

    sentences = split_sentences(text)
    if not sentences:
        return ""

    keywords = question_keywords or set()
    scored = [
        (s, _keyword_score(s, keywords) + _rule_bonus(s))
        for s in sentences
    ]
    # Sort by score desc, then by length (prefer medium length around 60 chars)
    scored.sort(key=lambda x: (-x[1], abs(len(x[0]) - 60)))
    best_sentence = scored[0][0]

    # Find all words in the original sentence to preserve exact characters
    words = list(re.finditer(r"\b\w+\b", best_sentence))
    if len(words) < min_words:
        return ""

    best_spans = []
    for start in range(len(words)):
        max_n = min(max_words, len(words) - start)
        for n in range(min_words, max_n + 1):
            end_idx = start + n - 1
            if end_idx >= len(words):
                continue
            first = words[start]
            last = words[end_idx]
            # Take the slice from the original sentence to ensure literal substring
            span = best_sentence[first.start() : last.end()]
            best_spans.append((span, _quote_span_score(span)))

    if not best_spans:
        return ""

    # Sort by score desc, then by length (prefer longer within max_words)
    best_spans.sort(key=lambda x: (-x[1], -len(x[0])))
    return best_spans[0][0].strip()


def _embed_query(query: str) -> list[float]:
    """Embed query using OpenAI (matches ingest model)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set for retrieval")
    client = OpenAI()
    resp = client.embeddings.create(model=EMBED_MODEL, input=[query])
    return resp.data[0].embedding


def index_ready(persist_dir: str | Path = DEFAULT_PERSIST_DIR) -> bool:
    """True if the Chroma index directory exists (index has been built)."""
    return Path(persist_dir).exists()


def get_chroma_collection(
    persist_dir: str | Path = DEFAULT_PERSIST_DIR,
    name: str = COLLECTION_NAME,
):
    """Get the Chroma collection for policy documents (no embedding fn; we provide embeddings)."""
    client = chromadb.PersistentClient(path=str(persist_dir))
    return client.get_collection(name=name)


def _rerank_by_keywords(results: list[dict], question: str) -> list[dict]:
    """Rerank by keyword_score desc, then distance asc."""
    keywords = _extract_keywords(question)
    for r in results:
        r["_keyword_score"] = _keyword_score(r.get("text", ""), keywords)
    results.sort(key=lambda x: (-x["_keyword_score"], x.get("distance", 0)))
    for r in results:
        r.pop("_keyword_score", None)
    return results


def retrieve(
    query: str,
    k: int = DEFAULT_K,
    persist_dir: str | Path = DEFAULT_PERSIST_DIR,
    collection_name: str = COLLECTION_NAME,
) -> list[dict]:
    """
    Retrieve top-k chunks by similarity, rerank by keywords, return with evidence snippets.
    Returns list of dicts: doc_id, title, section, chunk_id, snippet, text, distance.
    """
    collection = get_chroma_collection(persist_dir, collection_name)
    query_embedding = _embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    ids = results["ids"][0] if results["ids"] else []
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    dists = results["distances"][0] if results["distances"] else []

    out = []
    for id_, text, meta, dist in zip(ids, docs, metas, dists):
        text = text or ""
        meta = meta or {}
        out.append({
            "doc_id": meta.get("doc_id", ""),
            "title": meta.get("title", ""),
            "section": meta.get("section") or None,
            "chunk_id": meta.get("chunk_id", 0),
            "snippet": extract_evidence_sentences(text, query),
            "text": text,
            "distance": float(dist) if dist is not None else 0.0,
        })

    out = _rerank_by_keywords(out, query)
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
    best_distance = min(r.get("distance", float("inf")) for r in results)
    if best_distance > DISTANCE_REFUSE_THRESHOLD:
        return True, "No sufficiently relevant policy documents found."
    return False, ""
