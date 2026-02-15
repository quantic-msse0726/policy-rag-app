# policy-rag-app
End-to-end RAG system for policy question answering. Implements document ingestion, chunking, embeddings, vector search, citation-aware prompting, guardrails, evaluation pipeline, and CI/CD.

## Corpus

The `data/policies/` directory contains a synthetic company policy corpus (18+ files, ~50 pages) covering:

- **Formats**: Markdown (.md), plain text (.txt), HTML (.html), and PDF (.pdf)
- **Topics**: PTO, remote work, expenses, information security, acceptable use, code of conduct, diversity & inclusion, performance review, onboarding, termination, benefits, equipment, confidentiality, harassment prevention
- **Legal use**: All content is synthetically authored for this project and may be freely used and redistributed.

To regenerate the sample PDF: `python scripts/generate_sample_pdf.py`

## Evaluation

Success metrics (information quality and system performance) are defined in [EVALUATION.md](EVALUATION.md), including groundedness, citation accuracy, and latency targets.

## Setup

### Environment

Set your OpenAI API key in a `.env` file (copy from `.env.example`):

```
OPENAI_API_KEY=sk-your-key-here
```

Optional runtime guardrails:

```env
RAG_MAX_ANSWER_WORDS=140
RAG_MAX_OUTPUT_TOKENS=220
```

### Build index

Build the vector index from policy documents:

```bash
python -m rag.ingest --rebuild
```

Use `--rebuild` to delete the existing index and re-index from scratch. Without it, new documents are added to the existing index.

### Run server

```bash
uvicorn app.main:app --reload
```

### Test retrieval

Verify retrieval (uses OpenAI for query embedding; requires index and OPENAI_API_KEY):

```bash
python -m rag.query "PTO carryover"
```

### Test chat

With the server running, test the chat endpoint (PowerShell):

```powershell
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"How many PTO days can I carry over?\"}"
```

## Deploy to Render

1. Push code to GitHub.
2. In Render, create a new Web Service from the repo. `render.yaml` will be auto-detected.
3. Set required env var:
   - `OPENAI_API_KEY`
4. Deploy once and verify:
   - `/health` returns `{"status":"ok"}`
   - `/` loads chat UI
5. For auto-deploy from CI, set GitHub secret `RENDER_DEPLOY_HOOK_URL` (see `deployed.md`).

## Reproducibility Notes

- CI runs on Python 3.11 (`.github/workflows/ci.yml`).
- Retrieval/generation behavior is stabilized by deterministic prompt rules, citation filtering, and post-response length clamping in `app/main.py`.
- Evaluation uses a fixed 25-question set in `eval/questions.jsonl`.
- For deterministic eval artifacts, use: `python -m eval.run_eval --overwrite`
- For a manual quality audit sample, use: `python -m eval.export_manual_review --sample-size 10 --seed 42`
