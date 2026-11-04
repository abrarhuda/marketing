# Predictive modeling methodology

## Objective and feature boundary

The models predict whether a customer visits the website. The target is
`visit`.

The models use only these historical, pre-treatment attributes:

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

Treatment assignment is excluded from the predictive features and is used only
to preserve balance when making the data splits. The post-treatment fields
`visit`, `conversion`, and `spend` are never passed into a model.

## Data splitting and leakage prevention

The data is split into 60% training, 20% validation, and 20% held-out test
data. A fixed random seed is used, with stratification on randomized treatment
group combined with visit outcome. This preserves experiment-arm and target
balance where feasible while keeping treatment out of the model feature matrix.

Preprocessing and candidate models are fit on the training data. The
validation data selects hyperparameters, the selected pipeline is refit on the
training and validation rows, and the test data is used once for final
evaluation. No test row influences preprocessing, tuning, or model selection.

## Models

### Logistic regression

Logistic regression estimates the probability of a website visit from a
weighted combination of customer features. The model first calculates:

```text
z = beta_0 + beta_1*x_1 + beta_2*x_2 + ... + beta_k*x_k
```

The score becomes a probability between 0 and 1 through the sigmoid function:

```text
p(visit = 1) = 1 / (1 + e^(-z))
```

This model fits the binary visit target and provides probabilities that can be
compared with observed visit rates. Numeric features are standardized and
categorical features are one-hot encoded before the calculation.

### Decision tree

A decision tree predicts a class by applying a sequence of simple feature
rules. A split might ask whether `history` is below a chosen value. The split
creates smaller groups, and each final leaf estimates:

```text
predicted visit probability =
number of visitors in the leaf / number of customers in the leaf
```

This model fits the customer data because visit behavior can vary across
simple thresholds in history, recency, or other features. A small validation
grid compares tree depths and minimum leaf sizes:

- depth 3 with minimum leaf size 1;
- depth 5 with minimum leaf size 1;
- depth 8 with minimum leaf size 5.

The selected tree is refit on the combined training and validation rows before
evaluation on the held-out test data.

## Hyperparameter tuning

Candidates are selected using validation ROC-AUC:

- Logistic regression `C`: 0.1, 1.0, and 10.0.
- Decision tree depth and minimum leaf-size combinations listed above.

Validation data selects model settings. The test set is reserved for final
evaluation. Cross-validation could provide a more stable estimate in future
work, while the current three-way split keeps the workflow easy to follow.

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

Threshold metrics are calculated at 0.5 as a transparent baseline. Because
website visitation is relatively rare, the project also reports probability
metrics and ROC curves. These metrics show performance across classification
thresholds.

## Why calibration matters

Calibration is checked because a model can rank customers well while producing
probabilities that are too high or too low. If a model says 0.20 for a group
of customers, calibration asks whether about 20% of that group actually
visit. The project therefore reports log loss, Brier score, and a calibration plot instead
of relying on ROC-AUC alone.

The fitted preprocessing pipeline, selected hyperparameters, feature
names, target name, and random seed in `models/` for local reproducibility.
The directory is excluded from version control because model binaries are
generated artifacts.

## Classification versus regression

Classification predicts a category or probability, such as whether a customer
visits (`0` or `1`). Regression predicts a continuous quantity, such as
revenue. This project uses classification because the main machine-learning
target is a yes-or-no visit outcome.

## Overfitting

Overfitting occurs when a model learns noise or idiosyncrasies in training rows
and performs worse on new customers. The held-out test set provides a final
check, while validation tuning prevents selection based on test-sample fit.
