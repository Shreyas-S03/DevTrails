from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV

from .constants import FEATURE_COLUMNS_V0, FEATURE_COLUMNS_V1, MONOTONIC_CONSTRAINTS_V1, TARGET_COLUMN
from .utils import clip_risk, scale_risk_to_weekly_premium, to_feature_df


@dataclass
class RandomForestRiskPricingModel:
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS_V0
    random_state: int = 42
    n_estimators: int = 320
    max_depth: int = 9
    min_samples_leaf: int = 3

    def __post_init__(self) -> None:
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_leaf=self.min_samples_leaf,
            random_state=self.random_state,
            n_jobs=1,
        )
        self.is_trained = False

    def train(self, training_df: pd.DataFrame) -> None:
        required_columns = {*self.feature_columns, TARGET_COLUMN}
        missing_columns = required_columns - set(training_df.columns)
        if missing_columns:
            raise ValueError(
                f"training_df is missing required columns: {sorted(missing_columns)}"
            )

        x_train = training_df.loc[:, self.feature_columns]
        y_train = training_df[TARGET_COLUMN]
        self.model.fit(x_train, y_train)
        self.is_trained = True

    def tune_hyperparameters(
        self,
        training_df: pd.DataFrame,
        n_iter: int = 16,
        cv: int = 3,
        search_verbose: int = 0,
    ) -> dict[str, int]:
        x_train = training_df.loc[:, self.feature_columns]
        y_train = training_df[TARGET_COLUMN]
        param_distributions = {
            "n_estimators": [220, 280, 320, 380, 450],
            "max_depth": [5, 7, 9, 11, None],
            "min_samples_leaf": [1, 2, 3, 4, 6],
            "min_samples_split": [2, 4, 6, 8],
            "max_features": ["sqrt", 0.8, 1.0],
        }
        search = RandomizedSearchCV(
            estimator=self.model,
            param_distributions=param_distributions,
            n_iter=n_iter,
            scoring="neg_mean_absolute_error",
            cv=cv,
            random_state=self.random_state,
            n_jobs=1,
            verbose=search_verbose,
        )
        search.fit(x_train, y_train)
        self.model = search.best_estimator_
        self.is_trained = True
        return search.best_params_

    def predict_risk_score(
        self,
        features_array: Iterable[Iterable[float]] | np.ndarray,
    ) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Model is not trained. Call train() first.")
        features_df = to_feature_df(features_array, self.feature_columns)
        predicted_scores = self.model.predict(features_df)
        return clip_risk(predicted_scores)

    def calculate_weekly_premium(
        self,
        features_array: Iterable[Iterable[float]] | np.ndarray,
    ) -> np.ndarray:
        return scale_risk_to_weekly_premium(self.predict_risk_score(features_array))


@dataclass
class MonotonicHGBRRiskPricingModel:
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS_V1
    monotonic_constraints: Mapping[str, int] = field(
        default_factory=lambda: MONOTONIC_CONSTRAINTS_V1.copy()
    )
    random_state: int = 42
    learning_rate: float = 0.05
    max_iter: int = 320
    max_depth: int = 6
    min_samples_leaf: int = 12
    l2_regularization: float = 0.05

    def __post_init__(self) -> None:
        monotonic_vector = [
            int(self.monotonic_constraints.get(feature_name, 0))
            for feature_name in self.feature_columns
        ]
        self.model = HistGradientBoostingRegressor(
            loss="squared_error",
            learning_rate=self.learning_rate,
            max_iter=self.max_iter,
            max_depth=self.max_depth,
            min_samples_leaf=self.min_samples_leaf,
            l2_regularization=self.l2_regularization,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=15,
            random_state=self.random_state,
            monotonic_cst=monotonic_vector,
        )
        self.is_trained = False

    def train(self, training_df: pd.DataFrame) -> None:
        required_columns = {*self.feature_columns, TARGET_COLUMN}
        missing_columns = required_columns - set(training_df.columns)
        if missing_columns:
            raise ValueError(
                f"training_df is missing required columns: {sorted(missing_columns)}"
            )

        x_train = training_df.loc[:, self.feature_columns]
        y_train = training_df[TARGET_COLUMN]
        self.model.fit(x_train, y_train)
        self.is_trained = True

    def tune_hyperparameters(
        self,
        training_df: pd.DataFrame,
        n_iter: int = 12,
        cv: int = 3,
        search_verbose: int = 0,
    ) -> dict[str, float | int]:
        x_train = training_df.loc[:, self.feature_columns]
        y_train = training_df[TARGET_COLUMN]
        monotonic_vector = [
            int(self.monotonic_constraints.get(feature_name, 0))
            for feature_name in self.feature_columns
        ]
        base_model = HistGradientBoostingRegressor(
            loss="squared_error",
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=15,
            random_state=self.random_state,
            monotonic_cst=monotonic_vector,
        )
        param_distributions = {
            "learning_rate": [0.03, 0.05, 0.08, 0.1],
            "max_iter": [220, 280, 320, 380],
            "max_depth": [4, 5, 6, 7],
            "min_samples_leaf": [8, 12, 16, 20],
            "l2_regularization": [0.0, 0.02, 0.05, 0.1],
            "max_bins": [128, 192, 255],
        }
        search = RandomizedSearchCV(
            estimator=base_model,
            param_distributions=param_distributions,
            n_iter=n_iter,
            scoring="neg_mean_absolute_error",
            cv=cv,
            random_state=self.random_state,
            n_jobs=1,
            verbose=search_verbose,
        )
        search.fit(x_train, y_train)
        self.model = search.best_estimator_
        self.is_trained = True
        return search.best_params_

    def predict_risk_score(
        self,
        features_array: Iterable[Iterable[float]] | np.ndarray,
    ) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Model is not trained. Call train() first.")
        features_df = to_feature_df(features_array, self.feature_columns)
        predicted_scores = self.model.predict(features_df)
        return clip_risk(predicted_scores)

    def calculate_weekly_premium(
        self,
        features_array: Iterable[Iterable[float]] | np.ndarray,
    ) -> np.ndarray:
        return scale_risk_to_weekly_premium(self.predict_risk_score(features_array))


@dataclass
class EnsembleRiskPricingModel:
    rf_model: RandomForestRiskPricingModel
    hgbr_model: MonotonicHGBRRiskPricingModel
    rf_weight: float = 0.4
    hgbr_weight: float = 0.6

    def __post_init__(self) -> None:
        if not np.isclose(self.rf_weight + self.hgbr_weight, 1.0):
            raise ValueError("rf_weight + hgbr_weight must equal 1.0")

    def predict_risk_score(
        self,
        rf_features_array: Iterable[Iterable[float]] | np.ndarray,
        hgbr_features_array: Iterable[Iterable[float]] | np.ndarray,
    ) -> np.ndarray:
        rf_pred = self.rf_model.predict_risk_score(rf_features_array)
        hgbr_pred = self.hgbr_model.predict_risk_score(hgbr_features_array)
        return clip_risk((self.rf_weight * rf_pred) + (self.hgbr_weight * hgbr_pred))

    def calculate_weekly_premium(
        self,
        rf_features_array: Iterable[Iterable[float]] | np.ndarray,
        hgbr_features_array: Iterable[Iterable[float]] | np.ndarray,
    ) -> np.ndarray:
        return scale_risk_to_weekly_premium(
            self.predict_risk_score(rf_features_array, hgbr_features_array)
        )
