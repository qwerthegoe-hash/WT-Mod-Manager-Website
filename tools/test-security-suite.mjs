import assert from "node:assert/strict";
import fs from "node:fs";

const read = path => fs.readFileSync(new URL("../" + path, import.meta.url), "utf8");
const html = read("docs/profile/profile.html");
const js = read("docs/profile/profile.js");
const mfaSql = read("docs/database/optional_mfa_enforcement_2026_11_18.sql");
const limitsSql = read("docs/database/submission_rate_limits_2026_11_18.sql");
const scannerSql = read("docs/database/mod_malware_scanning_upgrade.sql");
const backups = read(".github/workflows/encrypted-database-backup.yml");
const releases = read(".github/workflows/release-checksums.yml");
const scanner = read(".github/workflows/scan-mod-packages.yml");

assert.ok(html.includes('id="mfaBegin"') && html.includes('id="mfaLoginCode"'));
assert.ok(html.includes('href="profile-security.css"'));
assert.ok(js.includes("setupProfileMfa"));
for(const name of [
  "wtmm_mfa_profile_insert", "wtmm_mfa_profile_update", "wtmm_mfa_report_insert",
  "wtmm_mfa_mod_insert", "wtmm_mfa_mod_update", "wtmm_mfa_mod_delete"
]) {
  assert.ok(mfaSql.includes(name), "Missing SQL MFA gate " + name);
}
assert.ok(mfaSql.includes("as restrictive"), "MFA gates must restrict existing RLS policies");
assert.ok(mfaSql.includes("auth.mfa_factors") && mfaSql.includes("auth.jwt()->>'aal'"));
assert.ok(mfaSql.includes("wtmm_security.mfa_satisfied()"));
assert.ok(mfaSql.includes("public.community_is_admin()"));
assert.ok(mfaSql.includes("public.wtmm_is_admin()"));
assert.ok(!/user_metadata|raw_user_meta_data/.test(mfaSql), "Never authorize from user metadata");
assert.ok(limitsSql.includes("pg_advisory_xact_lock"), "Prevent concurrent submission bypasses");
assert.ok(limitsSql.includes("new.created_at := now()"), "Use trusted server timestamps");
assert.ok(limitsSql.includes("community_reports") && limitsSql.includes("wtmm_mods"));
assert.ok(scannerSql.includes("scan_status") && scannerSql.includes("'clean'"));
assert.ok(scanner.includes("WTMM_SCAN_ENABLED"), "Scanner must be opt-in until secrets configured");

assert.ok(backups.includes("WTMM_BACKUP_ENABLED"), "Backups require explicit opt-in");
assert.ok(backups.includes("WTMM_BACKUP_DATABASE_URL"), "Connection URL must come from secrets");
assert.ok(backups.includes("WTMM_BACKUP_AGE_RECIPIENT"), "Encryption recipient required");
assert.ok(backups.includes("pg_dump") && backups.includes(" | age -r "));
assert.ok(backups.includes("retention-days: 14"));
assert.ok(!backups.includes("database.sql") && !backups.includes("database.dump"),
  "Do not upload plaintext backup artifacts");
assert.ok(releases.includes("release:") && releases.includes("types: [published]"));
assert.ok(releases.includes("sha256sum --check") && releases.includes("SHA256SUMS.txt"));
assert.ok(releases.includes("gh release upload"));
console.log("PASS: protected account operations, abuse throttles, encrypted backup and release integrity");
