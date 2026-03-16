# AI Parametric Insurance for Gig Workers - Agent Handoff

Last updated: 2026-03-16 (DB hardening + modular risk engine refactor + gitignore setup complete)
Repository root: `c:\Users\Shreyas S\OneDrive\Desktop\DevTrails`

## Project Goal
Hackathon prototype for parametric insurance focused on gig workers.

## Non-Negotiable Constraints
1. Coverage scope: **LOSS OF INCOME ONLY** from external disruptions:
   - Extreme weather
   - Severe pollution
   - Local strikes
2. Explicitly excluded:
   - Health
   - Life
   - Accidents
   - Vehicle repairs
3. Pricing basis: **STRICTLY WEEKLY**
4. Stack:
   - Backend/AI: Python, FastAPI, scikit-learn, LLM agents
   - Frontend: Next.js/React + Tailwind
   - Database: Supabase PostgreSQL

## Canonical Rider Schema (must remain consistent across API/DB/state)
```json
{
  "rider_id": "RIDER_8023",
  "profile": { "name": "Ravi Kumar", "phone": "+91-9876543210", "vehicle_type": "2_WHEELER", "primary_zone": "BLR_INDIRANAGAR" },
  "real_time_state": { "status": "ONLINE", "current_location": { "lat": 12.9784, "lon": 77.6408 }, "last_ping_timestamp": "2026-03-16T20:54:00Z" },
  "daily_performance": { "orders_completed_today": 14, "daily_target": 18, "incentive_at_risk": 250.00, "earnings_today": 650.00 },
  "insurance_profile": { "policy_active": true, "weekly_premium_paid": 22.50, "risk_score": 0.85 },
  "fraud_telemetry": { "current_speed_kmph": 0.0, "is_mock_location_enabled": false, "battery_level": 45 }
}
```

## Current Implementation Status
Step 1 implemented and optimized (DB + model baseline).

### Repo hygiene
- Added root `.gitignore` for:
  - Python artifacts (`__pycache__`, virtualenvs, coverage, build/dist)
  - Node/Next.js artifacts (`node_modules`, `.next`, `out`, logs)
  - env/secrets (`.env*` except `.env.example`)
  - editor/OS temp files
  - local Supabase dir (`.supabase/`)

### 1) Supabase schema
File: `supabase/schema.sql`

Created tables and safeguards:
- `public.riders`
  - `rider_id` primary key
  - JSONB columns for nested schema sections:
    - `profile`
    - `real_time_state`
    - `daily_performance`
    - `insurance_profile`
    - `fraud_telemetry`
  - generated query columns:
    - `primary_zone`
    - `rider_status`
    - `policy_active`
    - `risk_score`
    - `weekly_premium_paid`
  - strict JSON checks:
    - object shape checks
    - required-key checks
    - type checks for required fields
    - range checks (lat/lon, risk_score in `[0,1]`, battery bounds, non-negative performance metrics)
  - indexes:
    - zone, policy_active (partial true), rider_status, risk_score
    - GIN index on `real_time_state` JSONB
  - audit fields:
    - `created_at`
    - `updated_at` via trigger
- `public.claims`
  - `claim_id` primary key
  - `rider_id` foreign key to `riders(rider_id)`
  - required fields:
    - `amount`, `status`, `timestamp`, `disruption_type`
    - `coverage_week_start` (strict weekly basis)
  - lifecycle/ops fields:
    - `decision_reason`
    - `reviewed_at`
    - `paid_at`
    - `evidence_snapshot` JSONB
    - `created_at`, `updated_at`
  - disruption type constrained to:
    - `EXTREME_WEATHER`
    - `SEVERE_POLLUTION`
    - `LOCAL_STRIKE`
  - status constrained to:
    - `PENDING`, `APPROVED`, `REJECTED`, `PAID`
  - weekly enforcement:
    - `coverage_week_start` must be Monday-aligned
    - unique `(rider_id, disruption_type, coverage_week_start)` to prevent duplicate weekly claims for same disruption
  - lifecycle consistency checks:
    - `reviewed_at` required for approved/rejected/paid
    - `paid_at` only allowed for paid claims
    - `evidence_snapshot` must be JSON object
  - indexes:
    - rider/status/timestamp/coverage week
    - partial index for pending claims

Security and automation:
- Added shared `set_updated_at()` trigger function.
- Added update triggers for both tables.
- Enabled RLS for both tables.
- Added baseline policies for `authenticated` role (select/insert/update).

### 2) Predictive risk model
Primary files:
- Facade/entrypoint: `backend/ml/risk_model.py`
- Modular engine package: `backend/ml/risk_engine/`

Implemented:
- Modularity refactor:
  - `constants.py`:
    - feature sets, target name, monotonic constraints, risk/premium bounds
  - `utils.py`:
    - `clip_risk(...)`, `to_feature_df(...)`, `scale_risk_to_weekly_premium(...)`
  - `data_generation.py`:
    - `generate_dummy_training_data(...)`
    - `generate_dummy_training_data_v1(...)`
  - `models.py`:
    - `RandomForestRiskPricingModel`
    - `MonotonicHGBRRiskPricingModel`
    - `EnsembleRiskPricingModel`
  - `evaluation.py`:
    - `evaluate_model(...)`
    - monotonic violation utilities
  - `pipeline.py`:
    - `train_and_compare_models(...)`
    - `run_comparison_suite(...)`
    - model cache + premium helper APIs
  - `cli.py`:
    - parser + CLI run flow
