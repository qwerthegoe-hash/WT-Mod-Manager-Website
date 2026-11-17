-- WTMM security suite: read-only production audit. Returns only security metadata.
-- No user identifiers, messages, email, passwords or private storage objects.
select
  current_setting('server_version') as postgres_version,
  (select count(*) from pg_policies
    where schemaname='public'
      and policyname like 'wtmm_mfa_%'
      and permissive='RESTRICTIVE') as mfa_restrictive_policy_count,
  (select count(*) from pg_trigger where not tgisinternal
    and tgname in ('wtmm_report_submission_rate','wtmm_mod_submission_rate')) as active_abuse_triggers,
  (select has_function_privilege('authenticated','wtmm_security.mfa_satisfied()','EXECUTE')) as mfa_check_authenticated,
  (select has_function_privilege('anon','wtmm_security.mfa_satisfied()','EXECUTE')) as mfa_check_anon,
  (select count(*) from auth.mfa_factors where status='verified') as verified_mfa_factors,
  (select count(*) from information_schema.columns
    where table_schema='public' and table_name='wtmm_mods'
      and column_name='scan_status') as scan_status_columns,
  (select count(*) from pg_trigger
    where tgname='wtmm_enforce_mod_scan' and not tgisinternal) as malware_gate_triggers,
  (select has_table_privilege('authenticated','public.community_messages','INSERT')) as direct_chat_insert_allowed,
  (select count(*) from pg_class c
     join pg_namespace n on n.oid=c.relnamespace
     where n.nspname='public' and c.relkind in ('r','p')
       and not c.relrowsecurity) as public_tables_missing_rls;
