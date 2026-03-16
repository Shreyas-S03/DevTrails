from __future__ import annotations

from typing import Callable, Iterable, Mapping

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .constants import MONOTONIC_CONSTRAINTS_V1
from .models import MonotonicHGBRRiskPricingModel


def monotonic_violation_rate_for_predictor(
    predict_fn: Callable[[Iterable[Iterable[float]] | np.ndarray], np.ndarray],
    feature_columns: tuple[str, ...],
    reference_df: pd.DataFrame,
    monotonic_constraints: Mapping[str, int] = MONOTONIC_CONSTRAINTS_V1,
    n_base_points: int = 15,
    n_grid_points: int = 8,
    tolerance: float = 1e-4,
    random_state: int = 42,
) -> float:
    if reference_df.empty:
        return 0.0

    feature_cols_list = list(feature_columns)
    min_vals = reference_df.loc[:, feature_cols_list].min()
    max_vals = reference_df.loc[:, feature_cols_list].max()
    rng = np.random.default_rng(random_state)
    sample_size = min(n_base_points, len(reference_df))
    sampled_indices = rng.choice(reference_df.index, size=sample_size, replace=False)

    total_checks = 0
    violations = 0

    for row_idx in sampled_indices:
        base_row = reference_df.loc[row_idx, feature_cols_list].copy()
        for feature_name, direction in monotonic_constraints.items():
            if direction == 0 or feature_name not in feature_columns:
                continue

            probe_values = np.linspace(
                float(min_vals[feature_name]),
                float(max_vals[feature_name]),
                n_grid_points,
            )
            curve_predictions = []
            for probe in probe_values:
                probe_row = base_row.copy()
                probe_row[feature_name] = probe
                curve_predictions.append(
                    predict_fn([probe_row[col] for col in feature_cols_list])[0]
                )

            deltas = np.diff(curve_predictions)
            if direction == 1 and np.any(deltas < -tolerance):
                violations += 1
            if direction == -1 and np.any(deltas > tolerance):
                violations += 1
            total_checks += 1

    return round((violations / total_checks) if total_checks else 0.0, 4)


def monotonic_violation_rate(
    model: MonotonicHGBRRiskPricingModel,
    reference_df: pd.DataFrame,
    monotonic_constraints: Mapping[str, int] = MONOTONIC_CONSTRAINTS_V1,
    n_base_points: int = 15,
    n_grid_points: int = 8,
    tolerance: float = 1e-4,
    random_state: int = 42,
) -> float:
    return monotonic_violation_rate_for_predictor(
        predict_fn=model.predict_risk_score,
        feature_columns=model.feature_columns,
        reference_df=reference_df,
        monotonic_constraints=monotonic_constraints,
        n_base_points=n_base_points,
        n_grid_points=n_grid_points,
        tolerance=tolerance,
        random_state=random_state,
    )


def evaluate_model(
    model_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    monotonic_violation: float | None = None,
) -> dict[str, float | str]:
    return {
        "model": model_name,
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 4),
        "r2": round(float(r2_score(y_true, y_pred)), 4),
        "monotonic_violation_rate": (
            round(float(monotonic_violation), 4)
            if monotonic_violation is not None
            else np.nan
        ),
    }
