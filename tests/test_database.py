import pandas as pd

from marketing_ab.database import build_database, sample_join_queries, verify_database


def test_database_tables_and_joins(tmp_path) -> None:
    data = pd.DataFrame(
        [
            [1, 1, "low", 29.99, 1, 0, "Urban", 1, "Web", "No E-Mail", 0, 0, 0.0],
            [2, 2, "medium", 100.0, 0, 1, "Urban", 0, "Phone", "Mens E-Mail", 1, 1, 20.0],
            [3, 3, "high", 300.0, 1, 1, "Surburban", 1, "Web", "Womens E-Mail", 1, 0, 0.0],
        ],
        columns=[
            "customer_id",
            "recency",
            "history_segment",
            "history",
            "mens",
            "womens",
            "zip_code",
            "newbie",
            "channel",
            "segment",
            "visit",
            "conversion",
            "spend",
        ],
    )
    source_path = tmp_path / "validated.csv"
    data.to_csv(source_path, index=False)

    connection = build_database(tmp_path / "test.duckdb", source_path)
    try:
        results = verify_database(connection)
        joins = sample_join_queries(connection)
        assert results["customer_rows"] == 3
        assert results["assignment_rows"] == 3
        assert results["outcome_rows"] == 3
        assert results["analytical_rows"] == 3
        assert joins == {"inner_join_rows": 3, "left_join_rows": 3}
        aggregate = connection.execute(
            """
            SELECT treatment_group, COUNT(*) AS customers, SUM(visit) AS visitors
            FROM customer_experiment_analysis
            GROUP BY treatment_group
            ORDER BY treatment_group
            """
        ).fetchdf()
        assert aggregate.to_dict("records") == [
            {"treatment_group": "Mens E-Mail", "customers": 1, "visitors": 1},
            {"treatment_group": "No E-Mail", "customers": 1, "visitors": 0},
            {"treatment_group": "Womens E-Mail", "customers": 1, "visitors": 1},
        ]
        assert connection.execute(
            "SELECT COUNT(*) FROM pragma_table_info('customers')"
        ).fetchone()[0] == 9
    finally:
        connection.close()
