from __future__ import annotations

"""
Backward-compatible facade for the risk pricing engine.

All original public APIs are re-exported from the modular risk_engine package,
while keeping this file runnable as a script:

    python backend/ml/risk_model.py --tune-mode both
"""

try:
    from .risk_engine import (
        FEATURE_COLUMNS_V0,
        FEATURE_COLUMNS_V1,
        MONOTONIC_CONSTRAINTS_V1,
        RISK_SCORE_MAX,
        RISK_SCORE_MIN,
        TARGET_COLUMN,
        WEEKLY_PREMIUM_MAX,
        WEEKLY_PREMIUM_MIN,
        EnsembleRiskPricingModel,
        MonotonicHGBRRiskPricingModel,
        RandomForestRiskPricingModel,
        _default_model_cache,
        build_cli_parser,
        calculate_weekly_premium,
        calculate_weekly_premium_with_model,
        clip_risk,
        evaluate_model,
        generate_dummy_training_data,
        generate_dummy_training_data_v1,
        get_default_model,
        log_stage,
        monotonic_violation_rate,
        monotonic_violation_rate_for_predictor,
        predict_hgbr_risk,
        run_cli,
        run_comparison_suite,
        scale_risk_to_weekly_premium,
        to_feature_df,
        train_and_compare_models,
    )
except ImportError:
    from risk_engine import (
        FEATURE_COLUMNS_V0,
        FEATURE_COLUMNS_V1,
        MONOTONIC_CONSTRAINTS_V1,
        RISK_SCORE_MAX,
        RISK_SCORE_MIN,
        TARGET_COLUMN,
        WEEKLY_PREMIUM_MAX,
        WEEKLY_PREMIUM_MIN,
        EnsembleRiskPricingModel,
        MonotonicHGBRRiskPricingModel,
        RandomForestRiskPricingModel,
        _default_model_cache,
        build_cli_parser,
        calculate_weekly_premium,
        calculate_weekly_premium_with_model,
        clip_risk,
        evaluate_model,
        generate_dummy_training_data,
        generate_dummy_training_data_v1,
        get_default_model,
        log_stage,
        monotonic_violation_rate,
        monotonic_violation_rate_for_predictor,
        predict_hgbr_risk,
        run_cli,
        run_comparison_suite,
        scale_risk_to_weekly_premium,
        to_feature_df,
        train_and_compare_models,
    )

# Compatibility aliases for previous internal names.
_log_stage = log_stage
_clip_risk = clip_risk
_to_feature_df = to_feature_df
_build_cli_parser = build_cli_parser
_get_default_model = get_default_model

__all__ = [
    "FEATURE_COLUMNS_V0",
    "FEATURE_COLUMNS_V1",
    "TARGET_COLUMN",
    "MONOTONIC_CONSTRAINTS_V1",
    "RISK_SCORE_MIN",
    "RISK_SCORE_MAX",
    "WEEKLY_PREMIUM_MIN",
    "WEEKLY_PREMIUM_MAX",
    "_log_stage",
    "_clip_risk",
    "_to_feature_df",
    "scale_risk_to_weekly_premium",
    "generate_dummy_training_data",
    "generate_dummy_training_data_v1",
    "RandomForestRiskPricingModel",
    "MonotonicHGBRRiskPricingModel",
    "EnsembleRiskPricingModel",
    "monotonic_violation_rate_for_predictor",
    "monotonic_violation_rate",
    "evaluate_model",
    "train_and_compare_models",
    "run_comparison_suite",
    "_default_model_cache",
    "_build_cli_parser",
    "_get_default_model",
    "calculate_weekly_premium",
    "calculate_weekly_premium_with_model",
    "predict_hgbr_risk",
    "run_cli",
]


if __name__ == "__main__":
    run_cli()
