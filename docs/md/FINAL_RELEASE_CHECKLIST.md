# WT Mod Manager — final hardening / release checklist

## Confirmed in the connected Supabase project

- The existing ZIP package immutability trigger and storage policies remain present.
- The new RLS-preserving global search RPC has been deployed through an additive
  migration; users can now search database-wide across the allowed view.
- A role-limited SQL check verified authenticated EXECUTE, not anon EXECUTE,
  a rejected invalid view, and a synthetic non-admin user sees no private/admin mods.
- The Community image Edge Function is deployed and marked ACTIVE.
- SQL source and GitHub commits alone do not prove actual real-browser operation.

## Actions still blocked by missing external permissions or local access

1. **Activate real ZIP malware scanning:** requires the repository owner's
   encrypted GitHub Actions secrets and a successful manual ClamAV run. Only
   then apply `mod_malware_scanning_upgrade.sql` after a database backup, verify
   new approvals fail closed without a clean scan, and enable the scheduled worker.
   **The scan gate is currently NOT deployed.**
2. **Windows one-minute console:** execute
   `tools/windows-sync/setup-windows-sync.ps1 -Mode Disable` locally on the
   user's Windows computer. GitHub cannot change an existing scheduled task
   on a different PC, nor solve its untracked `README.md` conflict remotely.
   The optional `InstallSafe` mode makes a hidden logon-triggered task.
3. **Supabase Auth leaked password protection:** review the Auth dashboard.
   This is not configured by SQL and no tool to modify project Auth settings
   is exposed in the current connection.
4. **Full interactive QA:** test under normal user, anonymous user and admin
   accounts, including the chat, support submission, uploaded media, profiles,
   mod download/approval and author search on a populated dataset. GitHub
   static/syntax/regression tests do not substitute for those interactions.

## Feature integrity

All original sections and navigation remain. The global search RPC has a
legacy listing fallback if a different Supabase project lacks the migration.
Search/access filtering is done by a SECURITY INVOKER function and existing
RLS policies, not by client-provided admin claims.

Operational security is a continuous process. Avoid claiming that any
version is unhackable, or that an unconfigured malware scanner is active.
