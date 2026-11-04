# Predictive modeling methodology

## Objective and feature boundary

The models predict whether a customer visits the website. The target is
`visit`.

The only input features are historical, pre-treatment attributes:

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

Treatment assignment is excluded from this initial predictive baseline. The
assignment is used only to preserve balance when making the data splits. The
post-treatment fields `visit`, `conversion`, and `spend` are never passed to a
model as input features.

## Data splitting and leakage prevention

The data is split into:

- 60% training data;
- 20% validation data;
- 20% held-out test data.

Splits use a fixed random seed and stratify on the combination of randomized
treatment group and visit outcome. This preserves both experiment-arm and
target balance where feasible, while keeping treatment out of the model
feature matrix.

The training data fits preprocessing and candidate models. The validation
data selects hyperparameters. After selection, the winning pipeline is
refit on training plus validation rows. The test data is used once for final
evaluation. No test row influences preprocessing, tuning, or model selection.

## Models

### Logistic regression

Logistic regression estimates a linear relationship between features and the
log-odds of a binary outcome:

\[
\log\left(\frac{p}{1-p}\right)
= \beta_0 + \beta_1 x_1 + \cdots + \beta_k x_k
\]

The sigmoid transformation converts the log-odds into a probability. Logistic
regression is a useful baseline because it is relatively interpretable and
often produces reasonable probabilities when the relationship is
approximately additive.

Numerical features are standardized for logistic regression. Categorical
features are one-hot encoded, meaning each category becomes a model-ready
indicator column.

### Random forest

A random forest combines many decision trees. Each tree learns nonlinear
feature rules, and the forest averages their predictions. Random forests can
capture interactions and thresholds without requiring those relationships to
be specified manually.

The small validation grid changes tree depth and minimum leaf size. Larger
trees can fit more detail but may overfit.

## Hyperparameter tuning

The pipeline tunes a small set of candidates using validation ROC-AUC:

- Logistic regression `C`: 0.1, 1.0, 10.0.
- Random forest:
  - unlimited depth with leaf size 1;
  - depth 12 with leaf size 1;
  - depth 12 with leaf size 5.

This is explicit validation-based selection rather than test-set tuning.
Cross-validation is a useful extension when a more stable estimate is needed,
but the current three-way split makes the learning workflow easy to follow.

## Metrics

- **ROC-AUC:** ranking quality across classification thresholds. It is not
  sufficient alone because it does not measure probability calibration or
  business-threshold performance.
- **Precision:** among predicted visitors, the share who actually visited.
- **Recall:** among actual visitors, the share detected by the model.
- **F1:** harmonic mean of precision and recall.
- **Log loss:** penalizes incorrect probabilities, especially confident
  incorrect predictions.
- **Brier score:** mean squared error of predicted probabilities; lower is
  better.
- **Confusion matrix:** counts true negatives, false positives, false
  negatives, and true positives at the 0.5 threshold.

The reported precision, recall, F1 score, and confusion matrix use a
probability threshold of 0.5. This transparent default is not necessarily the
best business threshold for a relatively rare outcome such as website
visitation. Probability metrics and ROC curves preserve information across
thresholds.

## Why calibration matters

A model can rank customers well while producing probabilities that are too
high or too low. If a model says 0.20 for a group of customers, calibration
asks whether about 20% of that group actually visit. Calibrated probabilities
are important for capacity planning, expected-value decisions, and future
future decision-making. The pipeline therefore reports log loss, Brier score, and a
calibration plot rather than relying on ROC-AUC alone.

The saved model bundles contain the fitted preprocessing pipeline, selected
hyperparameters, feature names, target name, and random seed. They are written
to `models/` for local reproducibility, and that directory is excluded from
version control because model binaries are generated artifacts.

## Classification versus regression

Classification predicts a category or probability, such as whether a customer
visits (`0` or `1`). Regression predicts a continuous quantity, such as
revenue. This pipeline is a classification task; revenue modeling belongs to
a separate analysis because its outcome distribution is zero-inflated and
right-skewed.

## Overfitting

Overfitting occurs when a model learns noise or idiosyncrasies in its training
rows and performs worse on new customers. A held-out test set provides an
honest final check, while validation tuning helps avoid choosing a model
because it happens to fit the test sample.
