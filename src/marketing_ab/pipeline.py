"""Command-line orchestration for the complete reproducible project."""

import argparse
from pathlib import Path
from typing import Dict, Union

from .data_ingestion import run_ingestion_pipeline
from .database import build_database, sample_join_queries, verify_database
from .eda import export_eda_tables, validate_eda_metrics
from .machine_learning import run_machine_learning
from .revenue_analysis import analyze_revenue
from .statistical_testing import run_ab_test_analysis
from .visualizations import generate_all_figures

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_full_pipeline(
    project_root: Union[str, Path] = PROJECT_ROOT,
    *,
    download_if_missing: bool = True,
    random_state: int = 42,
) -> Dict[str, object]:
    """Run ingestion through visualizations using one fixed project root."""
    root = Path(project_root).resolve()
    report = run_ingestion_pipeline(
        raw_path=root / "data/raw/hillstrom.csv",
        processed_path=root / "data/processed/hillstrom_validated.csv",
        quality_report_path=root / "data/processed/data_quality_report.json",
        download_if_missing=download_if_missing,
    )
    database_path = root / "data/processed/hillstrom.duckdb"
    connection = build_database(
        database_path,
        root / "data/processed/hillstrom_validated.csv",
    )
    try:
        database_checks = verify_database(connection)
        database_checks.update(sample_join_queries(connection))
        eda_checks = validate_eda_metrics(connection)
        eda_outputs = export_eda_tables(connection, root / "reports/tables")
        ab_results = run_ab_test_analysis(connection, root / "reports/ab_test_results.csv")
        revenue_outputs = analyze_revenue(
            connection,
            random_state=random_state,
            output_directory=root / "reports",
        )
        ml_results = run_machine_learning(
            connection,
            output_directory=root / "reports",
            model_directory=root / "models",
            random_state=random_state,
        )
    finally:
        connection.close()
    figure_outputs = generate_all_figures(root)
    return {
        "ingestion": report,
        "database": database_checks,
        "eda": {"checks": eda_checks, "outputs": eda_outputs},
        "ab_testing": ab_results,
        "revenue": revenue_outputs,
        "machine_learning": ml_results,
        "visualizations": figure_outputs,
    }


def run() -> None:
    """Parse CLI arguments and run the complete project pipeline."""
    parser = argparse.ArgumentParser(description="Run the complete marketing analytics pipeline.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root containing data/, reports/, models/, and sql/.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Fail if the raw dataset is missing instead of downloading it.",
    )
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()
    results = run_full_pipeline(
        args.project_root,
        download_if_missing=not args.no_download,
        random_state=args.random_state,
    )
    row_count = results["ingestion"]["row_count"]
    print(f"Completed pipeline for {row_count:,} validated rows.")


if __name__ == "__main__":
    run()
