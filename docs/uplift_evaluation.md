# Held-out uplift model evaluation

## Evaluation question

The evaluation asks whether the fixed uplift predictions identify customers for
whom an email is more useful than no email. It uses only the previously
reserved held-out test data. The T-Learner is not refit, retuned, or selected
using these results.

The primary outcome is website visitation. Since each randomized customer has
only one observed outcome, an individual customer's unobserved counterfactual
cannot be checked directly. Evaluation therefore uses the known randomized
assignment mechanism.

## Inverse-propensity policy evaluation

For a policy recommendation \(d(X_i)\), the inverse-propensity-weighted
estimate is:

\[
\hat V(d) =
\frac{1}{n}\sum_i
\frac{I(A_i=d(X_i))Y_i}{e(A_i)}
\]

where \(A_i\) is the observed randomized assignment, \(Y_i\) is the observed
visit outcome, \(e(A_i)\) is the probability of receiving that assignment,
and \(d(X_i)\) is the treatment the policy would recommend.

The Hillstrom experiment has approximately equal randomized assignment, so the
evaluation uses \(e(A)=1/3\) for each of the three arms. Only rows whose
observed assignment agrees with a policy contribute an observed outcome. This
is fundamentally different from comparing observed visit rates among people
the model happened to recommend versus everyone else.

The evaluated policies are:

1. No E-Mail for everyone.
2. Mens E-Mail for everyone.
3. Womens E-Mail for everyone.
4. Send the email with the highest estimated uplift only when that uplift is
   positive; otherwise send no email.
5. Send the treatment with the highest predicted visit probability, including
   No E-Mail as an option.

The fourth policy is the main model-based targeting policy because it follows
the requested positive-uplift rule.

## Ranking curves and Qini interpretation

For each promotional email separately, customers are ranked from highest to
lowest estimated uplift relative to No E-Mail. At a target fraction \(k\), the
policy sends that email to the top \(k\) customers and sends no email to the
remainder. The ranking curve estimates the policy's visit rate using inverse
propensity weighting.

The Qini-style value is:

\[
\text{Qini}(k)=\hat V(d_k)-\hat V(\text{always No E-Mail})
\]

The exported `qini_incremental_visits` column multiplies this rate difference
by the held-out sample size. A positive value means that targeting the top
ranked customers is estimated to produce more visits than sending no email to
anyone at that targeting depth. Curves that rise early are more useful for
limited campaign capacity. A curve below zero indicates that targeting at that
depth is not supported as better than the all-control policy.

Qini curves are descriptive held-out evaluation tools, not proof of each
customer's causal effect. Their shape is affected by finite-sample noise,
model misspecification, and the fact that only one potential outcome is
observed per person.

## Bootstrap uncertainty

The evaluator resamples held-out customers with replacement, preserving each
customer's observed assignment, outcome, and fixed model predictions. It
recomputes every policy value for each resample and reports percentile 95%
bootstrap intervals. The default is 2,000 iterations with seed 42.

The bootstrap reflects sampling uncertainty in this held-out evaluation. It
does not account for all uncertainty from selecting the model, changing the
feature set, or trying many candidate models before this final evaluation.
Those decisions must remain isolated from the held-out test set.

## Outputs

Run:

```bash
source .venv/bin/activate
marketing-ab-uplift-evaluation
```

The command writes:

- `reports/uplift_policy_bootstrap_evaluation.csv`: IPW policy estimates,
  incremental estimates versus all-control, and bootstrap confidence intervals.
- `reports/uplift_ranking_curves.csv`: Mens and Womens treatment-specific
  ranking/Qini curve points.
- `reports/figures/uplift_qini_curves.png`: visualization of both curves.

## Limitations

An uplift policy can fail to outperform a simple always-control or
always-treatment policy because heterogeneous effects are difficult to
estimate. A point estimate above a baseline is not persuasive when its
confidence interval includes zero. Conversely, a confidence interval that
excludes zero describes evidence for the policy value on this evaluation
sample; it does not establish permanent campaign performance or profitability.
Email costs, margins, long-term effects, and operational constraints are not
included.
