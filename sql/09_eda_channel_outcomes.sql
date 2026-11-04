-- Business question: How do campaign outcomes vary by historical purchase channel?
-- Techniques: GROUP BY uses two dimensions; LEFT JOIN keeps channel categories
-- even if a future filtered outcome table has no matching result.
-- Interpretation: Compare response metrics within channel and treatment group.
WITH channel_customers AS (
    SELECT customer_id, channel
    FROM customers
),
channel_outcomes AS (
    SELECT customer_id, treatment_group, visit, conversion, spend
    FROM customer_experiment_analysis
)
SELECT
    cc.channel,
    co.treatment_group,
    COUNT(cc.customer_id) AS assigned_customers,
    SUM(CASE WHEN co.visit = 1 THEN 1 ELSE 0 END) AS visitors,
    SUM(CASE WHEN co.conversion = 1 THEN 1 ELSE 0 END) AS purchasers,
    AVG(COALESCE(co.spend, 0))::DECIMAL(14, 4) AS average_revenue_per_customer,
    SUM(CASE WHEN co.visit = 1 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(cc.customer_id), 0)::DOUBLE AS visit_rate,
    SUM(CASE WHEN co.conversion = 1 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(cc.customer_id), 0)::DOUBLE AS conversion_rate
FROM channel_customers AS cc
LEFT JOIN channel_outcomes AS co ON cc.customer_id = co.customer_id
GROUP BY cc.channel, co.treatment_group
ORDER BY cc.channel, co.treatment_group;
