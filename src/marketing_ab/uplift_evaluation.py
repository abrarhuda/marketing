"""Held-out randomized evaluation for customer uplift predictions."""

from pathlib import Path
from typing import Dict, Iterable, Union

import numpy as np
import pandas as pd

from .uplift import ALL_GROUPS, CONTROL_GROUP, TREATMENT_GROUPS

DEFAULT_BOOTSTRAP_ITERATIONS = 2000
DEFAULT_RANDOM_STATE = 42
DEFAULT_PROPENSITIES = {group: 1 / 3 for group in ALL_GROUPS}


def _validate_predictions(predictions: pd.DataFrame) -> None:
    required = {
        "observed_treatment",
        "observed_visit",
        "uplift_mens_email",
        "uplift_womens_email",
        "probability_no_email",
        "probability_mens_email",
        "probability_womens_email",
    }
    missing = required.difference(predictions.columns)
    if missing:
        raise ValueError(f"Uplift predictions are missing required columns: {sorted(missing)}")
    if not set(predictions["observed_treatment"]).issubset(set(ALL_GROUPS)):
        raise ValueError("Observed treatment contains an unknown experiment group.")
    if not set(predictions["observed_visit"].unique()).issubset({0, 1}):
        raise ValueError("Observed visit must be binary.")


def _validate_propensities(propensities: Dict[str, float]) -> None:
    if set(propensities) != set(ALL_GROUPS):
        raise ValueError("Propensities must contain exactly the three experiment groups.")
    if any(probability <= 0 or probability > 1 for probability in propensities.values()):
        raise ValueError("Every propensity must be greater than zero and at most one.")
    if not np.isclose(sum(propensities.values()), 1.0):
        raise ValueError("Assignment propensities must sum to one.")


def policy_value(
    predictions: pd.DataFrame,
    policy: Iterable[str],
    propensities: Dict[str, float] = DEFAULT_PROPENSITIES,
) -> float:
    """Estimate a policy's visit rate using inverse-propensity weighting."""
    _validate_predictions(predictions)
    _validate_propensities(propensities)
    assignments = np.asarray(list(policy))
    if len(assignments) != len(predictions):
        raise ValueError("A policy must contain one recommendation per test customer.")
    observed = predictions["observed_treatment"].to_numpy()
    outcomes = predictions["observed_visit"].to_numpy(dtype=float)
    weights = np.array([1 / propensities[group] for group in observed])
    return float(np.mean((assignments == observed) * outcomes * weights))


def _policy_series(predictions: pd.DataFrame) -> Dict[str, pd.Series]:
    """Return fixed policies evaluated without using observed outcomes."""
    mens = predictions["uplift_mens_email"]
    womens = predictions["uplift_womens_email"]
    positive = pd.Series(CONTROL_GROUP, index=predictions.index)
    positive.loc[mens > 0] = "Mens E-Mail"
    positive.loc[(womens > mens) & (womens > 0)] = "Womens E-Mail"
    highest = pd.Series(CONTROL_GROUP, index=predictions.index)
    highest.loc[mens >= womens] = "Mens E-Mail"
    highest.loc[womens > mens] = "Womens E-Mail"
    return {
        "always_no_email": pd.Series(CONTROL_GROUP, index=predictions.index),
        "always_mens_email": pd.Series("Mens E-Mail", index=predictions.index),
        "always_womens_email": pd.Series("Womens E-Mail", index=predictions.index),
        "model_highest_positive_uplift": positive,
        "model_highest_predicted_visit": highest,
    }


def _bootstrap_policy_values(
    predictions: pd.DataFrame,
    policies: Dict[str, pd.Series],
    propensities: Dict[str, float],
    iterations: int,
    random_state: int,
) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(random_state)
    n_rows = len(predictions)
    observed = predictions["observed_treatment"].to_numpy()
    outcomes = predictions["observed_visit"].to_numpy(dtype=float)
    weights = np.array([1 / propensities[group] for group in observed])
    values = {name: np.empty(iterations) for name in policies}
    for iteration in range(iterations):
        sample = rng.integers(0, n_rows, n_rows)
        for name, policy in policies.items():
            assignments = policy.to_numpy()[sample]
            values[name][iteration] = np.mean(
                (assignments == observed[sample]) * outcomes[sample] * weights[sample]
            )
    return values


