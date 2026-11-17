// WT Mod Manager: privacy-first, local-only error diagnostics.
// No personal data, URLs, tokens, full stack traces or network reports are stored.
"use strict";
(() => {
    const history = [];
    const MAX_ITEMS = 25;
    const MAX_COUNTER = 1000000;
    const counters = Object.create(null);
    const allowedEvents = new Set([
        "community-refresh-ok", "community-refresh-failed",
        "mods-refresh-ok", "mods-refresh-failed",
        "profile-load-ok", "profile-load-failed",
        "connectivity-offline", "connectivity-online"
    ]);
    function record(category) {
        // Only generic hard-coded categories may be recorded: never user input or URLs.
        if (typeof category !== "string" || !allowedEvents.has(category)) return false;
        counters[category] = Math.min((counters[category] || 0) + 1, MAX_COUNTER);
        return true;
    }
    function note(kind, detail = "") {
        history.push({
            time: new Date().toISOString(),
            kind: String(kind).slice(0, 48),
            detail: String(detail).slice(0, 80)
        });
        if (history.length > MAX_ITEMS) history.shift();
        console.warn("[WT diagnostics] " + kind, detail);
    }
    window.addEventListener("error", event => {
        const kind = event.error?.name || "ScriptError";
        note("javascript", /^[a-z]+error$/i.test(kind) ? kind : "ScriptError");
    });
    window.addEventListener("unhandledrejection", event => {
        const kind = event.reason?.name || "PromiseError";
        note("promise", /^[a-z]+error$/i.test(kind) ? kind : "PromiseError");
    });
    document.addEventListener("securitypolicyviolation", event => {
        note("csp", event.effectiveDirective || "blocked");
    });
    window.addEventListener("offline", () => record("connectivity-offline"));
    window.addEventListener("online", () => record("connectivity-online"));
    Object.defineProperty(window, "WTDiagnostics", {
        value: Object.freeze({
            // Keep the original public API for existing scripts and console users.
            summary: () => history.map(item => ({ ...item })),
            clear: () => { history.length = 0; for (const k of Object.keys(counters)) delete counters[k]; },
            record,
            health: () => ({
                online: typeof navigator !== "undefined" ? navigator.onLine !== false : true,
                issues: history.length,
                counters: { ...counters }
            }),
            // User-triggered diagnostics export: deliberately excludes URLs,
            // stack traces, credentials, message text and account identifiers.
            exportJSON: () => JSON.stringify({
                product: "WT Mod Manager Website",
                format: 2,
                generatedAt: new Date().toISOString(),
                online: typeof navigator !== "undefined" ? navigator.onLine !== false : true,
                counters: { ...counters },
                events: history.map(item => ({ ...item }))
            }, null, 2)
        }),
        configurable: false,
        writable: false
    });
})();
