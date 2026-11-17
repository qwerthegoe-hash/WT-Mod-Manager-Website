-- Read-only production readiness checks for the global mod search RPC.
select
  has_function_privilege('authenticated',
    'public.wtmm_search_mods(text,text,text,text,text,integer,integer)', 'EXECUTE')
    as authenticated_can_search,
  has_function_privilege('anon',
    'public.wtmm_search_mods(text,text,text,text,text,integer,integer)', 'EXECUTE')
    as unauthenticated_cannot_search_expected_false,
  (select prosecdef from pg_proc where oid =
    'public.wtmm_search_mods(text,text,text,text,text,integer,integer)'::regprocedure)
    as is_security_definer_expected_false,
  (select relrowsecurity from pg_class where oid = 'public.wtmm_mods'::regclass)
    as mods_rls_enabled,
  (select count(*) from public.wtmm_search_mods(p_view => 'invalid'))
    as invalid_view_result_count_expected_zero;
