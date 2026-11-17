-- WTMM: read-only inspection of the deployed mod scanning security chain.
-- Safe to run in Supabase SQL Editor before or after the scanning migration.
-- This script does not print records, credentials, UUIDs or individual mod paths.

select c.relname as table_name, c.relrowsecurity as rls_enabled
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relname = 'wtmm_mods';

select column_name, data_type, is_nullable
from information_schema.columns
where table_schema = 'public' and table_name = 'wtmm_mods'
  and column_name like 'scan_%'
order by column_name;

select t.tgname as trigger_name, pg_get_triggerdef(t.oid) as definition
from pg_trigger t
where t.tgrelid = to_regclass('public.wtmm_mods')
  and not t.tgisinternal
order by t.tgname;

select p.schemaname, p.tablename, p.policyname, p.roles, p.cmd
from pg_policies p
where (p.schemaname = 'public' and p.tablename = 'wtmm_mods')
  or (p.schemaname = 'storage' and p.tablename = 'objects'
      and p.policyname like 'wtmm_%')
order by p.schemaname, p.tablename, p.policyname;

select b.id, b.public as publicly_accessible,
       b.file_size_limit, b.allowed_mime_types
from storage.buckets b
where b.id in ('wtmm-mod-packages', 'wtmm-mod-previews')
order by b.id;
