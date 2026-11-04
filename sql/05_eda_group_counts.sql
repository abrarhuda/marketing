-- Business question: How many assigned customers are in each experiment group?
-- Techniques: GROUP BY counts rows; ORDER BY makes the output easy to compare.
-- Interpretation: These are assignment counts, not counts of customers who responded.
SELECT
    treatment_group,
    COUNT(*) AS assigned_customers
FROM customer_experiment_analysis
GROUP BY treatment_group
ORDER BY treatment_group;
