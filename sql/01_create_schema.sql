DROP VIEW IF EXISTS customer_experiment_analysis;
DROP TABLE IF EXISTS customer_outcomes;
DROP TABLE IF EXISTS experiment_assignments;
DROP TABLE IF EXISTS customers;

CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT PRIMARY KEY,
    recency INTEGER NOT NULL,
    history_segment VARCHAR NOT NULL,
    history DECIMAL(12, 2) NOT NULL,
    mens INTEGER NOT NULL,
    womens INTEGER NOT NULL,
    zip_code VARCHAR NOT NULL,
    newbie INTEGER NOT NULL,
    channel VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_assignments (
    customer_id BIGINT PRIMARY KEY,
    treatment_group VARCHAR NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS customer_outcomes (
    customer_id BIGINT PRIMARY KEY,
    visit INTEGER NOT NULL,
    conversion INTEGER NOT NULL,
    spend DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
