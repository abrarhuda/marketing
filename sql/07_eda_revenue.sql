-- Business question: What is average revenue per assigned customer by group?
-- Techniques: COALESCE handles a possible NULL spend; AVG and SUM summarize
-- customer-level outcomes without conditioning on purchase.
-- Interpretation: This is revenue per assigned customer, including zero spend.
SELECT
    treatment_group,
    COUNT(*) AS assigned_customers,
    COALESCE(SUM(spend), 0)::DECIMAL(14, 2) AS total_revenue,
    COALESCE(AVG(spend), 0)::DECIMAL(14, 4) AS average_revenue_per_assigned_customer
FROM customer_experiment_analysis
GROUP BY treatment_group
ORDER BY average_revenue_per_assigned_customer DESC;
