"""DuckDB schema, loading, join, and integrity helpers."""

from pathlib import Path
from typing import Dict, Union

import duckdb
import pandas as pd

from .data_ingestion import PROCESSED_FILENAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DIRECTORY = PROJECT_ROOT / "sql"


def connect(database_path: Union[str, Path] = ":memory:") -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection to a database file or an in-memory database."""
    return duckdb.connect(str(database_path))


def register_dataframe(
    connection: duckdb.DuckDBPyConnection, table_name: str, data: pd.DataFrame
) -> None:
    """Register a DataFrame as a DuckDB relation for SQL queries."""
    connection.register(table_name, data)


def execute_sql_file(
    connection: duckdb.DuckDBPyConnection, filename: str
) -> None:
    """Execute a repository SQL script."""
    script_path = SQL_DIRECTORY / filename
    if not script_path.exists():
        raise FileNotFoundError(f"SQL script not found: {script_path}")
    connection.execute(script_path.read_text(encoding="utf-8"))


def build_database(
    database_path: Union[str, Path] = ":memory:",
    processed_path: Union[str, Path] = Path("data/processed") / PROCESSED_FILENAME,
) -> duckdb.DuckDBPyConnection:
    """Build the normalized DuckDB database from validated processed data."""
    data_path = Path(processed_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Processed dataset not found: {data_path}")
    data = pd.read_csv(data_path)
    connection = connect(database_path)
    try:
        register_dataframe(connection, "validated_source", data)
        execute_sql_file(connection, "01_create_schema.sql")
        execute_sql_file(connection, "02_load_data.sql")
        execute_sql_file(connection, "03_create_analytical_view.sql")
    except Exception:
        connection.close()
        raise
    return connection


def verify_database(connection: duckdb.DuckDBPyConnection) -> Dict[str, int]:
    """Verify row-preserving joins and one-to-one assignment/outcome relations."""
    checks = {
        "customer_rows": "SELECT COUNT(*) FROM customers",
        "assignment_rows": "SELECT COUNT(*) FROM experiment_assignments",
        "outcome_rows": "SELECT COUNT(*) FROM customer_outcomes",
        "analytical_rows": "SELECT COUNT(*) FROM customer_experiment_analysis",
        "customers_without_assignment": """
            SELECT COUNT(*) FROM customers c
            LEFT JOIN experiment_assignments a ON c.customer_id = a.customer_id
            WHERE a.customer_id IS NULL
        """,
        "customers_without_outcome": """
            SELECT COUNT(*) FROM customers c
            LEFT JOIN customer_outcomes o ON c.customer_id = o.customer_id
            WHERE o.customer_id IS NULL
        """,
        "assignment_rows_without_customer": """
            SELECT COUNT(*) FROM experiment_assignments a
            LEFT JOIN customers c ON a.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        """,
        "outcome_rows_without_customer": """
            SELECT COUNT(*) FROM customer_outcomes o
            LEFT JOIN customers c ON o.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        """,
    }
    results = {
        name: int(connection.execute(query).fetchone()[0])
        for name, query in checks.items()
    }
    if any(results[name] for name in checks if name.endswith("_without_assignment") or
           name.endswith("_without_outcome") or name.endswith("_without_customer")):
        raise ValueError(f"Database referential-integrity check failed: {results}")
    if results["analytical_rows"] != results["customer_rows"]:
        raise ValueError(f"Analytical view changed customer row count: {results}")
    return results


def sample_join_queries(connection: duckdb.DuckDBPyConnection) -> Dict[str, int]:
    """Run representative INNER JOIN and LEFT JOIN checks."""
    inner_join = connection.execute(
        """
        SELECT COUNT(*) FROM customers c
        INNER JOIN experiment_assignments a ON c.customer_id = a.customer_id
        INNER JOIN customer_outcomes o ON c.customer_id = o.customer_id
        """
    ).fetchone()[0]
    left_join = connection.execute(
        """
        SELECT COUNT(*) FROM customers c
        LEFT JOIN experiment_assignments a ON c.customer_id = a.customer_id
        LEFT JOIN customer_outcomes o ON c.customer_id = o.customer_id
        """
    ).fetchone()[0]
    if inner_join != left_join:
        raise ValueError(f"INNER and LEFT JOIN row counts differ: {inner_join} vs {left_join}")
    return {"inner_join_rows": int(inner_join), "left_join_rows": int(left_join)}


def run_database() -> None:
    """Build and verify the default local DuckDB database."""
    database_path = Path("data/processed") / "hillstrom.duckdb"
    connection = build_database(database_path)
    try:
        results = verify_database(connection)
        results.update(sample_join_queries(connection))
        print(f"Built {database_path} with {results['customer_rows']:,} customers.")
        print(results)
    finally:
        connection.close()
