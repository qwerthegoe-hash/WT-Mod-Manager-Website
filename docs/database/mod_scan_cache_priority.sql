-- Bounded SHA-256 structural scan cache, server-only, and age-aware queue.
-- Cached "checked" / "review" is NOT an antivirus verdict or publication approval.
create table if not exists private.wtmm_scan_cache (
  sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  engine_version text not null check (length(engine_version) between 8 and 60),
  verdict text not null check (verdict in ('checked','review')),
  file_count integer not null check (file_count between 1 and 250),
  note text not null,
  created_at timestamptz not null default now(),
  primary key(sha256,engine_version)
);
alter table private.wtmm_scan_cache enable row level security;
revoke all on private.wtmm_scan_cache from public,anon,authenticated;
grant select,insert,update,delete on private.wtmm_scan_cache to service_role;

alter table private.wtmm_mod_scan_queue
  add column if not exists priority smallint not null default 0;
alter table private.wtmm_mod_scan_queue
  drop constraint if exists wtmm_mod_scan_queue_priority_check;
alter table private.wtmm_mod_scan_queue
  add constraint wtmm_mod_scan_queue_priority_check
  check(priority between 0 and 2);
-- Users cannot set priority; queue is private and only the server can write.

create or replace function public.wtmm_scan_cache_get(
  p_sha256 text,p_engine_version text
) returns jsonb language sql stable security definer set search_path=''
as $$
  select pg_catalog.jsonb_build_object(
    'verdict',c.verdict,'files',c.file_count,'note',c.note
  )
  from private.wtmm_scan_cache c
  where p_sha256 ~ '^[0-9a-f]{64}$'
    and length(p_engine_version) between 8 and 60
    and c.sha256=p_sha256
    and c.engine_version=p_engine_version
    and c.created_at > pg_catalog.now()-interval '30 days'
  limit 1;
$$;
revoke all on function public.wtmm_scan_cache_get(text,text)
  from public,anon,authenticated;
grant execute on function public.wtmm_scan_cache_get(text,text) to service_role;

create or replace function public.wtmm_scan_cache_put(
  p_sha256 text,p_engine_version text,p_verdict text,
  p_files integer,p_note text
) returns boolean language plpgsql security definer set search_path=''
as $$
begin
  if p_sha256 !~ '^[0-9a-f]{64}$'
     or length(p_engine_version) not between 8 and 60
     or p_verdict not in ('checked','review')
     or p_files not between 1 and 250
     or p_note is null
  then
    return false;
  end if;
  insert into private.wtmm_scan_cache(
    sha256,engine_version,verdict,file_count,note,created_at
  ) values(
    p_sha256,p_engine_version,p_verdict,p_files,left(p_note,180),pg_catalog.now()
  )
  on conflict(sha256,engine_version) do update
  set verdict=excluded.verdict,file_count=excluded.file_count,
      note=excluded.note,created_at=excluded.created_at;
  return true;
end
$$;
revoke all on function public.wtmm_scan_cache_put(text,text,text,integer,text)
  from public,anon,authenticated;
grant execute on function public.wtmm_scan_cache_put(text,text,text,integer,text) to service_role;

create or replace function public.wtmm_scan_claim()
returns jsonb language plpgsql security definer set search_path=''
as $$
declare job record; claimed timestamptz;
begin
  perform pg_catalog.pg_advisory_xact_lock(712,20261119);
  if exists(
    select 1 from private.wtmm_mod_scan_queue q
    join public.wtmm_mods m on m.id=q.mod_id
    where q.state='scanning' and m.status='pending'
      and q.started_at>pg_catalog.now()-interval '4 minutes'
  ) then return null; end if;

  select q.mod_id,q.file_path,q.attempts into job
  from private.wtmm_mod_scan_queue q
  join public.wtmm_mods m on m.id=q.mod_id
  where m.status='pending' and q.attempts<3
    and (
      q.state='queued'
      or (q.state='error' and q.finished_at <
          pg_catalog.now()-make_interval(mins=>2 * greatest(q.attempts,1)))
      or (q.state='scanning' and q.started_at <
          pg_catalog.now()-interval '4 minutes')
    )
  -- Age bonus ensures fresh high-priority items cannot starve older uploads.
  order by (q.priority + floor(extract(epoch from (
    pg_catalog.now()-q.submitted_at))/1800)) desc,
    q.submitted_at asc,q.mod_id asc
  limit 1 for update of q skip locked;
  if not found then return null; end if;
  claimed:=pg_catalog.clock_timestamp();
  update private.wtmm_mod_scan_queue
    set state='scanning',attempts=attempts+1,started_at=claimed,
        finished_at=null,note=null where mod_id=job.mod_id;
  update public.wtmm_mods
    set triage_status='scanning',triage_started_at=claimed,
        triage_completed_at=null,triage_note=null
    where id=job.mod_id and status='pending';
  return pg_catalog.jsonb_build_object(
    'id',job.mod_id,'file_path',job.file_path,'started_at',claimed
  );
end
$$;
revoke all on function public.wtmm_scan_claim() from public,anon,authenticated;
grant execute on function public.wtmm_scan_claim() to service_role;
