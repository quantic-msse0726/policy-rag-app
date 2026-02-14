# Design and Evaluation

## Evaluation

### Evaluation Method

**Question set composition**

- 18 answerable questions spanning PTO, expenses, security, remote work, harassment, onboarding, termination, benefits, equipment, acceptable use, and confidentiality.
- 7 unanswerable questions that cannot be answered from the policy corpus.

**Groundedness**

- **Answerable**: `grounded_ok` = citations not empty AND answer contains bracket-style citations (e.g., [1], [2]).
- **Unanswerable**: `grounded_ok` = citations empty AND snippets empty AND answer contains "cannot" or "can't".

**Citation accuracy**

- **Answerable**: `citation_ok` = grounded_ok AND answer includes at least one quoted phrase (`"..."`) that is an exact substring (after whitespace normalization) of at least one cited source. Quoted phrases must have length ≥20 characters or ≥5 words to avoid trivial matches.
- **Unanswerable**: `citation_ok` = same as grounded_ok (no citations/snippets, refusal wording).

**Limitation**

Exact-substring matching may fail on minor paraphrases or formatting differences; it avoids spurious matches from generic phrase overlap.

**Metrics**

- **Groundedness %**: `grounded_ok` count / total × 100
- **Citation accuracy %**: `citation_ok` count / total × 100
- **Latency p50/p95**: 50th and 95th percentile of response latency (ms)

**Run evaluation**

```bash
# Server must be running: uvicorn app.main:app --reload
python -m eval.run_eval
```

### Corpus Size

| Metric | Value |
|--------|-------|
| Documents | 19 |
| Tokens | ~21,600 |
| Chunks | ~99 |

### Metrics (Latest Run)

| Metric | Value |
|--------|-------|
| Groundedness % | 100.0 |
| Citation accuracy % | 80.0 |
| Latency p50 (ms) | 2862 |
| Latency p95 (ms) | 4358 |
