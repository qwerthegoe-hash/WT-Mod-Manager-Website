// WT Mod Manager: privacy-first, local-only error diagnostics.
// No personal data, URLs, tokens, full stack traces or network reports are stored.
"use strict";
(() => {
    const history = [];
    const MAX_ITEMS = 25;
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
    Object.defineProperty(window, "WTDiagnostics", {
        value: Object.freeze({
            summary: () => history.map(item => ({ ...item })),
            clear: () => { history.length = 0; }
        }),
        configurable: false,
        writable: false
    });
})();
