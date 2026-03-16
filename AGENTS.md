# AI Parametric Insurance for Gig Workers - Agent Handoff

Last updated: 2026-03-16 (requirements + gitignore + modular ML engine current)
Repository root: `c:\Users\Shreyas S\OneDrive\Desktop\DevTrails`

## Project Goal
Hackathon prototype for parametric insurance for gig workers.

## Non-Negotiable Constraints
1. Coverage scope: LOSS OF INCOME ONLY from external disruptions:
   - Extreme weather
   - Severe pollution
   - Local strikes
2. Exclusions:
   - Health
   - Life
   - Accidents
   - Vehicle repairs
3. Pricing basis: STRICTLY WEEKLY
4. Stack:
   - Backend/AI: Python, FastAPI, scikit-learn, LLM agents
   - Frontend: Next.js/React + Tailwind
   - Database: Supabase PostgreSQL

## Canonical Rider Schema
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

## Current State

### Database
File: `supabase/schema.sql`

Implemented:
1. `public.riders` with JSONB fields mapped to canonical schema.
2. Strong checks:
   - Required keys, value types, range checks.
   - Risk score bounds, lat/lon bounds, battery bounds.
3. Generated columns for query speed:
   - `primary_zone`, `rider_status`, `policy_active`, `risk_score`, `weekly_premium_paid`
4. `public.claims` includes:
   - `coverage_week_start`
   - `decision_reason`, `reviewed_at`, `paid_at`, `evidence_snapshot`
5. Weekly enforcement:
   - Monday-aligned `coverage_week_start`
   - Unique `(rider_id, disruption_type, coverage_week_start)`
6. Triggers:
   - `set_updated_at()` for both tables
7. RLS:
   - Enabled with baseline `authenticated` select/insert/update policies

### ML Risk/Pricing Engine
Facade file: `backend/ml/risk_model.py`
Modular package: `backend/ml/risk_engine/`

Modules:
1. `constants.py` - feature sets, bounds, monotonic constraints
2. `utils.py` - clipping, feature-shape conversion, premium scaling
3. `data_generation.py` - v0 and v1 synthetic data generators
4. `models.py` - RF model, monotonic HGBR model, ensemble model
5. `evaluation.py` - MAE/RMSE/R2 + monotonic violation checks
6. `pipeline.py` - training/comparison suite + model cache + premium helper APIs
7. `cli.py` - argparse commands and CLI runner

Backward compatibility preserved:
1. Existing imports from `backend.ml.risk_model` still work.
2. Existing CLI command still works:
   - `python backend/ml/risk_model.py ...`
3. Compatibility aliases preserved:
   - `_log_stage`, `_clip_risk`, `_to_feature_df`, `_build_cli_parser`, `_get_default_model`

## Model Features and Variants
1. v0 features:
   - `historical_rain_mm`, `zone_risk_index`, `rider_experience_months`
2. v1 features:
   - v0 + `aqi_index`, `strike_intensity_index`, `seasonal_risk_index`, `zone_baseline_risk`

Model options:
1. `rf_v0`
2. `rf_v1`
3. `hgbr_v1` (monotonic constraints)
4. `ensemble_v1` (RF + HGBR weighted blend)

## CLI Commands
1. Untuned comparison:
   - `python backend/ml/risk_model.py --tune-mode off`
2. Tuned comparison:
   - `python backend/ml/risk_model.py --tune-mode on`
3. Both runs:
   - `python backend/ml/risk_model.py --tune-mode both`
4. Custom ensemble weights:
   - `python backend/ml/risk_model.py --tune-mode both --rf-weight 0.5 --hgbr-weight 0.5`
5. Faster run:
   - `python backend/ml/risk_model.py --tune-mode both --skip-monotonic-checks`
6. Quiet mode:
   - `python backend/ml/risk_model.py --tune-mode both --quiet`

## Repo Hygiene
1. Root `.gitignore` added for Python/Node/env/editor/Supabase artifacts.
2. Root `requirements.txt` added with pinned core dependencies:
   - `fastapi`, `uvicorn[standard]`, `pydantic`
   - `numpy`, `pandas`, `scikit-learn`, `scipy`
   - `supabase`, `python-dotenv`

## Next Recommended Build Steps
1. FastAPI scaffold:
   - `POST /riders/upsert`
   - `POST /pricing/weekly-quote`
   - `POST /claims/create`
2. Pydantic request/response schemas aligned to rider schema and DB constraints.
3. Supabase repository layer with conflict-safe weekly claim inserts.
4. Unit tests for:
   - premium bounds and feature validation
   - disruption/status constraints
   - weekly uniqueness constraint

## Rule For Future Agents
Whenever code changes are made, update this `AGENTS.md` to match actual codebase state.
