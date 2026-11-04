-- These queries are intentionally result-producing checks used by Python.
SELECT COUNT(*) AS customers_without_assignment
FROM customers AS c
LEFT JOIN experiment_assignments AS a ON c.customer_id = a.customer_id
WHERE a.customer_id IS NULL;

SELECT COUNT(*) AS customers_without_outcome
FROM customers AS c
LEFT JOIN customer_outcomes AS o ON c.customer_id = o.customer_id
WHERE o.customer_id IS NULL;

SELECT COUNT(*) AS assignment_rows_without_customer
FROM experiment_assignments AS a
LEFT JOIN customers AS c ON a.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

SELECT COUNT(*) AS outcome_rows_without_customer
FROM customer_outcomes AS o
LEFT JOIN customers AS c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

SELECT
    (SELECT COUNT(*) FROM customers) AS customer_rows,
    (SELECT COUNT(*) FROM experiment_assignments) AS assignment_rows,
    (SELECT COUNT(*) FROM customer_outcomes) AS outcome_rows,
    (SELECT COUNT(*) FROM customer_experiment_analysis) AS analytical_rows;
