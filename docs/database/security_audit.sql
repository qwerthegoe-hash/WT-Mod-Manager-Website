-- WT Mod Manager read-only security audit.
-- Run in Supabase SQL Editor and review results. No schema or data changes.
-- Important: the SQL files in this repository are not applied automatically.
select n.nspname as schema_name, c.relname as table_name, c.relrowsecurity as rls_enabled,
       c.relforcerowsecurity as force_rls
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where c.relkind in ('r','p') and n.nspname = 'public'
  and c.relname in (
    'community_admins','community_messages','community_mutes','community_reports',
    'community_user_profiles','community_media_jobs','wtmm_mods',
    'guardian_settings','guardian_user_state','guardian_events','guardian_notices'
  )
order by c.relname;

select schemaname, tablename, policyname, roles, cmd, qual, with_check
from pg_policies
where schemaname in ('public','storage')
  and (tablename in ('community_admins','community_messages','community_mutes',
    'community_reports','community_user_profiles','community_media_jobs','wtmm_mods',
    'guardian_settings','guardian_user_state','guardian_events','guardian_notices','objects'))
order by schemaname, tablename, policyname;

select id, public, file_size_limit, allowed_mime_types
from storage.buckets
where id in ('community-media','community-pending','community-avatars',
  'community-banners','wtmm-mod-packages','wtmm-mod-previews')
order by id;

select routine_schema, routine_name, security_type
from information_schema.routines
where routine_schema = 'public' and
 (routine_name like 'community_%' or routine_name like 'wtmm_%' or routine_name like 'guardian_%')
order by routine_name;
