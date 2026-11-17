// Regression checks for full-search wiring and RLS-compatible fallback.
import assert from "node:assert/strict";
import fs from "node:fs";
const code = fs.readFileSync(new URL("../docs/mods/mods.js", import.meta.url), "utf8");
const sql = fs.readFileSync(new URL("../docs/database/mod_catalog_search_upgrade.sql", import.meta.url), "utf8");
assert.ok(code.includes('.rpc("wtmm_search_mods"'));
assert.ok(code.includes('p_offset: offset, p_limit: MOD_PAGE_SIZE'));
assert.ok(code.includes('const generation = ++queryGeneration'));
assert.ok(code.includes('if (generation !== queryGeneration) return false'));
assert.ok(code.includes('error.code !== "PGRST202"'));
assert.ok(code.includes('refresh().catch(error => say("Ошибка поиска модов:'));
assert.ok(sql.includes("security invoker"));
assert.ok(sql.includes("and (select public.wtmm_is_admin())"));
assert.ok(sql.includes("to authenticated"));
assert.ok(sql.includes("from public, anon"));
assert.ok(sql.includes("p.nickname ilike"));
assert.ok(sql.includes("limit least(greatest(coalesce(p_limit,150),1),150)"));
console.log("PASS: SQL global search, RLS restrictions, paging and stale-result avoidance");
