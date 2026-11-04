# Held-out uplift model evaluation report

## Executive summary

This report evaluates the already trained three-arm logistic-regression
T-Learner on the reserved 12,800-customer test set. No model was refit or
retuned using these customers. Policy values use the known one-third
randomization probabilities and inverse-propensity weighting. Uncertainty
comes from 2,000 customer-level bootstrap resamples.

The positive-uplift targeting policy had an estimated visit rate of **18.49%**
(95% bootstrap CI: **17.30% to 19.76%**), compared with:

- **10.59%** for No E-Mail for everyone;
- **18.26%** for Mens E-Mail for everyone;
- **15.19%** for Womens E-Mail for everyone.

Relative to all-control, the model policy's estimated incremental visit rate
was **7.90 percentage points** (95% CI: **6.23 to 9.49 points**). Its point
estimate was only **0.23 points above always-Mens**; the direct bootstrap
contrast was **-0.84 to +1.27 points**, so this evaluation does not establish
that targeting improves on simply sending Mens E-Mail to everyone. The model
policy was estimated **3.30 points above always-Womens** (95% CI:
**1.97 to 4.80 points**).

Therefore, the honest conclusion is that the model-based policy performs well
relative to all-control and always-Womens in this held-out evaluation, but it
does **not** show a statistically clear improvement over the strong
always-Mens baseline.

## Policy results

| Policy | Estimated visit rate | Increment vs all-control | 95% CI for increment |
|---|---:|---:|---:|
| No E-Mail for everyone | 10.59% | 0.00 pp | 0.00 to 0.00 pp |
| Mens E-Mail for everyone | 18.26% | 7.66 pp | 5.98 to 9.26 pp |
| Womens E-Mail for everyone | 15.19% | 4.59 pp | 3.07 to 6.07 pp |
| Highest positive estimated uplift | 18.49% | 7.90 pp | 6.23 to 9.49 pp |
| Highest predicted visit probability | 18.49% | 7.90 pp | 6.23 to 9.49 pp |

The positive-uplift policy recommended Mens E-Mail for 8,011 customers and
Womens E-Mail for 4,789 customers. It recommended No E-Mail for zero
customers. This recommendation distribution is a model output, not evidence
that every recommended customer benefits.

Direct model-policy contrasts were:

- versus always-Mens: **+0.23 pp**, 95% bootstrap CI **-0.84 to +1.27 pp**;
- versus always-Womens: **+3.30 pp**, 95% bootstrap CI **+1.97 to +4.80 pp**.

## Ranking and Qini results

The treatment-specific ranking curves rank customers by estimated uplift
relative to No E-Mail. At each targeting depth, inverse-propensity weighting
estimates the visit rate for sending that email to the ranked customers and
No E-Mail to the remainder.

The exported Qini-style curve is:

\[
\operatorname{Qini}(k)
= \widehat{V}(\text{target top } k)
- \widehat{V}(\text{always No E-Mail})
\]

The Mens curve reached a maximum incremental visit rate of **7.66 percentage
points** at approximately **99.9%** of the test set. Its trapezoidal area over
the target fraction was **0.0422**. The Womens curve reached a maximum of
**4.73 points** at approximately **93.7%** targeted and ended at **4.59
points** when everyone received Womens E-Mail; its area was **0.0286**.

These curves do not prove individual treatment effects. They assess whether
the ranking is useful when applied as a policy to randomized held-out
customers.

## Methodology

For a policy \(d(X_i)\), the inverse-propensity estimate was:

\[
\hat V(d)=\frac{1}{n}\sum_i
\frac{I(A_i=d(X_i))Y_i}{e(A_i)}
\]

where \(A_i\) is observed assignment, \(Y_i\) is observed visitation, and
\(e(A_i)=1/3\) for each randomized arm. This uses only the observed outcome
when the randomized assignment agrees with the policy recommendation.

The bootstrap resampled complete held-out customer rows with replacement,
keeping assignments, outcomes, and fixed model predictions together. It used
2,000 iterations and seed 42. The resulting percentile intervals quantify
sampling uncertainty for these policy estimates.

## Limitations

Raw observed outcomes among model-recommended and non-recommended customers
were not used as a treatment-effect estimate. Those groups can differ in
pretreatment characteristics and are not randomized comparisons.

Only one of each customer's three potential outcomes is observed. Uplift
predictions are therefore modeled counterfactual estimates, not directly
observed individual causal effects. The bootstrap does not capture every
source of model-selection or specification uncertainty. The results also do
not include email costs, profit margins, long-term customer value, contact
fatigue, or operational constraints. A higher visit rate is not by itself a
profitability result.
