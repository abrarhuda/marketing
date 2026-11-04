-- Business question: How do outcomes differ between new and returning customers?
-- Techniques: CASE WHEN labels the binary newbie flag; conditional aggregation
-- counts visitors and purchasers while retaining all assigned customers.
-- Interpretation: New and returning are pre-treatment customer categories.
SELECT
    CASE WHEN newbie = 1 THEN 'New' ELSE 'Returning' END AS customer_type,
    COUNT(*) AS assigned_customers,
    SUM(CASE WHEN visit = 1 THEN 1 ELSE 0 END) AS visitors,
    SUM(CASE WHEN conversion = 1 THEN 1 ELSE 0 END) AS purchasers,
    AVG(visit)::DECIMAL(14, 4) AS visit_rate,
    AVG(conversion)::DECIMAL(14, 4) AS conversion_rate,
    AVG(COALESCE(spend, 0))::DECIMAL(14, 4) AS average_revenue_per_customer
FROM customer_experiment_analysis
GROUP BY customer_type
ORDER BY customer_type;
