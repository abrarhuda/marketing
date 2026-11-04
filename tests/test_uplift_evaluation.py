import pandas as pd
import pytest

from marketing_ab.uplift_evaluation import (
    evaluate_policies,
    evaluate_ranking_curves,
    policy_value,
)


def predictions_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "observed_treatment": ["No E-Mail", "Mens E-Mail", "Womens E-Mail", "No E-Mail"],
            "observed_visit": [0, 1, 1, 1],
            "probability_no_email": [0.2] * 4,
            "probability_mens_email": [0.3] * 4,
            "probability_womens_email": [0.25] * 4,
            "uplift_mens_email": [0.1, 0.1, 0.1, 0.1],
            "uplift_womens_email": [0.05, 0.05, 0.05, 0.05],
        }
    )


def test_ipw_always_control_uses_only_control_outcomes() -> None:
    data = predictions_fixture()
    assert policy_value(data, ["No E-Mail"] * 4) == pytest.approx(0.75)


def test_policy_bootstrap_and_curve_outputs() -> None:
    data = predictions_fixture()
    policies = evaluate_policies(data, bootstrap_iterations=20, random_state=7)
    curves = evaluate_ranking_curves(data)
    assert set(policies["policy"]) == {
        "always_no_email",
        "always_mens_email",
        "always_womens_email",
        "model_highest_positive_uplift",
        "model_highest_predicted_visit",
    }
    assert len(curves) == 2 * (len(data) + 1)
    assert policies["bootstrap_iterations"].eq(20).all()
