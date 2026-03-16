from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from .logging_utils import log_stage
from .models import EnsembleRiskPricingModel
from .pipeline import (
    calculate_weekly_premium,
    calculate_weekly_premium_with_model,
    get_default_model,
    run_comparison_suite,
    train_and_compare_models,
)


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train and compare RF, monotonic HGBR, and ensemble risk models."
    )
    parser.add_argument("--records", type=int, default=500, help="Synthetic records count.")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio.")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--tune-mode",
        choices=["off", "on", "both"],
        default="off",
        help="Whether to run untuned, tuned, or both comparisons.",
    )
    parser.add_argument("--rf-weight", type=float, default=0.4, help="RF weight in ensemble.")
    parser.add_argument("--hgbr-weight", type=float, default=0.6, help="HGBR weight in ensemble.")
    parser.add_argument(
        "--rf-search-iter",
        type=int,
        default=8,
        help="RandomizedSearchCV iterations for RF when tuning.",
    )
    parser.add_argument(
        "--hgbr-search-iter",
        type=int,
        default=6,
        help="RandomizedSearchCV iterations for HGBR when tuning.",
    )
    parser.add_argument(
        "--tuning-cv",
        type=int,
        default=3,
        help="Cross-validation folds during tuning.",
    )
    parser.add_argument(
        "--skip-monotonic-checks",
        action="store_true",
        help="Skip monotonic violation checks to speed up run time.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable intermediate progress logs.",
    )
    return parser


def _build_sample_predictions_table() -> pd.DataFrame:
    sample_v0_features = np.array([[85.0, 8, 10], [25.0, 3, 36]])
    sample_v1_features = np.array(
        [
            [85.0, 8, 10, 210.0, 20.0, 0.74, 0.72],
            [25.0, 3, 36, 95.0, 8.0, 0.31, 0.28],
        ]
    )

    ensemble = EnsembleRiskPricingModel(
        rf_model=get_default_model("rf_v1"),
        hgbr_model=get_default_model("hgbr_v1"),
    )
    return pd.DataFrame(
        {
            "model": ["rf_v0", "rf_v1", "hgbr_v1", "ensemble_v1"],
            "weekly_premiums": [
                calculate_weekly_premium(sample_v0_features).tolist(),
                calculate_weekly_premium_with_model(sample_v1_features, model_key="rf_v1").tolist(),
                calculate_weekly_premium_with_model(sample_v1_features, model_key="hgbr_v1").tolist(),
                ensemble.calculate_weekly_premium(sample_v1_features, sample_v1_features).tolist(),
            ],
        }
    )


def run_cli() -> None:
    parser = build_cli_parser()
    args = parser.parse_args()
    verbose_logs = not args.quiet

    log_stage("Training and comparing risk models on synthetic data...", enabled=verbose_logs)
    if args.tune_mode == "both":
        comparison_df = run_comparison_suite(
            records=args.records,
            test_size=args.test_size,
            random_state=args.random_state,
            rf_weight=args.rf_weight,
            hgbr_weight=args.hgbr_weight,
            tuning_rf_n_iter=args.rf_search_iter,
            tuning_hgbr_n_iter=args.hgbr_search_iter,
            tuning_cv=args.tuning_cv,
            include_monotonic_checks=(not args.skip_monotonic_checks),
            verbose=verbose_logs,
        )
    else:
        comparison_df, _, _, _ = train_and_compare_models(
            records=args.records,
            test_size=args.test_size,
            random_state=args.random_state,
            tune=(args.tune_mode == "on"),
            rf_weight=args.rf_weight,
            hgbr_weight=args.hgbr_weight,
            tuning_rf_n_iter=args.rf_search_iter,
            tuning_hgbr_n_iter=args.hgbr_search_iter,
            tuning_cv=args.tuning_cv,
            include_monotonic_checks=(not args.skip_monotonic_checks),
            verbose=verbose_logs,
        )

    print(comparison_df.to_string(index=False))
    print("\nSample predictions:")
    print(_build_sample_predictions_table().to_string(index=False))
