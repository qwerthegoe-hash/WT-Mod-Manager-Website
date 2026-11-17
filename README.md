# WT Mod Manager Website

Official website for WT Mod Manager (independent fan project).

The public GitHub Pages site lives in [docs/](docs/). Open [docs/index.html](docs/index.html) using a local web server (for example VS Code Live Server); do not use file:// URLs for Supabase and module-based pages.

## Security and quality

- The site uses a Content Security Policy (CSP) with an allowlisted Supabase CDN and network origins.
- Private errors are kept in memory only: run WTDiagnostics.summary() in your browser console to inspect generic error types. No telemetry or credentials are uploaded.
- Client-side ZIP validation is a preflight only, not an antivirus scanner. Uploaded mods stay pending until manual moderation.
- Supabase storage and database permissions must be configured separately. The SQL sources here do not apply to your live project automatically.
- Each GitHub push and pull request is checked by GitHub Actions (links, JS, JSON, ZIP regression tests and Edge Function type checks).

Read the [security setup and limitations](docs/md/SECURITY_UPGRADE_GUIDE.md) before production deployment. Do not place Supabase service-role keys, API secrets or credentials in this repository.
