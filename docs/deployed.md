# Render Deployment

## Live App

- Public URL: `https://policy-rag-app.onrender.com/`
- Screenshot path: `render-live-app.png`

## Steps

### Build command
```bash
pip install -r requirements.txt && python -m rag.ingest --rebuild
```

### Start command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Environment variables
- `OPENAI_API_KEY` (required at build time and runtime)
- Optional guardrails:
  - `RAG_MAX_ANSWER_WORDS` (default `140`)
  - `RAG_MAX_OUTPUT_TOKENS` (default `220`)

### Python version pin
- Render may default to Python 3.14, which can fail with current `chromadb`/`pydantic.v1`.
- This project pins Python to `3.11` using `.python-version` (and `PYTHON_VERSION` in `render.yaml`).

### Indexing
The Chroma index is built during Render build in `render.yaml`, so startup remains fast and deterministic.

If a deploy fails while building the index, verify `OPENAI_API_KEY` is present in Render environment settings.

If the index is missing at runtime, `/chat` returns: `Index not built. Run: python -m rag.ingest --rebuild`. `/health` still returns `ok`.

## CI/CD Deploy Hook (GitHub Actions -> Render)

The workflow `.github/workflows/ci.yml` will trigger Render deployment on push to `main` **if** repository secret `RENDER_DEPLOY_HOOK_URL` is configured.

1. In Render service settings, copy the Deploy Hook URL.
2. In GitHub repo: `Settings -> Secrets and variables -> Actions -> New repository secret`
3. Name: `RENDER_DEPLOY_HOOK_URL`
4. Value: paste your Render deploy hook URL.
