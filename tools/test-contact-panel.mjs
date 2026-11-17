import assert from "node:assert/strict";
import fs from "node:fs";
import {
  normalizeContactTopic, validFormspreeId, validDeveloperEmail, validateContact
} from "../docs/contact/contact-core.mjs";

const html = fs.readFileSync(new URL("../docs/contact/contact.html",import.meta.url),"utf8");
const js = fs.readFileSync(new URL("../docs/contact/contact.js",import.meta.url),"utf8");
const home = fs.readFileSync(new URL("../docs/index.html",import.meta.url),"utf8");
const support = fs.readFileSync(new URL("../docs/support/support.html",import.meta.url),"utf8");
const css = fs.readFileSync(new URL("../docs/contact/contact.css",import.meta.url),"utf8");

assert.ok(home.includes('href="contact/contact.html"'), "Home must open dedicated contact");
assert.ok(support.includes('href="../contact/contact.html"'), "Support must link dedicated contact");
assert.ok(html.includes('type="module" src="contact.js"'), "Contact page must load its own JS module");
assert.ok(css.includes(".contact-layout") && css.includes("@media (max-width:670px)"),
  "Responsive contact layout required");
assert.ok(html.includes('name="_gotcha"'), "Include passive spam honeypot");
assert.ok(html.includes('id="contactConsent" required'), "Require consent");
assert.ok(js.includes("formspree.io/f/"), "Send via configured Formspree endpoint");
assert.ok(!js.includes("innerHTML"), "Do not interpolate user content as HTML");
assert.ok(!js.includes("sessionStorage"), "Do not persist personal drafts");

for(const l of ["ru: {","en: {","uk: {"]) assert.ok(js.includes(l), "Missing language "+l);
for(const id of ["contactName","contactEmail","contactTitle","contactMessage","contactTopic",
  "contactReply","contactReference","contactSubmit","contactForm","contactSuccess",
  "contactConsent","contactNotice"]) assert.ok(html.includes('id="'+id+'"'), "Missing form control "+id);

assert.equal(normalizeContactTopic("cooperation"), "cooperation");
assert.equal(normalizeContactTopic("javascript"), "question");
assert.equal(validFormspreeId("xoedeyva"),true);
assert.equal(validFormspreeId("hello/world"),false);
assert.equal(validDeveloperEmail("person@example.test"),true);
assert.equal(validDeveloperEmail("bad<>@example.test"),false);
const valid={
  website:"",name:"Player123",email:"player@example.test",title:"Question for developer",
  message:"Hello, I would like to ask a question about the program.",reference:"",
  reply:"email",consent:true
};
assert.equal(validateContact(valid),"valid");
assert.equal(validateContact({...valid,website:"spam.example"}),"honeypot");
assert.equal(validateContact({...valid,email:"not-an-email"}),"invalid");
assert.equal(validateContact({...valid,consent:false}),"invalid");
assert.equal(validateContact({...valid,message:"hi"}),"invalid");
assert.equal(validateContact({...valid,reference:"javascript:alert(1)"}),"invalid");
assert.equal(validateContact({...valid,email:"",reply:"none"}),"valid");

