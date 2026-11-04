"""Validation and cleaning rules for the Hillstrom experiment dataset."""

from collections.abc import Iterable
from typing import Any, Dict, Optional, Tuple

import pandas as pd

EXPECTED_COLUMNS = (
    "recency",
    "history_segment",
    "history",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
    "segment",
    "visit",
    "conversion",
    "spend",
)
EXPECTED_GROUPS = ("No E-Mail", "Mens E-Mail", "Womens E-Mail")
NUMERIC_COLUMNS = (
    "recency",
    "history",
    "mens",
    "womens",
    "newbie",
    "visit",
    "conversion",
    "spend",
)
CATEGORICAL_COLUMNS = ("history_segment", "zip_code", "channel", "segment")


def validate_required_columns(
    data: pd.DataFrame, required_columns: Iterable[str]
) -> None:
    """Raise an error when one or more required columns are absent."""
    missing_columns = sorted(set(required_columns).difference(data.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")


def validate_experiment_groups(
    data: pd.DataFrame, group_column: str, expected_groups: Iterable[str]
) -> None:
    """Raise an error when observed experiment groups are not as expected."""
    observed_groups = set(data[group_column].dropna().unique())
    expected_group_set = set(expected_groups)
    unexpected_groups = observed_groups.difference(expected_group_set)
    if unexpected_groups:
        raise ValueError(f"Unexpected experiment groups: {sorted(unexpected_groups)}")
    missing_groups = expected_group_set.difference(observed_groups)
    if missing_groups:
        raise ValueError(f"Missing experiment groups: {sorted(missing_groups)}")


def normalize_column_names(data: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with trimmed, lowercase, underscore-separated names."""
    normalized = data.copy()
    normalized.columns = (
        normalized.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[\s-]+", "_", regex=True)
    )
    return normalized


def standardize_dtypes(data: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric fields while preserving source category values."""
    standardized = data.copy()
    for column in NUMERIC_COLUMNS:
        converted = pd.to_numeric(standardized[column], errors="coerce")
        invalid = converted.isna() & standardized[column].notna()
        if invalid.any():
            values = standardized.loc[invalid, column].astype(str).unique().tolist()
            raise ValueError(f"Non-numeric values in {column}: {values}")
        standardized[column] = converted
    for column in CATEGORICAL_COLUMNS:
        standardized[column] = standardized[column].astype("string")
    return standardized


def validate_dataset(data: pd.DataFrame, expected_rows: Optional[int] = 64000) -> Dict[str, Any]:
    """Validate required fields and return a data-quality report.

    Exact duplicate feature rows are reported but retained. The source has no
    customer identifier, so identical rows cannot be interpreted as duplicate
    customers.
    """
    validate_required_columns(data, EXPECTED_COLUMNS)
    report: dict[str, Any] = {
        "row_count": int(len(data)),
        "expected_row_count": expected_rows,
        "missing_values": {column: int(data[column].isna().sum()) for column in EXPECTED_COLUMNS},
        "exact_duplicate_row_count": int(data.duplicated(keep=False).sum()),
        "observed_experiment_groups": sorted(data["segment"].dropna().unique().tolist()),
    }
    if expected_rows is not None and len(data) != expected_rows:
        raise ValueError(f"Expected {expected_rows} rows, found {len(data)}")
    if data[list(EXPECTED_COLUMNS)].isna().any().any():
        missing = {key: value for key, value in report["missing_values"].items() if value}
        raise ValueError(f"Missing values in required fields: {missing}")
    validate_experiment_groups(data, "segment", EXPECTED_GROUPS)
    for column in ("visit", "conversion"):
        invalid = sorted(set(data[column].unique()).difference({0, 1}))
        if invalid:
            raise ValueError(f"{column} must be binary 0/1; found {invalid}")
    if (data["spend"] < 0).any():
        raise ValueError("spend must be nonnegative")
    if (data["recency"] < 0).any() or (data["history"] < 0).any():
        raise ValueError("recency and history must be nonnegative")
    return report


def clean_dataset(
    data: pd.DataFrame, expected_rows: Optional[int] = 64000
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Normalize names, standardize types, validate, and add a row-position ID."""
    cleaned = normalize_column_names(data)
    validate_required_columns(cleaned, EXPECTED_COLUMNS)
    cleaned = standardize_dtypes(cleaned)
    report = validate_dataset(cleaned, expected_rows=expected_rows)
    cleaned.insert(0, "customer_id", range(1, len(cleaned) + 1))
    report["customer_id_note"] = (
        "Synthetic stable surrogate based on source row position; no source customer ID exists."
    )
    return cleaned, report
