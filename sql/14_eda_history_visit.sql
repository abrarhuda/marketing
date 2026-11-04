-- Business question: How does historical spending relate to website visitation?
-- Techniques: CTE plus CASE WHEN creates history bands; conditional aggregation
-- compares visitor and non-visitor counts within each band.
-- Interpretation: This describes association between pre-campaign history and
-- post-campaign visitation; it does not establish that history caused visits.
WITH history_bands AS (
    SELECT
        *,
        CASE
            WHEN history < 100 THEN '01_under_100'
            WHEN history < 500 THEN '02_100_to_499'
            WHEN history < 1000 THEN '03_500_to_999'
            ELSE '04_1000_or_more'
        END AS history_band
    FROM customer_experiment_analysis
    WHERE history IS NOT NULL
)
SELECT
    history_band,
    COUNT(*) AS assigned_customers,
    AVG(history)::DECIMAL(14, 4) AS average_historical_spend,
    SUM(CASE WHEN visit = 1 THEN 1 ELSE 0 END) AS visitors,
    SUM(CASE WHEN visit = 0 THEN 1 ELSE 0 END) AS non_visitors,
    AVG(visit)::DECIMAL(14, 4) AS visit_rate
FROM history_bands
GROUP BY history_band
ORDER BY history_band;
