# Revenue analysis with bootstrap confidence intervals

## Business question

The question is whether either promotional email changes average revenue per
assigned customer compared with `No E-Mail`.

The denominator is every randomized customer in the group. Customers who
spent `$0` remain in the data and in the denominator. This is different from
average spend among purchasers, which answers a different question.

## Why bootstrap revenue differences?

Revenue is more difficult to analyze than a binary visit outcome because it is
typically:

- zero-inflated: many assigned customers spend nothing;
- right-skewed: a small number of customers can spend much more than average;
- continuous: customers can have different positive spend amounts;
- sensitive to extreme values: a few large purchases can materially affect the
  mean.

The nonparametric bootstrap avoids assuming that revenue follows a normal
distribution. It repeatedly samples customers with replacement within each
experimental group, preserving that group's observed zero and positive-spend
pattern.

For each iteration:

1. Sample the treatment customers with replacement, using the original
   treatment sample size.
2. Sample the control customers with replacement, using the original control
   sample size.
3. Calculate each resampled mean.
4. Subtract the control mean from the treatment mean.
5. Store that difference.

After 2,000 iterations, the 2.5th and 97.5th percentiles of the stored
differences form the default 95% percentile bootstrap confidence interval.
The random seed is fixed at 42 so the result can be reproduced.

## Outputs

- [revenue_summary.csv](../reports/revenue_summary.csv): SQL-generated group
  means, totals, purchaser counts, and zero-spend rates.
- [revenue_bootstrap_results.csv](../reports/revenue_bootstrap_results.csv):
  treatment-control differences and bootstrap intervals.
- [revenue_distribution_diagnostics.csv](../reports/revenue_distribution_diagnostics.csv):
  means, medians, skewness, and zero-spend rates.
- [revenue_differences_bootstrap_ci.png](../reports/figures/revenue_differences_bootstrap_ci.png):
  point estimates and intervals.

## Comparing outcomes

Visit rate is a binary engagement outcome, so a two-proportion method directly
models the proportion of customers who visited. Conversion is also binary but
rarer. Revenue combines the probability of purchasing with the amount spent
among purchasers, so it has greater variability and can produce wider
uncertainty.

An interval that includes zero does not establish that the treatment has no
effect. It means the observed data and method do not rule out zero at the
chosen confidence level. An interval entirely above zero indicates an
estimated positive revenue difference, but it does not establish profitability.

Email costs, margins, refunds, and other financial inputs are not provided in
this dataset. Therefore, a positive revenue difference must not be described as
positive profit or a profitable campaign.
