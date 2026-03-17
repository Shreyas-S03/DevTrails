from .cli import build_cli_parser, run_cli
from .constants import (
    FEATURE_COLUMNS_V0,
    FEATURE_COLUMNS_V1,
    MONOTONIC_CONSTRAINTS_V1,
    RISK_SCORE_MAX,
    RISK_SCORE_MIN,
    TARGET_COLUMN,
    WEEKLY_PREMIUM_MAX,
    WEEKLY_PREMIUM_MIN,
)
from .data_generation import generate_dummy_training_data, generate_dummy_training_data_v1
from .evaluation import evaluate_model, monotonic_violation_rate, monotonic_violation_rate_for_predictor
from .logging_utils import log_stage
from .models import EnsembleRiskPricingModel, MonotonicHGBRRiskPricingModel, RandomForestRiskPricingModel
from .pipeline import (
    _default_model_cache,
    calculate_weekly_premium,
    calculate_weekly_premium_with_model,
    get_default_model,
    predict_hgbr_risk,
    run_comparison_suite,
    train_and_compare_models,
)
from .utils import clip_risk, scale_risk_to_weekly_premium, to_feature_df

__all__ = [
    "FEATURE_COLUMNS_V0",
    "FEATURE_COLUMNS_V1",
    "TARGET_COLUMN",
    "MONOTONIC_CONSTRAINTS_V1",
    "RISK_SCORE_MIN",
    "RISK_SCORE_MAX",
    "WEEKLY_PREMIUM_MIN",
    "WEEKLY_PREMIUM_MAX",
    "clip_risk",
    "to_feature_df",
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
    "calculate_weekly_premium",
    "calculate_weekly_premium_with_model",
    "predict_hgbr_risk",
    "get_default_model",
    "_default_model_cache",
    "build_cli_parser",
    "run_cli",
    "log_stage",
]
