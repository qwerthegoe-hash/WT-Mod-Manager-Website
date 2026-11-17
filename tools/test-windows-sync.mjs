import assert from "node:assert/strict";
import fs from "node:fs";

const script = fs.readFileSync(new URL("./windows-sync/sync-github-safe.ps1", import.meta.url), "utf8");
const launcher = fs.readFileSync(new URL("./windows-sync/launch-hidden.vbs", import.meta.url), "utf8");

for (const name of ["aces", "aces_BE", "aces-min-cpu"]) {
    assert.ok(script.includes('"' + name + '"'), "War Thunder process must be guarded: " + name);
}
assert.ok(script.includes("Get-Process -Name $processName"), "Worker must check Windows processes");
assert.ok(script.includes("function Test-GameRunning"), "Worker must share the game detection helper");
assert.ok((script.match(/if \(Test-GameRunning\) \{ exit 0 \}/g) || []).length >= 3,
    "Check for running games before work and before applying a Git merge");

const processCheck = script.indexOf("if (Test-GameRunning) { exit 0 }");
const firstGitInvocation = script.indexOf("& $gitExecutable -C $RepositoryPath");
assert.ok(processCheck >= 0 && firstGitInvocation > processCheck,
    "Game check must happen before any Git command");

const beforeMerge = script.lastIndexOf("if (Test-GameRunning) { exit 0 }");
const merge = script.indexOf("merge --ff-only");
assert.ok(beforeMerge >= 0 && beforeMerge < merge,
    "Game check must happen immediately before Git merge");
assert.ok(script.includes("status --porcelain --untracked-files=all"),
    "Do not overwrite changes or unknown local files");
assert.ok(!script.includes("reset --hard"), "Never use a destructive Git reset");
assert.ok(!script.includes("git clean"), "Never discard untracked files");

assert.ok(launcher.includes("-ExecutionPolicy RemoteSigned"),
    "Hidden launcher must support trusted local PowerShell scripts without global policy changes");
assert.ok(script.includes("Get-Command git.exe"), "Scheduled task must locate git.exe");
console.log("PASS: War Thunder process guard, safe fast-forward and silent launcher");
