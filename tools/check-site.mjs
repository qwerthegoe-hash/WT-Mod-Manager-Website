// WT Mod Manager: dependency-free static checks. Run with Node.js 22+.
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = path.resolve(import.meta.dirname, "..");
const docs = path.join(root, "docs");
const errors = [];
const configSource = fs.readFileSync(path.join(docs, "js", "community-config.js"), "utf8");
const configuredSupabase = configSource.match(/supabaseUrl:\s*["'](https:\/\/[a-z0-9-]+\.supabase\.co)["']/i)?.[1];
if (!configuredSupabase) errors.push("Could not locate configured Supabase origin for CSP checking");
let checkedLinks = 0, checkedScripts = 0, checkedPages = 0;
function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((item) => {
    const absolute = path.join(dir, item.name);
    return item.isDirectory() ? walk(absolute) : [absolute];
  });
}
function fail(context, message) { errors.push(context + ": " + message); }
function checkSyntax(code, label, module = true) {
  const args = ["--check", "--input-type=" + (module ? "module" : "commonjs")];
  const result = spawnSync(process.execPath, args, { input: code, encoding: "utf8" });
  checkedScripts++;
  if (result.status !== 0) fail(label, result.stderr.trim().slice(0, 700));
}
function checkLocalPath(src, file) {
  if (!src || src[0] === "#" || /^[a-z][\w+.-]*:/i.test(src) || src.startsWith("//")) return;
  const target = src.split(/[?#]/)[0];
  if (!target || target[0] === "/" || target.includes("{")) return;
  const absolute = path.resolve(path.dirname(file), decodeURIComponent(target));
  if (!absolute.startsWith(docs + path.sep) || !fs.existsSync(absolute)) fail(path.relative(root, file), "Missing local resource: " + src);
  checkedLinks++;
}
for (const file of walk(docs)) {
  const relative = path.relative(root, file);
  const extension = path.extname(file).toLowerCase();
  if (extension === ".js" || extension === ".mjs") {
    const code = fs.readFileSync(file, "utf8");
    checkSyntax(code, relative, true);
    for (const match of code.matchAll(/\b(?:import|from)\s*\(?\s*["'](\.[^"']+\.(?:js|mjs))["']/g)) checkLocalPath(match[1], file);
  }
  if (extension === ".json") {
    try { JSON.parse(fs.readFileSync(file, "utf8")); }
    catch (error) { fail(relative, String(error)); }
  }
  if (extension === ".html") {
    checkedPages++;
    const html = fs.readFileSync(file, "utf8");
    for (const match of html.matchAll(/\b(?:href|src)=["']([^"']+)["']/g)) checkLocalPath(match[1], file);
    for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
      if (!/\bsrc=/.test(match[1]) && match[2].trim()) {
        fail(relative, "Inline JavaScript conflicts with strict CSP");
        checkSyntax(match[2], relative + ":inline-script", /\btype=["']module["']/.test(match[1]));
      }
    }
    if (!/<meta\b[^>]*\bname=["']referrer["']/.test(html)) fail(relative, "Missing referrer meta");
    const csp = html.match(/<meta\b[^>]*\bhttp-equiv=["']Content-Security-Policy["'][^>]*>/);
    if (!csp) fail(relative, "Missing CSP meta");
    else {
      if (!csp[0].includes("object-src 'none'") || !csp[0].includes("base-uri 'self'"))
        fail(relative, "CSP must disable objects and external base URLs");
      if (/script-src[^;]*'unsafe-inline'/.test(csp[0]))
        fail(relative, "CSP must not allow inline scripts");
      if (/https:\/\/\*\.supabase\.co|wss:\/\/\*\.supabase\.co/.test(csp[0]))
        fail(relative, "CSP must not allow wildcard Supabase projects");
      if (/img-src[^;]*\shttps:(?:[\s;'"]|$)/.test(csp[0]))
        fail(relative, "CSP must not allow all HTTPS image hosts");
      if (configuredSupabase && (!csp[0].includes(configuredSupabase) ||
          !csp[0].includes(configuredSupabase.replace("https://", "wss://"))))
        fail(relative, "CSP does not match the configured Supabase origin");
    }
    for (const match of html.matchAll(/<a\b([^>]*)>/g)) {
      if (/target=["']_blank["']/.test(match[1]) && !/rel=["'][^"']*noopener[^"']*["']/.test(match[1]))
        fail(relative, "External tab link missing noopener");
    }
  }
  if ([".js", ".html", ".json", ".ts"].includes(extension)) {
    const text = fs.readFileSync(file, "utf8");
    if (/sb_secret_[\w-]{10,}/i.test(text) || /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/.test(text))
      fail(relative, "Possible secret material committed");
  }
}
if (fs.existsSync(path.join(root, "tools", "test-zip-validator.mjs"))) {
  const result = spawnSync(process.execPath, [path.join(root, "tools", "test-zip-validator.mjs")], { encoding: "utf8" });
  if (result.status !== 0) fail("ZIP validation tests", (result.stderr || result.stdout).slice(0, 1000));
  else process.stdout.write(result.stdout);
}
const reviewPolicyTest = spawnSync(process.execPath, [
  path.join(root, "tools", "test-mod-review-policy.mjs")
], { encoding: "utf8" });
if (reviewPolicyTest.status !== 0) {
  fail("Mod review policy tests", (reviewPolicyTest.stderr || reviewPolicyTest.stdout).slice(0, 1000));
} else {
  process.stdout.write(reviewPolicyTest.stdout);
}
const asyncPoolTest = spawnSync(process.execPath, [
  path.join(root, "tools", "test-async-pool.mjs")
], { encoding: "utf8" });
if (asyncPoolTest.status !== 0) {
  fail("Async request pool tests", (asyncPoolTest.stderr || asyncPoolTest.stdout).slice(0, 1000));
} else {
  process.stdout.write(asyncPoolTest.stdout);
}
// Guard against removing public routes, account UI, and community channels during refactors.
for (const test of [
  "test-supabase-session.mjs",
  "test-error-monitor.mjs",
  "test-site-functionality.mjs",
  "test-session-drafts.mjs",
  "test-feature-enhancements.mjs",
  "test-global-search.mjs",
  "test-home-refresh.mjs"
]) {
  const result = spawnSync(process.execPath, [
    path.join(root, "tools", test)
  ], { encoding: "utf8" });
  if (result.status !== 0) {
    fail(test, (result.stderr || result.stdout).slice(0, 1200));
  } else {
    process.stdout.write(result.stdout);
  }
}
console.log("Checked " + checkedPages + " pages, " + checkedLinks + " local links, " + checkedScripts + " JS scripts.");
if (errors.length) {
  for (const error of errors) console.error("FAIL: " + error);
  process.exitCode = 1;
} else {
  console.log("PASS: static website checks");
}
