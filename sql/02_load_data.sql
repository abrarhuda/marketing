INSERT INTO customers (
    customer_id, recency, history_segment, history, mens, womens,
    zip_code, newbie, channel
)
SELECT
    customer_id,
    CAST(recency AS INTEGER),
    CAST(history_segment AS VARCHAR),
    CAST(history AS DECIMAL(12, 2)),
    CAST(mens AS INTEGER),
    CAST(womens AS INTEGER),
    CAST(zip_code AS VARCHAR),
    CAST(newbie AS INTEGER),
    CAST(channel AS VARCHAR)
FROM validated_source;

INSERT INTO experiment_assignments (customer_id, treatment_group)
SELECT customer_id, CAST(segment AS VARCHAR)
FROM validated_source;

INSERT INTO customer_outcomes (customer_id, visit, conversion, spend)
SELECT
    customer_id,
    CAST(visit AS INTEGER),
    CAST(conversion AS INTEGER),
    CAST(spend AS DECIMAL(12, 2))
FROM validated_source;
