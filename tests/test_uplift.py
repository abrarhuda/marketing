import pandas as pd
import pytest

from marketing_ab.machine_learning import MODEL_FEATURES
from marketing_ab.uplift import (
    ALL_GROUPS,
    CONTROL_GROUP,
    _recommend_treatment,
    evaluate_uplift_policy,
    fit_t_learner,
    predict_counterfactual_visits,
)


def uplift_fixture() -> pd.DataFrame:
    rows = []
    for index in range(90):
        group = ALL_GROUPS[index % 3]
        rows.append(
            {
                "customer_id": index + 1,
                "recency": (index % 12) + 1,
                "history": float(50 + index),
                "history_segment": "low" if index % 2 else "high",
                "mens": index % 2,
                "womens": (index + 1) % 2,
                "zip_code": "Urban" if index % 3 else "Rural",
                "newbie": index % 2,
                "channel": "Web" if index % 2 else "Phone",
                "visit": index % 2,
                "treatment_group": group,
            }
        )
    return pd.DataFrame(rows)


def test_t_learner_predicts_all_counterfactual_arms() -> None:
    data = uplift_fixture()
    train = data.iloc[:60]
    validation = data.iloc[60:75]
    test = data.iloc[75:]
    models, _ = fit_t_learner(train, validation)
    predictions = predict_counterfactual_visits(models, test)

    assert len(predictions) == len(test)
    assert set(predictions["recommended_treatment"]).issubset(set(ALL_GROUPS))
    assert {"probability_no_email", "probability_mens_email", "probability_womens_email"}.issubset(
        predictions.columns
    )
    assert set(MODEL_FEATURES).isdisjoint(predictions.columns)


def test_policy_evaluation_uses_observed_randomized_outcome() -> None:
    predictions = pd.DataFrame(
        {
            "observed_treatment": ["No E-Mail", "Mens E-Mail", "Womens E-Mail"],
            "observed_visit": [0, 1, 1],
            "recommended_treatment": ["No E-Mail", "Mens E-Mail", "No E-Mail"],
        }
    )
    result = evaluate_uplift_policy(
        predictions,
        {"No E-Mail": 1 / 3, "Mens E-Mail": 1 / 3, "Womens E-Mail": 1 / 3},
    )
    model_row = result.loc[result["policy"] == "model_recommended_treatment"].iloc[0]
    assert model_row["estimated_visit_rate"] == pytest.approx(1.0)


def test_negative_uplift_recommends_no_email() -> None:
    row = pd.Series(
        {
            "uplift_mens_email": -0.10,
            "uplift_womens_email": -0.02,
        }
    )

    assert _recommend_treatment(row) == CONTROL_GROUP
