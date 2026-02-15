# Manual Adjudication Protocol

This protocol adds a human-verified quality check to complement automated metrics.

## Goal

Validate a sample of model outputs for:

- Groundedness: factual claims are supported by cited evidence.
- Citation accuracy: cited sources actually support the claim they are attached to.

## Procedure

1. Run evaluation:
   - `python -m eval.run_eval --overwrite`
2. Export a deterministic review sample:
   - `python -m eval.export_manual_review --sample-size 10 --seed 42`
3. Open `eval/manual_review_sample.csv`.
4. For each row, set:
   - `human_grounded_ok` = `true` or `false`
   - `human_citation_ok` = `true` or `false`
   - `notes` with short evidence/rationale.

## Decision Rules

- `human_grounded_ok = true` only if all material claims in the answer are supported by retrieved evidence.
- `human_citation_ok = true` only if the cited document(s)/snippet(s) directly support the specific claim.
- If any claim is unsupported or citation is misleading, mark `false`.

## Reporting

Report sample agreement rates:

- Human groundedness agreement = `% rows where human_grounded_ok == auto_grounded_ok`
- Human citation agreement = `% rows where human_citation_ok == auto_citation_ok`

These rates provide an audit signal on automated metric reliability.
