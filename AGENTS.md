# AI Parametric Insurance for Gig Workers - Agent Handoff

Last updated: 2026-03-17 (Step 2 orchestrator implemented + REST Supabase auth for sb_secret)
Repository root: `c:\Users\Shreyas S\OneDrive\Desktop\DevTrails`

## Project Goal
Hackathon prototype for parametric insurance focused on gig workers.

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
   - Backend/AI: Python, FastAPI, scikit-learn, LangGraph
   - Frontend: Next.js/React + Tailwind
   - Database: Supabase PostgreSQL

## Canonical Rider Schema
Use this shape across payloads, DB records, and app logic:
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

### 1) Database schema
Files:
1. `supabase/schema.sql` (strict/production-leaning)
2. `supabase/schema_hackathon.sql` (lean/fast setup, recommended for hackathon demo)

Implemented:
1. `public.riders` with JSONB schema sections + strict key/type/range constraints.
2. Generated query columns: `primary_zone`, `rider_status`, `policy_active`, `risk_score`, `weekly_premium_paid`.
3. `public.claims` with:
   - `coverage_week_start`
   - lifecycle fields (`decision_reason`, `reviewed_at`, `paid_at`, `evidence_snapshot`)
4. Weekly uniqueness:
   - unique `(rider_id, disruption_type, coverage_week_start)`
5. `updated_at` trigger and RLS policies enabled.

Important DB constraint differences:
1. Strict schema (`schema.sql`):
   - `claims.amount > 0`
2. Hackathon schema (`schema_hackathon.sql`):
   - `claims.amount >= 0`
   - fewer deep JSON constraints for faster seeding and lower friction

### 2) ML risk/pricing engine (modular)
Facade file: `backend/ml/risk_model.py`
Modules: `backend/ml/risk_engine/`

Implemented:
1. Dual models + ensemble:
   - `RandomForestRiskPricingModel`
   - `MonotonicHGBRRiskPricingModel`
   - `EnsembleRiskPricingModel`
2. v0 and v1 synthetic data generators.
3. Comparison pipeline:
   - `train_and_compare_models(...)`
   - `run_comparison_suite(...)`
4. Premium APIs:
   - `calculate_weekly_premium(...)`
   - `calculate_weekly_premium_with_model(...)`
5. Added HGBR risk API for orchestration:
   - `predict_hgbr_risk(features_array)`

### 3) Step 2 backend orchestrator (FastAPI + deterministic LangGraph)
Root: `backend/orchestrator/`

Files:
1. `main.py`:
   - FastAPI app
   - `POST /evaluate_claim`
   - startup wiring for Supabase repo + compiled graph
2. `schemas.py`:
   - `DisruptionPayload`
   - `ClaimRequest`
   - `ClaimDecision`
3. `state.py`:
   - `ClaimState` TypedDict with required keys:
     - `rider_id`, `disruption`, `rider_db_data`, `is_parametric_valid`, `is_fraud`, `hgbr_event_risk`, `final_decision`
4. `config.py`:
   - thresholds + disruption type normalization map + env loader
5. `repository.py`:
   - Supabase REST read/write (`fetch_rider_by_id`, `insert_claim_decision`)
   - uses HTTP with `apikey` + `Authorization: Bearer <key>` headers
6. `utils.py`:
   - disruption normalization
   - Monday week-start helper
   - HGBr feature vector builder
   - API->DB claim status mapping
7. `nodes.py`:
   - `fetch_db_context`
   - `evaluate_parametric`
   - `fraud_check_llm` (deterministic mock)
   - `risk_evaluator` (calls `predict_hgbr_risk`)
   - `execute_decision` (decision + claim insert)
   - deterministic tool functions:
     - `evaluate_parametric_rules(...)`
     - `check_fraud_telemetry(...)`
8. `graph.py`:
   - deterministic flow:
     - `fetch_db_context -> evaluate_parametric -> fraud_check_llm -> risk_evaluator -> execute_decision`

## Endpoint Behavior (`POST /evaluate_claim`)
Input:
- `rider_id`
- `disruption` with `type`, `intensity_value`, `zone`

Decision logic:
1. Rider fetch from Supabase and policy_active gate.
2. Parametric validation:
   - zone matches primary zone
   - rider status is `ONLINE`
   - type-specific threshold met
3. Fraud check:
   - mock location enabled OR speed > 15 km/h
4. HGBR risk:
   - compute `hgbr_event_risk`
5. Final outcome:
   - parametric fail -> `DENIED`
   - fraud -> `FRAUD_FLAGGED`
   - risk > 0.95 -> `MANUAL_REVIEW`
   - else -> `APPROVED`, payout = `daily_performance.incentive_at_risk`

Returns:
```json
{ "claim_status": "...", "payout_amount": 0.0, "reason": "..." }
```

## Disruption Type Normalization
Supported aliases:
1. `heavy_rain`, `extreme_weather` -> `EXTREME_WEATHER`
2. `severe_pollution`, `pollution` -> `SEVERE_POLLUTION`
3. `local_strike`, `strike` -> `LOCAL_STRIKE`

Unknown type:
- immediately denied at state initialization (`Unsupported disruption type`)

## Claim Insert Details
`execute_decision` inserts into `public.claims` with:
1. generated `claim_id` (`CLM_<12 hex chars>`)
2. DB `status` mapping:
   - `APPROVED` -> `APPROVED`
   - `MANUAL_REVIEW` -> `PENDING`
   - `DENIED` / `FRAUD_FLAGGED` -> `REJECTED`
3. Monday `coverage_week_start`
4. `decision_reason`
5. `evidence_snapshot` JSON
6. `reviewed_at` set only when status is approved/rejected

Important:
- For compatibility with strict schema (`amount > 0`), inserted `amount` uses `max(incentive_at_risk, 0.01)` even for denied/manual paths.
- API payout remains `0.0` for denied/fraud/manual review.

## Dependencies / Runtime
File: `requirements.txt`

Added:
1. FastAPI stack
2. ML stack
3. LangGraph (`langgraph>=0.2.0,<0.3.0`)

Required env vars:
1. `SUPABASE_URL`
2. `SUPABASE_SECRET_KEY` (preferred for REST flow) or `SUPABASE_SERVICE_ROLE_KEY` (fallback)
3. `.env` is auto-loaded by orchestrator config via `python-dotenv`

## Run Commands
1. Install deps:
   - `pip install -r requirements.txt`
2. Start API:
   - `uvicorn backend.orchestrator.main:app --reload`
3. Open docs:
   - `http://127.0.0.1:8000/docs`

## Verification Notes
Local static checks completed:
1. `py_compile` passed for orchestrator + ML modules.
2. Existing ML CLI still works after changes.

Not executed in this environment:
1. LangGraph runtime import (package not installed in sandbox).
2. Live FastAPI + Supabase integration run.

## Next Recommended Steps
1. Run manual endpoint tests for:
   - approved
   - denied (parametric fail)
   - fraud flagged
   - manual review
2. Add unit tests for node functions and status mapping.
3. Add dedicated pricing endpoint using tuned HGBR for weekly premium quotes.

## Rule For Future Agents
Whenever code changes are made, update this `AGENTS.md` immediately so continuity remains exact.
