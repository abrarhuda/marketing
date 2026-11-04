"""Leakage-safe scikit-learn baseline models for website visitation."""

from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union

import duckdb
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from .database import build_database

DEFAULT_RANDOM_STATE = 42
TARGET_COLUMN = "visit"
NUMERIC_FEATURES = ("recency", "history", "mens", "womens", "newbie")
CATEGORICAL_FEATURES = ("history_segment", "zip_code", "channel")
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
POST_TREATMENT_COLUMNS = ("visit", "conversion", "spend")
EXCLUDED_ASSIGNMENT_COLUMN = "treatment_group"


def fetch_modeling_data(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Fetch only pretreatment features and the website-visit target."""
    columns = ", ".join(("customer_id", *MODEL_FEATURES, TARGET_COLUMN, "treatment_group"))
    data = connection.execute(
        f"SELECT {columns} FROM customer_experiment_analysis"
    ).fetchdf()
    validate_modeling_data(data)
    return data


def validate_modeling_data(data: pd.DataFrame) -> None:
    """Reject missing fields, invalid targets, and post-treatment features."""
    required = set(MODEL_FEATURES) | {TARGET_COLUMN, "treatment_group"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing modeling columns: {sorted(missing)}")
    invalid_target = set(data[TARGET_COLUMN].unique()).difference({0, 1})
    if invalid_target:
        raise ValueError(f"{TARGET_COLUMN} must be binary 0/1; found {sorted(invalid_target)}")
    if data[list(MODEL_FEATURES)].isna().any().any():
        raise ValueError("Modeling features must not contain missing values.")
    if set(MODEL_FEATURES).intersection(POST_TREATMENT_COLUMNS):
        raise ValueError("Post-treatment outcomes must not be model features.")


def split_modeling_data(
    data: pd.DataFrame, random_state: int = DEFAULT_RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Create 60/20/20 train, validation, and test splits.

    The stratification label combines randomized treatment assignment and
    visit outcome. Treatment is used only to preserve split balance, never as
    a model feature.
    """
    validate_modeling_data(data)
    stratification = data["treatment_group"].astype(str) + "_" + data[TARGET_COLUMN].astype(str)
    train, temporary = train_test_split(
        data,
        test_size=0.4,
        random_state=random_state,
        stratify=stratification,
    )
    temporary_stratification = (
        temporary["treatment_group"].astype(str) + "_" + temporary[TARGET_COLUMN].astype(str)
    )
    validation, test = train_test_split(
        temporary,
        test_size=0.5,
        random_state=random_state,
        stratify=temporary_stratification,
    )
    return (
        train[list(MODEL_FEATURES)],
        validation[list(MODEL_FEATURES)],
        test[list(MODEL_FEATURES)],
        train[TARGET_COLUMN],
        validation[TARGET_COLUMN],
        test[TARGET_COLUMN],
    )


def build_model_pipeline(model: object, scale_numeric: bool) -> Pipeline:
    """Build preprocessing and estimator as one leakage-safe pipeline."""
    numeric_transformer = (
        Pipeline([("scaler", StandardScaler())]) if scale_numeric else "passthrough"
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_transformer, list(NUMERIC_FEATURES)),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(CATEGORICAL_FEATURES),
            ),
        ],
        remainder="drop",
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def _candidate_pipelines(random_state: int) -> Dict[str, List[Pipeline]]:
    return {
        "logistic_regression": [
            build_model_pipeline(
                LogisticRegression(
                    C=c,
                    max_iter=1000,
                    random_state=random_state,
                    solver="liblinear",
                ),
                scale_numeric=True,
            )
            for c in (0.1, 1.0, 10.0)
        ],
        "decision_tree": [
            build_model_pipeline(
                DecisionTreeClassifier(
                    max_depth=depth,
                    min_samples_leaf=leaf,
                    random_state=random_state,
                ),
                scale_numeric=False,
            )
            for depth, leaf in ((3, 1), (5, 1), (8, 5))
        ],
    }


