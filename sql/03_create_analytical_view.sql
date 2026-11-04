CREATE OR REPLACE VIEW customer_experiment_analysis AS
SELECT
    c.customer_id,
    c.recency,
    c.history_segment,
    c.history,
    c.mens,
    c.womens,
    c.zip_code,
    c.newbie,
    c.channel,
    a.treatment_group,
    o.visit,
    o.conversion,
    o.spend
FROM customers AS c
INNER JOIN experiment_assignments AS a
    ON c.customer_id = a.customer_id
INNER JOIN customer_outcomes AS o
    ON c.customer_id = o.customer_id;
