"""
Test retrieval (uses OpenAI for query embedding; no Chat Completions call).
Run: python -m rag.query "your question"
"""

import sys

from dotenv import load_dotenv

load_dotenv()

from rag.retriever import retrieve

DISPLAY_CHARS = 200


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m rag.query \"your question\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    results = retrieve(question, k=5)

    print(f"Query: {question}\n")
    if results:
        best_dist = min(r.get("distance", float("inf")) for r in results)
        print(f"Retrieved {len(results)} chunks (best distance: {best_dist:.4f})\n")
    else:
        print(f"Retrieved 0 chunks\n")

    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        section = r.get("section") or "(no section)"
        text = r.get("text", "")
        distance = r.get("distance", 0)
        preview = text[:DISPLAY_CHARS] + "..." if len(text) > DISPLAY_CHARS else text
        preview = preview.replace("\n", " ").strip()
        print(f"--- Result {i} (distance={distance:.4f}) ---")
        print(f"Title: {title}")
        print(f"Section: {section}")
        print(f"Preview: {preview}\n")


if __name__ == "__main__":
    main()
