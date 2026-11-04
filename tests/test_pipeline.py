import pandas as pd

from marketing_ab.pipeline import run_full_pipeline


def test_pipeline_orchestration_runs_all_stages(monkeypatch, tmp_path) -> None:
    calls = []

    def fake_ingestion(**_kwargs):
        calls.append("ingestion")
        return {"row_count": 3}

    class FakeConnection:
        def close(self):
            calls.append("close")

    def fake_build_database(*_args, **_kwargs):
        calls.append("database")
        return FakeConnection()

    monkeypatch.setattr("marketing_ab.pipeline.run_ingestion_pipeline", fake_ingestion)
    monkeypatch.setattr("marketing_ab.pipeline.build_database", fake_build_database)
    monkeypatch.setattr("marketing_ab.pipeline.verify_database", lambda _: {"customer_rows": 3})
    monkeypatch.setattr("marketing_ab.pipeline.sample_join_queries", lambda _: {})
    monkeypatch.setattr("marketing_ab.pipeline.validate_eda_metrics", lambda _: {})
    monkeypatch.setattr("marketing_ab.pipeline.export_eda_tables", lambda *_args: {})
    monkeypatch.setattr(
        "marketing_ab.pipeline.run_ab_test_analysis", lambda *_args: pd.DataFrame()
    )
    monkeypatch.setattr(
        "marketing_ab.pipeline.analyze_revenue", lambda *_args, **_kwargs: {}
    )
    monkeypatch.setattr(
        "marketing_ab.pipeline.run_machine_learning", lambda *_args, **_kwargs: {}
    )
    monkeypatch.setattr(
        "marketing_ab.pipeline.run_uplift_modeling", lambda *_args, **_kwargs: {}
    )
    monkeypatch.setattr(
        "marketing_ab.pipeline.run_uplift_evaluation", lambda *_args, **_kwargs: {}
    )
    monkeypatch.setattr("marketing_ab.pipeline.generate_all_figures", lambda *_args: {})

    result = run_full_pipeline(tmp_path, download_if_missing=False)

    assert result["ingestion"]["row_count"] == 3
    assert calls == ["ingestion", "database", "close"]
