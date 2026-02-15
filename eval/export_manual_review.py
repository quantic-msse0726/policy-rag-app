"""
Export a deterministic manual-review CSV from eval/results.jsonl.

Run:
  python -m eval.export_manual_review --sample-size 10 --seed 42
"""

import argparse
import csv
import json
import random
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
RESULTS_PATH = EVAL_DIR / "results.jsonl"
OUT_PATH = EVAL_DIR / "manual_review_sample.csv"


def load_results(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def latest_by_question(rows: list[dict]) -> list[dict]:
    latest = {}
    for r in rows:
        qid = r.get("id", "")
        ts = r.get("timestamp", "")
        if qid not in latest or ts > latest[qid].get("timestamp", ""):
            latest[qid] = r
    return [latest[k] for k in sorted(latest.keys())]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export manual adjudication sample CSV.")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of rows to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    rows = load_results(RESULTS_PATH)
    if not rows:
        raise SystemExit(f"No rows found in {RESULTS_PATH}. Run eval first.")

    latest = latest_by_question(rows)
    random.seed(args.seed)
    sample_size = min(args.sample_size, len(latest))
    sample = random.sample(latest, sample_size)

    header = [
        "id",
        "type",
        "question",
        "answer",
        "citations_count",
        "auto_grounded_ok",
        "auto_citation_ok",
        "human_grounded_ok",
        "human_citation_ok",
        "notes",
    ]

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in sample:
            writer.writerow(
                [
                    r.get("id", ""),
                    r.get("type", ""),
                    r.get("question", ""),
                    r.get("answer", ""),
                    len(r.get("citations", [])),
                    r.get("grounded_ok", False),
                    r.get("citation_ok", False),
                    "",
                    "",
                    "",
                ]
            )

    print(f"Wrote {sample_size} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
