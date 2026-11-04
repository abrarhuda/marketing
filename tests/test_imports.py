"""Smoke tests for the installable project package."""

import marketing_ab
from marketing_ab import (
    data_ingestion,
    data_validation,
    database,
    evaluation,
    machine_learning,
    pipeline,
    statistical_testing,
    uplift,
    uplift_evaluation,
    visualizations,
)


def test_package_imports() -> None:
    """All planned package modules should import successfully."""
    assert marketing_ab.__version__ == "0.1.0"
    assert all(
        module is not None
        for module in (
            data_ingestion,
            data_validation,
            database,
            evaluation,
            machine_learning,
            pipeline,
            statistical_testing,
            uplift,
            uplift_evaluation,
            visualizations,
        )
    )
