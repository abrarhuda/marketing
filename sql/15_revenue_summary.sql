-- Business question: What is average revenue per assigned customer by experiment group?
-- Techniques: GROUP BY, COUNT, SUM, AVG, CASE WHEN, and NULLIF. Every assigned
-- customer remains in the denominator, including customers with spend = 0.
-- Interpretation: These are descriptive revenue-per-assignment summaries. They
-- do not include email costs or profit margins.
SELECT
    treatment_group,
    COUNT(*) AS assigned_customers,
    SUM(COALESCE(spend, 0)) AS total_revenue,
    AVG(COALESCE(spend, 0)) AS average_revenue_per_assigned_customer,
    SUM(CASE WHEN COALESCE(spend, 0) > 0 THEN 1 ELSE 0 END) AS purchasers,
    SUM(CASE WHEN COALESCE(spend, 0) = 0 THEN 1 ELSE 0 END) AS zero_spend_customers,
    SUM(CASE WHEN COALESCE(spend, 0) = 0 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0)::DOUBLE AS zero_spend_rate
FROM customer_experiment_analysis
GROUP BY treatment_group
ORDER BY treatment_group;
