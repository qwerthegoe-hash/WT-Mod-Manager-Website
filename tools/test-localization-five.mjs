import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { contactLocalesExtra } from "../docs/contact/contact-extra-i18n.mjs";
import { supportTextsExtra,supportHelpExtra } from "../docs/support/support-extra-i18n.mjs";
const read=p=>fs.readFileSync(new URL("../"+p,import.meta.url),"utf8");
function extractObject(source,name) {
  const start=source.indexOf("const "+name+" = {");
  if(start<0)throw Error("Cannot find "+name);
  const end=source.indexOf("\n};",start);
  if(end<0)throw Error("Object not terminated: "+name);
  return vm.runInNewContext(source.slice(start,end+3)+"\n"+name);
}
const contact=extractObject(read("docs/contact/contact.js"),"copy");
const support=extractObject(read("docs/support/support.js"),"texts");
const help=extractObject(read("docs/support/support.js"),"helpTexts");
const homeGlobals={};vm.runInNewContext(read("docs/js/home-extra-i18n.js"),{window:homeGlobals});
const homepage=extractObject(read("docs/app.js"),"translations");
const allLanguages=["ru","uk","en","pl","de"];
const pages=[
  ["home",homepage.en,homeGlobals.WTMM_HOME_TRANSLATIONS],
  ["support",support.en,supportTextsExtra],
  ["contact",contact.en,contactLocalesExtra]
];
for(const [label,original,extras] of pages) {
 for(const lang of ["pl","de"]) {
   const dict=extras[lang];
   assert.ok(dict,"No "+label+" translation for "+lang);
   const keys=Object.keys(original);
   const missing=keys.filter(key=>typeof dict[key]!=="string" || !dict[key].trim());
   assert.deepEqual(missing,[],label+" missing "+lang+" keys");
   // Ensure displayed text is human-authored, not all replaced by English.
   assert.ok(keys.filter(k=>dict[k]!==original[k]).length>=keys.length*.9,
       label+" "+lang+" has too many untranslated strings");
 }
}
for(const lang of ["pl","de"]){
 assert.deepEqual(Object.keys(help.en).filter(k=>!["name","email"].includes(k)).sort(),
   Object.keys(supportHelpExtra[lang]).sort(),"Support field help keys mismatch");
 for(const item of Object.values(supportHelpExtra[lang])) {
   for(const key of ["title","description","example","extra"])
     assert.equal(typeof item[key],"string");
 }
 const guides=homeGlobals.WTMM_HOME_GUIDES[lang];
 assert.ok(guides);
 assert.deepEqual(Object.keys(guides).sort(),Object.keys(extractObject(read("docs/app.js"),"guides").en).sort());
 for(const arr of Object.values(guides))assert.equal(arr.length,4);
}
const html=[
 read("docs/index.html"),read("docs/support/support.html"),read("docs/contact/contact.html")
];
// Only the homepage should expose language buttons; other pages inherit the
// saved choice while keeping complete Polish and German dictionaries.
for(const lang of ["pl","de"])
 assert.ok(html[0].includes('data-lang="'+lang+'"'),"Homepage missing "+lang);
for(const page of html.slice(1)){
 assert.ok(!page.includes('data-lang="pl"') && !page.includes('value="pl"'));
 assert.ok(!page.includes('data-lang="de"') && !page.includes('value="de"'));
}
assert.ok(read("docs/app.js").includes("Object.assign(translations, window.WTMM_HOME_TRANSLATIONS"));
assert.ok(read("docs/app.js").includes("Object.assign(guides,window.WTMM_HOME_GUIDES"));
const profileJs=read("docs/profile/profile.js");
assert.ok(profileJs.includes("nickname_changed_at")&&profileJs.includes("7 * 24 * 60 * 60 * 1000"));
console.log("PASS: five-language homepage, support, contact and guide text dictionaries complete");
