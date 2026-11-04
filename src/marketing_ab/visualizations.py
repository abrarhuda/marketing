"""Reproducible, publication-quality figures from saved analysis outputs."""

from pathlib import Path
from typing import Dict, Tuple, Union

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.metrics import roc_curve

from .database import build_database
from .machine_learning import split_modeling_data

GROUP_ORDER = ["No E-Mail", "Mens E-Mail", "Womens E-Mail"]
GROUP_COLORS = {"No E-Mail": "#4C566A", "Mens E-Mail": "#2E86AB", "Womens E-Mail": "#D95F59"}
MODEL_COLORS = {"logistic_regression": "#2E86AB", "decision_tree": "#D95F59"}
FIGURE_SIZE = (8.5, 5.5)
DPI = 220


def ensure_output_directory(path: Union[str, Path]) -> Path:
    """Create and return a directory for generated figures."""
    output_directory = Path(path)
    output_directory.mkdir(parents=True, exist_ok=True)
    return output_directory


def _configure_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook", font_scale=1.0)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "figure.titlesize": 16,
            "savefig.bbox": "tight",
        }
    )


def _save(figure: plt.Figure, path: Path, caption: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.text(0.5, 0.015, caption, ha="center", va="bottom", fontsize=9, color="#4C566A")
    figure.subplots_adjust(bottom=0.20)
    figure.savefig(path, dpi=DPI)
    plt.close(figure)
    return path


def _format_group_axis(axis: plt.Axes) -> None:
    axis.set_xticks(range(len(GROUP_ORDER)), GROUP_ORDER)
    axis.tick_params(axis="x", rotation=12)


def _read_table(reports: Path, name: str) -> pd.DataFrame:
    path = reports / "tables" / name
    if not path.exists():
        raise FileNotFoundError(f"Required analysis table was not found: {path}")
    return pd.read_csv(path)


def _plot_group_sizes(reports: Path, figures: Path) -> Path:
    data = (
        _read_table(reports, "group_outcomes.csv")
        .set_index("treatment_group")
        .reindex(GROUP_ORDER)
    )
    figure, axis = plt.subplots(figsize=FIGURE_SIZE)
    bars = axis.bar(
        GROUP_ORDER, data["assigned_customers"], color=[GROUP_COLORS[g] for g in GROUP_ORDER]
    )
    axis.bar_label(bars, fmt="%.0f", padding=3)
    axis.set(title="Experimental group sizes", ylabel="Assigned customers")
    _format_group_axis(axis)
    return _save(
        figure,
        figures / "01_experimental_group_sizes.png",
        "Business question: Was random assignment approximately balanced across the three groups?",
    )


def _plot_binary_rates(
    reports: Path, figures: Path, metric: str, filename: str, title: str, caption: str
) -> Path:
    data = (
        _read_table(reports, "group_outcomes.csv")
        .set_index("treatment_group")
        .reindex(GROUP_ORDER)
    )
    figure, axis = plt.subplots(figsize=FIGURE_SIZE)
    values = data[metric] * 100
    bars = axis.bar(GROUP_ORDER, values, color=[GROUP_COLORS[g] for g in GROUP_ORDER])
    axis.bar_label(bars, fmt="%.2f%%", padding=3)
    axis.set(title=title, ylabel="Rate (%)", ylim=(0, max(values) * 1.25))
    _format_group_axis(axis)
    return _save(figure, figures / filename, caption)


def _plot_treatment_effects(reports: Path, figures: Path) -> Path:
    data = pd.read_csv(reports / "ab_test_results.csv")
    data = data[data["analysis_type"] == "primary"].copy()
    figure, axis = plt.subplots(figsize=FIGURE_SIZE)
    x = np.arange(len(data))
    effects = data["absolute_effect_percentage_points"].to_numpy()
    lower = effects - data["confidence_interval_low_percentage_points"].to_numpy()
    upper = data["confidence_interval_high_percentage_points"].to_numpy() - effects
    axis.errorbar(x, effects, yerr=[lower, upper], fmt="o", capsize=5, linewidth=2, color="#2E86AB")
    axis.axhline(0, color="black", linewidth=1)
    axis.set(
        title="Website visit effects versus No E-Mail",
        ylabel="Absolute effect (percentage points)",
        xticks=x,
        xticklabels=data["treatment_group"],
    )
    axis.tick_params(axis="x", rotation=12)
    return _save(
        figure,
        figures / "04_visit_effects_confidence_intervals.png",
        "Business question: Treatment-versus-control visit effects with "
        "95% uncertainty intervals.",
    )


def _plot_revenue(reports: Path, figures: Path) -> Path:
    data = _read_table(reports, "revenue.csv").set_index("treatment_group").reindex(GROUP_ORDER)
    figure, axis = plt.subplots(figsize=FIGURE_SIZE)
    values = data["average_revenue_per_assigned_customer"]
    bars = axis.bar(GROUP_ORDER, values, color=[GROUP_COLORS[g] for g in GROUP_ORDER])
    axis.bar_label(bars, fmt="$%.2f", padding=3)
    axis.set(title="Average revenue per assigned customer", ylabel="Revenue (USD)")
    _format_group_axis(axis)
    return _save(
        figure,
        figures / "05_average_revenue_by_group.png",
        "Business question: Revenue per randomized customer, including "
        "customers who spent $0.",
    )


def _plot_historical_spending(processed_data: Path, figures: Path) -> Path:
    data = pd.read_csv(processed_data)
    figure, axis = plt.subplots(figsize=FIGURE_SIZE)
    sns.histplot(
        data=data,
        x="history",
        hue="segment",
        hue_order=GROUP_ORDER,
        palette=GROUP_COLORS,
        bins=45,
        element="step",
        stat="density",
        common_norm=False,
        alpha=0.20,
        ax=axis,
    )
    axis.set(
        title="Historical customer spending distribution",
        xlabel="Historical spend (USD)",
        ylabel="Density",
    )
    return _save(
        figure,
        figures / "06_historical_spending_distribution.png",
        "Business question: Similarity of pre-treatment spending "
        "distributions across randomized groups.",
    )


def _plot_segment_results(processed_data: Path, figures: Path) -> Path:
    data = pd.read_csv(processed_data)
    data = (
        data.groupby(["history_segment", "segment"], as_index=False)
        .agg(visit_rate=("visit", "mean"), assigned_customers=("customer_id", "size"))
        .rename(columns={"segment": "treatment_group"})
    )
    figure, axis = plt.subplots(figsize=FIGURE_SIZE)
    sns.barplot(
        data=data,
        x="history_segment",
        y="visit_rate",
        hue="treatment_group",
        hue_order=GROUP_ORDER,
        palette=GROUP_COLORS,
        ax=axis,
    )
    axis.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    axis.set(title="Website visits by historical customer segment", ylabel="Visit rate")
    axis.legend(title="Experiment group", frameon=False)
    return _save(
        figure,
        figures / "07_campaign_results_by_customer_segment.png",
        "Business question: Do campaign visit outcomes differ by "
        "historical customer segment?",
    )


def _plot_model_performance(reports: Path, figures: Path) -> Path:
    data = pd.read_csv(reports / "model_comparison.csv")
    metrics = [("roc_auc", "ROC-AUC"), ("log_loss", "Log loss"), ("brier_score", "Brier score")]
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.5))
    for axis, (metric, label) in zip(axes, metrics):
        values = data.set_index("model")[metric]
        bars = axis.bar(
            [name.replace("_", " ").title() for name in values.index],
            values,
            color=[MODEL_COLORS[name] for name in values.index],
        )
        axis.bar_label(bars, fmt="%.3f", padding=3)
        axis.set_title(label)
        axis.tick_params(axis="x", rotation=18)
    figure.suptitle("Held-out predictive model performance")
    return _save(
        figure,
        figures / "08_model_performance_comparison.png",
        "Business question: Which baseline model predicts website "
        "visitation better on the untouched test set.",
    )


