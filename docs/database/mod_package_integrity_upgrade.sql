-- WT Mod Manager - prevent in-review ZIP/cover replacement and metadata tampering.
-- Apply MANUALLY in Supabase SQL Editor after community_platform_upgrade.sql.
-- Back up the database first. A GitHub push does NOT deploy SQL.
-- This is an additive protection; it preserves existing mods and current user workflows.
begin;

-- Moderators should review the same object that remains associated with a submission.
-- Prevent users (and administrative UI bugs) from changing the referenced package,
-- owner, identity or original submission timestamp after creation.
create or replace function public.wtmm_guard_mod_package_integrity()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    if new.id is distinct from old.id
       or new.owner_id is distinct from old.owner_id
       or new.created_at is distinct from old.created_at
       or new.file_path is distinct from old.file_path
       or new.cover_path is distinct from old.cover_path
    then
        raise exception 'Mod identity, package, cover and submission time are immutable; create a new submission instead.';
    end if;
    return new;
end;
$$;

revoke all on function public.wtmm_guard_mod_package_integrity()
from public, anon, authenticated;

drop trigger if exists wtmm_mod_package_integrity on public.wtmm_mods;
create trigger wtmm_mod_package_integrity
before update on public.wtmm_mods
for each row execute function public.wtmm_guard_mod_package_integrity();

-- Prevent a pending file from being deleted and replaced after human review.
-- The existing UI deletes the submission record BEFORE removing its files.
-- Rejected/orphaned files remain removable by their owner.
drop policy if exists "wtmm_packages_remove" on storage.objects;
create policy "wtmm_packages_remove"
on storage.objects for delete to authenticated
using (
    bucket_id = 'wtmm-mod-packages'
    and (storage.foldername(name))[1] = (select auth.uid())::text
    and not exists (
        select 1 from public.wtmm_mods m
        where m.file_path = name
          and m.status in ('pending','approved')
    )
);

drop policy if exists "wtmm_previews_remove" on storage.objects;
create policy "wtmm_previews_remove"
on storage.objects for delete to authenticated
using (
    bucket_id = 'wtmm-mod-previews'
    and (storage.foldername(name))[1] = (select auth.uid())::text
    and not exists (
        select 1 from public.wtmm_mods m
        where m.cover_path = name
          and m.status in ('pending','approved')
    )
);
commit;
