-- Sequential structural ZIP triage for the existing WTMM mod catalogue.
-- Fail closed: no auto-publish; administrator must still review the submission.
create schema if not exists private;
revoke all on schema private from public, anon, authenticated;
grant usage on schema private to service_role;

alter table public.wtmm_mods
  add column if not exists triage_status text not null default 'queued',
  add column if not exists triage_note text,
  add column if not exists triage_sha256 text,
  add column if not exists triage_files integer,
  add column if not exists triage_started_at timestamptz,
  add column if not exists triage_completed_at timestamptz,
  add column if not exists scan_status text not null default 'pending',
  add column if not exists scan_attempts integer not null default 0,
  add column if not exists scan_started_at timestamptz,
  add column if not exists scan_completed_at timestamptz,
  add column if not exists scan_sha256 text,
  add column if not exists scan_note text;

create table if not exists private.wtmm_mod_scan_queue (
  mod_id uuid primary key references public.wtmm_mods(id) on delete cascade,
  file_path text not null,
  state text not null default 'queued' check (state in ('queued','scanning','checked','blocked','error')),
  submitted_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz,
  attempts integer not null default 0 check (attempts >= 0),
  note text
);
create index if not exists wtmm_mod_scan_queue_fifo_idx
  on private.wtmm_mod_scan_queue(state,submitted_at,mod_id);
alter table private.wtmm_mod_scan_queue enable row level security;
revoke all on private.wtmm_mod_scan_queue from public, anon, authenticated;
grant select,insert,update,delete on private.wtmm_mod_scan_queue to service_role;
grant select,update on public.wtmm_mods to service_role;

-- Reject spoofed scan results by users, including upload INSERT attempts.
create or replace function private.wtmm_scan_submission_guard()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
  if tg_op = 'INSERT' then
    new.triage_status := 'queued';
    new.triage_note := null;
    new.triage_sha256 := null;
    new.triage_files := null;
    new.triage_started_at := null;
    new.triage_completed_at := null;
    new.scan_status := 'pending';
    new.scan_attempts := 0;
    new.scan_sha256 := null;
    new.scan_started_at := null;
    new.scan_completed_at := null;
    new.scan_note := null;
  elsif current_user not in ('postgres','service_role') then
    if (new.triage_status, new.triage_note, new.triage_sha256,
        new.triage_files, new.triage_started_at, new.triage_completed_at,
        new.scan_status, new.scan_attempts, new.scan_started_at,
        new.scan_completed_at, new.scan_sha256, new.scan_note)
       is distinct from
       (old.triage_status, old.triage_note, old.triage_sha256,
        old.triage_files, old.triage_started_at, old.triage_completed_at,
        old.scan_status, old.scan_attempts, old.scan_started_at,
        old.scan_completed_at, old.scan_sha256, old.scan_note)
    then
      raise exception 'Scanner results are server managed';
    end if;
  end if;
  if tg_op = 'UPDATE' and new.status = 'approved' and
     old.status is distinct from new.status and old.triage_status <> 'checked'
  then
    raise exception 'Mod must pass server ZIP triage before approval';
  end if;
  return new;
end
$$;

drop trigger if exists wtmm_scan_submission_guard on public.wtmm_mods;
create trigger wtmm_scan_submission_guard
before insert or update on public.wtmm_mods
for each row execute function private.wtmm_scan_submission_guard();

create or replace function private.wtmm_queue_submitted_mod()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  insert into private.wtmm_mod_scan_queue(mod_id,file_path,submitted_at)
  values(new.id,new.file_path,new.created_at)
  on conflict (mod_id) do nothing;
  return new;
end
$$;
revoke all on function private.wtmm_queue_submitted_mod() from public,anon,authenticated;
drop trigger if exists wtmm_mod_scan_enqueue on public.wtmm_mods;
create trigger wtmm_mod_scan_enqueue after insert on public.wtmm_mods
for each row execute function private.wtmm_queue_submitted_mod();

