# Statistical Analysis Plan

## Purpose and scope

This document defines the statistical analysis plan for the Hillstrom
MineThatData Email Marketing Experiment. It is a **retrospective analysis
plan** for an existing randomized dataset; it is not a preregistered
experiment.

The business question is:

> Does sending a promotional email increase customer engagement compared with
> sending no email?

The three original experiment groups are preserved:

- **Control:** `No E-Mail`
- **Treatment A:** `Mens E-Mail`
- **Treatment B:** `Womens E-Mail`

The analysis will compare each treatment with the same control group. The
Mens-versus-Womens comparison may be reported as an additional exploratory
comparison, but it is not one of the two primary hypothesis tests defined
below.

## Analysis population and assignment

The analysis population consists of all valid records in the source dataset
that have an experiment assignment and observed campaign outcomes. The
analysis follows the **intention-to-treat** principle: customers are analyzed
according to their randomized assignment, regardless of whether they visited,
purchased, or were otherwise engaged.

The source does not provide actual customer identifiers. This project uses a
stable row-position surrogate only to relate records across its normalized
DuckDB tables. It does not create additional customers or imply event
timestamps.

## Outcomes and estimands

### Primary outcome: website visit rate

For group \(g\), the visit rate is:

\[
\hat{p}_g =
\frac{\text{number of assigned customers with visit}=1}
{\text{number of assigned customers}}
\]

The primary estimand for each treatment \(t\) is the absolute visit-rate
difference:

\[
\Delta_{\text{visit},t} = p_t - p_C
\]

where \(C\) denotes `No E-Mail`. A positive value means the treatment is
associated with a higher probability of visiting the website than no email.

The primary outcome is website visit rate because purchases are comparatively
rare and a visit captures an earlier stage of customer engagement.

### Secondary outcome: purchase conversion rate

For group \(g\), the conversion rate is:

\[
\hat{q}_g =
\frac{\text{number of assigned customers with conversion}=1}
{\text{number of assigned customers}}
\]

For treatment \(t\), the secondary estimand is:

\[
\Delta_{\text{conversion},t} = q_t - q_C
\]

Conversion is analyzed using all assigned customers as the denominator, not
only customers who visited. This preserves the intention-to-treat
interpretation.

### Secondary outcome: revenue per assigned customer

Revenue per assigned customer is:

\[
\bar{R}_g =
\frac{\sum_{i \in g} \text{spend}_i}
{\text{number of assigned customers in }g}
\]

For treatment \(t\), the secondary estimand is:

\[
\Delta_{\text{revenue},t} = \bar{R}_t - \bar{R}_C
\]

This metric includes customers with zero spend. It therefore measures
campaign revenue per assigned customer rather than average spend conditional on
purchase.

## Primary hypotheses

There are two primary treatment-versus-control comparisons. Each uses website
visit rate.

### Mens email versus no email

Null hypothesis:

\[
H_{0,A}: p_A - p_C = 0
\]

Alternative hypothesis:

\[
H_{1,A}: p_A - p_C \ne 0
\]

Here, \(A\) is `Mens E-Mail` and \(C\) is `No E-Mail`.

### Womens email versus no email

Null hypothesis:

\[
H_{0,B}: p_B - p_C = 0
\]

Alternative hypothesis:

\[
H_{1,B}: p_B - p_C \ne 0
\]

Here, \(B\) is `Womens E-Mail` and \(C\) is `No E-Mail`.

The alternatives are two-sided because the analysis should detect either an
increase or a decrease in engagement. A directional business expectation does
not justify ignoring a potentially harmful decrease.

## Secondary hypotheses

The same treatment-versus-control structure will be used for each secondary
outcome:

### Conversion

\[
H_{0,A}^{\text{conversion}}: q_A - q_C = 0
\]

\[
H_{1,A}^{\text{conversion}}: q_A - q_C \ne 0
\]

\[
H_{0,B}^{\text{conversion}}: q_B - q_C = 0
\]

\[
H_{1,B}^{\text{conversion}}: q_B - q_C \ne 0
\]

### Revenue per assigned customer

\[
H_{0,A}^{\text{revenue}}: \bar{R}_A - \bar{R}_C = 0
\]

\[
H_{1,A}^{\text{revenue}}: \bar{R}_A - \bar{R}_C \ne 0
\]

\[
H_{0,B}^{\text{revenue}}: \bar{R}_B - \bar{R}_C = 0
\]

\[
H_{1,B}^{\text{revenue}}: \bar{R}_B - \bar{R}_C \ne 0
\]

These are secondary outcomes and should not replace the primary engagement
analysis.

## Significance level and confidence intervals

The family of the two primary visit-rate tests uses:

\[
\alpha = 0.05
\]

The reported confidence intervals are 95% intervals. For a difference in
proportions, the interval should be reported on the absolute difference scale
in percentage points, along with the corresponding group rates.

For each comparison, the report should include:

- control rate;
- treatment rate;
- absolute difference in percentage points;
- confidence interval;
- raw p-value;
- Holm-adjusted p-value;
- conclusion under the adjusted decision rule.

The secondary outcomes should also report estimates and 95% confidence
intervals. Their multiplicity status must be stated clearly rather than
presenting them as additional primary confirmations.

## Multiple testing: Holm correction

The two primary tests share the same control group, so treating both raw
p-values as independently confirmatory at 0.05 would increase the chance of
at least one false positive.

