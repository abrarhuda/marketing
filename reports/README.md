# Reports

The reports folder contains executive-facing findings and locally generated
analysis artifacts.

- `executive_summary.md` is the concise business-facing project summary.
- `figures/` receives generated PNG charts.
- `tables/` receives generated SQL summary tables.
- Generated CSVs, figures, and tables are intentionally excluded from Git
  because they can be recreated by the pipeline.

Revenue analysis outputs are generated under `reports/`:

- `revenue_summary.csv`: DuckDB group-level revenue and zero-spend summary.
- `revenue_bootstrap_results.csv`: treatment-control mean differences and
  percentile bootstrap intervals.
- `revenue_distribution_diagnostics.csv`: zero-inflation and skewness
  diagnostics.
- `figures/revenue_differences_bootstrap_ci.png`: estimated differences with
  95% bootstrap confidence intervals.
