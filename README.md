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

### Indexing

Build the vector index from policy documents:

```bash
python -m rag.ingest --rebuild
```

Use `--rebuild` to delete the existing index and re-index from scratch. Without it, new documents are added to the existing index.
