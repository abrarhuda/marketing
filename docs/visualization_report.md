# Marketing analysis visualization report

I generate the figures in `reports/figures/` with the reusable module
`marketing_ab.visualizations`. I regenerate them with:

```bash
source .venv/bin/activate
marketing-ab-visualizations
```

All figures use real saved analysis outputs. The charts do not contain
fabricated observations or model results.

## Figure interpretations

### 1. Experimental group sizes

The three randomized groups are close in size: 21,306 No E-Mail customers,
21,307 Mens E-Mail customers, and 21,387 Womens E-Mail customers. This supports
the intended approximately equal assignment and avoids treating group-size
differences as campaign effects.

### 2. Website visit rates by treatment group

Mens E-Mail has the highest observed visit rate at 18.28%, followed by Womens
E-Mail at 15.14% and No E-Mail at 10.62%. These are assigned-customer rates,
not purchaser-only rates. The randomized design supports treatment-versus-control
causal interpretation at the population level, subject to the retrospective
analysis limitations.

### 3. Purchase conversion rates by treatment group

Purchase conversion is rarer than visitation. Mens E-Mail has a 1.25%
conversion rate, Womens E-Mail has 0.88%, and No E-Mail has 0.57%. The chart
shows the outcome difference, while the statistical report supplies the
uncertainty and multiple-testing context.

### 4. Absolute treatment effects with 95% confidence intervals

Relative to No E-Mail, the estimated visit-rate effect is 7.66 percentage
points for Mens E-Mail, with a 95% interval of 7.00 to 8.32 points. The
Womens E-Mail effect is 4.52 points, with a 95% interval of 3.89 to 5.16
points. These are absolute percentage-point effects, not relative percentage
lifts.

### 5. Average customer revenue

Average revenue per assigned customer is $1.42 for Mens E-Mail, $1.08 for
Womens E-Mail, and $0.65 for No E-Mail. The denominator includes all
randomized customers, including those with zero spend. Higher revenue is not
automatically profit because campaign costs and margins are unavailable.

### 6. Historical spending distribution

The overlaid distributions show that my pretreatment historical spending is
similarly shaped across the randomized groups. The distributions are strongly
right-skewed, with most customers at relatively low historical spend and a
small high-spend tail. This skew explains why revenue uncertainty is more
difficult to summarize than a binary visit outcome.

### 7. Campaign results by customer segment

I use the chart to show visit rates by the dataset's historical purchase-value
segments and experiment group. Higher historical-value segments generally have
higher engagement, and Mens E-Mail is above No E-Mail across the displayed
segments. This is descriptive segmentation evidence; it is not a separate
causal claim for every subgroup.

### 8. Logistic regression versus decision tree performance

On the held-out predictive test set, logistic regression has ROC-AUC 0.627,
log loss 0.405, and Brier score 0.122. The decision tree has ROC-AUC 0.606,
log loss 0.408, and Brier score 0.123. Logistic regression therefore performs
better on these ranking and probability metrics. Neither model predicted a
positive class at the default 0.5 threshold, so ROC-AUC and probability
metrics are more informative here than threshold metrics alone.

### 9. ROC curves and probability calibration

I use the ROC chart to compare discrimination across thresholds and the
calibration chart to compare predicted visit probabilities with observed visit
frequencies. I interpret both alongside ROC-AUC, log loss, and Brier score.
The plots use my saved final model bundles and held-out test split.

## Design and reproducibility notes

- PNG files use a consistent 8.5 by 5.5 inch base size and 220 DPI.
- Group colors and model colors are consistent across charts.
- Percentages use percentage formatting and treatment effects use percentage
  points.
- Revenue charts use dollar formatting.
- Confidence intervals are shown wherever saved analysis outputs provide them.
- The reserved test set is not used to retune the predictive models.
