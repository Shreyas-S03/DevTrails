from __future__ import annotations

from time import perf_counter
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .constants import FEATURE_COLUMNS_V0, FEATURE_COLUMNS_V1, MONOTONIC_CONSTRAINTS_V1, TARGET_COLUMN
from .data_generation import generate_dummy_training_data, generate_dummy_training_data_v1
from .evaluation import evaluate_model, monotonic_violation_rate, monotonic_violation_rate_for_predictor
from .logging_utils import log_stage
from .models import EnsembleRiskPricingModel, MonotonicHGBRRiskPricingModel, RandomForestRiskPricingModel


def train_and_compare_models(
    records: int = 500,
    test_size: float = 0.2,
    random_state: int = 42,
    tune: bool = False,
    rf_weight: float = 0.4,
    hgbr_weight: float = 0.6,
    tuning_rf_n_iter: int = 8,
    tuning_hgbr_n_iter: int = 6,
    tuning_cv: int = 3,
    include_monotonic_checks: bool = True,
    verbose: bool = True,
) -> tuple[
    pd.DataFrame,
    RandomForestRiskPricingModel,
    MonotonicHGBRRiskPricingModel,
    EnsembleRiskPricingModel,
]:
    run_start = perf_counter()
    log_stage(
        f"Starting train/eval run (tune={tune}, records={records}, test_size={test_size})",
        enabled=verbose,
    )
    log_stage("Generating synthetic v1 dataset...", enabled=verbose)
    training_df = generate_dummy_training_data_v1(records=records, random_state=random_state)
    model_df = training_df.loc[:, [*FEATURE_COLUMNS_V1, TARGET_COLUMN]]

    log_stage("Splitting into train/test sets...", enabled=verbose)
    x_train, x_test, y_train, y_test = train_test_split(
        model_df.loc[:, FEATURE_COLUMNS_V1],
        model_df[TARGET_COLUMN],
        test_size=test_size,
        random_state=random_state,
    )
    log_stage(
        f"Split complete: train_rows={len(x_train)}, test_rows={len(x_test)}",
        enabled=verbose,
    )

    train_df = pd.concat([x_train, y_train], axis=1)
    test_df = pd.concat([x_test, y_test], axis=1)

    rf_model = RandomForestRiskPricingModel(
        feature_columns=FEATURE_COLUMNS_V1,
        random_state=random_state,
    )
    hgbr_model = MonotonicHGBRRiskPricingModel(
        feature_columns=FEATURE_COLUMNS_V1,
        random_state=random_state,
    )
    ensemble_model = EnsembleRiskPricingModel(
        rf_model=rf_model,
        hgbr_model=hgbr_model,
        rf_weight=rf_weight,
        hgbr_weight=hgbr_weight,
    )

    if tune:
        log_stage(
            f"Tuning RF (n_iter={tuning_rf_n_iter}, cv={tuning_cv})...",
            enabled=verbose,
        )
        rf_best_params = rf_model.tune_hyperparameters(
            train_df,
            n_iter=tuning_rf_n_iter,
            cv=tuning_cv,
            search_verbose=1 if verbose else 0,
        )
        log_stage(f"RF tuning complete. Best params: {rf_best_params}", enabled=verbose)
        log_stage(
            f"Tuning HGBR (n_iter={tuning_hgbr_n_iter}, cv={tuning_cv})...",
            enabled=verbose,
        )
        hgbr_best_params = hgbr_model.tune_hyperparameters(
            train_df,
            n_iter=tuning_hgbr_n_iter,
            cv=tuning_cv,
            search_verbose=1 if verbose else 0,
        )
        log_stage(f"HGBR tuning complete. Best params: {hgbr_best_params}", enabled=verbose)
    else:
        log_stage("Training RF (untuned)...", enabled=verbose)
        rf_model.train(train_df)
        log_stage("Training HGBR (untuned)...", enabled=verbose)
        hgbr_model.train(train_df)
        log_stage("Untuned training complete.", enabled=verbose)

    log_stage("Running test predictions for RF, HGBR, and Ensemble...", enabled=verbose)
    x_test_np = test_df.loc[:, FEATURE_COLUMNS_V1].to_numpy()
    rf_predictions = rf_model.predict_risk_score(x_test_np)
    hgbr_predictions = hgbr_model.predict_risk_score(x_test_np)
    ensemble_predictions = ensemble_model.predict_risk_score(x_test_np, x_test_np)

    rf_violation_rate = np.nan
    hgbr_violation_rate = np.nan
    ensemble_violation_rate = np.nan

    if include_monotonic_checks:
        log_stage("Computing monotonic violation rate for RF...", enabled=verbose)
        monotonic_probe_df = test_df.loc[:, FEATURE_COLUMNS_V1]
        rf_violation_rate = monotonic_violation_rate_for_predictor(
            predict_fn=rf_model.predict_risk_score,
            feature_columns=FEATURE_COLUMNS_V1,
            reference_df=monotonic_probe_df,
            monotonic_constraints=MONOTONIC_CONSTRAINTS_V1,
        )
        log_stage("Computing monotonic violation rate for HGBR...", enabled=verbose)
        hgbr_violation_rate = monotonic_violation_rate(
            hgbr_model,
            reference_df=monotonic_probe_df,
            monotonic_constraints=MONOTONIC_CONSTRAINTS_V1,
        )
        log_stage("Computing monotonic violation rate for Ensemble...", enabled=verbose)
        ensemble_violation_rate = monotonic_violation_rate_for_predictor(
            predict_fn=lambda features: ensemble_model.predict_risk_score(features, features),
            feature_columns=FEATURE_COLUMNS_V1,
            reference_df=monotonic_probe_df,
            monotonic_constraints=MONOTONIC_CONSTRAINTS_V1,
        )
        log_stage("Monotonic checks complete.", enabled=verbose)
    else:
        log_stage("Monotonic checks skipped.", enabled=verbose)

    log_stage("Computing evaluation metrics...", enabled=verbose)
    y_test_np = y_test.to_numpy()
    comparison_rows = [
        evaluate_model(
            "random_forest_v1",
            y_test_np,
            rf_predictions,
            monotonic_violation=rf_violation_rate,
        ),
        evaluate_model(
            "monotonic_hgbr_v1",
            y_test_np,
            hgbr_predictions,
            monotonic_violation=hgbr_violation_rate,
        ),
        evaluate_model(
            "ensemble_v1",
            y_test_np,
            ensemble_predictions,
            monotonic_violation=ensemble_violation_rate,
        ),
    ]
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df["tuned"] = tune
    comparison_df["rf_weight"] = rf_weight
    comparison_df["hgbr_weight"] = hgbr_weight
    comparison_df = comparison_df.loc[
        :,
        [
            "model",
            "tuned",
            "rf_weight",
            "hgbr_weight",
            "mae",
            "rmse",
            "r2",
            "monotonic_violation_rate",
        ],
    ]
    run_elapsed_sec = perf_counter() - run_start
    log_stage(f"Train/eval run complete in {run_elapsed_sec:.1f}s.", enabled=verbose)
    return comparison_df, rf_model, hgbr_model, ensemble_model


