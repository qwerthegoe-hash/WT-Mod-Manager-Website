-- Protect uploads even if an optional ClamAV worker flags malware later.
create or replace function private.wtmm_block_av_rejected_approval()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
  if new.status = 'approved'
     and old.status is distinct from new.status
     and old.scan_status = 'blocked' then
    raise exception 'Antivirus-blocked package cannot be approved';
  end if;
  return new;
end
$$;
drop trigger if exists wtmm_mod_av_approval_gate on public.wtmm_mods;
create trigger wtmm_mod_av_approval_gate
before update of status on public.wtmm_mods
for each row execute function private.wtmm_block_av_rejected_approval();

-- RLS does not protect TRUNCATE; do not allow normal web users to empty
-- the mod catalogue or create their own table triggers.
revoke truncate, trigger, references on public.wtmm_mods from anon, authenticated;
