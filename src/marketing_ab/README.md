# `marketing_ab` package

Reusable modules for the marketing campaign experiment:

- `data_ingestion.py` downloads and loads the real Hillstrom dataset.
- `data_validation.py` normalizes fields and enforces data-quality rules.
- `database.py` builds and verifies the DuckDB relational layer.
- `eda.py` executes SQL exploratory queries and exports summary tables.
- `statistical_testing.py` runs treatment-versus-control A/B tests.
- `revenue_analysis.py` calculates revenue summaries and bootstrap intervals.
- `machine_learning.py` trains leakage-safe predictive models.

- `visualizations.py` regenerates publication-quality figures.
- `pipeline.py` orchestrates the complete workflow.

I configure the command-line entry points in `pyproject.toml`.
