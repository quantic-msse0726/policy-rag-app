# Policy RAG App

[![CI](https://github.com/quantic-msse0726/policy-rag-app/actions/workflows/ci.yml/badge.svg)](https://github.com/quantic-msse0726/policy-rag-app/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/live-demo-3B8EA5?style=flat-square)](https://policy-rag-app.onrender.com/)
[![Uptime Status](https://img.shields.io/badge/uptime-status%20page-2F6F9F?style=flat-square)](https://stats.uptimerobot.com/EhIcAe5nKS)
[![Python](https://img.shields.io/badge/python-3.11-2F4F90?logo=python&logoColor=white&style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-api-0E7C86?logo=fastapi&logoColor=white&style=flat-square)](https://fastapi.tiangolo.com/)
[![Chroma](https://img.shields.io/badge/chroma-vector%20db-4A5BCF?style=flat-square)](https://www.trychroma.com/)
[![OpenAI](https://img.shields.io/badge/openai-llm-2F2F2F?logo=openai&logoColor=white&style=flat-square)](https://platform.openai.com/)
[![Render](https://img.shields.io/badge/render-deploy-3B8EA5?logo=render&logoColor=white&style=flat-square)](https://render.com/)

End-to-end Retrieval-Augmented Generation (RAG) application for answering company policy questions with citations.

## Project Summary

This project implements the full assignment scope:

- Multi-format policy ingestion (`.md`, `.txt`, `.html`, `.pdf`)
- Chunking + embedding + vector indexing (Chroma)
- Top-k retrieval with lightweight reranking
- Guardrailed generation with citation markers and refusal behavior
- Web application with:
  - `/` chat UI
  - `/chat` JSON API
  - `/health` health endpoint
- Automated evaluation (groundedness, citation accuracy, latency)
- CI checks and optional Render deploy hook

## Corpus

Policy corpus is in `data/policies/`.

- Size: 19 documents, ~50 pages, ~21.6k tokens, ~99 chunks
- Topics: PTO, remote work, expenses, information security, acceptable use, code of conduct, D&I, performance, onboarding, termination, benefits, equipment, confidentiality, harassment reporting
- Legal status: synthetic content authored for this project and safe to include in repo

To regenerate the sample PDF document:

```bash
python scripts/generate_sample_pdf.py
```

## Tech Stack

- Backend: FastAPI, Uvicorn
- LLM/Embeddings: OpenAI API
- Vector store: Chroma (local persistent)
- Parsing: BeautifulSoup (HTML), pypdf (PDF)
- Evaluation: Python scripts + JSONL artifacts
- CI/CD: GitHub Actions + optional Render deploy hook

## Repository Layout

- `app/main.py`: FastAPI app and `/chat` orchestration
- `app/templates/index.html`: web chat UI
- `rag/ingest.py`: document parsing, chunking, embedding, indexing
- `rag/retriever.py`: retrieval, reranking, refusal heuristics
- `rag/prompts.py`: prompt construction
- `eval/run_eval.py`: automated evaluation runner
- `eval/export_manual_review.py`: deterministic manual-review sample export
- `eval/manual_adjudication.md`: human adjudication rubric
- `.github/workflows/ci.yml`: CI pipeline and optional deploy hook
- `render.yaml`: Render service configuration

## Local Setup

### 1) Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

Copy `.env.example` to `.env` and set:

```env
OPENAI_API_KEY=sk-your-key-here
```

Optional runtime guardrails:

```env
RAG_MAX_ANSWER_WORDS=140
RAG_MAX_OUTPUT_TOKENS=220
```

### 4) Build the vector index

```bash
python -m rag.ingest --rebuild
```

### 5) Run tests

```bash
python -m pytest -q
```

### 6) Start server

```bash
uvicorn app.main:app --reload
```

Open:

- UI: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/health`

## API Usage

### POST `/chat`

Request body:

```json
{ "question": "How many PTO days can I carry over?" }
```

Returns:

- `answer`
- `citations[]` with `doc_id`, `title`, `section`, `snippet`
- `snippets[]`
- `latency_ms`

PowerShell example:

```powershell
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"How many PTO days can I carry over?\"}"
```

## Evaluation

### Automated metrics

Run deterministic evaluation:

```bash
python -m eval.run_eval --overwrite
```

Produces/updates:

- `eval/results.jsonl`

Reported metrics:

- Groundedness %
- Citation accuracy %
- Latency p50 / p95

### Manual audit add-on

Export deterministic sample for human review:

```bash
python -m eval.export_manual_review --sample-size 10 --seed 42
```

Then adjudicate with:

- `eval/manual_review_sample.csv`
- `eval/manual_adjudication.md`

## Deployment (Render)

This repo includes `render.yaml`.

### Render settings (if configuring manually)

- Runtime: `Python 3`
- Python version: `3.11.x` (required for current `chromadb` compatibility)
- Branch: `main`
- Root directory: blank
- Build command:

```bash
pip install -r requirements.txt && test -n "$OPENAI_API_KEY" && python -m rag.ingest --rebuild
```

- Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Health check path: `/health`
- Required env var: `OPENAI_API_KEY`

If Render defaults to Python 3.14+, deploy can fail in `chromadb`/`pydantic.v1`. This repo pins Python to 3.11 via `render.yaml` and `.python-version`.

After deploy, validate:

1. `https://<your-service>.onrender.com/health`
2. `https://<your-service>.onrender.com/`
3. Ask a sample question and confirm citations/snippets in response

See `docs/deployed.md` for live URL and deploy evidence fields.

## CI/CD

Workflow: `.github/workflows/ci.yml`

On push/PR:

- Install dependencies
- Compile modules
- Run tests (`python -m pytest -q`)

Optional deploy-on-main:

- If secret `RENDER_DEPLOY_HOOK_URL` is configured, CI triggers Render deploy hook after tests pass on `main`.

## Reproducibility Notes

- Python 3.11 in CI
- Fixed evaluation set (`eval/questions.jsonl`)
- Deterministic evaluation output mode (`--overwrite`)
- Explicit output-length guardrails in app runtime

## Submission Artifacts

- Code and docs: this repository
- Setup and run guide: `README.md`
- Design and evaluation summary: `docs/design-and-evaluation.md`
- Metric definitions: `docs/EVALUATION.md`
- AI tooling disclosure: `docs/ai-tooling.md`
- Deployment notes: `docs/deployed.md`

## Troubleshooting

- Error: `Index not built` on `/chat`
  - Run: `python -m rag.ingest --rebuild`
- CI failure due to import paths
  - Use: `python -m pytest -q` (already configured)
- Render health check failing
  - Ensure health path is `/health` and start command uses Uvicorn with `$PORT`