The Holm step-down procedure will control the family-wise error rate at 0.05:

1. Let \(m=2\) be the number of primary hypotheses.
2. Sort the two raw p-values from smallest to largest:
   \(p_{(1)} \le p_{(2)}\).
3. Compare \(p_{(1)}\) with \(0.05 / 2\).
4. If the first hypothesis is rejected, compare \(p_{(2)}\) with
   \(0.05 / 1 = 0.05\).
5. Stop at the first comparison that fails; all later hypotheses are not
   rejected under the step-down procedure.

Software may report equivalent Holm-adjusted p-values. The analysis should
retain the raw p-values for transparency but base primary conclusions on the
Holm-adjusted results.

The shared control does not invalidate the comparisons. It does mean that the
tests are statistically related, which is exactly why a family-wise
multiple-testing procedure is used.

## A/B testing versus A/B/n testing

An **A/B test** compares two variants, commonly one control and one treatment:

```text
Control versus Treatment A
```

An **A/B/n test** compares more than two variants, such as:

```text
Control, Treatment A, Treatment B, ..., Treatment n
```

This experiment is an A/B/n design with three arms: one control and two email
treatments. It contains two planned treatment-versus-control comparisons. A
three-group experiment should not be analyzed as though only one treatment
comparison existed, because that would understate the number of primary
comparisons.

## Statistical significance versus practical significance

**Statistical significance** asks whether the observed data are sufficiently
inconsistent with a null hypothesis under the chosen statistical model. A
small p-value is evidence against the null hypothesis, after applying the
specified multiplicity correction.

**Practical significance** asks whether the estimated effect is large enough
to matter for a business decision. A very large sample can make a tiny effect
statistically significant. Conversely, a potentially valuable effect may have
an interval that is too wide to estimate precisely.

Results should therefore be interpreted using both:

- the estimated absolute lift;
- the 95% confidence interval;
- the adjusted p-value;
- campaign costs and business value, when those inputs are available.

This dataset alone does not establish a profitability threshold. Any
recommendation about profitability must state its cost and value assumptions.

## Type I and Type II errors

A **Type I error** is a false positive: rejecting a no-effect hypothesis when
the treatment has no true effect. With the Holm-adjusted primary family, the
target probability of at least one Type I error across the two primary tests
is controlled at 0.05 under the procedure's assumptions.

A **Type II error** is a false negative: failing to reject a no-effect
hypothesis when a meaningful treatment effect exists. Type II error probability
is commonly denoted by \(\beta\).

Statistical power is:

\[
\text{Power} = 1 - \beta
\]

It is the probability of detecting a specified true effect under a specified
sample size, variability, significance level, and testing procedure.

## Power and minimum detectable effects

The **minimum detectable effect** (MDE) is the smallest effect the planned
design can detect with a chosen power, often 80% or 90%, at the chosen alpha
level.

For the primary outcome, an MDE should be defined on the absolute visit-rate
difference scale:

\[
\text{MDE}_{\text{visit}} = p_t - p_C
\]

An MDE calculation requires assumptions about:

- the baseline control visit rate;
- the treatment visit rate considered meaningful;
- the sample size in each arm;
- the target power;
- the alpha level;
- the two-test Holm correction;
- whether the comparison is one-sided or two-sided.

Because this is a retrospective analysis, the MDE should be presented as a
design-sensitivity exercise, not as evidence that the dataset was planned
around that effect. Observed results must not be used to claim that the study
was powered for an effect after seeing the results.

## Group-size balance check

Random assignment was intended to place approximately equal numbers of
customers in the three arms. The analysis will report the observed count and
percentage in each group and compare them with the nominal target:

\[
\text{Expected share per arm} = \frac{1}{3}
\]

This is a diagnostic of assignment balance, not a test that can prove
randomization was successful. Small deviations are expected by chance. Large
deviations should prompt investigation of data loading, filtering, or source
documentation before outcome results are interpreted.

The balance check will not remove observations or rebalance groups.

## Why random assignment supports causal inference

Under proper random assignment, treatment assignment is independent of
pre-treatment customer characteristics in expectation. Therefore, before
sampling variation, the groups are comparable with respect to both observed
and unobserved customer characteristics.

The treatment-versus-control difference estimates the average treatment effect
for the randomized population:

\[
\text{ATE}_t = E[Y(t) - Y(C)]
\]

where \(Y(t)\) is the potential outcome under treatment \(t\), and \(Y(C)\) is
the potential outcome under no email. A customer cannot be observed under both
conditions, so the randomized group averages provide the comparison needed to
estimate the average effect.

Randomization does not automatically guarantee a correct analysis. The
project must still preserve assignments, avoid post-treatment adjustment,
account for multiple primary tests, report uncertainty, and avoid changing
the analysis population after viewing results.

## Planned reporting sequence

For each primary comparison:

1. Report group counts and assignment percentages.
2. Report visit counts and visit rates.
3. Report the absolute visit-rate difference.
4. Report a 95% confidence interval.
5. Report raw and Holm-adjusted p-values.
6. State whether the adjusted result rejects the null at \(\alpha=0.05\).
7. Discuss practical magnitude separately from statistical significance.

Then report conversion and revenue per assigned customer as secondary
outcomes, clearly labeled as secondary and accompanied by confidence
intervals.

No numerical results are included in this methodology document. They must be
computed from the validated dataset and database queries.