def _load_test_predictions(
    model_directory: Path, database_path: Path
) -> Tuple[pd.Series, Dict[str, np.ndarray]]:
    connection = build_database(database_path)
    try:
        data = connection.execute(
            "SELECT customer_id, recency, history, history_segment, mens, womens, "
            "zip_code, newbie, channel, visit, treatment_group "
            "FROM customer_experiment_analysis"
        ).fetchdf()
    finally:
        connection.close()
    _, _, test_x, _, _, test_y = split_modeling_data(data)
    probabilities = {}
    for model_name in MODEL_COLORS:
        bundle = joblib.load(model_directory / f"{model_name}.joblib")
        probabilities[model_name] = bundle["pipeline"].predict_proba(test_x)[:, 1]
    return test_y.reset_index(drop=True), probabilities


def _plot_roc_and_calibration(
    model_directory: Path, database_path: Path, figures: Path
) -> Tuple[Path, Path]:
    target, probabilities = _load_test_predictions(model_directory, database_path)
    roc_figure, roc_axis = plt.subplots(figsize=FIGURE_SIZE)
    calibration_figure, calibration_axis = plt.subplots(figsize=FIGURE_SIZE)
    for name, values in probabilities.items():
        false_positive, true_positive, _ = roc_curve(target, values)
        label = name.replace("_", " ").title()
        roc_axis.plot(false_positive, true_positive, label=label, color=MODEL_COLORS[name])
        fraction_true, mean_predicted = calibration_curve(
            target, values, n_bins=10, strategy="quantile"
        )
        calibration_axis.plot(
            mean_predicted, fraction_true, marker="o", label=label, color=MODEL_COLORS[name]
        )
    roc_axis.plot([0, 1], [0, 1], "--", color="#777777", label="Random")
    roc_axis.set(
        title="Held-out ROC curves", xlabel="False positive rate", ylabel="True positive rate"
    )
    roc_axis.legend(frameon=False)
    calibration_axis.plot([0, 1], [0, 1], "--", color="#777777", label="Perfect calibration")
    calibration_axis.set(
        title="Held-out probability calibration",
        xlabel="Mean predicted probability",
        ylabel="Observed visit rate",
    )
    calibration_axis.legend(frameon=False)
    roc_path = _save(
        roc_figure,
        figures / "09_roc_curves.png",
        "Business question: How well models rank visitors versus "
        "non-visitors on held-out customers.",
    )
    calibration_path = _save(
        calibration_figure,
        figures / "09_probability_calibration.png",
        "Business question: Agreement between predicted visit "
        "probabilities and observed visit frequencies.",
    )
    return roc_path, calibration_path


