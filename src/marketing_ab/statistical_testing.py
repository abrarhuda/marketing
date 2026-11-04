"""Reusable two-proportion A/B testing for the Hillstrom experiment."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Union

import duckdb
import pandas as pd
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportions_ztest,
)

CONTROL_GROUP = "No E-Mail"
PRIMARY_TREATMENTS = ("Mens E-Mail", "Womens E-Mail")
ALPHA = 0.05


@dataclass(frozen=True)
class ProportionComparison:
    """Results for one treatment-versus-control binary-outcome comparison."""

    outcome: str
    analysis_type: str
    treatment_group: str
    control_group: str
    treatment_n: int
    control_n: int
    treatment_events: int
    control_events: int
    treatment_rate: float
    control_rate: float
    absolute_effect: float
    relative_lift: float
    z_statistic: float
    p_value: float
    confidence_interval_low: float
    confidence_interval_high: float
    adjusted_p_value: float = float("nan")
    reject_null_after_correction: bool = False

    def as_dict(self) -> Dict[str, Union[str, int, float, bool]]:
        """Return a flat record suitable for a CSV or DataFrame."""
        return {
            "outcome": self.outcome,
            "analysis_type": self.analysis_type,
            "treatment_group": self.treatment_group,
            "control_group": self.control_group,
            "treatment_n": self.treatment_n,
            "control_n": self.control_n,
            "treatment_events": self.treatment_events,
            "control_events": self.control_events,
            "treatment_rate": self.treatment_rate,
            "control_rate": self.control_rate,
            "absolute_effect_percentage_points": self.absolute_effect * 100,
            "relative_lift_percentage": self.relative_lift * 100,
            "z_statistic": self.z_statistic,
            "unadjusted_p_value": self.p_value,
            "holm_adjusted_p_value": self.adjusted_p_value,
            "confidence_interval_low_percentage_points": self.confidence_interval_low * 100,
            "confidence_interval_high_percentage_points": self.confidence_interval_high * 100,
            "reject_null_after_holm": self.reject_null_after_correction,
        }


def validate_comparison_groups(
    comparison_groups: Sequence[str], available_groups: Sequence[str]
) -> None:
    """Validate that requested comparison groups are present."""
    missing_groups = sorted(set(comparison_groups).difference(available_groups))
    if missing_groups:
        raise ValueError(f"Comparison groups are not available: {', '.join(missing_groups)}")


def compare_proportions(
    treatment_events: int,
    treatment_n: int,
    control_events: int,
    control_n: int,
    *,
    outcome: str,
    treatment_group: str,
    control_group: str = CONTROL_GROUP,
    analysis_type: str = "primary",
    alpha: float = ALPHA,
) -> ProportionComparison:
    """Run a two-sided two-proportion z-test and CI for treatment minus control."""
    if treatment_n <= 0 or control_n <= 0:
        raise ValueError("Both treatment and control sample sizes must be positive.")
    if not 0 <= treatment_events <= treatment_n:
        raise ValueError("Treatment event count must be between zero and treatment_n.")
    if not 0 <= control_events <= control_n:
        raise ValueError("Control event count must be between zero and control_n.")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between zero and one.")

    counts = [treatment_events, control_events]
    sample_sizes = [treatment_n, control_n]
    z_statistic, p_value = proportions_ztest(counts, sample_sizes, alternative="two-sided")
    confidence_interval = confint_proportions_2indep(
        treatment_events,
        treatment_n,
        control_events,
        control_n,
        method="wald",
        compare="diff",
        alpha=alpha,
    )
    treatment_rate = treatment_events / treatment_n
    control_rate = control_events / control_n
    absolute_effect = treatment_rate - control_rate
    relative_lift = (
        absolute_effect / control_rate if control_rate != 0 else float("nan")
    )
    return ProportionComparison(
        outcome=outcome,
        analysis_type=analysis_type,
        treatment_group=treatment_group,
        control_group=control_group,
        treatment_n=treatment_n,
        control_n=control_n,
        treatment_events=treatment_events,
        control_events=control_events,
        treatment_rate=treatment_rate,
        control_rate=control_rate,
        absolute_effect=absolute_effect,
        relative_lift=relative_lift,
        z_statistic=float(z_statistic),
        p_value=float(p_value),
        confidence_interval_low=float(confidence_interval[0]),
        confidence_interval_high=float(confidence_interval[1]),
    )


def apply_holm_correction(
    comparisons: Sequence[ProportionComparison], alpha: float = ALPHA
) -> List[ProportionComparison]:
    """Apply Holm adjustment within one explicitly supplied hypothesis family."""
    if not comparisons:
        return []
    rejected, adjusted_p_values, _, _ = multipletests(
        [comparison.p_value for comparison in comparisons],
        alpha=alpha,
        method="holm",
    )
    return [
        ProportionComparison(
            **{
                **comparison.__dict__,
                "adjusted_p_value": float(adjusted_p_value),
                "reject_null_after_correction": bool(reject),
            }
        )
        for comparison, adjusted_p_value, reject in zip(
            comparisons, adjusted_p_values, rejected
        )
    ]


def analyze_group_counts(
    group_counts: pd.DataFrame,
    *,
    outcome: str,
    analysis_type: str,
    treatments: Iterable[str] = PRIMARY_TREATMENTS,
    control_group: str = CONTROL_GROUP,
) -> List[ProportionComparison]:
    """Analyze binary event counts already aggregated by experiment group."""
    required_columns = {"treatment_group", "assigned_customers", outcome}
    missing_columns = required_columns.difference(group_counts.columns)
    if missing_columns:
        raise ValueError(f"Missing aggregate columns: {sorted(missing_columns)}")
    available_groups = group_counts["treatment_group"].tolist()
    validate_comparison_groups([control_group, *treatments], available_groups)
    rows = group_counts.set_index("treatment_group")
    comparisons = []
    for treatment in treatments:
        comparisons.append(
            compare_proportions(
                int(rows.loc[treatment, outcome]),
                int(rows.loc[treatment, "assigned_customers"]),
                int(rows.loc[control_group, outcome]),
                int(rows.loc[control_group, "assigned_customers"]),
                outcome=outcome,
                treatment_group=treatment,
                control_group=control_group,
                analysis_type=analysis_type,
            )
        )
    return apply_holm_correction(comparisons)


def fetch_binary_group_counts(
    connection: duckdb.DuckDBPyConnection, outcome_column: str
) -> pd.DataFrame:
    """Aggregate a binary outcome in DuckDB before statistical testing."""
    if outcome_column not in {"visit", "conversion"}:
        raise ValueError("outcome_column must be 'visit' or 'conversion'.")
    query = f"""
        SELECT
            treatment_group,
            COUNT(*) AS assigned_customers,
            SUM(CASE WHEN {outcome_column} = 1 THEN 1 ELSE 0 END) AS events
        FROM customer_experiment_analysis
        GROUP BY treatment_group
        ORDER BY treatment_group
    """
    return connection.execute(query).fetchdf().rename(columns={"events": outcome_column})


def run_ab_test_analysis(
    connection: duckdb.DuckDBPyConnection,
    output_path: Union[str, Path] = Path("reports/ab_test_results.csv"),
) -> pd.DataFrame:
    """Run primary visit and exploratory secondary conversion analyses."""
    visit_counts = fetch_binary_group_counts(connection, "visit")
    conversion_counts = fetch_binary_group_counts(connection, "conversion")
    primary = analyze_group_counts(
        visit_counts, outcome="visit", analysis_type="primary"
    )
    secondary = analyze_group_counts(
        conversion_counts, outcome="conversion", analysis_type="exploratory_secondary"
    )
    results = pd.DataFrame(
        [comparison.as_dict() for comparison in [*primary, *secondary]]
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(destination, index=False)
    return results


def run_statistical_analysis() -> None:
    """Build the database, run the analyses, and export the result table."""
    from .database import build_database

    connection = build_database(Path("data/processed") / "hillstrom.duckdb")
    try:
        results = run_ab_test_analysis(connection)
        print(results.to_string(index=False))
    finally:
        connection.close()
