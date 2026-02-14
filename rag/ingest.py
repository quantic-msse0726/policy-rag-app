"""
Policy document ingestion pipeline: load, chunk, embed, and persist to Chroma.
Run: python -m rag.ingest [--rebuild] [--chunk-tokens N] [--overlap-tokens N]
"""

import argparse
import logging
import os
import re
import shutil
from pathlib import Path

import chromadb
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import tiktoken

# Default paths
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "policies"
INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "index"
COLLECTION_NAME = "policies"

# Chunking defaults
CHUNK_TOKENS = 300
OVERLAP_TOKENS = 60

# File filtering
ALLOWED_EXTENSIONS = (".md", ".txt", ".html", ".htm", ".pdf")
EXCLUDED_FILENAMES = frozenset({"README.md", "readme.md"})

# Thresholds
MIN_TEXT_CHARS = 500

# Embedding config
EMBED_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100

# Tokenizer (cached)
_tiktoken_enc = None


def _get_encoder():
    """Lazy-load tiktoken encoder."""
    global _tiktoken_enc
    if _tiktoken_enc is None:
        _tiktoken_enc = tiktoken.get_encoding("cl100k_base")
    return _tiktoken_enc


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    return len(_get_encoder().encode(text))


def _strip_html(html: str) -> str:
    """Extract plain text from HTML using BeautifulSoup. Remove script/style, collapse whitespace."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_documents(data_dir: Path) -> tuple[list[dict], int, int]:
    """
    Load .md, .txt, .html, and .pdf files from data_dir.
    Skips hidden files/folders and excluded filenames.
    Returns (docs, discovered_count, ingested_count).
    """
    data_dir = Path(data_dir)
    docs = []
    discovered = 0

    for path in sorted(data_dir.iterdir()):
        if path.name.startswith("."):
            continue
        if not path.is_file():
            continue
        if path.suffix not in ALLOWED_EXTENSIONS:
            continue
        discovered += 1
        if path.name in EXCLUDED_FILENAMES:
            continue

        if path.suffix in (".md", ".txt"):
            text = path.read_text(encoding="utf-8")
            docs.append({"filename": path.name, "text": text})
        elif path.suffix in (".html", ".htm"):
            html = path.read_text(encoding="utf-8")
            text = _strip_html(html)
            docs.append({"filename": path.name, "text": text})
        elif path.suffix == ".pdf":
            reader = PdfReader(path)
            page_texts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    page_texts.append(extracted)
            text = "\n".join(page_texts)
            docs.append({"filename": path.name, "text": text})

    return docs, discovered, len(docs)


def chunk_text(
    text: str,
    chunk_tokens: int = CHUNK_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
) -> list[str]:
    """Split text into token-based chunks with overlap."""
    enc = _get_encoder()
    tokens = enc.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = start + chunk_tokens
        chunk_tok = tokens[start:end]
        chunk_str = enc.decode(chunk_tok)
        chunks.append(chunk_str)
        start = end - overlap_tokens
        if start >= len(tokens):
            break

    return chunks


def _first_heading(text: str) -> str | None:
    """Extract the first Markdown heading from text."""
    m = re.search(r"^#+\s+(.+)$", text.strip(), re.MULTILINE)
    return m.group(1).strip() if m else None


def _section_in_chunk(chunk_text: str) -> str | None:
    """Extract the last heading in a chunk (section context)."""
    matches = list(re.finditer(r"^#+\s+(.+)$", chunk_text, re.MULTILINE))
    return matches[-1].group(1).strip() if matches else None


def build_chunks(
    docs: list[dict],
    chunk_tokens: int = CHUNK_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
) -> tuple[list[dict], list[str]]:
    """
    Build chunk dicts with doc_id, title, section, text.
    Returns (chunks, warnings).
    """
    chunks = []
    warnings = []
    total_chars = 0
    total_tokens = 0
    total_chunks = 0

    for doc in docs:
        filename = doc["filename"]
        text = doc["text"]
        title = _first_heading(text) or filename

        extracted_chars = len(text)
        extracted_tokens = count_tokens(text)
        text_chunks = chunk_text(text, chunk_tokens=chunk_tokens, overlap_tokens=overlap_tokens)
        chunks_created = len(text_chunks)

        total_chars += extracted_chars
        total_tokens += extracted_tokens
        total_chunks += chunks_created

        if extracted_chars < MIN_TEXT_CHARS:
            warnings.append(f"WARNING: very little text extracted from {filename}")

        logging.info(
            f"  {filename}: {extracted_chars} chars, {extracted_tokens} tokens, "
            f"{chunks_created} chunks"
        )

        for i, chunk_str in enumerate(text_chunks):
            section = _section_in_chunk(chunk_str)
            chunks.append({
                "doc_id": filename,
                "title": title,
                "section": section,
                "text": chunk_str,
                "chunk_id": i,
            })

    return chunks, warnings, total_chars, total_tokens, total_chunks


def embed_chunks(chunks: list[dict]) -> list[list[float]]:
    """Get OpenAI embeddings for chunk texts. Returns list of embedding vectors."""
    client = OpenAI()
    texts = [c["text"] for c in chunks]
    embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        for item in resp.data:
            embeddings.append(item.embedding)

    return embeddings


def persist_to_chroma(
    chunks: list[dict],
    embeddings: list[list[float]],
    index_dir: Path,
) -> None:
    """Persist chunks and embeddings to Chroma at index_dir."""
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(index_dir))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    ids = [f"{c['doc_id']}:{c['chunk_id']}" for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "doc_id": c["doc_id"],
            "title": c["title"],
            "section": c["section"] if c["section"] is not None else "",
            "chunk_id": c["chunk_id"],
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )


def run(
    rebuild: bool = False,
    chunk_tokens: int = CHUNK_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
) -> None:
    """Run the full ingestion pipeline."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    load_dotenv()

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY must be set in .env")

    if rebuild and INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
        logging.info(f"Removed existing index at {INDEX_DIR}")

    docs, discovered, ingested = load_documents(DATA_DIR)
    if not docs:
        raise SystemExit(f"No documents found in {DATA_DIR}")

    logging.info(f"Discovered {discovered} files")
    logging.info(f"Ingested {ingested} documents")
    logging.info("Per-document stats:")
    chunks, warnings, total_chars, total_tokens, total_chunks = build_chunks(
        docs,
        chunk_tokens=chunk_tokens,
        overlap_tokens=overlap_tokens,
    )
    logging.info(f"Total tokens: {total_tokens:,}")
    logging.info(f"Built {len(chunks)} chunks")

    for w in warnings:
        logging.warning(w)

    logging.info("Embedding chunks...")
    embeddings = embed_chunks(chunks)

    logging.info(f"Persisting to {INDEX_DIR}...")
    persist_to_chroma(chunks, embeddings, INDEX_DIR)
    logging.info("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest policy documents into Chroma.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete existing index before indexing",
    )
    parser.add_argument(
        "--chunk-tokens",
        type=int,
        default=CHUNK_TOKENS,
        help=f"Target tokens per chunk (default: {CHUNK_TOKENS})",
    )
    parser.add_argument(
        "--overlap-tokens",
        type=int,
        default=OVERLAP_TOKENS,
        help=f"Overlap between chunks in tokens (default: {OVERLAP_TOKENS})",
    )
    args = parser.parse_args()
    run(
        rebuild=args.rebuild,
        chunk_tokens=args.chunk_tokens,
        overlap_tokens=args.overlap_tokens,
    )


if __name__ == "__main__":
    main()