def generate_all_figures(
    project_directory: Union[str, Path] = Path("."),
) -> Dict[str, Path]:
    """Regenerate all requested figures from saved analysis artifacts."""
    root = Path(project_directory)
    reports = root / "reports"
    figures = ensure_output_directory(reports / "figures")
    _configure_style()
    paths = {
        "group_sizes": _plot_group_sizes(reports, figures),
        "visit_rates": _plot_binary_rates(
            reports,
            figures,
            "visit_rate",
            "02_visit_rates_by_group.png",
            "Website visit rates by treatment group",
            "Business question: Which randomized group generated the highest website engagement?",
        ),
        "conversion_rates": _plot_binary_rates(
            reports,
            figures,
            "conversion_rate",
            "03_conversion_rates_by_group.png",
            "Purchase conversion rates by treatment group",
            "Business question: Which randomized group generated the "
            "highest purchase conversion rate?",
        ),
        "treatment_effects": _plot_treatment_effects(reports, figures),
        "average_revenue": _plot_revenue(reports, figures),
        "historical_spending": _plot_historical_spending(
            root / "data" / "processed" / "hillstrom_validated.csv", figures
        ),
        "campaign_by_segment": _plot_segment_results(
            root / "data" / "processed" / "hillstrom_validated.csv", figures
        ),
        "model_performance": _plot_model_performance(reports, figures),
    }
    roc_path, calibration_path = _plot_roc_and_calibration(
        root / "models", root / "data" / "processed" / "hillstrom.duckdb", figures
    )
    paths["roc_curves"] = roc_path
    paths["calibration"] = calibration_path
    return paths


def run_visualizations() -> None:
    """Regenerate the complete publication-quality figure set."""
    for name, path in generate_all_figures().items():
        print(f"{name}: {path}")
