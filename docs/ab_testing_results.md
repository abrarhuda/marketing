# A/B Testing Results

The result table is generated from the DuckDB
`customer_experiment_analysis` view:

[ab_test_results.csv](../reports/ab_test_results.csv)

Run the analysis with:

```bash
source .venv/bin/activate
marketing-ab-statistics
```

## How to read the output

- `treatment_rate` and `control_rate` are proportions between 0 and 1.
- `absolute_effect_percentage_points` is the treatment rate minus the control
  rate, expressed in percentage points. For example, `2.5` means a 2.5
  percentage-point difference, not a 2.5% relative increase.
- `relative_lift_percentage` divides the absolute difference by the control
  rate. It expresses the difference relative to the control baseline.
- `z_statistic` and `unadjusted_p_value` come from the two-sided
  statsmodels two-proportion z-test.
- The confidence interval is for the absolute treatment-minus-control
  difference, in percentage points.
- `holm_adjusted_p_value` applies Holm correction within the two comparisons
  for the same outcome.
- Primary decisions use the Holm-adjusted p-value and alpha = 0.05.
- Conversion results are exploratory secondary analyses. They should not be
  described as replacing or confirming the primary visit-rate analysis.

Failure to reject a null hypothesis does not prove that the treatment effect
is exactly zero. The confidence interval describes the range of effects
compatible with the data and method.