def run_comparison_suite(
    records: int = 500,
    test_size: float = 0.2,
    random_state: int = 42,
    rf_weight: float = 0.4,
    hgbr_weight: float = 0.6,
    tuning_rf_n_iter: int = 8,
    tuning_hgbr_n_iter: int = 6,
    tuning_cv: int = 3,
    include_monotonic_checks: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    log_stage("Running untuned comparison suite...", enabled=verbose)
    untuned_df, _, _, _ = train_and_compare_models(
        records=records,
        test_size=test_size,
        random_state=random_state,
        tune=False,
        rf_weight=rf_weight,
        hgbr_weight=hgbr_weight,
        tuning_rf_n_iter=tuning_rf_n_iter,
        tuning_hgbr_n_iter=tuning_hgbr_n_iter,
        tuning_cv=tuning_cv,
        include_monotonic_checks=include_monotonic_checks,
        verbose=verbose,
    )
    log_stage("Running tuned comparison suite...", enabled=verbose)
    tuned_df, _, _, _ = train_and_compare_models(
        records=records,
        test_size=test_size,
        random_state=random_state,
        tune=True,
        rf_weight=rf_weight,
        hgbr_weight=hgbr_weight,
        tuning_rf_n_iter=tuning_rf_n_iter,
        tuning_hgbr_n_iter=tuning_hgbr_n_iter,
        tuning_cv=tuning_cv,
        include_monotonic_checks=include_monotonic_checks,
        verbose=verbose,
    )
    log_stage("Comparison suite complete.", enabled=verbose)
    return pd.concat([untuned_df, tuned_df], ignore_index=True)


_default_model_cache: dict[str, RandomForestRiskPricingModel | MonotonicHGBRRiskPricingModel] = {}


def get_default_model(
    model_key: str = "rf_v0",
) -> RandomForestRiskPricingModel | MonotonicHGBRRiskPricingModel:
    if model_key in _default_model_cache:
        return _default_model_cache[model_key]

    if model_key == "rf_v0":
        model = RandomForestRiskPricingModel(feature_columns=FEATURE_COLUMNS_V0)
        model.train(generate_dummy_training_data(records=500, random_state=42))
    elif model_key == "rf_v1":
        model = RandomForestRiskPricingModel(feature_columns=FEATURE_COLUMNS_V1)
        model.train(generate_dummy_training_data_v1(records=500, random_state=42))
    elif model_key == "hgbr_v1":
        model = MonotonicHGBRRiskPricingModel(feature_columns=FEATURE_COLUMNS_V1)
        model.train(generate_dummy_training_data_v1(records=500, random_state=42))
    else:
        raise ValueError("model_key must be one of: rf_v0, rf_v1, hgbr_v1")

    _default_model_cache[model_key] = model
    return model


def calculate_weekly_premium(
    features_array: Iterable[Iterable[float]] | np.ndarray,
) -> np.ndarray:
    """
    Backward-compatible helper using the v0 random-forest model.
    Input order:
      [historical_rain_mm, zone_risk_index, rider_experience_months]
    """
    return get_default_model("rf_v0").calculate_weekly_premium(features_array)


def calculate_weekly_premium_with_model(
    features_array: Iterable[Iterable[float]] | np.ndarray,
    model_key: str = "hgbr_v1",
) -> np.ndarray:
    """
    Model-selectable premium helper.
    model_key in {'rf_v0', 'rf_v1', 'hgbr_v1'}.
    """
    return get_default_model(model_key).calculate_weekly_premium(features_array)


def predict_hgbr_risk(
    features_array: Iterable[Iterable[float]] | np.ndarray,
) -> np.ndarray:
    """
    Predict risk score(s) using the default tuned-compatible HGBR v1 model.
    Input order:
      [historical_rain_mm, zone_risk_index, rider_experience_months,
       aqi_index, strike_intensity_index, seasonal_risk_index, zone_baseline_risk]
    """
    model = get_default_model("hgbr_v1")
    return model.predict_risk_score(features_array)
