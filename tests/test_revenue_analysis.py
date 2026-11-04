import numpy as np
import pandas as pd
import pytest

from marketing_ab.revenue_analysis import (
    bootstrap_mean_difference,
    revenue_distribution_diagnostics,
)


def test_bootstrap_is_reproducible_and_includes_zero_spend() -> None:
    treatment = [0.0, 0.0, 10.0, 10.0]
    control = [0.0, 0.0, 0.0, 0.0]

    first = bootstrap_mean_difference(
        treatment,
        control,
        treatment_group="Treatment",
        iterations=500,
        random_state=7,
    )
    second = bootstrap_mean_difference(
        treatment,
        control,
        treatment_group="Treatment",
        iterations=500,
        random_state=7,
    )

    assert first.observed_difference == pytest.approx(5.0)
    assert first.treatment_n == 4
    assert first.control_n == 4
    assert first == second


def test_distribution_diagnostics_capture_zero_inflation() -> None:
    data = pd.DataFrame(
        {
            "treatment_group": ["A"] * 4,
            "spend": [0.0, 0.0, 0.0, 10.0],
        }
    )

    diagnostics = revenue_distribution_diagnostics(data).iloc[0]

    assert diagnostics["assigned_customers"] == 4
    assert diagnostics["zero_spend_customers"] == 3
    assert diagnostics["zero_spend_rate"] == pytest.approx(0.75)
    assert np.isfinite(diagnostics["spend_skewness"])


def test_bootstrap_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        bootstrap_mean_difference([-1.0], [0.0], treatment_group="Treatment")

    with pytest.raises(ValueError, match="iterations"):
        bootstrap_mean_difference([1.0], [0.0], treatment_group="Treatment", iterations=0)
