"""Evaluation helpers for predictive and uplift models."""

from collections.abc import Sequence
from typing import Dict


def validate_matching_lengths(*sequences: Sequence[object]) -> None:
    """Raise an error when evaluation inputs do not have matching lengths."""
    lengths = {len(sequence) for sequence in sequences}
    if len(lengths) > 1:
        raise ValueError("Evaluation inputs must have matching lengths.")


def validate_probability_metrics(metrics: Dict[str, float]) -> None:
    """Validate that probability-based metrics are finite and nonnegative."""
    for name in ("roc_auc", "precision", "recall", "f1", "log_loss", "brier_score"):
        value = metrics[name]
        if value != value or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative.")
