# Reports

Generated figures belong in `reports/figures/`; generated tables belong in
`reports/tables/`. These outputs are intentionally excluded from Git until
the analysis pipeline produces them.

Revenue analysis outputs are generated under `reports/`:

- `revenue_summary.csv`: DuckDB group-level revenue and zero-spend summary.
- `revenue_bootstrap_results.csv`: treatment-control mean differences and
  percentile bootstrap intervals.
- `revenue_distribution_diagnostics.csv`: zero-inflation and skewness
  diagnostics.
- `figures/revenue_differences_bootstrap_ci.png`: estimated differences with
  95% bootstrap confidence intervals.
