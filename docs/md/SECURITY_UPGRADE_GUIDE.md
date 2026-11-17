# WT Mod Manager — security, performance and release checklist

## Implemented in source code

1. **XSS hardening:** CSP meta tags on the six public pages. No inline JavaScript; allowlisted scripts, forms, network destinations, and no object embeds. GitHub Pages is a static host: CSP via meta cannot set frame-ancestors, HSTS, or response headers. Use a header-capable host or reverse proxy for those protections.
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
