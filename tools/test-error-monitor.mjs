import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const events = Object.create(null);
const window = {
  addEventListener: (name, handler) => { (events[name] ??= []).push(handler); }
};
const document = { addEventListener: (name, handler) => { (events[name] ??= []).push(handler); } };
const consoleStub = { warn: () => {} };
const program = fs.readFileSync(new URL("../docs/js/error-monitor.js", import.meta.url), "utf8");
vm.runInNewContext(program, { window, document, console: consoleStub, navigator: { onLine: true }, Date });
assert.equal(window.WTDiagnostics.record("mods-refresh-ok"), true);
assert.equal(window.WTDiagnostics.record("private-user-input"), false);
assert.equal(window.WTDiagnostics.health().counters["mods-refresh-ok"], 1);
const exportedReport = JSON.parse(window.WTDiagnostics.exportJSON());
assert.equal(exportedReport.product, "WT Mod Manager Website");
assert.equal(exportedReport.counters["mods-refresh-ok"], 1);
events.error[0]({ error: { name: "TypeError", message: "private data" } });
const eventsBefore = window.WTDiagnostics.summary();
assert.equal(eventsBefore.length, 1);
assert.ok(!JSON.stringify(eventsBefore).includes("private data"));
events.offline[0]();
assert.equal(window.WTDiagnostics.health().counters["connectivity-offline"], 1);
window.WTDiagnostics.clear();
assert.equal(window.WTDiagnostics.summary().length, 0);
assert.equal(Object.keys(window.WTDiagnostics.health().counters).length, 0);
console.log("PASS: privacy-safe diagnostics keep legacy API and aggregate health");
