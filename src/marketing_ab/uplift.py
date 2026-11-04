"""T-Learner uplift modeling for the three-arm Hillstrom experiment."""

from pathlib import Path
from typing import Dict, Tuple, Union

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline

from .database import build_database
from .machine_learning import (
    DEFAULT_RANDOM_STATE,
    MODEL_FEATURES,
    build_model_pipeline,
    fetch_modeling_data,
)

CONTROL_GROUP = "No E-Mail"
TREATMENT_GROUPS = ("Mens E-Mail", "Womens E-Mail")
ALL_GROUPS = (CONTROL_GROUP, *TREATMENT_GROUPS)
DEFAULT_C_VALUES = (0.01, 0.1, 1.0)


def split_uplift_data(
    data: pd.DataFrame, random_state: int = DEFAULT_RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Reuse the predictive pipeline's 60/20/20 stratified full-row split."""
    from .machine_learning import split_modeling_data

    train_x, validation_x, test_x, train_y, validation_y, test_y = split_modeling_data(
        data, random_state
    )
    train_indices, validation_indices, test_indices = _split_indices(data, random_state)
    train = data.loc[train_indices].copy()
    validation = data.loc[validation_indices].copy()
    test = data.loc[test_indices].copy()
    if not (
        len(train) == len(train_x)
        and len(validation) == len(validation_x)
        and len(test) == len(test_x)
        and train[TARGET].equals(train_y)
        and validation[TARGET].equals(validation_y)
        and test[TARGET].equals(test_y)
    ):
        raise RuntimeError("Uplift and predictive split partitions did not match.")
    return train, validation, test


TARGET = "visit"


def _split_indices(
    data: pd.DataFrame, random_state: int
) -> Tuple[pd.Index, pd.Index, pd.Index]:
    from sklearn.model_selection import train_test_split

    stratification = data["treatment_group"].astype(str) + "_" + data[TARGET].astype(str)
    train, temporary = train_test_split(
        data.index,
        test_size=0.4,
        random_state=random_state,
        stratify=stratification,
    )
    temporary_stratification = (
        data.loc[temporary, "treatment_group"].astype(str)
        + "_"
        + data.loc[temporary, TARGET].astype(str)
    )
    validation, test = train_test_split(
        temporary,
        test_size=0.5,
        random_state=random_state,
        stratify=temporary_stratification,
    )
    return pd.Index(train), pd.Index(validation), pd.Index(test)


def _fit_arm_model(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    group: str,
    random_state: int,
) -> Tuple[Pipeline, float]:
    """Tune logistic-regression regularization using only one arm."""
    train_arm = train[train["treatment_group"] == group]
    validation_arm = validation[validation["treatment_group"] == group]
    if train_arm[TARGET].nunique() < 2 or validation_arm[TARGET].nunique() < 2:
        raise ValueError(
            f"Treatment arm {group!r} needs both visit classes in train and validation."
        )
    best_model = None
    best_score = -np.inf
    best_c = None
    for c_value in DEFAULT_C_VALUES:
        candidate = build_model_pipeline(
            LogisticRegression(
                C=c_value,
                max_iter=1000,
                random_state=random_state,
                solver="liblinear",
            ),
            scale_numeric=True,
        )
        candidate.fit(train_arm[list(MODEL_FEATURES)], train_arm[TARGET])
        score = roc_auc_score(
            validation_arm[TARGET],
            candidate.predict_proba(validation_arm[list(MODEL_FEATURES)])[:, 1],
        )
        if score > best_score:
            best_model = candidate
            best_score = score
            best_c = c_value
    assert best_model is not None and best_c is not None
    return best_model, float(best_c)


def fit_t_learner(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> Tuple[Dict[str, Pipeline], Dict[str, float]]:
    """Fit one logistic-regression outcome model for each randomized arm."""
    models: Dict[str, Pipeline] = {}
    selected_c: Dict[str, float] = {}
    for group in ALL_GROUPS:
        selected_model, c_value = _fit_arm_model(train, validation, group, random_state)
        combined_arm = pd.concat(
            [
                train[train["treatment_group"] == group],
                validation[validation["treatment_group"] == group],
            ],
            ignore_index=True,
        )
        selected_model.fit(combined_arm[list(MODEL_FEATURES)], combined_arm[TARGET])
        models[group] = selected_model
        selected_c[group] = c_value
    return models, selected_c


def predict_counterfactual_visits(
    models: Dict[str, Pipeline], test: pd.DataFrame
) -> pd.DataFrame:
    """Predict each test customer's visit probability under all three arms."""
    predictions = test[["customer_id", "treatment_group", TARGET]].copy()
    features = test[list(MODEL_FEATURES)]
    for group in ALL_GROUPS:
        column = _probability_column(group)
        predictions[column] = models[group].predict_proba(features)[:, 1]
    predictions["uplift_mens_email"] = (
        predictions["probability_mens_email"] - predictions["probability_no_email"]
    )
    predictions["uplift_womens_email"] = (
        predictions["probability_womens_email"] - predictions["probability_no_email"]
    )
    predictions["recommended_treatment"] = predictions.apply(
        _recommend_treatment,
        axis=1,
    )
    predictions["observed_treatment"] = predictions["treatment_group"]
    predictions["observed_visit"] = predictions[TARGET]
    return predictions.drop(columns=[TARGET])


def _probability_column(group: str) -> str:
    return "probability_" + group.lower().replace(" ", "_").replace("-", "")


def _recommend_treatment(row: pd.Series) -> str:
    uplift_by_group = {
        CONTROL_GROUP: 0.0,
        "Mens E-Mail": float(row["uplift_mens_email"]),
        "Womens E-Mail": float(row["uplift_womens_email"]),
    }
    return max(
        uplift_by_group,
        key=lambda group: (uplift_by_group[group], -ALL_GROUPS.index(group)),
    )


def evaluate_uplift_policy(
    predictions: pd.DataFrame,
    assignment_probabilities: Dict[str, float],
) -> pd.DataFrame:
    """Estimate held-out policy value using known randomized propensities.

    Inverse-propensity weighting uses only outcomes observed under the assigned
    arm. It does not pretend that an individual customer's counterfactual was
    observed.
    """
    rows = []
    for policy_name, treatment in [
        ("always_no_email", CONTROL_GROUP),
        ("always_mens_email", "Mens E-Mail"),
        ("always_womens_email", "Womens E-Mail"),
    ]:
        recommended = pd.Series(treatment, index=predictions.index)
        rows.append(_policy_row(policy_name, recommended, predictions, assignment_probabilities))
    rows.append(
        _policy_row(
            "model_recommended_treatment",
            predictions["recommended_treatment"],
            predictions,
            assignment_probabilities,
        )
    )
    return pd.DataFrame(rows)


def _policy_row(
    policy_name: str,
    recommended: pd.Series,
    predictions: pd.DataFrame,
    assignment_probabilities: Dict[str, float],
) -> Dict[str, Union[str, float, int]]:
    matches = recommended.to_numpy() == predictions["observed_treatment"].to_numpy()
    weights = np.array(
        [
            1 / assignment_probabilities[group]
            if match
            else 0.0
            for match, group in zip(matches, predictions["observed_treatment"])
        ]
    )
    outcomes = predictions["observed_visit"].to_numpy(dtype=float)
    value = float(np.mean(weights * outcomes))
    return {
        "policy": policy_name,
        "estimated_visit_rate": value,
        "test_customers": int(len(predictions)),
        "recommended_no_email": int((recommended == CONTROL_GROUP).sum()),
        "recommended_mens_email": int((recommended == "Mens E-Mail").sum()),
        "recommended_womens_email": int((recommended == "Womens E-Mail").sum()),
    }


def evaluate_outcome_models(
    models: Dict[str, Pipeline], test: pd.DataFrame
) -> pd.DataFrame:
    """Evaluate each arm model on held-out customers assigned to that arm."""
    rows = []
    for group, model in models.items():
        arm = test[test["treatment_group"] == group]
        probabilities = model.predict_proba(arm[list(MODEL_FEATURES)])[:, 1]
        rows.append(
            {
                "treatment_group": group,
                "test_customers_assigned": len(arm),
                "factual_test_roc_auc": roc_auc_score(arm[TARGET], probabilities),
                "factual_test_log_loss": log_loss(arm[TARGET], probabilities),
                "factual_test_brier_score": brier_score_loss(arm[TARGET], probabilities),
            }
        )
    return pd.DataFrame(rows)


def run_uplift_modeling(
    connection: duckdb.DuckDBPyConnection,
    output_directory: Union[str, Path] = Path("reports"),
    model_directory: Union[str, Path] = Path("models"),
    random_state: int = DEFAULT_RANDOM_STATE,
) -> Dict[str, Path]:
    """Train the T-Learner, score the held-out test set, and export artifacts."""
    data = fetch_modeling_data(connection)
    train, validation, test = split_uplift_data(data, random_state)
    models, selected_c = fit_t_learner(train, validation, random_state)
    predictions = predict_counterfactual_visits(models, test)
    assignment_probabilities = (
        train["treatment_group"].value_counts(normalize=True).reindex(ALL_GROUPS).to_dict()
    )
    policy_results = evaluate_uplift_policy(predictions, assignment_probabilities)
    model_results = evaluate_outcome_models(models, test)
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    model_path = Path(model_directory)
    model_path.mkdir(parents=True, exist_ok=True)
    predictions_path = output_path / "uplift_predictions.csv"
    policy_path = output_path / "uplift_policy_evaluation.csv"
    model_results_path = output_path / "uplift_arm_model_evaluation.csv"
    predictions.to_csv(predictions_path, index=False)
    policy_results.to_csv(policy_path, index=False)
    model_results["selected_c"] = model_results["treatment_group"].map(selected_c)
    model_results.to_csv(model_results_path, index=False)
    bundle = {
        "models": models,
        "feature_columns": list(MODEL_FEATURES),
        "treatment_groups": list(ALL_GROUPS),
        "target_column": TARGET,
        "random_state": random_state,
        "selected_c": selected_c,
    }
    joblib.dump(bundle, model_path / "t_learner_logistic_regression.joblib")
    return {
        "predictions": predictions_path,
        "policy_evaluation": policy_path,
        "arm_model_evaluation": model_results_path,
        "model_bundle": model_path / "t_learner_logistic_regression.joblib",
    }


def run_uplift_pipeline() -> None:
    """Build the database, run T-Learner uplift modeling, and export outputs."""
    connection = build_database(Path("data/processed") / "hillstrom.duckdb")
    try:
        paths = run_uplift_modeling(connection)
        for name, path in paths.items():
            print(f"{name}: {path}")
    finally:
        connection.close()
