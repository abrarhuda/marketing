import pandas as pd
import pytest

from marketing_ab.data_validation import EXPECTED_COLUMNS, clean_dataset


def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [1, "1) 100 - 200", 100.0, 1, 0, "Urban", 1, "Phone", "No E-Mail", 0, 0, 0.0],
            [2, "2) 200 - 500", 200.0, 0, 1, "Surburban", 0, "Web", "Mens E-Mail", 1, 1, 25.0],
            [
                3,
                "3) 500 - 1,000",
                500.0,
                1,
                1,
                "Urban",
                0,
                "Multichannel",
                "Womens E-Mail",
                1,
                0,
                0.0,
            ],
        ],
        columns=EXPECTED_COLUMNS,
    )


def test_clean_dataset_preserves_rows_and_adds_surrogate_id() -> None:
    cleaned, report = clean_dataset(sample_data(), expected_rows=None)

    assert len(cleaned) == 3
    assert cleaned.columns.tolist() == ["customer_id", *EXPECTED_COLUMNS]
    assert cleaned["customer_id"].tolist() == [1, 2, 3]
    assert report["exact_duplicate_row_count"] == 0


def test_identical_rows_are_reported_not_removed() -> None:
    data = pd.concat([sample_data(), sample_data().iloc[[0]]], ignore_index=True)

    cleaned, report = clean_dataset(data, expected_rows=None)

    assert len(cleaned) == 4
    assert report["exact_duplicate_row_count"] == 2


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("visit", 2, "visit must be binary"),
        ("conversion", -1, "conversion must be binary"),
        ("spend", -0.01, "spend must be nonnegative"),
    ],
)
def test_invalid_values_fail_validation(column: str, value: float, message: str) -> None:
    data = sample_data()
    data.loc[0, column] = value

    with pytest.raises(ValueError, match=message):
        clean_dataset(data, expected_rows=None)


def test_missing_required_column_fails() -> None:
    data = sample_data().drop(columns=["segment"])

    with pytest.raises(ValueError, match="Missing required columns"):
        clean_dataset(data, expected_rows=None)


def test_missing_experiment_group_fails() -> None:
    data = sample_data()
    data.loc[data["segment"] == "Mens E-Mail", "segment"] = "No E-Mail"

    with pytest.raises(ValueError, match="Missing experiment groups"):
        clean_dataset(data, expected_rows=None)
