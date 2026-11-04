"""DuckDB-first exploratory analysis queries and CSV export."""

from pathlib import Path
from typing import Dict, Iterable, Union

import duckdb

from .database import SQL_DIRECTORY, build_database

EDA_QUERY_FILES = (
    "05_eda_group_counts.sql",
    "06_eda_group_outcomes.sql",
    "07_eda_revenue.sql",
    "08_eda_history_by_group.sql",
    "09_eda_channel_outcomes.sql",
    "10_eda_recency_outcomes.sql",
    "11_eda_new_vs_returning.sql",
    "12_eda_history_segments.sql",
    "13_eda_purchase_percentage.sql",
    "14_eda_history_visit.sql",
)


def _output_name(sql_filename: str) -> str:
    stem = Path(sql_filename).stem
    return stem.split("_eda_", 1)[-1] + ".csv"


def export_eda_tables(
    connection: duckdb.DuckDBPyConnection,
    output_directory: Union[str, Path] = Path("reports/tables"),
    query_files: Iterable[str] = EDA_QUERY_FILES,
) -> Dict[str, Path]:
    """Execute EDA SQL files and export each result to a CSV."""
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    exported: Dict[str, Path] = {}
    for query_file in query_files:
        query_path = SQL_DIRECTORY / query_file
        query = query_path.read_text(encoding="utf-8")
        result = connection.execute(query).fetchdf()
        destination = output_path / _output_name(query_file)
        result.to_csv(destination, index=False)
        exported[query_file] = destination
    return exported


def validate_eda_metrics(connection: duckdb.DuckDBPyConnection) -> Dict[str, int]:
    """Validate core EDA totals and rate bounds before exporting results."""
    customer_count = int(
        connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    )
    group_total = int(
        connection.execute(
            "SELECT COUNT(*) FROM customer_experiment_analysis GROUP BY treatment_group"
        ).fetchdf().sum(numeric_only=True).iloc[0]
    )
    outcome_total = int(
        connection.execute("SELECT COUNT(*) FROM customer_experiment_analysis").fetchone()[0]
    )
    invalid_rates = int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT treatment_group, AVG(visit) AS visit_rate,
                       AVG(conversion) AS conversion_rate
                FROM customer_experiment_analysis
                GROUP BY treatment_group
            )
            WHERE visit_rate NOT BETWEEN 0 AND 1
               OR conversion_rate NOT BETWEEN 0 AND 1
            """
        ).fetchone()[0]
    )
    if group_total != customer_count or outcome_total != customer_count:
        raise ValueError(
            f"EDA totals do not reconcile: customers={customer_count}, "
            f"group_total={group_total}, outcomes={outcome_total}"
        )
    if invalid_rates:
        raise ValueError(f"Found {invalid_rates} group rows with invalid rates")
    return {
        "customer_count": customer_count,
        "group_total": group_total,
        "outcome_total": outcome_total,
        "invalid_rate_rows": invalid_rates,
    }


def run_eda() -> None:
    """Build the default database, validate metrics, and export EDA tables."""
    connection = build_database(Path("data/processed") / "hillstrom.duckdb")
    try:
        metrics = validate_eda_metrics(connection)
        exported = export_eda_tables(connection)
        print(f"Validated EDA metrics: {metrics}")
        print(f"Exported {len(exported)} EDA tables to reports/tables.")
    finally:
        connection.close()
