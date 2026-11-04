-- Business question: How does historical spending differ between groups?
-- Techniques: GROUP BY summarizes baseline history; percentile functions are
-- useful for skewed spending distributions.
-- Interpretation: History is pre-campaign spending, so this is descriptive balance
-- information rather than a treatment effect.
SELECT
    treatment_group,
    COUNT(*) AS assigned_customers,
    AVG(history)::DECIMAL(14, 4) AS average_historical_spend,
    MIN(history)::DECIMAL(14, 2) AS minimum_historical_spend,
    MAX(history)::DECIMAL(14, 2) AS maximum_historical_spend,
    MEDIAN(history)::DECIMAL(14, 2) AS median_historical_spend
FROM customer_experiment_analysis
GROUP BY treatment_group
ORDER BY average_historical_spend DESC;
