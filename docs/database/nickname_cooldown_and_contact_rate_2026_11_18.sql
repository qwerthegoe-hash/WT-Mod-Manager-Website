-- WTMM: nickname cooldown independent of client timezone, and private mail request throttling.
begin;
alter table public.community_user_profiles
  add column if not exists nickname_changed_at timestamptz;

-- Trigger is authoritative; callers cannot backdate/rewrite the cooldown.
create or replace function public.wtmm_protect_nickname_cooldown()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
  if TG_OP = 'INSERT' then
    new.nickname_changed_at := now();
    return new;
  end if;
  if btrim(new.nickname) is distinct from btrim(old.nickname) then
    if old.nickname_changed_at is not null
      and old.nickname_changed_at > now() - interval '7 days'
    then
      raise exception 'NICKNAME_COOLDOWN: next change at %',
        (old.nickname_changed_at + interval '7 days')
      using errcode = 'P0001';
    end if;
    new.nickname_changed_at := now();
  else
    new.nickname_changed_at := old.nickname_changed_at;
  end if;
  return new;
end;
$$;
revoke all on function public.wtmm_protect_nickname_cooldown() from public, anon, authenticated;

drop trigger if exists wtmm_nickname_cooldown on public.community_user_profiles;
create trigger wtmm_nickname_cooldown
before insert or update on public.community_user_profiles
for each row execute function public.wtmm_protect_nickname_cooldown();

-- Neither RLS nor the nickname trigger should be bypassed through table
-- maintenance privileges held by browser roles.
revoke truncate, references, trigger on public.community_user_profiles from anon, authenticated;

-- Minimal tracking: only verified Supabase account UUID and server timestamp,
-- never a message body, email, nickname or IP address.
create table if not exists public.wtmm_contact_attempts(
  id bigint generated always as identity primary key,
  user_id uuid not null,
  created_at timestamptz not null default now()
);
create index if not exists wtmm_contact_attempts_user_time_idx
  on public.wtmm_contact_attempts(user_id, created_at desc);
alter table public.wtmm_contact_attempts enable row level security;
revoke all on public.wtmm_contact_attempts from public, anon, authenticated;
grant select, insert, delete on public.wtmm_contact_attempts to service_role;
grant usage, select on sequence public.wtmm_contact_attempts_id_seq to service_role;

create or replace function public.wtmm_contact_limit_before_insert()
returns trigger language plpgsql security invoker set search_path = ''
as $$
declare last_at timestamptz;
declare hour_count integer;
declare day_count integer;
begin
  new.created_at := now();
  if new.user_id is null then
    raise exception 'Contact sender must be authenticated' using errcode='42501';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('wtmm-contact:' || new.user_id::text, 0));
  select max(created_at),
    count(*) filter (where created_at > now() - interval '1 hour'),
    count(*) filter (where created_at > now() - interval '24 hours')
  into last_at, hour_count, day_count
  from public.wtmm_contact_attempts where user_id = new.user_id
    and created_at > now() - interval '24 hours';
  if last_at > now() - interval '60 seconds'
    or hour_count >= 4 or day_count >= 15 then
    raise exception 'CONTACT_RATE_LIMIT' using errcode='P0001';
  end if;
  return new;
end;
$$;
revoke all on function public.wtmm_contact_limit_before_insert()
  from public, anon, authenticated;
drop trigger if exists wtmm_contact_limit on public.wtmm_contact_attempts;
create trigger wtmm_contact_limit
before insert on public.wtmm_contact_attempts
for each row execute function public.wtmm_contact_limit_before_insert();
commit;
