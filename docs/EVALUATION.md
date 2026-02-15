# Evaluation Metrics

This document defines success metrics for the Policy RAG application. Metrics cover both information quality and system performance.

## Information-Quality Metrics

### 1. Citation Accuracy

**Definition**: The proportion of answers where citations and quote attribution correctly support claims.

- **Metric**: `citation_accuracy = correct_answers_with_valid_citations / total_answers`
- **Evaluation**: For answerable questions, require at least one indexed quote `Quote: "..." [n]` that appears verbatim in cited source `n`.
- **Target**: >= 95% citation accuracy on held-out policy Q&A.

### 2. Groundedness

**Definition**: The extent to which answers are supported by retrieved context without hallucination.

- **Metric**: Binary per response (`grounded_ok` true/false), aggregated as a percentage.
- **Evaluation**:
  - Answerable: citation markers present and aligned with returned citations.
  - Unanswerable: refusal with empty citations/snippets.
- **Target**: >= 90% groundedness on curated evaluation set.

### 3. Retrieval Relevance

**Definition**: Whether returned context is relevant to the user question.

- **Metric**: proxy check via citation/source alignment and manual spot-check.
- **Target**: majority of top-k citations should be topically relevant.

## System Metrics

### 4. Latency

**Definition**: End-to-end time from request receipt to response delivery.

- **Metric**: `latency_ms` from `/chat`; report p50 and p95.
- **Target**: p95 < 5000 ms for typical single-turn questions.

### 5. Error Rate

**Definition**: Proportion of requests that fail.

- **Metric**: `error_rate = failed_requests / total_requests`
- **Target**: < 1% during normal usage.

## Evaluation Set

- **Format**: JSONL with `{id, type, question}` where `type` is `answerable` or `unanswerable`.
- **Size**: 25 questions in `eval/questions.jsonl`.
- **Coverage**: PTO, expenses, security, remote work, harassment, onboarding, termination, benefits, equipment, confidentiality.

## Reporting

- Run `python -m eval.run_eval` with the app running locally.
- Report groundedness, citation accuracy, latency p50, and latency p95.
- Store detailed runs in `eval/results.jsonl`.
