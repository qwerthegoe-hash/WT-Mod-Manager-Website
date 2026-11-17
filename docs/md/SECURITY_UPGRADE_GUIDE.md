# WT Mod Manager — security, performance and release checklist

## Implemented in source code

1. **XSS hardening:** CSP meta tags on the six public pages. No inline JavaScript; allowlisted scripts, forms, network destinations, and no object embeds. Supabase network and image origins now point to the configured project only; if you migrate to another Supabase project, update the six CSP policies together with community-config.js. GitHub Pages is a static host: CSP via meta cannot set frame-ancestors, HSTS, or response headers. Use a header-capable host or reverse proxy for those protections.
2. **Supabase and accounts:** existing server RLS policies are retained, and a read-only SQL audit is provided. Login no longer permits duplicate requests, and the password input is cleared on success. Supabase project settings (email confirmation, login rate limits, MFA, Auth providers) must be configured in the Supabase dashboard separately.
3. **ZIP uploads:** new browser-side central-directory validator rejects obvious traversal paths, symlinks, encryption, unsupported compression, excessive decompression ratios and invalid ZIP structures. Moderator-only structural check added. These are basic safety checks, NOT malware scans. Server-side archive inspection and malware scanning must be added before treating user-submitted ZIPs as trusted.
4. **Performance:** timeouts on support and site configuration fetches; expiration-aware caching of Supabase cover previews; lazy and asynchronous thumbnail decoding. No features have been removed, and existing artwork stays unchanged.
5. **Rate limiting:** existing WT Guardian server-side protections and the mod submission queue limits are preserved. Client-only throttling must never be considered a permission boundary.
6. **Modular architecture:** upload validator, local diagnostics and profile watchdog live in separate small modules. Existing pages, public URLs and functions are retained.
7. **Automated testing:** GitHub Actions runs dependency-free JavaScript syntax/JSON checks, local links, CSP rules, ZIP regression cases, mod review approval-gate unit checks and Deno Edge Function type-checks.
8. **Diagnostics:** WTDiagnostics.summary() exposes in-memory *generic* error categories only (no logs uploaded, no tokens, no request URLs). Reloading the page clears this information.
9. **Dependency control:** browser and Edge Function Supabase SDK pinned to the verified 2.119.0 release; Dependabot keeps GitHub Actions up to date. Re-pin the SDK after testing security updates.
10. **Secret hygiene:** .gitignore excludes common credential files; do not store service-role or admin secrets in public files. Supabase public/publishable keys are designed for browser use but RLS must protect all data.

## Database: manual steps (NOT deployed)

1. Back up the Supabase database using your usual administrative process.
2. Review the existing schemas and RLS migrations in docs/database/, particularly community_platform_upgrade.sql, profile_upgrade.sql, media_upgrade.sql and guardian_upgrade.sql.
3. Run **security_audit.sql** in the Supabase SQL Editor (read-only) and inspect the RLS table, storage buckets and SECURITY DEFINER functions.
4. Only after checking compatibility, run **security_hardening.sql** (permission hardening and enabling RLS on sensitive tables).
5. After **community_platform_upgrade.sql** is applied, review and run **mod_package_integrity_upgrade.sql** to make mod package paths and submission identities immutable and prevent replacement of files awaiting approval. To replace a submitted ZIP, delete the submission and create a new one.
6. Verify anonymous and email sessions, the community, uploads, approved mod downloads, reports and moderator tools from separate test accounts. Specifically test: ZIP preflight must pass before approval, pending files cannot be deleted and re-uploaded while referenced by a pending submission, and rejected submissions can still be removed.
7. Deploy docs/supabase/functions/community-media/index.ts separately using Supabase tooling if you need its updated code to run. A GitHub push does NOT deploy this Edge Function automatically. Keep server keys in Supabase secrets, never in GitHub Pages.
8. Add a separate mandatory server-side ZIP scanning and approval service before distributing untrusted uploaded archives. Never run untrusted mods on a developer machine.

## Manual functionality checks (required before production)

- Open docs/index.html through HTTP/HTTPS, not file://, and verify assets and navigation.
- Check the Community chat sends, updates and loads older messages while online.
- Check profiles, email login, avatar/banner upload and public creator pages.
- Check mods catalog, search, cover thumbnails, the ZIP preflight and the admin review interface.
- Test support forms and download/donation links.
- Inspect browser Console for blocked CSP requests, then revise allowlists if your actual deployment adds new trusted origins.
- Confirm the live Supabase RLS policies against a normal user and an administrator.
- Confirm automatic desktop Git sync pulls only tested main commits.

## Limitations

Static tests and TypeScript type-checks cannot confirm actual Supabase permissions, form delivery or browser behavior against the live database. The new SQL files are opt-in administrative scripts; do not assume they have run. The website is improved and protected in several layers, but cannot be called fully secure or malware-proof on source inspection alone.

## Server-side antivirus workflow (new; NOT automatically enabled)

