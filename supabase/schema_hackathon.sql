-- Lean hackathon schema for fast setup/testing.
-- Keeps compatibility with existing backend/orchestrator code.
-- Original strict schema is preserved in: supabase/schema.sql

create table if not exists public.riders (
    rider_id text primary key,
    profile jsonb not null,
    real_time_state jsonb not null,
    daily_performance jsonb not null,
    insurance_profile jsonb not null,
    fraud_telemetry jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint riders_profile_is_object check (jsonb_typeof(profile) = 'object'),
    constraint riders_real_time_state_is_object check (jsonb_typeof(real_time_state) = 'object'),
    constraint riders_daily_performance_is_object check (jsonb_typeof(daily_performance) = 'object'),
    constraint riders_insurance_profile_is_object check (jsonb_typeof(insurance_profile) = 'object'),
    constraint riders_fraud_telemetry_is_object check (jsonb_typeof(fraud_telemetry) = 'object')
);

create table if not exists public.claims (
    claim_id text primary key,
    rider_id text not null references public.riders(rider_id) on delete cascade,
    amount numeric(10, 2) not null check (amount >= 0),
    status text not null check (status in ('PENDING', 'APPROVED', 'REJECTED', 'PAID')),
    "timestamp" timestamptz not null default now(),
    coverage_week_start date not null,
    disruption_type text not null check (
        disruption_type in ('EXTREME_WEATHER', 'SEVERE_POLLUTION', 'LOCAL_STRIKE')
    ),
    decision_reason text,
    reviewed_at timestamptz,
    paid_at timestamptz,
    evidence_snapshot jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint claims_coverage_week_starts_on_monday check (
        coverage_week_start = date_trunc('week', coverage_week_start::timestamp)::date
    ),
    constraint claims_evidence_snapshot_object check (
        jsonb_typeof(evidence_snapshot) = 'object'
    ),
    constraint claims_one_per_week_per_disruption unique (rider_id, disruption_type, coverage_week_start)
);

create index if not exists idx_claims_rider_id on public.claims (rider_id);
create index if not exists idx_claims_status on public.claims (status);
create index if not exists idx_claims_coverage_week_start on public.claims (coverage_week_start);
create index if not exists idx_claims_timestamp on public.claims ("timestamp" desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_riders_set_updated_at on public.riders;
create trigger trg_riders_set_updated_at
before update on public.riders
for each row
execute function public.set_updated_at();

drop trigger if exists trg_claims_set_updated_at on public.claims;
create trigger trg_claims_set_updated_at
before update on public.claims
for each row
execute function public.set_updated_at();

-- Optional hardening for later:
-- alter table public.riders enable row level security;
-- alter table public.claims enable row level security;
