from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from .constants import (
    RISK_SCORE_MAX,
    RISK_SCORE_MIN,
    WEEKLY_PREMIUM_MAX,
    WEEKLY_PREMIUM_MIN,
)


def clip_risk(predicted_scores: np.ndarray) -> np.ndarray:
    return np.clip(predicted_scores, RISK_SCORE_MIN, RISK_SCORE_MAX)


def to_feature_df(
    features_array: Iterable[Iterable[float]] | np.ndarray,
    feature_columns: tuple[str, ...],
) -> pd.DataFrame:
    features = np.asarray(features_array, dtype=float)
    if features.ndim == 1:
        features = features.reshape(1, -1)
    if features.shape[1] != len(feature_columns):
        raise ValueError(
            f"Each row must have {len(feature_columns)} features in order: {feature_columns}"
        )
    return pd.DataFrame(features, columns=feature_columns)


def scale_risk_to_weekly_premium(predicted_scores: np.ndarray) -> np.ndarray:
    normalized_scores = (predicted_scores - RISK_SCORE_MIN) / (
        RISK_SCORE_MAX - RISK_SCORE_MIN
    )
    premiums = WEEKLY_PREMIUM_MIN + normalized_scores * (
        WEEKLY_PREMIUM_MAX - WEEKLY_PREMIUM_MIN
    )
    return np.round(np.clip(premiums, WEEKLY_PREMIUM_MIN, WEEKLY_PREMIUM_MAX), 2)