This project now includes `tools/scan_mod_packages.py`, a ClamAV-based worker,
and `.github/workflows/scan-mod-packages.yml`. The worker downloads private ZIP
packages only with a server-side credential, validates ZIP structures, scans
recursively with ClamAV and writes an audit status and SHA-256 fingerprint.
Invalid files and antivirus alerts are marked `blocked`. Scanner errors are
marked `error` and never treated as clean. Every new transition to `approved`
is rejected by the database unless its scan is `clean`, has a digest and a
completion time, **once the migration has been applied**.

### Production rollout order (manual; do not skip)

1. Back up the Supabase database. Check the deployed schema with
   `docs/database/mod_scan_audit.sql` and `security_audit.sql`. Source SQL is
   not evidence that a migration was applied to the hosted project.
2. Confirm `community_platform_upgrade.sql` and
   `mod_package_integrity_upgrade.sql` have already been applied. Validate
   that pending ZIP objects cannot be deleted/replaced by the owner while a
   pending database record refers to them.
3. Set encrypted GitHub Actions repository secrets
   `WTMM_SUPABASE_URL` and `WTMM_SUPABASE_SERVICE_ROLE_KEY`.
   Use the **server-only service_role credential**, never the publishable
   browser key. The worker uses a JWT bearer token for its REST and private
   Storage requests; validate compatibility with your current Supabase keys.
   Never put credentials into Markdown, code, browser files or Actions logs.
4. Apply `docs/database/mod_malware_scanning_upgrade.sql` manually in Supabase
   SQL Editor. This starts with scan status `pending` for existing records.
   New approvals now fail closed until the scan worker succeeds. Previously
   approved mods remain visible while backfill occurs; the scanner also checks
   them and automatically rejects legacy approved archives it marks blocked.
5. In GitHub Actions, run **WTMM server-side ZIP malware scanning** manually.
   Verify ClamAV signatures updated, the job passed, the scan audit columns
   changed, and normal uploads still work. Use a clean non-production test ZIP
   and an intentionally invalid ZIP to verify clean vs blocked behavior.
6. Only after the end-to-end test succeeds, add repository variable
   `WTMM_SCAN_ENABLED=true` to enable the scheduled 30-minute scans.
   Stop the schedule by changing the variable to `false`. Jobs use a
   concurrency lock to avoid overlapping privileged scans.
7. Verify from separate test accounts that a member cannot set scan fields,
   cannot approve their own mod, and cannot replace a pending ZIP after review.
   Verify admin can still reject submissions and owner can delete rejected
   submissions. Verify site pages, profile, chat, moderation and downloads.

**Important limitations:** This is a periodically scheduled GitHub-hosted
server-side worker, not a permanently running scanning server. ClamAV scanning
reduces risk but never guarantees that a mod is harmless. A successful GitHub
push **does not** apply SQL or grant the scanner access to Supabase. Existing
published files are not guaranteed clean until backfill has finished.
Production deployment and database state must be verified separately.


## November 17, 2026: full-site stability and live Supabase review

### Verified in the connected production project

- Project `wt-mod-manager-community` was reachable and its existing user-facing
  public tables had RLS enabled.
- Explicit `EXECUTE` access for `anon` and `authenticated` was revoked on
  `public.rls_auto_enable()`. A post-change SQL check confirmed both roles
  cannot execute it; privileged database execution remains available.
- `mod_package_integrity_upgrade.sql` was applied to protect ZIP files
  and preview paths while submissions are awaiting moderation.
- `performance_rls_policy_merge.sql` was applied; profile SELECT and
  mod UPDATE access rules were merged without intentionally changing access.
- The missing `community-media` Edge Function was deployed with JWT
  verification enabled and its ACTIVE status was confirmed.
- Supabase security and performance advisors were checked. Because community
  supports anonymous sign-in, not every anonymous-role advisory implies
  a vulnerability. Known additional operational work includes leaked-password
  protection in Auth, careful audit of privileged RPC functions and
  end-to-end role testing using controlled test accounts.

### Additional source improvements

- `docs/js/supabase-session.mjs` centralizes verified session initialization,
  preserving both anonymous users and email accounts.
- `docs/js/error-monitor.js` exposes generic, in-memory health counters through
  `WTDiagnostics.health()`. It never sends metrics over the network.
- `mods/mods.js` adds an administrator-only summary based on records already
  authorized by Supabase RLS.
- Public creator pages use bounded image-request concurrency.
- Community refresh pauses while offline and resumes through its existing
  online event listener; essential messages and channels remain intact.
- CI protects the existing navigation, forms, features, session behavior
  and diagnostics with regression tests.

### Still not activated

The GitHub-hosted ZIP antivirus worker remains opt-in. Do NOT apply
`mod_malware_scanning_upgrade.sql` until encrypted repository secrets,
an initial successful scan and the scheduled worker are ready. Otherwise
new mod approvals will fail closed. A deployed Edge Function for chat images
is not a substitute for server-side ZIP antivirus scanning.

Also note: a passing CI run does not verify real browser interactions, existing
form delivery, Auth settings, or every runtime RLS permission. Test those before
claiming a complete security audit.
