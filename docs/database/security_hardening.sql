-- WT Mod Manager safe, additive database permission hardening.
-- Review and run manually in Supabase SQL Editor after a database backup.
-- Does not remove functionality, roles, rows or existing policies.
-- Application policy checks remain in the existing *_upgrade.sql migrations.
begin;
-- Avoid SECURITY DEFINER function search-path hijacking via PUBLIC schema CREATE privileges.
revoke create on schema public from public;

-- Ensure existing sensitive tables cannot become unprotected after schema changes.
alter table if exists public.community_admins enable row level security;
alter table if exists public.community_messages enable row level security;
alter table if exists public.community_mutes enable row level security;
alter table if exists public.community_reports enable row level security;
alter table if exists public.community_user_profiles enable row level security;
alter table if exists public.community_media_jobs enable row level security;
alter table if exists public.wtmm_mods enable row level security;
alter table if exists public.guardian_settings enable row level security;
alter table if exists public.guardian_user_state enable row level security;
alter table if exists public.guardian_events enable row level security;
alter table if exists public.guardian_notices enable row level security;
commit;
