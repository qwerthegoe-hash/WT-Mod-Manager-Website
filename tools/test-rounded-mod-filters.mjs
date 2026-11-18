import assert from "node:assert/strict";
import fs from "node:fs";
import { upgradeModFilterSelects,nextFilterIndex } from "../docs/mods/rounded-filters.mjs";

const read=p=>fs.readFileSync(new URL("../"+p,import.meta.url),"utf8");
const html=read("docs/mods/mods.html");
const js=read("docs/mods/mods.js");
const css=read("docs/mods/rounded-filters.css");
const modCss=read("docs/mods/mods.css");
const language=read("docs/js/site-language.mjs");
assert.ok(html.includes('href="rounded-filters.css"'),"Must load custom style sheet");
assert.ok(js.includes('import { upgradeModFilterSelects } from "./rounded-filters.mjs"'));
assert.ok(js.includes("    upgradeModFilterSelects();"),"Must initialize on mods page");
assert.ok(css.includes(".mods-select-menu[hidden]"),"Closed menus must not show");
assert.ok(css.includes("border-radius: 15px"),"Opened menu must have rounded corners");
assert.ok(css.includes(".mods-select-option.is-selected"),"Selected value needs distinct style");
const menuStyles = css.match(/\.mods-select-menu\s*\{([^}]+)\}/)?.[1] || "";
assert.match(menuStyles,/display:\s*flex\s*;/,"Dropdown menu must lay out options in a vertical stack");
assert.match(menuStyles,/flex-direction:\s*column\s*;/,"Dropdown options must stack vertically");
assert.match(menuStyles,/gap:\s*12px\s*;/,"Dropdown options must have 12px of breathing room");
assert.match(menuStyles,/padding:\s*10px\s*;/,"Dropdown needs comfortable inner padding");
assert.ok(css.includes("flex: 0 0 auto;"),"Items must not collapse when dropdown scrolls");
assert.match(html,/<input id="modsFavoritesOnly" type="checkbox" role="switch">/,"Favorites filter must remain an accessible checkbox switch");
assert.ok(modCss.includes(".mods-favorites-switch input:checked + .mods-switch-track"),"Favorites switch needs a checked state");
assert.ok(js.includes('p_favorites_only: $("modsFavoritesOnly").checked'),"Favorites switch must preserve server filtering");
assert.ok(html.includes('id="modsLoading" class="mods-loading"'),"Resource-loading indicator must be present");
assert.ok(js.includes('uiText("Загружаются ресурсы...")'),"Load state must be localized");
assert.ok(js.includes('loader.hidden = true'),"Load state must clear after refresh");
assert.ok(language.includes('["Загружаются ресурсы..."'),"Loading resources must have five-language translations");
assert.ok(language.includes('["Вкл", "On"'),"Switch state must have five-language translations");
assert.ok(!html.includes('class="mods-select-menu"'),"JS-enhanced menu must not appear without JS");
assert.ok(html.includes('id="modsCategory" aria-labelledby="modsCategoryLabel"'));
assert.ok(html.includes('id="modsSort" aria-labelledby="modsSortLabel"'));
assert.ok(html.includes('name="category" required'),"Upload form remains native and unchanged");
assert.equal(nextFilterIndex(0,"ArrowDown",5),1);
assert.equal(nextFilterIndex(0,"ArrowUp",5),4);
assert.equal(nextFilterIndex(3,"Home",5),0);
assert.equal(nextFilterIndex(1,"End",5),4);

