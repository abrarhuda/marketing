-- Business question: How do purchase behavior and engagement vary by recency?
-- Techniques: CASE WHEN creates interpretable recency buckets; CTEs make the
-- derived classification reusable in the aggregate query.
-- Interpretation: Lower recency means a more recent prior purchase in this dataset.
WITH recency_buckets AS (
    SELECT
        *,
        CASE
            WHEN recency <= 3 THEN '01_recent_1_to_3'
            WHEN recency <= 6 THEN '02_middle_4_to_6'
            ELSE '03_older_7_to_12'
        END AS recency_bucket
    FROM customer_experiment_analysis
)
SELECT
    recency_bucket,
    COUNT(*) AS assigned_customers,
    AVG(visit)::DECIMAL(14, 4) AS visit_rate,
    AVG(conversion)::DECIMAL(14, 4) AS conversion_rate,
    AVG(COALESCE(spend, 0))::DECIMAL(14, 4) AS average_revenue_per_customer
FROM recency_buckets
GROUP BY recency_bucket
ORDER BY recency_bucket;
