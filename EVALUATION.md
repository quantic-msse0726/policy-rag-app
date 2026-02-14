# Evaluation Metrics

This document defines success metrics for the Policy RAG application. Metrics support both **information quality** (answer correctness and attribution) and **system performance** (latency and reliability).

## Information-Quality Metrics

### 1. Citation Accuracy

**Definition**: The proportion of cited documents that actually support the claim made in the answer.

- **Metric**: `citation_accuracy = (correct_citations / total_citations)` per response
- **Evaluation**: For each citation returned, a human or automated checker verifies whether the cited passage supports the specific claim. Binary: correct (1) or incorrect (0).
- **Target**: ≥ 95% citation accuracy on a held-out test set of policy Q&A pairs.

### 2. Groundedness

**Definition**: The extent to which the answer is supported by the retrieved context, without hallucination.

- **Metric**: Score 0–1 per response; aggregate as mean groundedness across a test set.
- **Evaluation**: Compare answer claims against retrieved snippets. Claims with no supporting evidence reduce the score. Can use an LLM-as-judge with a rubric: "Does each factual claim in the answer appear in the context?"
- **Target**: Mean groundedness ≥ 0.85 on a curated evaluation set.

### 3. Relevance (Retrieval)

**Definition**: Whether the retrieved chunks are relevant to the user question.

- **Metric**: `recall@k` or `precision@k` against a gold set of relevant passage IDs per question.
- **Target**: Recall@5 ≥ 0.80 (at least one highly relevant chunk in top 5).

---

## System Metrics

### 4. Latency

**Definition**: End-to-end time from request receipt to response delivery.

- **Metric**: `latency_ms` (milliseconds) per `/chat` request; report p50, p95, p99.
- **Target**: p95 latency < 5,000 ms for typical questions (single-turn, moderate context).

### 5. Throughput

**Definition**: Number of successful requests per second under load.

- **Metric**: Requests per second (RPS) at a defined concurrency level.
- **Target**: ≥ 2 RPS at concurrency 5 without errors.

### 6. Error Rate

**Definition**: Proportion of requests that fail or return errors.

- **Metric**: `error_rate = failed_requests / total_requests`
- **Target**: < 0.1% under normal load.

---

## Evaluation Set

To measure these metrics, maintain a curated evaluation set:

- **Format**: `{ "question": str, "expected_answer_snippets": list[str], "expected_doc_ids": list[str] }`
- **Size**: Minimum 20–50 question-answer pairs covering all major policy areas.
- **Creation**: Mix of synthetic (model-generated) and human-authored questions with ground-truth labels.

Example entry:

```json
{
  "question": "How many PTO days do I get with 4 years of service?",
  "expected_answer_snippets": ["20 days"],
  "expected_doc_ids": ["pto_policy.md"]
}
```

---

## Reporting

- Run evaluation periodically (e.g., per release or weekly).
- Report metrics in a simple table or dashboard.
- Track trends over time; alert when metrics drop below targets.
