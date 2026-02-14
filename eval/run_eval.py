"""
Evaluation runner for Policy RAG /chat endpoint.
Run: python -m eval.run_eval
Requires: server running at http://127.0.0.1:8000
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests

# Paths
EVAL_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = EVAL_DIR / "questions.jsonl"
RESULTS_PATH = EVAL_DIR / "results.jsonl"
CHAT_URL = "http://127.0.0.1:8000/chat"

# Regex for quoted phrases in answers (standard double quotes only)
QUOTED_PHRASE_RE = re.compile(r'"([^"]+)"')


def normalize_ws(s: str) -> str:
    """Collapse whitespace to single spaces and strip."""
    return re.sub(r"\s+", " ", s).strip()


def _strip_trailing_punct(s: str) -> str:
    """Strip trailing punctuation from both ends."""
    return s.strip(".,;:!?)\"'")


def extract_cited_indices(answer_text: str) -> list[int]:
    """Extract bracketed citation markers (e.g. [1], [2]). Returns sorted unique list."""
    matches = re.findall(r"\[(\d+)\]", answer_text)
    return sorted({int(m) for m in matches})


def load_questions() -> list[dict]:
    """Load questions from JSONL."""
    questions = []
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


def call_chat(question: str) -> dict:
    """Call the /chat endpoint. Raises on connection error."""
    try:
        resp = requests.post(
            CHAT_URL,
            json={"question": question},
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError as e:
        raise SystemExit(
            f"Error: Cannot connect to server at {CHAT_URL}. "
            "Ensure the server is running: uvicorn app.main:app --reload"
        ) from e
    except requests.exceptions.RequestException as e:
        raise SystemExit(f"Error calling /chat: {e}") from e


def _word_count(text: str) -> int:
    """Count words (length >= 1)."""
    return len(re.findall(r"\b\w+\b", text))


def score_answerable(result: dict) -> tuple[bool, bool]:
    """Score answerable question. Returns (grounded_ok, citation_ok)."""
    answer = result.get("answer", "")
    citations = result.get("citations", [])
    snippets = result.get("snippets", [])

    cited = extract_cited_indices(answer)
    has_citations = len(citations) > 0
    has_bracket_citations = len(cited) > 0
    grounded_ok = has_citations and has_bracket_citations

    # citation_ok: grounded_ok AND at least one quoted phrase is exact substring in source
    quoted_phrases = QUOTED_PHRASE_RE.findall(answer)
    citation_ok = False
    if grounded_ok and quoted_phrases:
        sources = []
        for c in citations:
            if isinstance(c, dict):
                t = c.get("text") or c.get("snippet")
            else:
                t = getattr(c, "text", None) or getattr(c, "snippet", "")
            if t:
                sources.append(t)
        if not sources:
            sources = snippets
        for phrase in quoted_phrases:
            norm = _strip_trailing_punct(normalize_ws(phrase))
            if len(norm) >= 20 or _word_count(norm) >= 5:
                norm_srcs = [normalize_ws(src) for src in sources]
                for norm_src in norm_srcs:
                    if norm.lower() in norm_src.lower():
                        citation_ok = True
                        break
            if citation_ok:
                break

    return grounded_ok, citation_ok


def score_unanswerable(result: dict) -> tuple[bool, bool]:
    """Score unanswerable question. Returns (grounded_ok, citation_ok)."""
    answer = result.get("answer", "")
    citations = result.get("citations", [])
    snippets = result.get("snippets", [])

    citations_empty = len(citations) == 0
    snippets_empty = len(snippets) == 0
    has_refusal = "cannot" in answer.lower() or "can't" in answer.lower()

    ok = citations_empty and snippets_empty and has_refusal
    return ok, ok


def run_eval() -> None:
    """Run evaluation and append results to results.jsonl."""
    questions = load_questions()
    if not questions:
        raise SystemExit(f"No questions found in {QUESTIONS_PATH}")

    print(f"Evaluating {len(questions)} questions against {CHAT_URL}...")

    grounded_ok_count = 0
    citation_ok_count = 0
    latencies = []

    for i, q in enumerate(questions):
        qid = q.get("id", f"q{i+1:02d}")
        qtype = q.get("type", "answerable")
        question = q.get("question", "")

        result = call_chat(question)
        answer = result.get("answer", "")
        citations = result.get("citations", [])
        snippets = result.get("snippets", [])
        latency_ms = result.get("latency_ms", 0)

        if qtype == "answerable":
            grounded_ok, citation_ok = score_answerable(result)
        else:
            grounded_ok, citation_ok = score_unanswerable(result)

        if grounded_ok:
            grounded_ok_count += 1
        if citation_ok:
            citation_ok_count += 1
        latencies.append(latency_ms)

        citations_data = [
            {"doc_id": c.get("doc_id"), "title": c.get("title"),
             "section": c.get("section"), "snippet": c.get("snippet"),
             "text": c.get("text")}
            for c in citations
        ]
        record = {
            "id": qid,
            "type": qtype,
            "question": question,
            "answer": answer,
            "citations": citations_data,
            "snippets": snippets,
            "latency_ms": latency_ms,
            "grounded_ok": grounded_ok,
            "citation_ok": citation_ok,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with open(RESULTS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        status = "OK" if (grounded_ok and citation_ok) else ("WARN" if grounded_ok else "X")
        print(f"  [{i+1}/{len(questions)}] {qid} {status} ({latency_ms}ms)")

    # Metrics
    total = len(questions)
    groundedness_pct = (grounded_ok_count / total * 100) if total else 0
    citation_accuracy_pct = (citation_ok_count / total * 100) if total else 0
    latency_p50 = float(np.percentile(latencies, 50)) if latencies else 0
    latency_p95 = float(np.percentile(latencies, 95)) if latencies else 0

    # Report
    print("\n--- Report ---")
    print(f"Total questions: {total}")
    print(f"Groundedness: {groundedness_pct:.1f}%")
    print(f"Citation accuracy: {citation_accuracy_pct:.1f}%")
    print(f"Latency p50: {latency_p50:.0f} ms")
    print(f"Latency p95: {latency_p95:.0f} ms")
    print(f"\nResults appended to {RESULTS_PATH}")


def main() -> None:
    run_eval()


if __name__ == "__main__":
    main()
