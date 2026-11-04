-- Business question: What percentage of assigned customers purchased after treatment?
-- Techniques: conditional aggregation and NULLIF produce a safe percentage.
-- Interpretation: This is the observed post-treatment purchase rate across all
-- assignments, not an estimate of incremental treatment effect.
SELECT
    COUNT(*) AS assigned_customers,
    SUM(CASE WHEN conversion = 1 THEN 1 ELSE 0 END) AS purchasers,
    100.0 * SUM(CASE WHEN conversion = 1 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0) AS purchaser_percentage
FROM customer_experiment_analysis;
