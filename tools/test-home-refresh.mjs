import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const html = fs.readFileSync(new URL("../docs/index.html", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("../docs/home-refresh.css", import.meta.url), "utf8");
const script = fs.readFileSync(new URL("../docs/app.js", import.meta.url), "utf8");

assert.ok(html.includes('href="home-refresh.css"'), "Homepage CSS must be loaded");
assert.ok(!html.includes('class="pulse"'), "Remove green dot next to beta");
assert.ok(html.includes('class="hero-title-main"'), "Headline should have relaxed line layout");
assert.ok(css.includes(".hero h1 .hero-title-main"), "Modern hero typography styles missing");
assert.ok(html.includes('href="contact/contact.html"'), "Contact developer must link to dedicated Contact panel");
for (const key of ["q1","q2","q3","q4","q5","a1","a2","a3","a4","a5"]) {
  assert.ok(html.includes('data-i18n="' + key + '"'), "FAQ missing " + key);
}

const mockButtons = ["sights", "camouflages", "sounds", "settings"].map(name => {
  const handlers = {};
  return {
    dataset: { preview: name },
    attributes: {},
    handlers,
    classList: { toggle() {} },
    setAttribute(key,val) { this.attributes[key] = val; },
    addEventListener(event,callback) { handlers[event] = callback; }
  };
});
const mockScenes = mockButtons.map(button => ({ dataset: { scene: button.dataset.preview }, hidden: false }));
const mockLabels = [0,1,2].map(() => {
  const child = { textContent: "" };
  return { child, querySelector() { return child; } };
});
const heading = { textContent: "" };
const description = { textContent: "" };
const panel = { dataset: {} };
const reveals = Array.from({ length: 4 }, () => ({
  revealed: false,
  classList: { add(value) { if (value === "revealed") this.parent.revealed = true; } }
}));
for (const item of reveals) item.classList.parent = item;
let htmlJsClassAdds = 0;
let observed = 0;
const memory = new Map();
const storage = {
  getItem: key => memory.get(key) || null,
  setItem: (key,value) => memory.set(key,value)
};
const document = {
  addEventListener() {},
  getElementById(id) {
    return { previewHeading: heading, previewDescription: description, mockPreviewPanel: panel }[id] || null;
  },
  querySelectorAll(selector) {
    if (selector === ".mock-item[data-preview]") return mockButtons;
    if (selector === ".preview-scene[data-scene]") return mockScenes;
    if (selector === "#previewGrid > div") return mockLabels;
    if (selector === ".reveal") return reveals;
    return [];
  },
  documentElement: { classList: { add(value) { if (value === "js") htmlJsClassAdds++; } } }
};
class IntersectionObserverMock {
  observe() { observed++; }
  unobserve() {}
}
const window = {
  matchMedia: () => ({ matches: false }),
  IntersectionObserver: IntersectionObserverMock
};
const context = vm.createContext({
  document, window, sessionStorage: storage,
  IntersectionObserver: IntersectionObserverMock,
  console, URL, navigator: {language:"ru"}
});
vm.runInContext(script, context, { filename: "app.js" });
const translations = vm.runInContext("translations", context);
for (const language of ["en","ru","uk"]) {
  const t = translations[language];
  for (const key of [
    "headline", "eyebrow", "previewHint", "previewSightsTitle", "previewCamoTitle",
    "previewSoundsTitle", "previewSettingsTitle", "contactTitle","contactButton",
    "faqTitle", "q4", "a4", "q5", "a5"
  ]) assert.equal(typeof t[key], "string", language + " missing translation " + key);
}
assert.equal(translations.ru.faqTitle, "Задаваемые вопросы вами");

vm.runInContext("setupMockShowcase()",context);
assert.equal(panel.dataset.mode,"sights");
assert.equal(heading.textContent,translations.en.previewSightsTitle);
assert.equal(mockScenes[0].hidden,false);
mockButtons[1].handlers.click();
assert.equal(panel.dataset.mode,"camouflages");
assert.equal(heading.textContent,translations.en.previewCamoTitle);
assert.equal(mockButtons[1].attributes["aria-pressed"],"true");
assert.equal(mockScenes[0].hidden,true);
assert.equal(mockScenes[1].hidden,false);
vm.runInContext('currentLanguage = "ru"; renderMockPreview()',context);
assert.equal(heading.textContent,translations.ru.previewCamoTitle);
assert.equal(mockLabels[0].child.textContent,translations.ru.previewCamoNote1);
mockButtons[3].handlers.click();
assert.equal(heading.textContent,translations.ru.previewSettingsTitle);

vm.runInContext("setupRevealAnimations()",context);
assert.equal(htmlJsClassAdds,1);
assert.equal(observed,reveals.length);
assert.equal(memory.get("wtmm-home-intro-seen-v1"),"1");
vm.runInContext("setupRevealAnimations()",context);
assert.equal(htmlJsClassAdds,1,"Intro must not replay after returning from another page");
assert.ok(reveals.every(item => item.revealed),"Revisited homepage should show all sections immediately");
console.log("PASS: interactive showcase, 3 languages, one-time intro, FAQ and contact links");
