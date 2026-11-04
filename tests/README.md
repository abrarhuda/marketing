# Tests

This folder contains pytest tests for the reusable project modules.

The tests use small synthetic fixtures for fast, deterministic unit testing;
they never replace the real Hillstrom dataset used by the analysis pipeline.
Coverage includes:

- data validation and invalid-value handling;
- DuckDB schema, joins, and SQL aggregates;
- A/B testing calculations and Holm correction;
- revenue bootstrap reproducibility;
- feature exclusions and train/test split reproducibility;
- T-Learner predictions and uplift policies; and
- complete pipeline stage orchestration.

Run them from the repository root with:

```bash
python -m pytest
```
