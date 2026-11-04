-- Business question: What are visit and purchase conversion rates by group?
-- Techniques: conditional aggregation uses CASE WHEN inside AVG; NULLIF prevents
-- division by zero if a future subset has no customers.
-- Interpretation: Rates use all assigned customers as the denominator.
SELECT
    treatment_group,
    COUNT(*) AS assigned_customers,
    SUM(CASE WHEN visit = 1 THEN 1 ELSE 0 END) AS visitors,
    SUM(CASE WHEN conversion = 1 THEN 1 ELSE 0 END) AS purchasers,
    SUM(CASE WHEN visit = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)::DOUBLE
        AS visit_rate,
    SUM(CASE WHEN conversion = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)::DOUBLE
        AS conversion_rate
FROM customer_experiment_analysis
GROUP BY treatment_group
ORDER BY treatment_group;
