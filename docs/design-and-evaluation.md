# Design and Evaluation

## Evaluation

### Evaluation Method

**Question set composition**

- 18 answerable questions spanning PTO, expenses, security, remote work, harassment, onboarding, termination, benefits, equipment, acceptable use, and confidentiality.
- 7 unanswerable questions that cannot be answered from the policy corpus.

**Groundedness**

- **Answerable**: `grounded_ok` = citations not empty AND answer contains bracket-style citations (e.g., [1], [2]) AND citation markers map to returned citations.
- **Unanswerable**: `grounded_ok` = citations empty AND snippets empty AND answer contains "cannot" or "can't".

**Citation accuracy**

- **Answerable**: `citation_ok` = grounded_ok AND answer includes at least one indexed quote line `Quote: "..." [n]` where the quote is an exact substring (after whitespace normalization) of source `n`.
- **Unanswerable**: `citation_ok` = same as grounded_ok (no citations/snippets, refusal wording).

**Metrics**

- **Groundedness %**: `grounded_ok` count / total x 100
- **Citation accuracy %**: `citation_ok` count / total x 100
- **Latency p50/p95**: 50th and 95th percentile of response latency (ms)

**Run evaluation**

```bash
# Server must be running: uvicorn app.main:app --reload
python -m eval.run_eval --overwrite
```

**Manual audit add-on**

```bash
python -m eval.export_manual_review --sample-size 10 --seed 42
```

Then review `eval/manual_review_sample.csv` using `eval/manual_adjudication.md`.

### What You Measured

- **What**: Groundedness (citations present and properly cited), citation accuracy (indexed quote matches exact cited source), and latency.
- **How**: Automated evaluation against 25 curated questions (18 answerable, 7 unanswerable). Each response is scored for citation marker consistency, quote-to-source overlap, and refusal wording where appropriate.
- **Why quote injection improves citation accuracy**:
  - The Quote line is injected from retrieved evidence, so it is verifiable.
  - The model is instructed not to produce its own quotes to avoid paraphrased "fake quotes."
  - Sentence splitting avoids decimals so accrual statements (e.g., "1.67 days") remain intact.

**Limitation**

Heuristic evaluation depends on overlap/substring checks and may not capture all paraphrases.
To reduce this risk, this project includes a manual adjudication protocol and deterministic review sampling.

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
| Citation accuracy % | 100.0 |
| Latency p50 (ms) | 2859 |
| Latency p95 (ms) | 3716 |
