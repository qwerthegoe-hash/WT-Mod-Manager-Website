-- WTMM optional TOTP enforcement. A verified factor upgrades the protection of
-- account writes and administrator access, without forcing MFA on accounts
-- which have not enrolled. Uses Supabase-signed JWT AAL, never user_metadata.
begin;

create schema if not exists wtmm_security;
revoke all on schema wtmm_security from public, anon;
grant usage on schema wtmm_security to authenticated;

-- Auth factor table is private; read only a boolean about auth.uid(), never
-- reveal factor identifiers or secrets to public API callers.
create or replace function wtmm_security.mfa_satisfied()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select auth.uid() is not null and (
    not exists(
      select 1 from auth.mfa_factors f
      where f.user_id = auth.uid() and f.status = 'verified'
    )
    or coalesce(auth.jwt()->>'aal', 'aal1') = 'aal2'
  );
$$;
revoke all on function wtmm_security.mfa_satisfied() from public, anon;
grant execute on function wtmm_security.mfa_satisfied() to authenticated;

-- The existing administrator identity check is retained, with an additional
-- AAL2 requirement only if that account has opted into verified TOTP.
create or replace function public.community_is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.community_admins a where a.user_id = auth.uid()
  ) and wtmm_security.mfa_satisfied();
$$;

create or replace function public.wtmm_is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.community_admins a where a.user_id = auth.uid()
  ) and wtmm_security.mfa_satisfied();
$$;

-- Restrictive policies are ANDed with existing owner/admin policies.
-- A user with no enrolled factor still passes. An MFA-enrolled user cannot
-- make sensitive writes with only an AAL1 token.
drop policy if exists wtmm_mfa_profile_insert on public.community_user_profiles;
create policy wtmm_mfa_profile_insert on public.community_user_profiles
  as restrictive for insert to authenticated
  with check ((select wtmm_security.mfa_satisfied()));

drop policy if exists wtmm_mfa_profile_update on public.community_user_profiles;
create policy wtmm_mfa_profile_update on public.community_user_profiles
  as restrictive for update to authenticated
  using ((select wtmm_security.mfa_satisfied()))
  with check ((select wtmm_security.mfa_satisfied()));

drop policy if exists wtmm_mfa_report_insert on public.community_reports;
create policy wtmm_mfa_report_insert on public.community_reports
  as restrictive for insert to authenticated
  with check ((select wtmm_security.mfa_satisfied()));

drop policy if exists wtmm_mfa_mod_insert on public.wtmm_mods;
create policy wtmm_mfa_mod_insert on public.wtmm_mods
  as restrictive for insert to authenticated
  with check ((select wtmm_security.mfa_satisfied()));

drop policy if exists wtmm_mfa_mod_update on public.wtmm_mods;
create policy wtmm_mfa_mod_update on public.wtmm_mods
  as restrictive for update to authenticated
  using ((select wtmm_security.mfa_satisfied()))
  with check ((select wtmm_security.mfa_satisfied()));

drop policy if exists wtmm_mfa_mod_delete on public.wtmm_mods;
create policy wtmm_mfa_mod_delete on public.wtmm_mods
  as restrictive for delete to authenticated
  using ((select wtmm_security.mfa_satisfied()));

commit;
