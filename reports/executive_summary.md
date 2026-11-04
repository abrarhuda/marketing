# Executive Summary

## 1. Executive Summary

This project analyzed Kevin Hillstrom's randomized MineThatData email
experiment, covering 64,000 customers assigned to No E-Mail, Mens E-Mail, or
Womens E-Mail. The analysis measured website visits, purchases, and revenue;
tested treatment-versus-control differences; built predictive models; and
evaluated whether customer-level uplift targeting could improve campaign
responsiveness.

The central business conclusion is straightforward: promotional email
increased engagement in this experiment, with Mens E-Mail performing best on
the main website-visit outcome. The uplift model produced a targeting policy
that was slightly better than always sending Mens E-Mail in point estimate,
but the difference was too uncertain to establish a clear advantage. The
results support email experimentation and favor Mens E-Mail as the current
simple benchmark, not an unqualified claim that personalized targeting or
profitability has been proven.

The five major takeaways are:

1. Promotional email increased website visits, with Mens E-Mail strongest.
2. Conversion and average revenue were also higher after email, but revenue is
   not profit.
3. The primary visit-rate differences are statistically convincing.
4. Logistic regression provided modest predictive ranking ability.
5. Uplift targeting did not clearly outperform always sending Mens E-Mail.

## 2. Experimental Results

### Website visits

Website visit rates were:

- No E-Mail: **10.62%**
- Mens E-Mail: **18.28%**
- Womens E-Mail: **15.14%**

Compared with No E-Mail, the estimated absolute visit-rate effects were:

- Mens E-Mail: **+7.66 percentage points**
- Womens E-Mail: **+4.52 percentage points**

The experiment groups were approximately balanced, with about 21,300
customers in each group. This supports a fair randomized comparison.

### Purchases and revenue

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

Statistical significance means the observed differences are unlikely to be
explained by random assignment variation alone under the stated test
assumptions. It does not establish campaign profitability, long-term customer
value, or the same result in every future audience.

## 4. Machine Learning Results

### Predictive model performance

The logistic regression model performed better than the random forest on the
held-out website-visit prediction task:

- Logistic regression ROC-AUC: **0.627**
- Random forest ROC-AUC: **0.593**

Logistic regression also had lower log loss (**0.405 versus 0.415**) and a
lower Brier score (**0.122 versus 0.125**). Both models predicted no positive
customers at the default 0.50 probability threshold, so their probabilities
and rankings are more useful than a simple threshold classification.

### Uplift targeting

The three-arm logistic-regression T-Learner estimated visit probabilities under
No E-Mail, Mens E-Mail, and Womens E-Mail for each held-out customer. Policy
performance was estimated with inverse-propensity weighting using the known
one-third randomized assignment probabilities:

- No E-Mail for everyone: **10.59%**
- Mens E-Mail for everyone: **18.26%**
- Womens E-Mail for everyone: **15.19%**
- Highest positive estimated uplift: **18.49%**

The model-based policy was estimated **3.30 percentage points above
always-Womens**, with a bootstrap 95% interval of **+1.97 to +4.80 points**.
However, its estimated advantage over always-Mens was only **+0.23 points**,
with an interval of **-0.84 to +1.27 points**. Therefore, the model did not
demonstrate a statistically clear improvement over simply sending Mens E-Mail
to everyone.

The uplift model's ranking curves showed positive estimated incremental visits
relative to all-control, but the largest gains occurred close to broad
targeting rather than only in a small high-response group. The model's
recommendations are modeled counterfactual estimates, not directly observed
individual treatment effects.

## 5. Business Recommendations

Mens E-Mail is the appropriate current benchmark for broad promotional
testing because it led on visits, conversions, revenue per assigned customer,
and simple-policy visit rate. Future campaigns should retain a randomized
No E-Mail holdout so incremental performance is measured directly. Personalized
uplift targeting should remain an experimental challenger rather than replace
the Mens policy: it exceeded all-control and always-Womens, but did not clearly
beat always-Mens. Recent and historically higher-value customers are sensible
segments for additional randomized tests, but not automatic exclusion rules.
Finally, no profitability decision should be approved without campaign costs,
margins, unsubscribe effects, and longer-term customer value.

## 6. Limitations

- The experiment measures one observed outcome per customer. The other
  treatment outcomes are counterfactual and cannot be directly checked for the
  same person.
- Uplift estimates can reflect model misspecification, sampling noise, and
  regularization. Different predicted uplift values do not prove causal
  heterogeneity.
- The held-out uplift evaluation used inverse-propensity weighting and
  customer-level bootstrap intervals. It did not compare raw outcomes among
  model-recommended and non-recommended customers, which would be misleading
  because those groups need not be randomized.
- The bootstrap quantifies evaluation-sample uncertainty but does not capture
  every uncertainty from model choice, feature design, or future audience
  changes.
- Revenue is highly zero-inflated and right-skewed. Average revenue is
  informative but not a complete financial evaluation.
- The dataset does not provide campaign cost, gross margin, unsubscribe
  behavior, repeat purchases, or long-term customer value. No ROI, savings, or
  profitability claim is made.

## 7. Next Steps

1. Run a prospective holdout experiment comparing broad Mens E-Mail with the
   proposed uplift-targeting policy, while preserving a No E-Mail control.
2. Predefine the primary outcome, policy comparison, sample size, and
   decision threshold before opening the next test set.
3. Capture email delivery, opens, clicks, unsubscribes, order margin, and
   longer-term revenue so business value can be evaluated rather than visits
   alone.
4. Validate whether recent and high historical-value customer segments show
   reproducible incremental treatment effects in a new randomized sample.
5. Reassess the uplift model only after collecting a new test set; do not
   repeatedly tune the model against the current held-out results.