insert into private.wtmm_mod_scan_queue(mod_id,file_path,submitted_at)
select id,file_path,created_at from public.wtmm_mods
where status='pending' and triage_status='queued'
on conflict (mod_id) do nothing;

-- Lock the entire queue for one worker at a time. Calls are serialized even
-- if two cron deliveries arrive in the same second.
create or replace function public.wtmm_scan_claim()
returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
  job record;
  claimed timestamptz;
begin
  perform pg_catalog.pg_advisory_xact_lock(712,20261119);
  if exists (
    select 1 from private.wtmm_mod_scan_queue q
    join public.wtmm_mods m on m.id=q.mod_id
    where q.state='scanning' and m.status='pending'
      and q.started_at > pg_catalog.now()-interval '4 minutes'
  ) then return null; end if;

  select q.mod_id,q.file_path,q.attempts into job
    from private.wtmm_mod_scan_queue q
    join public.wtmm_mods m on m.id=q.mod_id
   where m.status='pending' and q.attempts<3
     and (q.state='queued' or
          (q.state='error' and q.finished_at < pg_catalog.now()-interval '1 minute') or
          (q.state='scanning' and q.started_at < pg_catalog.now()-interval '4 minutes'))
   order by q.submitted_at asc,q.mod_id asc
   limit 1 for update of q skip locked;
  if not found then return null; end if;
  claimed:=pg_catalog.clock_timestamp();
  update private.wtmm_mod_scan_queue
    set state='scanning',attempts=attempts+1,started_at=claimed,
        finished_at=null,note=null
    where mod_id=job.mod_id;
  update public.wtmm_mods
    set triage_status='scanning',triage_started_at=claimed,
        triage_completed_at=null,triage_note=null
    where id=job.mod_id and status='pending';
  return pg_catalog.jsonb_build_object('id',job.mod_id,
    'file_path',job.file_path,'started_at',claimed);
end
$$;
revoke all on function public.wtmm_scan_claim() from public,anon,authenticated;
grant execute on function public.wtmm_scan_claim() to service_role;

create or replace function public.wtmm_scan_finish(
  p_id uuid,p_started_at timestamptz,p_state text,p_note text,
  p_sha256 text,p_file_count integer
) returns boolean language plpgsql security definer set search_path = ''
as $$
declare
  n integer;
begin
  if p_state not in ('checked','blocked','error') or
     (p_sha256 is not null and p_sha256 !~ '^[a-f0-9]{64}$') or
     (p_file_count is not null and (p_file_count<0 or p_file_count>250))
  then raise exception 'Invalid scanner completion'; end if;
  update private.wtmm_mod_scan_queue
    set state=p_state,finished_at=pg_catalog.clock_timestamp(),note=left(p_note,180)
    where mod_id=p_id and state='scanning' and started_at=p_started_at;
  get diagnostics n=row_count;
  if n=0 then return false; end if;
  update public.wtmm_mods set
      triage_status=p_state,
      triage_note=left(p_note,180),
      triage_sha256=p_sha256,
      triage_files=p_file_count,
      triage_completed_at=pg_catalog.clock_timestamp(),
      status=case when p_state='blocked' then 'rejected' else status end,
      rejection_reason=case when p_state='blocked'
        then 'Автоматический фильтр отклонил ZIP: '||left(coalesce(p_note,'invalid archive'),120)
        else rejection_reason end
  where id=p_id and status='pending';
  return true;
end
$$;
revoke all on function public.wtmm_scan_finish(uuid,timestamptz,text,text,text,integer)
  from public,anon,authenticated;
grant execute on function public.wtmm_scan_finish(uuid,timestamptz,text,text,text,integer)
  to service_role;

create or replace function public.wtmm_scan_authorized(p_token text)
returns boolean language sql stable security definer set search_path = ''
as $$
  select coalesce((
    select p_token = decrypted_secret
    from vault.decrypted_secrets where name='wtmm_scan_cron_token'
    limit 1
  ),false)
$$;
revoke all on function public.wtmm_scan_authorized(text)
  from public,anon,authenticated;
grant execute on function public.wtmm_scan_authorized(text) to service_role;
