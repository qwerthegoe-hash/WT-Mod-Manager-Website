-- WT Mod Manager: live-reported privilege hardening, additive and reversible.
-- public.rls_auto_enable() is an event trigger callback, not a public API endpoint.
-- Keep the event-trigger behavior intact, but prevent HTTP roles from invoking it.
begin;
revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
commit;
