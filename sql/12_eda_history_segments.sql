-- Business question: Which customer segments have the highest historical spending?
-- Techniques: ROW_NUMBER ranks customers within channel; PERCENT_RANK gives a
-- relative position from 0 to 1 without discarding any observations.
-- Interpretation: The output is a ranked sample of the top historical spenders
-- in each channel, not a causal campaign result.
WITH ranked_customers AS (
    SELECT
        customer_id,
        channel,
        history_segment,
        history,
        ROW_NUMBER() OVER (
            PARTITION BY channel ORDER BY history DESC, customer_id
        ) AS channel_spend_rank,
        PERCENT_RANK() OVER (
            PARTITION BY channel ORDER BY history
        ) AS channel_spend_percent_rank
    FROM customers
    WHERE history IS NOT NULL
)
SELECT
    channel,
    history_segment,
    COUNT(*) AS customers_in_segment,
    AVG(history)::DECIMAL(14, 4) AS average_historical_spend,
    MAX(history)::DECIMAL(14, 2) AS maximum_historical_spend,
    MIN(channel_spend_rank) AS highest_rank_in_channel,
    AVG(channel_spend_percent_rank)::DECIMAL(14, 4) AS average_percentile_in_channel
FROM ranked_customers
GROUP BY channel, history_segment
ORDER BY average_historical_spend DESC, channel;
