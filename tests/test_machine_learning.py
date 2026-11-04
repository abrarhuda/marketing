import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from marketing_ab.machine_learning import (
    MODEL_FEATURES,
    build_model_pipeline,
    split_modeling_data,
    validate_modeling_data,
)


def modeling_fixture() -> pd.DataFrame:
    rows = []
    for index in range(30):
        rows.append(
            {
                "recency": (index % 12) + 1,
                "history": float(50 + index),
                "history_segment": "low" if index % 2 else "high",
                "mens": index % 2,
                "womens": (index + 1) % 2,
                "zip_code": "Urban" if index % 3 else "Rural",
                "newbie": index % 2,
                "channel": "Web" if index % 2 else "Phone",
                "visit": index % 2,
                "treatment_group": ["No E-Mail", "Mens E-Mail", "Womens E-Mail"][index % 3],
            }
        )
    return pd.DataFrame(rows)


def test_split_excludes_treatment_and_post_treatment_features() -> None:
    data = modeling_fixture()
    train_x, validation_x, test_x, *_ = split_modeling_data(data)

    assert train_x.columns.tolist() == list(MODEL_FEATURES)
    assert validation_x.columns.tolist() == list(MODEL_FEATURES)
    assert test_x.columns.tolist() == list(MODEL_FEATURES)
    assert "treatment_group" not in train_x.columns
    assert "visit" not in train_x.columns


def test_split_is_reproducible_with_fixed_random_state() -> None:
    data = modeling_fixture()
    first = split_modeling_data(data, random_state=42)
    second = split_modeling_data(data, random_state=42)

    for first_part, second_part in zip(first, second):
        if hasattr(first_part, "equals"):
            assert first_part.equals(second_part)
        else:
            assert first_part == second_part


def test_pipeline_handles_categorical_and_numeric_features() -> None:
    data = modeling_fixture()
    train_x, _, _, train_y, _, _ = split_modeling_data(data)
    pipeline = build_model_pipeline(LogisticRegression(max_iter=1000), scale_numeric=True)
    pipeline.fit(train_x, train_y)

    probabilities = pipeline.predict_proba(train_x)
    assert probabilities.shape == (len(train_x), 2)
    assert ((probabilities >= 0) & (probabilities <= 1)).all()


def test_invalid_target_is_rejected() -> None:
    data = modeling_fixture()
    data.loc[0, "visit"] = 2

    with pytest.raises(ValueError, match="binary"):
        validate_modeling_data(data)
