# Customer-level uplift modeling

## Business question

The question is not simply which customers are likely to visit. It is:

> Which customers are most likely to benefit from receiving an email, and
> which email version should they receive?

The project preserves all three randomized arms:

- `No E-Mail`
- `Mens E-Mail`
- `Womens E-Mail`

## Potential outcomes and counterfactuals

For a customer with pretreatment features \(X\), imagine three potential
visit outcomes:

\[
Y(\text{No E-Mail}),\quad
Y(\text{Mens E-Mail}),\quad
Y(\text{Womens E-Mail})
\]

Only one of these outcomes is observed for a particular customer because each
customer receives only one randomized assignment. The other two are
counterfactuals: outcomes we would have observed under different assignments,
but cannot directly observe for that same customer.

An individual treatment effect is therefore:

\[
\tau_{\text{Mens}}(X)
= P(Y=1 \mid X,\text{Mens E-Mail})
- P(Y=1 \mid X,\text{No E-Mail})
\]

and similarly:

\[
\tau_{\text{Womens}}(X)
= P(Y=1 \mid X,\text{Womens E-Mail})
- P(Y=1 \mid X,\text{No E-Mail})
\]

These are modeled estimates, not directly observed individual causal effects.

## T-Learner

A T-Learner fits one separate outcome model for each treatment arm:

```text
Model 0: visit probability under No E-Mail
Model 1: visit probability under Mens E-Mail
Model 2: visit probability under Womens E-Mail
```

All three models use the same pretreatment feature set as the predictive
baseline. Treatment assignment, visit, conversion, and spend are not model
inputs.

For every held-out customer, the pipeline sends the same feature vector through
all three models. This creates three predicted probabilities, even though only
one actual treatment outcome was observed.

The recommendation is the arm with the greatest predicted visit probability.
Because `No E-Mail` is included as a candidate, a customer is recommended no
email when both estimated treatment uplifts are negative.

## Leakage prevention and evaluation

The existing 60/20/20 stratified train, validation, and test partitions are
reused. Each arm model is fitted only on customers assigned to that arm in the
training data. The validation customers in the same arm select logistic
regression regularization from `C = 0.01, 0.1, 1.0`. The selected model is then refit on training plus
validation customers from that arm.

The held-out test set is used to:

- generate counterfactual probability predictions;
- evaluate each arm model on customers actually assigned to that arm;
- evaluate treatment policies using randomized assignment.

The policy evaluation uses inverse-propensity weighting. For a test customer,
the observed visit contributes to a policy's estimate only when the observed
random assignment matches the policy recommendation. The contribution is
weighted by the inverse probability of receiving that observed arm.

This uses the randomized experiment for held-out policy evaluation. It does
not make the unobserved counterfactual directly observable.

## Interpretation cautions

Different customers can receive different uplift estimates because the models
predict different probabilities for their feature profiles. That pattern is
not, by itself, proof that causal treatment heterogeneity has been
established. It can reflect model uncertainty, sampling noise, regularization,
or misspecification.

Uplift estimates should be evaluated on held-out randomized data and compared
with simple policies such as always sending no email or always sending one
email version. The model should not be used to claim individual certainty.

## Outputs

Run:

```bash
source .venv/bin/activate
marketing-ab-uplift
```

The command writes:

- `reports/uplift_predictions.csv`: all three predicted probabilities,
  estimated uplifts, observed assignment, observed outcome, and recommended
  treatment for each held-out customer.
- `reports/uplift_policy_evaluation.csv`: inverse-propensity-weighted
  held-out policy estimates and recommendation counts.
- `reports/uplift_arm_model_evaluation.csv`: factual held-out metrics for each
  arm-specific outcome model.
- `models/t_learner_logistic_regression.joblib`: a reproducible local model
  bundle, excluded from Git.
