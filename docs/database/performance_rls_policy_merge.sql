-- WT Mod Manager: equivalent RLS policy merging for fewer evaluations.
-- Verified against the deployed public schema on 2026-11-17.
-- Additive behavior: self + explicitly public profiles stay readable;
-- owners can edit pending/rejected mods, admins retain full moderation.
begin;
drop policy if exists "wtmm_profiles_read_optimized" on public.community_user_profiles;
create policy "wtmm_profiles_read_optimized" on public.community_user_profiles
for select to authenticated using (
  user_id = (select auth.uid()) OR is_public = true
);
drop policy if exists "community_profile_select_self" on public.community_user_profiles;
drop policy if exists "wtmm_profiles_public_read" on public.community_user_profiles;

drop policy if exists "wtmm_mods_update_optimized" on public.wtmm_mods;
create policy "wtmm_mods_update_optimized" on public.wtmm_mods
for update to authenticated
using (
  (owner_id = (select auth.uid()) and status in ('pending','rejected'))
  or (select public.wtmm_is_admin())
)
with check (
  (owner_id = (select auth.uid()) and status = 'pending'
   and reviewed_at is null and rejection_reason is null)
  or (select public.wtmm_is_admin())
);
drop policy if exists "wtmm_mods_owner_edit" on public.wtmm_mods;
drop policy if exists "wtmm_mods_admin_review" on public.wtmm_mods;
commit;
