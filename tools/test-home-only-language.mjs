import assert from "node:assert/strict";
import fs from "node:fs";
import {
  readSiteLanguage, siteLanguage, siteLocale, uiText, setupSiteLanguage
} from "../docs/js/site-language.mjs";

const load = p => fs.readFileSync(new URL("../"+p,import.meta.url),"utf8");
const home = load("docs/index.html");
const internal = [
  "profile/profile", "mods/mods", "community/community",
  "creator/creator", "support/support", "contact/contact"
];
assert.ok(home.includes('id="languageToggle"') && home.includes('id="languageMenu"'));
for(const lang of ["en","ru","uk","pl","de"])
  assert.ok(home.includes('data-lang="'+lang+'"'),"Homepage missing "+lang);
for(const route of internal) {
  const html = load("docs/"+route+".html");
  assert.ok(!/\b(?:id="(?:languageToggle|supportLanguageToggle|contactLanguage)"|class="lang-wrap"|data-lang="(?:en|ru|uk|pl|de)")/.test(html),
    "Secondary page has a language selector: "+route);
}
for(const route of ["profile/profile","mods/mods","community/community","creator/creator"]){
 const js=load("docs/"+route+".js");
 assert.ok(js.includes('from "../js/site-language.mjs"') && js.includes("setupSiteLanguage()"),
   "Internal page missing centralized language reader: "+route);
}
for(const route of ["support/support","contact/contact"]){
 const js=load("docs/"+route+".js");
 assert.ok(js.includes('localStorage.getItem("wtmm-language"') ||
           js.includes('localStorage.getItem(\n            "wtmm-language"'),
   "Page must read selected homepage language: "+route);
 assert.ok(!js.includes('localStorage.setItem("wtmm-language"'),
   "Secondary page must not change homepage preference: "+route);
 assert.ok(js.includes('event.key === "wtmm-language"'),
   "Secondary page must update after homepage selection: "+route);
}
const map = {
 ru:["Главная","Мой профиль","Напиши сообщение..."],
 uk:["Головна","Мій профіль","Напиши повідомлення..."],
 en:["Home","My profile","Write a message..."],
 pl:["Strona główna","Mój profil","Napisz wiadomość..."],
 de:["Startseite","Mein Profil","Nachricht schreiben..."]
};
for(const [lang, expected] of Object.entries(map))
  assert.deepEqual(["Главная","Мой профиль","Напиши сообщение..."].map(k=>uiText(k,lang)),expected);
assert.equal(uiText("AnOriginalUserNickname","de"),"AnOriginalUserNickname");
assert.equal(uiText("MyCustomModName","pl"),"MyCustomModName");

// Simulate DOM translations and a previously translated node being replaced
// with a user-created nickname. A regression here corrupts visible user data.
globalThis.Node={ELEMENT_NODE:1,TEXT_NODE:3,DOCUMENT_NODE:9};
globalThis.NodeFilter={SHOW_ELEMENT:1,SHOW_TEXT:4};
class Element {
  constructor(tag,id="",className="") {
    this.nodeType=1;this.tagName=tag.toUpperCase();this.id=id;
    this.classes=new Set(className.split(/\s+/).filter(Boolean));
    this.children=[];this.parentElement=null;this.attributes={};this.dataset={};
  }
  append(child){child.parentElement=this;this.children.push(child);return child;}
  closest(selectors) {
    for(let current=this;current;current=current.parentElement){
      for(const selector of selectors.split(",")){
        const part=selector.trim();
        if(part.startsWith("#") && current.id===part.slice(1))return current;
        if(part.startsWith(".") && !part.includes(" ") && current.classes.has(part.slice(1)))return current;
        if(!part.includes(" ") && part===current.tagName.toLowerCase())return current;
        if(part===".mod-card h3" && current.tagName==="H3" &&
           current.parentElement?.classes.has("mod-card"))return current;
      }
    }
    return null;
  }
  getAttribute(name){return this.attributes[name]??null;}
  setAttribute(name,value){this.attributes[name]=String(value);}
}
class Text {
  constructor(value){this.nodeType=3;this.nodeValue=value;this.parentElement=null;}
}
const body=new Element("body");
const label=body.append(new Element("h2"));
const labelText=label.append(new Text("Библиотека модов"));
const chat=body.append(new Element("div","messages"));
const chatText=chat.append(new Text("Главная")); // user message; must never change
const mod=body.append(new Element("article","","mod-card"));
const modTitle=mod.append(new Element("h3"));
const modText=modTitle.append(new Text("Библиотека модов")); // user mod title
const input=body.append(new Element("input"));
input.setAttribute("placeholder","Название или автор");

const listeners={};let onMutation=null;
globalThis.MutationObserver=class {
  constructor(fn){onMutation=fn;}
  observe(){}
};
globalThis.window={addEventListener(name,fn){listeners[name]=fn;}};
let selected="pl";
globalThis.localStorage={getItem(key){return key==="wtmm-language"?selected:null;}};
Object.defineProperty(globalThis,"navigator",{value:{language:"en-US"},configurable:true});
globalThis.document={
  body, title:"Библиотека модов — WT Mod Manager",documentElement:{lang:"ru"},
  createTreeWalker(root){
    const all=[];
    function walk(node){for(const child of node.children||[]){all.push(child);walk(child);}}
    walk(root);let i=0;return {nextNode(){return all[i++]||null;}};
  }
};
assert.equal(readSiteLanguage(),"pl");
setupSiteLanguage();
assert.equal(siteLanguage(),"pl");
assert.equal(siteLocale(),"pl-PL");
assert.equal(document.documentElement.lang,"pl");
assert.equal(labelText.nodeValue,"Biblioteka modów");
assert.equal(document.title,"Biblioteka modów — WT Mod Manager");
assert.equal(input.getAttribute("placeholder"),"Nazwa lub autor");
assert.equal(chatText.nodeValue,"Главная");
assert.equal(modText.nodeValue,"Библиотека модов");
selected="de";listeners.storage({key:"wtmm-language"});
assert.equal(labelText.nodeValue,"Mod-Bibliothek");
assert.equal(document.title,"Mod-Bibliothek — WT Mod Manager");
assert.equal(input.getAttribute("placeholder"),"Titel oder Autor");
assert.equal(chatText.nodeValue,"Главная");
labelText.nodeValue="PrivateNickFromDatabase";
onMutation([{type:"characterData",target:labelText,addedNodes:[]}]);
assert.equal(labelText.nodeValue,"PrivateNickFromDatabase",
  "Translation must never overwrite nickname created by application");
assert.equal(modText.nodeValue,"Библиотека модов");
console.log("PASS: only homepage selects language, all internal routes follow five-language preference, user content preserved");