- Backward compatibility:
  - `backend/ml/risk_model.py` now re-exports all previous public APIs and aliases old internal names:
    - `_log_stage`, `_clip_risk`, `_to_feature_df`, `_build_cli_parser`, `_get_default_model`
  - Existing commands and imports continue to work.
- Data generation:
  - `generate_dummy_training_data(...)` for v0 baseline (3 features)
  - `generate_dummy_training_data_v1(...)` for improved realism:
    - includes `aqi_index` and `strike_intensity_index`
    - adds zone-level effects (`zone_baseline_risk`)
    - adds seasonality (`seasonal_risk_index`)
    - injects rare disruption outliers
- Models are separated for easy selection/combination:
  - `RandomForestRiskPricingModel`
    - supports v0 and v1 feature sets
    - includes optional hyperparameter tuning via `RandomizedSearchCV`
  - `MonotonicHGBRRiskPricingModel`
    - uses `HistGradientBoostingRegressor`
    - applies monotonic constraints so pricing behavior stays consistent
    - includes optional hyperparameter tuning via `RandomizedSearchCV`
  - `EnsembleRiskPricingModel`
    - weighted blend of RF + HGBR predictions
- Evaluation utilities:
  - `train_and_compare_models(...)` to train and compare RF vs HGBR vs Ensemble
  - `run_comparison_suite(...)` to run untuned and tuned experiments together
  - `monotonic_violation_rate(...)` and `monotonic_violation_rate_for_predictor(...)` to quantify monotonic rule violations
  - metrics: MAE, RMSE, R2, monotonic_violation_rate
  - stage logs: timestamped progress output during data generation, split, train/tune, prediction, and evaluation
- Premium helpers:
  - `calculate_weekly_premium(features_array)` (backward-compatible `rf_v0`)
  - `calculate_weekly_premium_with_model(features_array, model_key=...)`
    - `model_key` in `rf_v0`, `rf_v1`, `hgbr_v1`
  - all pricing remains strictly weekly with bounds `[15, 40]`

## How to Run Current Step
1. Install dependencies:
   - `pip install pandas numpy scikit-learn`
2. Compare untuned RF/HGBR/Ensemble:
   - `python backend/ml/risk_model.py --tune-mode off`
3. Compare tuned RF/HGBR/Ensemble:
   - `python backend/ml/risk_model.py --tune-mode on`
4. Compare both untuned and tuned in one run:
   - `python backend/ml/risk_model.py --tune-mode both`
5. Optional faster run (skip monotonic checks):
   - `python backend/ml/risk_model.py --tune-mode both --skip-monotonic-checks`
6. Optional tune intensity controls:
   - `--rf-search-iter` (default 8)
   - `--hgbr-search-iter` (default 6)
   - `--tuning-cv` (default 3)
7. Optional disable intermediate logs:
   - `--quiet`
8. Programmatic training/testing:
   - `train_and_compare_models(records=500, test_size=0.2, tune=False)`
   - `train_and_compare_models(records=500, test_size=0.2, tune=True)`
   - `run_comparison_suite(records=500, test_size=0.2)`
9. Entry points:
   - CLI script: `python backend/ml/risk_model.py ...`
   - Programmatic import:
     - `from backend.ml.risk_model import ...`
     - `from backend.ml.risk_engine import ...`

## Model Comparison Guidance
When comparing RF vs HGBR vs Ensemble outputs, prioritize:
1. Lower MAE and RMSE (prediction error quality)
2. Higher R2 (fit quality)
3. Lower monotonic violation rate (pricing consistency with business logic)
4. Premium stability in plausible range, especially under feature stress tests

Current local run snapshot (synthetic v1):
- Untuned:
  - `random_forest_v1`: MAE `0.0403`, RMSE `0.0486`, R2 `0.8484`, monotonic violations `0.2857`
  - `monotonic_hgbr_v1`: MAE `0.0318`, RMSE `0.0385`, R2 `0.9048`, monotonic violations `0.0000`
  - `ensemble_v1`: MAE `0.0337`, RMSE `0.0400`, R2 `0.8975`, monotonic violations `0.1048`
- Tuned:
  - `random_forest_v1`: MAE `0.0391`, RMSE `0.0475`, R2 `0.8557`, monotonic violations `0.3619`
  - `monotonic_hgbr_v1`: MAE `0.0314`, RMSE `0.0377`, R2 `0.9092`, monotonic violations `0.0000`
  - `ensemble_v1`: MAE `0.0337`, RMSE `0.0400`, R2 `0.8978`, monotonic violations `0.1048`

## Important Design Choices
1. Kept rider nested data in JSONB to preserve canonical payload shape.
2. Added strict DB constraints to enforce schema integrity and policy scope.
3. Encapsulated ML logic in class + module function for easy FastAPI integration later.
4. Weekly premium bounds hardcoded in one place for maintainability.
5. Added weekly claims deduping and lifecycle audit columns for explainability and ops readiness.

## Next Recommended Steps
1. Create FastAPI app with:
   - `POST /riders/upsert`
   - `POST /pricing/weekly-quote`
   - `POST /claims/create`
2. Add Pydantic models mirroring canonical Rider schema + DB constraints.
3. Add Supabase access layer (insert/update riders, weekly claim insert with conflict handling).
4. Add unit tests for:
   - premium bounds
   - invalid feature shapes
   - DB disruption/status/weekly-uniqueness constraints

## Rule For Future Agents
Whenever code changes are made, update this `AGENTS.md` so continuity is preserved.
