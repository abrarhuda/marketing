import pandas as pd

from marketing_ab.database import build_database
from marketing_ab.eda import export_eda_tables, validate_eda_metrics


def test_eda_metrics_and_exports(tmp_path) -> None:
    processed_path = tmp_path / "hillstrom_validated.csv"
    pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "recency": [1, 3, 5],
            "history_segment": ["low", "medium", "high"],
            "history": [50.0, 250.0, 1200.0],
            "mens": [0, 1, 0],
            "womens": [1, 0, 1],
            "zip_code": ["Urban", "Rural", "Surburban"],
            "newbie": [1, 0, 0],
            "channel": ["Web", "Phone", "Web"],
            "segment": ["No E-Mail", "Mens E-Mail", "Womens E-Mail"],
            "visit": [0, 1, 1],
            "conversion": [0, 1, 0],
            "spend": [0.0, 20.0, 0.0],
        }
    ).to_csv(processed_path, index=False)
    database = build_database(processed_path=processed_path)
    try:
        metrics = validate_eda_metrics(database)
        assert metrics == {
            "customer_count": 3,
            "group_total": 3,
            "outcome_total": 3,
            "invalid_rate_rows": 0,
        }
        exported = export_eda_tables(database, tmp_path)
        assert len(exported) == 10
        assert all(path.exists() for path in exported.values())
        assert all(path.stat().st_size > 0 for path in exported.values())
    finally:
        database.close()
