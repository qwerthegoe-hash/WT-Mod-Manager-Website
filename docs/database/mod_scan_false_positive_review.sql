-- WT Mod Scanner: distinguish invalid ZIPs from ambiguous but structurally
-- valid mod content. "review" is NEVER auto-published and is not a clean verdict.
alter table private.wtmm_mod_scan_queue
  drop constraint if exists wtmm_mod_scan_queue_state_check;
alter table private.wtmm_mod_scan_queue
  add constraint wtmm_mod_scan_queue_state_check
  check (state in ('queued','scanning','checked','review','blocked','error'));

create or replace function public.wtmm_scan_finish(
  p_id uuid,p_started_at timestamptz,p_state text,p_note text,
  p_sha256 text,p_file_count integer
) returns boolean language plpgsql security definer set search_path = ''
as $$
declare n integer;
begin
  if p_state not in ('checked','review','blocked','error') or
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
        then 'Архив нарушает требования безопасности: '||
             left(coalesce(p_note,'invalid archive'),120)
        else rejection_reason end
  where id=p_id and status='pending';
  return true;
end
$$;
revoke all on function public.wtmm_scan_finish(uuid,timestamptz,text,text,text,integer)
  from public,anon,authenticated;
grant execute on function public.wtmm_scan_finish(uuid,timestamptz,text,text,text,integer)
  to service_role;

-- Existing moderators must manually inspect ZIP structure and contents.
-- Only authenticated MFA admins may approve a "review" submission;
-- other statuses remain blocked until the structural scan finishes.
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
    then raise exception 'Scanner results are server managed'; end if;
  end if;
  if tg_op = 'UPDATE' and new.status='approved' and
      old.status is distinct from new.status then
    if old.scan_status='blocked' or (
      old.triage_status <> 'checked'
      and not (
        old.triage_status='review' and public.wtmm_is_admin()
      )
    ) then
      raise exception 'Archive requires completed scanning and authorized review';
    end if;
  end if;
  return new;
end
$$;
