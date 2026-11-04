from marketing_ab.database import build_database
from marketing_ab.eda import export_eda_tables, validate_eda_metrics


def test_eda_metrics_and_exports(tmp_path) -> None:
    database = build_database()
    try:
        metrics = validate_eda_metrics(database)
        assert metrics == {
            "customer_count": 64000,
            "group_total": 64000,
            "outcome_total": 64000,
            "invalid_rate_rows": 0,
        }
        exported = export_eda_tables(database, tmp_path)
        assert len(exported) == 10
        assert all(path.exists() for path in exported.values())
        assert all(path.stat().st_size > 0 for path in exported.values())
    finally:
        database.close()
