-- WTMM security suite: server-side abuse protection for report and mod submissions.
-- Bounded per-account submission rates, regardless of browser JS.
-- Separate from existing WT Guardian chat flood checks.
-- Safe additive migration. No existing rows are deleted.
begin;

create index if not exists wtmm_reports_reporter_recent_idx
  on public.community_reports (reporter_id, created_at desc);
create index if not exists wtmm_mods_owner_recent_idx
  on public.wtmm_mods (owner_id, created_at desc);

create or replace function public.wtmm_throttle_submissions()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  actor uuid := auth.uid();
  recent_count integer;
  day_count integer;
  group_name text;
  actor_id uuid;
  hour_limit integer;
  day_limit integer;
begin
  -- Service-role maintenance/imports are not treated as user submissions.
  if current_user = 'service_role' then
    return new;
  end if;
  if tg_table_name = 'community_reports' then
    group_name := 'reports';
    actor_id := new.reporter_id;
    hour_limit := 10;
    day_limit := 40;
  elsif tg_table_name = 'wtmm_mods' then
    group_name := 'mods';
    actor_id := new.owner_id;
    hour_limit := 8;
    day_limit := 30;
  else
    raise exception 'Unsupported submission type' using errcode='22023';
  end if;

  if actor is null or actor_id is distinct from actor then
    raise exception 'Submitted user does not match authenticated user' using errcode='42501';
  end if;

  -- Prevent clients from bypassing the rolling window with a backdated timestamp.
  new.created_at := now();

  -- Serialize submissions per user to avoid parallel-request races.
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('wtmm-rate:' || group_name || ':' || actor::text, 0)
  );

  if group_name = 'reports' then
    select count(*) into recent_count from public.community_reports
      where reporter_id = actor and created_at >= now() - interval '1 hour';
    select count(*) into day_count from public.community_reports
      where reporter_id = actor and created_at >= now() - interval '24 hours';
  else
    select count(*) into recent_count from public.wtmm_mods
      where owner_id = actor and created_at >= now() - interval '1 hour';
    select count(*) into day_count from public.wtmm_mods
      where owner_id = actor and created_at >= now() - interval '24 hours';
  end if;
  if recent_count >= hour_limit or day_count >= day_limit then
    raise exception 'Submission rate limit reached, please retry later'
      using errcode='P0001';
  end if;
  return new;
end;
$$;

revoke all on function public.wtmm_throttle_submissions()
  from public, anon, authenticated;

drop trigger if exists wtmm_report_submission_rate on public.community_reports;
create trigger wtmm_report_submission_rate
before insert on public.community_reports
for each row execute function public.wtmm_throttle_submissions();

drop trigger if exists wtmm_mod_submission_rate on public.wtmm_mods;
create trigger wtmm_mod_submission_rate
before insert on public.wtmm_mods
for each row execute function public.wtmm_throttle_submissions();

commit;
