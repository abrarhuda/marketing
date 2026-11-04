import pandas as pd
import pytest
from scipy.stats import norm

from marketing_ab.statistical_testing import (
    analyze_group_counts,
    compare_proportions,
)


def test_two_proportion_result_is_independently_checkable() -> None:
    result = compare_proportions(
        treatment_events=30,
        treatment_n=100,
        control_events=10,
        control_n=100,
        outcome="visit",
        treatment_group="Treatment",
    )

    pooled_rate = 40 / 200
    expected_z = (0.30 - 0.10) / (pooled_rate * (1 - pooled_rate) * (1 / 100 + 1 / 100)) ** 0.5
    expected_p = 2 * norm.sf(abs(expected_z))
    assert result.treatment_rate == pytest.approx(0.30)
    assert result.control_rate == pytest.approx(0.10)
    assert result.absolute_effect == pytest.approx(0.20)
    assert result.relative_lift == pytest.approx(2.0)
    assert result.z_statistic == pytest.approx(expected_z)
    assert result.p_value == pytest.approx(expected_p)
    assert result.confidence_interval_low < result.absolute_effect < result.confidence_interval_high


def test_holm_adjustment_and_comparison_direction() -> None:
    counts = pd.DataFrame(
        {
            "treatment_group": ["Mens E-Mail", "No E-Mail", "Womens E-Mail"],
            "assigned_customers": [100, 100, 100],
            "visit": [30, 10, 12],
        }
    )

    results = analyze_group_counts(
        counts,
        outcome="visit",
        analysis_type="primary",
        treatments=("Mens E-Mail", "Womens E-Mail"),
    )

    assert [result.control_group for result in results] == ["No E-Mail", "No E-Mail"]
    assert [result.treatment_group for result in results] == ["Mens E-Mail", "Womens E-Mail"]
    assert all(result.adjusted_p_value >= result.p_value for result in results)