class Element {
  constructor(tag){
    this.tagName=tag.toUpperCase();this.children=[];this.parentElement=null;this.dataset={};
    this.attributes={};this.listeners={};this.id="";this.type="";this.value="";
    this.hidden=false;this.disabled=false;this.tabIndex=0;this.textContent="";
    this.selectedOptions=[];
    this.classes=new Set();
    this.classList={
      add:(...items)=>items.forEach(x=>this.classes.add(x)),
      remove:(...items)=>items.forEach(x=>this.classes.delete(x)),
      toggle:(item,on)=>{if(on===false)this.classes.delete(item);else this.classes.add(item);return this.classes.has(item);}
    };
  }
  set className(text){this.classes=new Set(String(text).split(/\s+/).filter(Boolean));}
  get className(){return [...this.classes].join(" ");}
  setAttribute(k,v){this.attributes[k]=String(v);}
  getAttribute(k){return this.attributes[k]??null;}
  append(...nodes){for(const node of nodes){node.parentElement=this;this.children.push(node);}}
  replaceChildren(...nodes){this.children=[];this.append(...nodes);}
  contains(node){for(let current=node;current;current=current.parentElement)if(current===this)return true;return false;}
  addEventListener(type,callback){(this.listeners[type]??=[]).push(callback);}
  dispatchEvent(event){for(const cb of this.listeners[event.type]||[])cb(event);}
  fire(type,props={}){this.dispatchEvent({type,preventDefault(){this.prevented=true;},key:props.key,target:props.target||this});}
  focus(){globalThis.document.activeElement=this;}
  scrollIntoView(){}
  querySelector(selector){if(selector==="span[id]")return this.children.find(n=>n.tagName==="SPAN"&&n.id)||null;return null;}
}
function makeSelect(id,labels,values){
 const field=new Element("div");
 const label=new Element("span");label.id=id+"Label";label.textContent=id==="modsCategory"?"Категория":"Сортировка";
 const select=new Element("select");select.id=id;
 select.options=values.map((value,i)=>({value,textContent:labels[i],disabled:false}));
 select.value=values[0];
 Object.defineProperty(select,"selectedOptions",{get(){return select.options.filter(x=>x.value===select.value).slice(0,1);}});
 field.append(label,select);
 return {field,select};
}
const category=makeSelect("modsCategory",["Все категории","Графика и эффекты","Камуфляжи","Звуки"],["all","visuals","camouflage","sounds"]);
const sort=makeSelect("modsSort",["Сначала новые","Сначала старые","По названию","По популярности","По соответствию"],["new","old","name","popular","relevance"]);
const controls={modsCategory:category.select,modsSort:sort.select};
const doc=new Element("document");
doc.getElementById=id=>controls[id]||null;
doc.createElement=tag=>new Element(tag);
const win=new Element("window");
globalThis.document=doc;globalThis.window=win;
globalThis.MutationObserver=class{observe(){}};
let categoryChanges=0;let sortChanges=0;
category.select.addEventListener("change",()=>categoryChanges++);
sort.select.addEventListener("change",()=>sortChanges++);
upgradeModFilterSelects();
upgradeModFilterSelects(); // should be idempotent
for(const field of [category.field,sort.field]){
 assert.equal(field.children.length,3,"Native select and exactly one enhanced control");
}
assert.equal(category.select.tabIndex,-1);
assert.equal(category.select.getAttribute("aria-hidden"),"true");
assert.equal(category.select.dataset.roundedFilterReady,"true");
const categoryRoot=category.field.children[2];
const sortRoot=sort.field.children[2];
const categoryTrigger=categoryRoot.children[0];
const categoryMenu=categoryRoot.children[1];
const sortTrigger=sortRoot.children[0];
const sortMenu=sortRoot.children[1];
assert.equal(categoryMenu.hidden,true);
categoryTrigger.fire("click");
assert.equal(categoryMenu.hidden,false);
assert.equal(categoryTrigger.getAttribute("aria-expanded"),"true");
assert.equal(categoryMenu.children.length,4);
categoryMenu.children[2].fire("click");
assert.equal(category.select.value,"camouflage");
assert.equal(categoryChanges,1,"Chosen custom option must fire native change");
assert.equal(categoryMenu.hidden,true);
assert.equal(categoryTrigger.children[0].textContent,"Камуфляжи");
assert.equal(categoryTrigger.getAttribute("aria-expanded"),"false");

sortTrigger.fire("click");
assert.equal(sortMenu.hidden,false);
assert.equal(sortMenu.children.length,5);
sortMenu.fire("keydown",{key:"End"});
assert.equal(doc.activeElement,sortMenu.children[4]);
sortMenu.fire("keydown",{key:"Enter"});
assert.equal(sort.select.value,"relevance");
assert.equal(sortChanges,1);
assert.equal(sortMenu.hidden,true);

sortTrigger.fire("keydown",{key:"ArrowUp"});
assert.equal(sortMenu.hidden,false);
assert.equal(doc.activeElement,sortMenu.children[3]);
sortMenu.fire("keydown",{key:"Escape"});
assert.equal(sortMenu.hidden,true);
assert.equal(doc.activeElement,sortTrigger);

sortTrigger.fire("click");
categoryTrigger.fire("click");
assert.equal(sortMenu.hidden,true,"Opening another dropdown must close the first");
assert.equal(categoryMenu.hidden,false);
doc.fire("pointerdown",{target:new Element("div")});
assert.equal(categoryMenu.hidden,true,"Clicking outside must close a dropdown");

assert.equal(category.select.value,"camouflage","A canceled dropdown must not change the selection");
assert.equal(categoryChanges,1);
assert.equal(sortChanges,1);
console.log("PASS: rounded native-compatible mod filters, option selection, keyboard, close outside and unchanged values");
