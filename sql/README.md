# SQL scripts

DuckDB schema, loading, quality-check, and analysis queries are organized in
numbered scripts:

- `01_create_schema.sql` defines three normalized tables.
- `02_load_data.sql` loads the validated pandas relation.
- `03_create_analytical_view.sql` creates the consolidated analytical view.
- `04_quality_checks.sql` contains referential-integrity and row-count queries.

The source is one denormalized CSV row per experimental assignment and outcome.
The tables separate customer baseline attributes, randomized treatment
assignment, and post-assignment outcomes. `customer_id` is a stable surrogate
based on source row position; it is not an identifier supplied by Hillstrom.

`customers.customer_id` is the primary key. The other two tables use the same
key as both a primary key and foreign key, enforcing one assignment and one
outcome per represented source row. This is a one-to-one relational
representation, not evidence that the source contained customer events or
timestamps.

The schema script drops and recreates these project tables so rebuilding a
local database from a new validated input is deterministic. It does not alter
the raw or processed CSV files.

EDA queries are in `05_eda_*.sql` through `14_eda_*.sql`. They are executed by
`marketing-ab-eda` and exported to `reports/tables/`.
