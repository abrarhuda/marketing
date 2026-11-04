# My predictive modeling methodology

## Objective and feature boundary

I predict whether a customer visits the website. The target is `visit`.

I use only these historical, pre-treatment attributes:

```text
recency
history
history_segment
mens
womens
zip_code
newbie
channel
```

I exclude treatment assignment from the predictive features and use it only to
preserve balance when making the data splits. I never pass the post-treatment
fields `visit`, `conversion`, or `spend` into a model.

## Data splitting and leakage prevention

I split the data into 60% training, 20% validation, and 20% held-out test
data. I use a fixed random seed and stratify on randomized treatment group
combined with visit outcome. This preserves experiment-arm and target balance
where feasible while keeping treatment out of the model feature matrix.

I fit preprocessing and candidate models on the training data, select
hyperparameters with the validation data, refit the selected pipeline on the
training and validation rows, and use the test data once for final evaluation.
No test row influences preprocessing, tuning, or model selection.

## Models

### Logistic regression

I use logistic regression as an interpretable baseline. It estimates a linear
relationship between features and the log-odds of a binary outcome:

```text
log(p / (1 - p)) = beta_0 + beta_1*x_1 + ... + beta_k*x_k
```

The sigmoid transformation converts the log-odds into a probability. I use
standardized numeric features and one-hot encoded categorical features so the
model can work with the mixed input data.

### Decision tree

I use a decision tree as a simple nonlinear comparison. It learns a sequence of
feature-based rules that divide customers into smaller groups. It can
represent nonlinear patterns and interactions without requiring me to specify
them in advance.

A deep tree can memorize training data, so I compare a small validation grid
of tree depths and minimum leaf sizes:

- depth 3 with minimum leaf size 1;
- depth 5 with minimum leaf size 1;
- depth 8 with minimum leaf size 5.

The selected tree is refit on the combined training and validation rows before
I evaluate it on the held-out test data.

## Hyperparameter tuning

I select candidates using validation ROC-AUC:

- Logistic regression `C`: 0.1, 1.0, and 10.0.
- Decision tree depth and minimum leaf-size combinations listed above.

I use validation-based selection rather than test-set tuning. Cross-validation
would be a useful extension for a more stable estimate, but the current
three-way split keeps the workflow easy to follow.

## Metrics

- **ROC-AUC:** ranking quality across classification thresholds.
- **Precision:** among predicted visitors, the share who actually visited.
- **Recall:** among actual visitors, the share detected by the model.
- **F1:** harmonic mean of precision and recall.
- **Log loss:** penalty for incorrect probabilities, especially confident
  incorrect predictions.
- **Brier score:** mean squared error of predicted probabilities; lower is
  better.
- **Confusion matrix:** counts of true negatives, false positives, false
  negatives, and true positives at the 0.5 threshold.

I calculate threshold metrics at 0.5 as a transparent baseline. Because
website visitation is relatively rare, I also report probability metrics and
ROC curves rather than relying on one classification threshold.

## Why calibration matters

I check calibration because a model can rank customers well while producing
probabilities that are too high or too low. If a model says 0.20 for a group
of customers, calibration asks whether about 20% of that group actually
visit. I therefore report log loss, Brier score, and a calibration plot instead
of relying on ROC-AUC alone.

I save the fitted preprocessing pipeline, selected hyperparameters, feature
names, target name, and random seed in `models/` for local reproducibility.
The directory is excluded from version control because model binaries are
generated artifacts.

## Classification versus regression

I use classification to predict a category or probability, such as whether a
customer visits (`0` or `1`). Regression predicts a continuous quantity, such
as revenue. I use classification here; revenue remains a separate analysis
because its outcome distribution is zero-inflated and right-skewed.

## Overfitting

I treat overfitting as a risk when a model learns noise or idiosyncrasies in
training rows and performs worse on new customers. The held-out test set gives
me a final check, while validation tuning prevents me from choosing a model
because it happens to fit the test sample.