def evaluate_policies(
    predictions: pd.DataFrame,
    propensities: Dict[str, float] = DEFAULT_PROPENSITIES,
    bootstrap_iterations: int = DEFAULT_BOOTSTRAP_ITERATIONS,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> pd.DataFrame:
    """Compare baseline and model policies with customer-level bootstrap intervals."""
    if bootstrap_iterations <= 0:
        raise ValueError("bootstrap_iterations must be positive.")
    policies = _policy_series(predictions)
    bootstrap = _bootstrap_policy_values(
        predictions, policies, propensities, bootstrap_iterations, random_state
    )
    control_value = policy_value(predictions, policies["always_no_email"], propensities)
    baseline_names = ("always_mens_email", "always_womens_email")
    rows = []
    for name, policy in policies.items():
        value = policy_value(predictions, policy, propensities)
        interval = np.percentile(bootstrap[name], [2.5, 97.5])
        incremental = bootstrap[name] - bootstrap["always_no_email"]
        incremental_interval = np.percentile(incremental, [2.5, 97.5])
        rows.append(
            {
                "policy": name,
                "estimated_visit_rate": value,
                "incremental_vs_always_no_email": value - control_value,
                "bootstrap_ci_lower": interval[0],
                "bootstrap_ci_upper": interval[1],
                "incremental_ci_lower": incremental_interval[0],
                "incremental_ci_upper": incremental_interval[1],
                "bootstrap_iterations": bootstrap_iterations,
                "test_customers": len(predictions),
                "recommended_no_email": int((policy == CONTROL_GROUP).sum()),
                "recommended_mens_email": int((policy == "Mens E-Mail").sum()),
                "recommended_womens_email": int((policy == "Womens E-Mail").sum()),
            }
        )
        for baseline_name in baseline_names:
            difference = bootstrap[name] - bootstrap[baseline_name]
            difference_interval = np.percentile(difference, [2.5, 97.5])
            rows[-1][f"difference_vs_{baseline_name}"] = value - policy_value(
                predictions, policies[baseline_name], propensities
            )
            rows[-1][f"difference_ci_lower_vs_{baseline_name}"] = difference_interval[0]
            rows[-1][f"difference_ci_upper_vs_{baseline_name}"] = difference_interval[1]
    return pd.DataFrame(rows)


def ranking_curve(
    predictions: pd.DataFrame,
    treatment: str,
    propensities: Dict[str, float] = DEFAULT_PROPENSITIES,
) -> pd.DataFrame:
    """Build a treatment-versus-control Qini-style ranking curve.

    Customers are ranked by estimated treatment uplift. At each depth, the
    policy sends the selected treatment to the top-ranked customers and sends
    no email to the remainder. The curve reports the IPW incremental visits
    versus sending no email to everyone.
    """
    if treatment not in TREATMENT_GROUPS:
        raise ValueError(f"treatment must be one of {TREATMENT_GROUPS}.")
    score_column = "uplift_" + treatment.lower().replace(" ", "_").replace("-", "")
    ordered = predictions.sort_values(score_column, ascending=False).reset_index(drop=True)
    observed = ordered["observed_treatment"].to_numpy()
    outcomes = ordered["observed_visit"].to_numpy(dtype=float)
    weights = np.array([1 / propensities[group] for group in observed])
    control_contribution = (observed == CONTROL_GROUP) * outcomes * weights
    treatment_contribution = (observed == treatment) * outcomes * weights
    baseline_total = control_contribution.sum()
    cumulative = np.cumsum(treatment_contribution - control_contribution)
    depths = np.arange(0, len(ordered) + 1)
    qini = np.concatenate(([0.0], cumulative)) / len(ordered)
    policy_values = np.concatenate(
        ([baseline_total], baseline_total + cumulative)
    ) / len(ordered)
    return pd.DataFrame(
        {
            "treatment": treatment,
            "ranked_customers": depths,
            "target_fraction": depths / len(ordered),
            "policy_visit_rate": policy_values,
            "qini_incremental_visit_rate": qini,
            "qini_incremental_visits": np.concatenate(([0.0], cumulative)),
        }
    )


def evaluate_ranking_curves(
    predictions: pd.DataFrame,
    propensities: Dict[str, float] = DEFAULT_PROPENSITIES,
) -> pd.DataFrame:
    """Evaluate separate Mens-versus-control and Womens-versus-control curves."""
    return pd.concat(
        [ranking_curve(predictions, treatment, propensities) for treatment in TREATMENT_GROUPS],
        ignore_index=True,
    )


def run_uplift_evaluation(
    predictions_path: Union[str, Path] = Path("reports/uplift_predictions.csv"),
    output_directory: Union[str, Path] = Path("reports"),
    bootstrap_iterations: int = DEFAULT_BOOTSTRAP_ITERATIONS,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> Dict[str, Path]:
    """Evaluate fixed held-out predictions and export tables and a Qini figure."""
    predictions = pd.read_csv(predictions_path)
    _validate_predictions(predictions)
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    policy_path = output_path / "uplift_policy_bootstrap_evaluation.csv"
    curve_path = output_path / "uplift_ranking_curves.csv"
    policies = evaluate_policies(
        predictions,
        bootstrap_iterations=bootstrap_iterations,
        random_state=random_state,
    )
    curves = evaluate_ranking_curves(predictions)
    policies.to_csv(policy_path, index=False)
    curves.to_csv(curve_path, index=False)
    figure_path = output_path / "figures" / "uplift_qini_curves.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    _plot_ranking_curves(curves, figure_path)
    return {"policy_evaluation": policy_path, "ranking_curves": curve_path, "figure": figure_path}


def _plot_ranking_curves(curves: pd.DataFrame, output_path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots(figsize=(8, 5))
    for treatment, group in curves.groupby("treatment", sort=False):
        axis.plot(
            group["target_fraction"],
            group["qini_incremental_visit_rate"],
            label=treatment,
        )
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(
        title="Held-out uplift ranking curves",
        xlabel="Fraction of customers targeted",
        ylabel="IPW incremental visit rate vs. all-control",
    )
    axis.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def run_uplift_evaluation_pipeline() -> None:
    """Run evaluation using the already generated held-out predictions."""
    for name, path in run_uplift_evaluation().items():
        print(f"{name}: {path}")