def tune_on_validation(
    train_features: pd.DataFrame,
    validation_features: pd.DataFrame,
    train_target: pd.Series,
    validation_target: pd.Series,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> Dict[str, Tuple[Pipeline, Dict[str, object], float]]:
    """Select one small candidate grid per model using validation ROC-AUC."""
    selected: Dict[str, Tuple[Pipeline, Dict[str, object], float]] = {}
    for model_name, candidates in _candidate_pipelines(random_state).items():
        best_pipeline = None
        best_score = -np.inf
        for candidate in candidates:
            candidate.fit(train_features, train_target)
            validation_probabilities = candidate.predict_proba(validation_features)[:, 1]
            score = roc_auc_score(validation_target, validation_probabilities)
            if score > best_score:
                best_pipeline = candidate
                best_score = score
        assert best_pipeline is not None
        selected[model_name] = (
            best_pipeline,
            best_pipeline.named_steps["model"].get_params(),
            float(best_score),
        )
    return selected


def evaluate_classifier(
    model_name: str,
    pipeline: Pipeline,
    features: pd.DataFrame,
    target: pd.Series,
    split_name: str = "test",
) -> Tuple[Dict[str, object], np.ndarray]:
    """Calculate discrimination, calibration, and confusion metrics."""
    probabilities = pipeline.predict_proba(features)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    matrix = confusion_matrix(target, predictions, labels=[0, 1])
    metrics: Dict[str, object] = {
        "model": model_name,
        "split": split_name,
        "roc_auc": float(roc_auc_score(target, probabilities)),
        "precision": float(precision_score(target, predictions, zero_division=0)),
        "recall": float(recall_score(target, predictions, zero_division=0)),
        "f1": float(f1_score(target, predictions, zero_division=0)),
        "log_loss": float(log_loss(target, probabilities)),
        "brier_score": float(brier_score_loss(target, probabilities)),
        "true_negatives": int(matrix[0, 0]),
        "false_positives": int(matrix[0, 1]),
        "false_negatives": int(matrix[1, 0]),
        "true_positives": int(matrix[1, 1]),
    }
    return metrics, probabilities


def run_machine_learning(
    connection: duckdb.DuckDBPyConnection,
    output_directory: Union[str, Path] = Path("reports"),
    model_directory: Union[str, Path] = Path("models"),
    random_state: int = DEFAULT_RANDOM_STATE,
) -> pd.DataFrame:
    """Tune on validation data, refit on train+validation, and evaluate on test."""
    data = fetch_modeling_data(connection)
    train_x, validation_x, test_x, train_y, validation_y, test_y = split_modeling_data(
        data, random_state
    )
    selected = tune_on_validation(train_x, validation_x, train_y, validation_y, random_state)
    final_features = pd.concat([train_x, validation_x], ignore_index=True)
    final_target = pd.concat([train_y, validation_y], ignore_index=True)
    output_path = Path(output_directory)
    model_path = Path(model_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    model_path.mkdir(parents=True, exist_ok=True)
    rows = []
    curves = []
    for model_name, (pipeline, parameters, validation_auc) in selected.items():
        pipeline.fit(final_features, final_target)
        metrics, probabilities = evaluate_classifier(model_name, pipeline, test_x, test_y)
        metrics["validation_roc_auc"] = validation_auc
        metrics["selected_parameters"] = str(parameters)
        rows.append(metrics)
        false_positive_rate, true_positive_rate, _ = roc_curve(test_y, probabilities)
        curves.append((model_name, false_positive_rate, true_positive_rate))
        joblib.dump(
            {
                "pipeline": pipeline,
                "feature_columns": list(MODEL_FEATURES),
                "target_column": TARGET_COLUMN,
                "random_state": random_state,
                "selected_parameters": parameters,
            },
            model_path / f"{model_name}.joblib",
        )
    results = pd.DataFrame(rows)
    results.to_csv(output_path / "model_comparison.csv", index=False)
    _plot_roc_curves(curves, output_path / "figures" / "model_roc_curves.png")
    _plot_calibration_comparison(
        selected, final_features, final_target, test_x, test_y,
        output_path / "figures" / "model_calibration.png",
    )
    return results


def _plot_roc_curves(
    curves: Iterable[Tuple[str, np.ndarray, np.ndarray]], destination: Path
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(7, 5))
    for name, false_positive_rate, true_positive_rate in curves:
        axis.plot(false_positive_rate, true_positive_rate, label=name.replace("_", " ").title())
    axis.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random")
    axis.set(xlabel="False positive rate", ylabel="True positive rate", title="Test ROC curves")
    axis.legend()
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(destination, dpi=160)
    plt.close(figure)


def _plot_calibration_comparison(
    selected: Dict[str, Tuple[Pipeline, Dict[str, object], float]],
    train_features: pd.DataFrame,
    train_target: pd.Series,
    test_features: pd.DataFrame,
    test_target: pd.Series,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")
    for name, (pipeline, _, _) in selected.items():
        pipeline.fit(train_features, train_target)
        probabilities = pipeline.predict_proba(test_features)[:, 1]
        bins = pd.DataFrame({"probability": probabilities, "actual": test_target.to_numpy()})
        bins["bin"] = pd.qcut(bins["probability"], q=10, duplicates="drop")
        grouped = bins.groupby("bin", observed=True).agg(
            predicted=("probability", "mean"), observed=("actual", "mean")
        )
        label = name.replace("_", " ").title()
        axis.plot(grouped["predicted"], grouped["observed"], marker="o", label=label)
    axis.set(
        xlabel="Mean predicted probability",
        ylabel="Observed visit rate",
        title="Test calibration",
    )
    axis.legend()
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(destination, dpi=160)
    plt.close(figure)


def run_machine_learning_pipeline() -> None:
    """Build the database, train models, and export model evaluation results."""
    connection = build_database(Path("data/processed") / "hillstrom.duckdb")
    try:
        results = run_machine_learning(connection)
        print(results.to_string(index=False))
    finally:
        connection.close()
