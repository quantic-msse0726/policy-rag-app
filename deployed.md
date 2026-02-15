# Render Deployment

## Steps

### Build command
```bash
pip install -r requirements.txt
```

### Start command
From Procfile:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Or explicitly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Environment variables
- `OPENAI_API_KEY` (required for /chat)

### Indexing
The Chroma index must exist before /chat will work. Either:

1. **Run indexing locally** before deploy: `python -m rag.ingest --rebuild`, then commit the `data/index/` directory (if not gitignored), or
2. **Add a one-time Render shell step** to build the index after deploy: run `python -m rag.ingest --rebuild` in a background job or manually via the Render shell.

If the index is missing, /chat returns: "Index not built. Run: python -m rag.ingest --rebuild". /health still returns ok.
