// Offline checks for the current mod catalogue UX. No browser or API keys.
import assert from "node:assert/strict";
import fs from "node:fs";
import {DEFAULT_MOD_FILTERS, hasActiveModFilters, emptyModState}
  from "../docs/mods/mods-filter-state.mjs";

const defaults = {...DEFAULT_MOD_FILTERS};
assert.equal(hasActiveModFilters(defaults), false);
assert.equal(hasActiveModFilters({...defaults, search: "   "}), false);
assert.equal(hasActiveModFilters({...defaults, search: "Sight"}), true);
assert.equal(hasActiveModFilters({...defaults, category: "sounds"}), true);
assert.equal(hasActiveModFilters({...defaults, author: "abc"}), true);
assert.equal(hasActiveModFilters({...defaults, sort: "old"}), true);
assert.equal(hasActiveModFilters({...defaults, favoritesOnly: true}), true);
assert.equal(emptyModState("catalog", true).title, "Ничего не найдено");
assert.equal(emptyModState("mine", false).title, "У тебя пока нет модов");
assert.equal(emptyModState("downloads", false).title, "Пока нет скачанных модов");
assert.equal(emptyModState("moderation", false).title, "Очередь пуста");
assert.equal(emptyModState("catalog", false).title, "Здесь пока пусто");

const html = fs.readFileSync(new URL("../docs/mods/mods.html", import.meta.url), "utf8");
const js = fs.readFileSync(new URL("../docs/mods/mods.js", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("../docs/mods/mods.css", import.meta.url), "utf8");
const locale = fs.readFileSync(new URL("../docs/js/site-language.mjs", import.meta.url), "utf8");
for (const id of ["modsResetFilters", "modsEmptyReset", "modsRetry", "modsEmptyTitle", "modsEmptyDescription"]) {
  assert.ok(html.includes('id="' + id + '"'), "Missing catalog control " + id);
  assert.ok(js.includes('$("' + id + '")'), "Missing catalog handler " + id);
}
assert.ok(js.includes('resettingModsFilters = true'));
assert.ok(js.includes('if (resettingModsFilters) return'));
assert.ok(js.includes('++queryGeneration; // Invalidate pending results'));
assert.ok(js.includes('$(id).dispatchEvent(new Event("change"'));
assert.ok(js.includes('$("modsRetry").hidden = false;'));
assert.ok(css.includes('#modsEmptyReset[hidden]'));
for (const phrase of ["Сбросить фильтры", "Повторить загрузку", "Ничего не найдено"]) {
  assert.ok(locale.includes('["' + phrase + '"'), "Missing translated label " + phrase);
}
console.log("PASS: catalog reset, localized empty states, keyboard-compatible dropdown sync, retry wiring");
