-- Supabase/PostgreSQL schema for AI Parametric Insurance for Gig Workers.
-- Coverage is strictly loss-of-income from external disruptions only.

create table if not exists public.riders (
    rider_id text primary key,
    profile jsonb not null,
    real_time_state jsonb not null,
    daily_performance jsonb not null,
    insurance_profile jsonb not null,
    fraud_telemetry jsonb not null,
    primary_zone text generated always as (profile ->> 'primary_zone') stored,
    rider_status text generated always as (real_time_state ->> 'status') stored,
    policy_active boolean generated always as ((insurance_profile ->> 'policy_active')::boolean) stored,
    risk_score numeric(4, 3) generated always as ((insurance_profile ->> 'risk_score')::numeric) stored,
    weekly_premium_paid numeric(10, 2) generated always as ((insurance_profile ->> 'weekly_premium_paid')::numeric) stored,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint riders_profile_is_object check (jsonb_typeof(profile) = 'object'),
    constraint riders_real_time_state_is_object check (jsonb_typeof(real_time_state) = 'object'),
    constraint riders_daily_performance_is_object check (jsonb_typeof(daily_performance) = 'object'),
    constraint riders_insurance_profile_is_object check (jsonb_typeof(insurance_profile) = 'object'),
    constraint riders_fraud_telemetry_is_object check (jsonb_typeof(fraud_telemetry) = 'object'),
    constraint riders_profile_required_keys check (
        profile ?& array['name', 'phone', 'vehicle_type', 'primary_zone']
    ),
    constraint riders_real_time_state_required_keys check (
        real_time_state ?& array['status', 'current_location', 'last_ping_timestamp']
    ),
    constraint riders_daily_performance_required_keys check (
        daily_performance ?& array['orders_completed_today', 'daily_target', 'incentive_at_risk', 'earnings_today']
    ),
    constraint riders_insurance_profile_required_keys check (
        insurance_profile ?& array['policy_active', 'weekly_premium_paid', 'risk_score']
    ),
    constraint riders_fraud_telemetry_required_keys check (
        fraud_telemetry ?& array['current_speed_kmph', 'is_mock_location_enabled', 'battery_level']
    ),
    constraint riders_profile_types check (
        jsonb_typeof(profile -> 'name') = 'string'
        and jsonb_typeof(profile -> 'phone') = 'string'
        and jsonb_typeof(profile -> 'vehicle_type') = 'string'
        and jsonb_typeof(profile -> 'primary_zone') = 'string'
    ),
    constraint riders_real_time_state_types check (
        jsonb_typeof(real_time_state -> 'status') = 'string'
        and jsonb_typeof(real_time_state -> 'current_location') = 'object'
        and jsonb_typeof(real_time_state #> '{current_location,lat}') = 'number'
        and jsonb_typeof(real_time_state #> '{current_location,lon}') = 'number'
        and jsonb_typeof(real_time_state -> 'last_ping_timestamp') = 'string'
    ),
    constraint riders_daily_performance_types check (
        jsonb_typeof(daily_performance -> 'orders_completed_today') = 'number'
        and jsonb_typeof(daily_performance -> 'daily_target') = 'number'
        and jsonb_typeof(daily_performance -> 'incentive_at_risk') = 'number'
        and jsonb_typeof(daily_performance -> 'earnings_today') = 'number'
    ),
    constraint riders_insurance_profile_types check (
        jsonb_typeof(insurance_profile -> 'policy_active') = 'boolean'
        and jsonb_typeof(insurance_profile -> 'weekly_premium_paid') = 'number'
        and jsonb_typeof(insurance_profile -> 'risk_score') = 'number'
    ),
    constraint riders_fraud_telemetry_types check (
        jsonb_typeof(fraud_telemetry -> 'current_speed_kmph') = 'number'
        and jsonb_typeof(fraud_telemetry -> 'is_mock_location_enabled') = 'boolean'
        and jsonb_typeof(fraud_telemetry -> 'battery_level') = 'number'
    ),
    constraint riders_real_time_location_bounds check (
        ((real_time_state #>> '{current_location,lat}')::numeric between -90 and 90)
        and ((real_time_state #>> '{current_location,lon}')::numeric between -180 and 180)
    ),
    constraint riders_daily_performance_non_negative check (
        (daily_performance ->> 'orders_completed_today')::numeric >= 0
        and (daily_performance ->> 'daily_target')::numeric >= 0
        and (daily_performance ->> 'incentive_at_risk')::numeric >= 0
        and (daily_performance ->> 'earnings_today')::numeric >= 0
    ),
    constraint riders_fraud_telemetry_bounds check (
        (fraud_telemetry ->> 'current_speed_kmph')::numeric >= 0
        and (fraud_telemetry ->> 'battery_level')::numeric between 0 and 100
    ),
    constraint riders_risk_score_range check (
        (insurance_profile ->> 'risk_score')::numeric between 0 and 1
    ),
    constraint riders_weekly_premium_positive check (
        (insurance_profile ->> 'weekly_premium_paid')::numeric >= 0
    )
);

create index if not exists idx_riders_primary_zone on public.riders (primary_zone);
create index if not exists idx_riders_policy_active_true on public.riders (policy_active) where policy_active is true;
create index if not exists idx_riders_rider_status on public.riders (rider_status);
create index if not exists idx_riders_risk_score on public.riders (risk_score);
create index if not exists idx_riders_real_time_state_gin on public.riders using gin (real_time_state);

create table if not exists public.claims (
    claim_id text primary key,
    rider_id text not null references public.riders(rider_id) on delete cascade,
    amount numeric(10, 2) not null check (amount > 0),
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
    constraint claims_reviewed_timestamp_consistency check (
        (
            status in ('APPROVED', 'REJECTED', 'PAID')
            and reviewed_at is not null
        )
        or (
            status = 'PENDING'
            and reviewed_at is null
        )
    ),
    constraint claims_paid_timestamp_consistency check (
        (
            status = 'PAID'
            and paid_at is not null
        )
        or (
            status <> 'PAID'
            and paid_at is null
        )
    ),
    constraint claims_one_per_week_per_disruption unique (rider_id, disruption_type, coverage_week_start)
);

create index if not exists idx_claims_rider_id on public.claims (rider_id);
create index if not exists idx_claims_status on public.claims (status);
create index if not exists idx_claims_timestamp on public.claims ("timestamp" desc);
create index if not exists idx_claims_coverage_week_start on public.claims (coverage_week_start);
create index if not exists idx_claims_pending_by_time on public.claims ("timestamp" desc) where status = 'PENDING';

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

alter table public.riders enable row level security;
alter table public.claims enable row level security;

drop policy if exists riders_select_authenticated on public.riders;
create policy riders_select_authenticated
on public.riders
for select
to authenticated
using (true);

drop policy if exists riders_insert_authenticated on public.riders;
create policy riders_insert_authenticated
on public.riders
for insert
to authenticated
with check (true);

drop policy if exists riders_update_authenticated on public.riders;
create policy riders_update_authenticated
on public.riders
for update
to authenticated
using (true)
with check (true);

drop policy if exists claims_select_authenticated on public.claims;
create policy claims_select_authenticated
on public.claims
for select
to authenticated
using (true);

drop policy if exists claims_insert_authenticated on public.claims;
create policy claims_insert_authenticated
on public.claims
for insert
to authenticated
with check (true);

drop policy if exists claims_update_authenticated on public.claims;
create policy claims_update_authenticated
on public.claims
for update
to authenticated
using (true)
with check (true);