// Simulate browser and Formspree responses; never contact a real service.
const controls={};
const handlers=new Map();
function element(id="") {
  return {
    id, value:"", checked:false, hidden:false, disabled:false, dataset:{},
    placeholder:"", textContent:"", href:"", attributes:{},
    classList:{toggle(){}},
    addEventListener(type,fn){handlers.set(id+":"+type,fn);},
    setAttribute(key,value){this.attributes[key]=value;},
    removeAttribute(key){delete this.attributes[key];},
    querySelector(){return controls.sendText;},
    reset(){ for(const key of ["contactName","contactEmail","contactTitle","contactMessage","contactReference"]) controls[key].value=""; controls.contactConsent.checked=false; controls.contactReply.value="email"; },
    checkValidity(){return true;},
    reportValidity(){},
    focus(){this.focused=true;},
    replaceChildren(){}
  };
}
for(const [,id] of html.matchAll(/\bid="([^"]+)"/g)) controls[id]=element(id);
controls.sendText=element("send-text");
controls.contactReply.value="email";
controls.contactLanguage.value="ru";
controls.contactForm.hidden=false;
controls.contactSuccess.hidden=true;
controls.contactSubmit.disabled=true;
const topics=["question","cooperation","feedback","other"].map(name=>{
  const el=element("topic-"+name);
  el.dataset.topic=name;
  return el;
});
globalThis.document={
  documentElement:{lang:""},
  getElementById(id){return controls[id]??null;},
  querySelectorAll(selector){
    if(selector==="[data-topic]")return topics;
    if(selector==="[data-t]" || selector==="[data-placeholder]")return [];
    return [];
  },
  querySelector(selector){
    if(selector==='label[for="contactEmail"]')return controls.emailLabel||(controls.emailLabel=element("email-label"));
    return null;
  },
  createTextNode(text){return {textContent:text};},
  createElement(){return element();}
};
globalThis.window={ location:{origin:"http://localhost:5500",pathname:"/docs/contact/contact.html"} };
Object.defineProperty(globalThis,"navigator",{configurable:true,value:{language:"ru"}});
globalThis.localStorage={getItem(){return "ru";},setItem(){}};
let outbound=null;
let shouldFail=false;
globalThis.fetch=async (url,options)=>{
  if(url==="../json/site-config.json")
    return {ok:true,json:async()=>({formspree_form_id:"xoedeyva",developer_email:"developer@example.test"})};
  assert.equal(url,"https://formspree.io/f/xoedeyva");
  assert.equal(options.method,"POST");
  assert.equal(options.headers.Accept,"application/json");
  outbound=options.body;
  if(shouldFail) throw new Error("simulated connection loss");
  return {ok:true};
};
globalThis.FormData=class {
  constructor(){this.data=new Map();}
  set(key,value){this.data.set(key,value);}
  delete(key){this.data.delete(key);}
  get(key){return this.data.get(key);}
};
await import("../docs/contact/contact.js");
await new Promise(resolve=>setImmediate(resolve));
assert.equal(controls.contactSubmit.disabled,false,"Configured service must enable submit");
assert.equal(controls.contactNotice.textContent,"Форма готова к отправке.");

handlers.get("topic-cooperation:click")();
assert.equal(controls.contactTopic.value,"cooperation");
assert.equal(topics[1].attributes["aria-pressed"],"true");
controls.contactName.value="Tester";
controls.contactEmail.value="tester@example.test";
controls.contactTitle.value="Potential collaboration";
controls.contactMessage.value="Hello, could we discuss a project collaboration?";
controls.contactConsent.checked=true;
await handlers.get("contactForm:submit")({preventDefault(){}});
assert.ok(outbound,"A valid form must POST to the configured service");
assert.equal(outbound.get("topic"),"cooperation");
assert.equal(outbound.get("title"),"Potential collaboration");
assert.equal(outbound.get("language"),"ru");
assert.equal(controls.contactForm.hidden,true);
assert.equal(controls.contactSuccess.hidden,false);

handlers.get("contactAgain:click")();
controls.contactName.value="Tester";
controls.contactEmail.value="tester@example.test";
controls.contactTitle.value="Another question";
controls.contactMessage.value="Hello, could I ask another question today?";
controls.contactConsent.checked=true;
shouldFail=true;
const oldNow=Date.now;
Date.now=()=>oldNow()+61000;
try { await handlers.get("contactForm:submit")({preventDefault(){}}); }
finally { Date.now=oldNow; }
assert.equal(controls.contactForm.hidden,false,"Failed send should retain editable form");
assert.equal(controls.contactSuccess.hidden,true,"Failed send must not show success");
assert.ok(controls.contactNotice.classList,"Error status must be visible");
assert.equal(controls.contactMessage.value,"Hello, could I ask another question today?");
assert.ok(!controls.contactEmailFallback.hidden,"An email fallback should be available when configured");
console.log("PASS: contact panel route, 3-language content, validation, successful send and error retention");
