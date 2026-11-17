# WT Mod Manager — security suite (18 November 2026)

This document distinguishes **deployed** protections from **configured but inactive**
services. Source code, a passing CI check, and a database migration are not the
same thing as production readiness. Avoid making claims that mods are malware-free.

## 1. Server-side ZIP scanning — prepared, NOT ACTIVE

- Source: `tools/scan_mod_packages.py`, `.github/workflows/scan-mod-packages.yml`.
- Existing browser ZIP validation is structural only; it is not an antivirus.
- At the last verified production audit, `public.wtmm_mods` had **no
  `scan_status` column**, so the scan-to-approve database trigger is NOT active.
- To activate safely: (a) create a recoverable Supabase backup; (b) in the
  **repository GitHub UI** add encrypted Actions secrets
  `WTMM_SUPABASE_URL` and `WTMM_SUPABASE_SERVICE_ROLE_KEY`; (c) validate
  that the current scanner supports the project's service role key format;
  (d) apply `docs/database/mod_malware_scanning_upgrade.sql` after review;
  (e) manually trigger "WTMM server-side ZIP malware scanning"; (f) verify
  that a valid test archive is `clean` and invalid ZIPs are `blocked`;
  (g) set Actions variable `WTMM_SCAN_ENABLED=true` to enable the schedule.
- Do **not** apply the approval gate first: approvals would fail until the
  scanner is authorized and verified. Never commit service-role keys or paste
  them in a chat. Scanner failures must not be treated as clean scans.

## 2. Accounts / optional 2FA — deployed server rules; UI awaiting live user QA

- Database: `optional_mfa_enforcement_2026_11_18.sql` (applied).
- Profile: `docs/js/profile-mfa.mjs`, `docs/profile/profile.html`.
- Account owners with a confirmed email can enroll TOTP, verify their device,
  challenge on login, and remove their factor after confirmation.
- If a user has enrolled a verified factor, **AAL2 is required** for
  sensitive profile writes, mod submissions/edits/deletions, reports, and
  public admin checker functions.
- Users without MFA continue to work with existing anonymous/email sign-in.
- This is an opt-in defense, not a claim that every single API call is
  MFA-restricted. Evaluate additional exposed RPCs separately.
- Live MFA setup and verification with the owner's real authenticator must
  be completed before considering the entire login flow production-verified.
- The Supabase adviser reports leaked-password checking **disabled**. Enable
  it from Auth configuration if the project's plan supports it; Supabase's
  password security documentation lists it as Pro tier or higher.
- Confirm email verification, SMTP deliverability and recovery routes in
  Supabase Dashboard before requiring MFA for all administrators. Do not
  globally require it yet; the only existing admin could be locked out.

## 3. Abuse prevention — deployed and verified in database

- `submission_rate_limits_2026_11_18.sql` is applied.
- Existing WT Guardian chat flood/duplicate/link protections are retained.
- New limits: reports <=10 per hour and <=40 per rolling day;
  mod submissions <=8 per hour and <=30 per rolling day **per user**.
- Requests share a transaction-scoped advisory lock and use server time to
  prevent parallel submission race and client-supplied timestamp bypass.
- These limits apply to **database submissions**, not to direct Storage
  object creation. Set Storage size/quantity limits and remove orphaned files
  as a separate hardening step.

## 4. RLS and account-data separation — deployed, audit provided

- Existing profile owner/private and moderator checks remain.
- The added TOTP restrictive policies protect sensitive writes.
- See `docs/database/security_suite_audit.sql` for exact active policy
  and trigger checks. Supabase security adviser warnings require review;
  do not blindly revoke purposeful Guardian RPC functions or public reads.
- Tests using synthetic users and normal/admin browser sessions remain
  important. A policy definition alone does not test all application paths.

## 5. Encrypted database backups — workflow prepared, NOT SCHEDULED YET

- `.github/workflows/encrypted-database-backup.yml` schedules daily
  backups and supports manual runs **only after owner opt-in**.
- PostgreSQL 17 `pg_dump` output is piped directly into `age` encryption.
  No unencrypted database artifact is written to disk for upload.
- In GitHub Settings > Secrets and variables > Actions:
    - Repository secret: `WTMM_BACKUP_DATABASE_URL`. Supabase Postgres
      connection string, with `sslmode=require` (or `verify-full`).
      Never publish this secret.
    - Repository variable: `WTMM_BACKUP_AGE_RECIPIENT`. The *public*
      age recipient (`age1...`); keep its corresponding *private* identity
      offline in multiple secure locations.
    - Repository variable: `WTMM_BACKUP_ENABLED=true` when ready.
- Run workflow manually, download the *encrypted* artifact from Actions,
  decrypt **locally**, run `pg_restore --list` and test a full restore to a
  separate staging database. Only then count backup/restore as working.
- Backup artifacts expire after 14 days; use separate long-term offline
  retention, if required. Never upload decrypted dumps back to GitHub.
- This is an additional backup option, not a replacement for Supabase native
  backups or a tested recovery plan.

## 6. Release integrity — automation prepared; no releases yet

- `.github/workflows/release-checksums.yml` runs when a GitHub Release is
  published and creates a checked `SHA256SUMS.txt` for .exe/.msi/.zip assets.
- The Windows helper `tools/verify-release-checksum.ps1` compares a downloaded
  release file against its manifest.
- At the time of this audit, the repository had **zero GitHub Releases**.
  End-to-end signing/checksum publication cannot be verified before the
  first real artifact is published.
- SHA-256 detects accidental/tampered file differences relative to the
  manifest; it is **not** a substitute for Authenticode signing, which needs
  a trusted signing certificate and a release workflow configured by its owner.

## Suggested end-to-end test order

1. Run `node tools/check-site.mjs`; review GitHub CI results on PR and main.
2. Confirm actual Supabase policies/triggers with `security_suite_audit.sql`.
3. Sign in with two non-admin test accounts and verify private profile
   isolation; test moderator actions under a distinct admin identity.
4. Register a test email account and enroll/verify TOTP; verify AAL1 writes
   are refused after enrollment, AAL2 writes succeed, and no-MFA accounts
   keep working. Use only test accounts and do not share OTP/QR secrets.
5. Configure and test encrypted backup/restore to a **separate** database.
6. Configure private scanner credentials, deploy scanner gate, scan a test
   archive, confirm approval fails without a clean scan; enable scheduling.
7. Publish a test release with harmless installer fixture and check that
   SHA256SUMS.txt is attached and the Windows verifier matches it.

All enabled protections are additive. The system is not "unhackable"; keep
monitoring logs, dependencies, account recovery and restore drills.
