# Policy Corpus

## Synthetic Content

**All content in this directory is synthetic** and was created for demonstration and development purposes. It does not represent any real organization's policies. Safe for use in repositories, RAG applications, and educational contexts.

## Files and Formats

| Format | Count | Files |
|--------|-------|-------|
| Markdown (.md) | 14 | acceptable_use_policy, benefits_overview, code_of_conduct, confidentiality_nda, diversity_inclusion, equipment_assets, expenses_policy, harassment_complaints, information_security_policy, onboarding, performance_review, pto_policy, remote_work_policy, termination |
| Plain text (.txt) | 2 | policy_index, quick_reference |
| HTML (.html) | 2 | code_of_conduct, pto_policy |
| PDF (.pdf) | 1 | expenses_policy (generated from expenses_policy.md) |

**Total: 19 files**

## Target Size

- **~50 pages** total across the corpus
- Markdown policies: ~1,200–2,000 words each
- Includes sections: Scope, Definitions, Policy, Procedures, Examples, Enforcement, FAQ
- Cross-references between policies (e.g., Information Security ↔ Acceptable Use)

## Regenerating the PDF

To regenerate `expenses_policy.pdf` from the Markdown source:

```bash
python scripts/generate_sample_pdf.py
```

## Ingestion

To index this corpus into Chroma:

```bash
python -m rag.ingest --rebuild
```
