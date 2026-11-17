// Audit-preserving checks for this site-wide enhancement batch.
// They supplement (not replace) browser QA and Supabase RLS tests.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
const root = path.resolve(import.meta.dirname, "..");
const read = p => fs.readFileSync(path.join(root,p),"utf8");
const features = [
  ["docs/community/community.js", [
    "chatDrafts.write(activeChannel", "chatDrafts.read(next)",
    "messageSignature(message)", "previousById", "updateUnreadBadge",
    "eventFilter.addEventListener", "Обновить статусы"
  ]],
  ["docs/mods/mods.js", [
    "fetchModPage", ".range(offset, offset + MOD_PAGE_SIZE - 1)",
    "loadMoreMods", "modsLoadMore", "extendAuthorProfiles"
  ]],
  ["docs/profile/profile.js", [
    "saveProfileDraft", "restoreProfileDraft", "profileDrafts.clear"
  ]],
  ["docs/support/support.js", [
    "saveSupportDraft", "restoreSupportDraft", "clearSupportDraft",
    "setupDiagnosticsExport"
  ]],
  ["docs/js/error-monitor.js", ["exportJSON", "counters: { ...counters }"]],
  ["tools/windows-sync/sync-github-safe.ps1", [
    "status --porcelain --untracked-files=all", "merge --ff-only",
    "SKIP: game currently running"
  ]]
];
for(const [file, expected] of features){
  const content=read(file);
  for(const symbol of expected){
    assert.ok(content.includes(symbol), "Missing enhancement " + file + ": " + symbol);
  }
}
assert.ok(!read("tools/windows-sync/sync-github-safe.ps1").includes("reset --hard"));
assert.ok(!read("tools/windows-sync/sync-github-safe.ps1").includes("git clean"));
console.log("PASS existing feature upgrades and non-destructive Windows sync");
