"""Bootstrap analysis of revenue per assigned customer."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Union

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import skew

from .database import SQL_DIRECTORY, build_database

CONTROL_GROUP = "No E-Mail"
TREATMENT_GROUPS = ("Mens E-Mail", "Womens E-Mail")
DEFAULT_ITERATIONS = 2000
DEFAULT_RANDOM_STATE = 42


@dataclass(frozen=True)
class RevenueComparison:
    """Bootstrap result for treatment revenue minus control revenue."""

    treatment_group: str
    control_group: str
    treatment_n: int
    control_n: int
    treatment_mean: float
    control_mean: float
    observed_difference: float
    confidence_interval_low: float
    confidence_interval_high: float
    bootstrap_iterations: int
    random_state: int

    def as_dict(self) -> Dict[str, Union[str, int, float]]:
        return {
            "treatment_group": self.treatment_group,
            "control_group": self.control_group,
            "treatment_n": self.treatment_n,
            "control_n": self.control_n,
            "treatment_mean_revenue": self.treatment_mean,
            "control_mean_revenue": self.control_mean,
            "observed_difference": self.observed_difference,
            "confidence_interval_low": self.confidence_interval_low,
            "confidence_interval_high": self.confidence_interval_high,
            "bootstrap_iterations": self.bootstrap_iterations,
            "random_state": self.random_state,
        }


def bootstrap_mean_difference(
    treatment_spend: Iterable[float],
    control_spend: Iterable[float],
    *,
    treatment_group: str,
    control_group: str = CONTROL_GROUP,
    iterations: int = DEFAULT_ITERATIONS,
    random_state: int = DEFAULT_RANDOM_STATE,
    confidence_level: float = 0.95,
) -> RevenueComparison:
    """Estimate a treatment-control mean difference with percentile bootstrap."""
    treatment = np.asarray(list(treatment_spend), dtype=float)
    control = np.asarray(list(control_spend), dtype=float)
    if treatment.size == 0 or control.size == 0:
        raise ValueError("Treatment and control spend arrays must not be empty.")
    if np.isnan(treatment).any() or np.isnan(control).any():
        raise ValueError("Spend arrays must not contain NaN values.")
    if (treatment < 0).any() or (control < 0).any():
        raise ValueError("Spend arrays must be nonnegative.")
    if iterations < 1:
        raise ValueError("iterations must be at least 1.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be strictly between zero and one.")

    rng = np.random.default_rng(random_state)
    treatment_indices = rng.integers(0, treatment.size, size=(iterations, treatment.size))
    control_indices = rng.integers(0, control.size, size=(iterations, control.size))
    bootstrap_differences = (
        treatment[treatment_indices].mean(axis=1) - control[control_indices].mean(axis=1)
    )
    tail_probability = (1 - confidence_level) / 2
    interval = np.quantile(
        bootstrap_differences, [tail_probability, 1 - tail_probability]
    )
    treatment_mean = float(treatment.mean())
    control_mean = float(control.mean())
    return RevenueComparison(
        treatment_group=treatment_group,
        control_group=control_group,
        treatment_n=int(treatment.size),
        control_n=int(control.size),
        treatment_mean=treatment_mean,
        control_mean=control_mean,
        observed_difference=treatment_mean - control_mean,
        confidence_interval_low=float(interval[0]),
        confidence_interval_high=float(interval[1]),
        bootstrap_iterations=iterations,
        random_state=random_state,
    )


def fetch_revenue_data(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Fetch all assigned customers' spend values from DuckDB."""
    return connection.execute(
        """
        SELECT treatment_group, spend
        FROM customer_experiment_analysis
        ORDER BY treatment_group, customer_id
        """
    ).fetchdf()


def fetch_revenue_summary(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Execute the SQL revenue summary query."""
    query = (SQL_DIRECTORY / "15_revenue_summary.sql").read_text(encoding="utf-8")
    return connection.execute(query).fetchdf()


def revenue_distribution_diagnostics(data: pd.DataFrame) -> pd.DataFrame:
    """Describe skewness and zero inflation for each assigned group."""
    rows: List[Dict[str, Union[str, int, float]]] = []
    for group, group_data in data.groupby("treatment_group", sort=True):
        spend = group_data["spend"].to_numpy(dtype=float)
        rows.append(
            {
                "treatment_group": group,
                "assigned_customers": int(spend.size),
                "zero_spend_customers": int((spend == 0).sum()),
                "zero_spend_rate": float((spend == 0).mean()),
                "mean_spend": float(spend.mean()),
                "median_spend": float(np.median(spend)),
                "spend_skewness": float(skew(spend, bias=False)),
            }
        )
    return pd.DataFrame(rows)


def analyze_revenue(
    connection: duckdb.DuckDBPyConnection,
    *,
    iterations: int = DEFAULT_ITERATIONS,
    random_state: int = DEFAULT_RANDOM_STATE,
    output_directory: Union[str, Path] = Path("reports"),
) -> Dict[str, Path]:
    """Run SQL summaries, bootstrap comparisons, diagnostics, and plotting."""
    data = fetch_revenue_data(connection)
    groups = {
        group: data.loc[data["treatment_group"] == group, "spend"].to_numpy()
        for group in (CONTROL_GROUP, *TREATMENT_GROUPS)
    }
    results = [
        bootstrap_mean_difference(
            groups[treatment],
            groups[CONTROL_GROUP],
            treatment_group=treatment,
            iterations=iterations,
            random_state=random_state,
        ).as_dict()
        for treatment in TREATMENT_GROUPS
    ]
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    summary_path = output_path / "revenue_summary.csv"
    comparison_path = output_path / "revenue_bootstrap_results.csv"
    diagnostics_path = output_path / "revenue_distribution_diagnostics.csv"
    fetch_revenue_summary(connection).to_csv(summary_path, index=False)
    pd.DataFrame(results).to_csv(comparison_path, index=False)
    revenue_distribution_diagnostics(data).to_csv(diagnostics_path, index=False)
    figure_path = output_path / "figures" / "revenue_differences_bootstrap_ci.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    _plot_revenue_differences(pd.DataFrame(results), figure_path)
    return {
        "summary": summary_path,
        "comparisons": comparison_path,
        "diagnostics": diagnostics_path,
        "figure": figure_path,
    }


def _plot_revenue_differences(results: pd.DataFrame, destination: Path) -> None:
    """Plot observed treatment-control revenue differences and bootstrap CIs."""
    figure, axis = plt.subplots(figsize=(8, 5))
    positions = np.arange(len(results))
    effects = results["observed_difference"].to_numpy()
    lower_errors = effects - results["confidence_interval_low"].to_numpy()
    upper_errors = results["confidence_interval_high"].to_numpy() - effects
    axis.errorbar(
        positions,
        effects,
        yerr=[lower_errors, upper_errors],
        fmt="o",
        capsize=5,
        color="#1769aa",
    )
    axis.axhline(0, color="black", linewidth=1, linestyle="--")
    axis.set_xticks(positions, results["treatment_group"])
    axis.set_ylabel("Revenue difference vs No E-Mail")
    axis.set_title("Average revenue per assigned customer\nBootstrap 95% confidence intervals")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(destination, dpi=160)
    plt.close(figure)


def run_revenue_analysis() -> None:
    """Build the database and export the default revenue analysis."""
    connection = build_database(Path("data/processed") / "hillstrom.duckdb")
    try:
        paths = analyze_revenue(connection)
        for name, path in paths.items():
            print(f"{name}: {path}")
    finally:
        connection.close()
