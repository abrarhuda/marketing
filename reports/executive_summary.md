# Executive Summary

## 1. Executive Summary

I analyzed Kevin Hillstrom's randomized MineThatData email experiment, covering
64,000 customers assigned to No E-Mail, Mens E-Mail, or Womens E-Mail. I
measured website visits, purchases, and revenue; tested
treatment-versus-control differences; and trained introductory
scikit-learn models to predict website visits from pretreatment customer
attributes.

My central business conclusion is straightforward: promotional email increased
engagement in this experiment, with Mens E-Mail performing best on the main
website-visit outcome. I use the models as an introduction to classification
and to rank customers by predicted visit probability. I keep this prediction
task separate from estimating the effect of a different email assignment.

The five major takeaways are:

1. Promotional email increased website visits, with Mens E-Mail strongest.
2. Conversion and average revenue were also higher after email, but revenue is
   not profit.
3. The primary visit-rate differences are statistically convincing.
4. Logistic regression performed better than the decision tree on the held-out
   baseline prediction task.
5. Predictive rankings should support future testing, not replace randomized
   measurement.

## 2. Experimental Results

Website visit rates were:

- No E-Mail: **10.62%**
- Mens E-Mail: **18.28%**
- Womens E-Mail: **15.14%**

Compared with No E-Mail, the estimated absolute visit-rate effects were:

- Mens E-Mail: **+7.66 percentage points**
- Womens E-Mail: **+4.52 percentage points**

Purchase conversion rates were:

- No E-Mail: **0.57%**
- Mens E-Mail: **1.25%**
- Womens E-Mail: **0.88%**

Average revenue per assigned customer, including customers who spent $0, was:

- No E-Mail: **$0.65**
- Mens E-Mail: **$1.42**
- Womens E-Mail: **$1.08**

Bootstrap 95% confidence intervals for the average-revenue differences versus
No E-Mail were **$0.50 to $1.07** for Mens E-Mail and **$0.18 to $0.69** for
Womens E-Mail. These are revenue differences, not profit or ROI estimates.

## 3. Statistical Confidence

The primary outcome was website visitation because visits are more common and
therefore provide more information than purchases. Both treatment-versus-control
visit comparisons remained statistically significant after Holm correction for
the two primary tests, using a 0.05 threshold. The confidence intervals were
approximately **+7.00 to +8.32 percentage points** for Mens E-Mail and
**+3.89 to +5.16 points** for Womens E-Mail.

The conversion analysis was designated exploratory secondary analysis. Its
estimated effects were also positive, but the low purchase rate means the
results are less stable than the visit analysis. Revenue intervals were
estimated with 2,000 customer-level bootstrap resamples and remained above
zero for both promotional emails.

Statistical significance does not establish campaign profitability, long-term
customer value, or the same result in every future audience.

## 4. Machine Learning Results

The classification models predict website visits using only pretreatment
features. Logistic regression performed better than the decision tree on the
held-out test set:

- Logistic regression ROC-AUC: **0.627**
- Decision tree ROC-AUC: **0.606**
- Logistic regression log loss: **0.405**
- Decision tree log loss: **0.408**
- Logistic regression Brier score: **0.122**
- Decision tree Brier score: **0.123**

Both models predicted no positive customers at the default 0.50 probability
threshold because the visit outcome is relatively rare. Their probability
metrics and rankings are more useful than a single threshold classification.

These results describe prediction performance. A customer with a high
predicted visit probability is not necessarily a customer whose behavior would
change after receiving an email.

## 5. Business Recommendations

1. Use Mens E-Mail as the current simple benchmark because it led on visits,
   conversions, and revenue per assigned customer in this experiment.
2. Preserve a randomized No E-Mail holdout in future campaigns so incremental
   performance can be measured directly.
3. Use the introductory models for learning, prioritization, and planning
   experiments rather than as proof of individual customer response.
4. Do not approve a profitability decision without campaign costs, margins,
   unsubscribe effects, and longer-term customer value.
5. Validate any proposed customer segment or decision threshold in a new
   randomized sample before operational use.

## 6. Limitations

- I use the models to predict visits rather than estimate individual treatment
  effects.
- The available pretreatment features may not contain enough information for
  strong customer-level prediction.
- Revenue is highly zero-inflated and right-skewed. Average revenue is
  informative but not a complete financial evaluation.
- The dataset does not provide campaign cost, gross margin, unsubscribe
  behavior, repeat purchases, or long-term customer value.
- The experiment is historical and may not represent a future audience or
  channel mix.

## 7. Next Steps

1. Predefine a primary outcome, decision threshold, and sample-size target for
   a prospective follow-up experiment.
2. Capture email delivery, opens, clicks, unsubscribes, order margin, and
   longer-term revenue.
3. Compare model-assisted targeting rules with simple benchmark policies in a
   new randomized sample.
4. Evaluate additional feature engineering and probability-threshold choices
   using validation data only.
5. Monitor model performance after deployment for drift and calibration.
