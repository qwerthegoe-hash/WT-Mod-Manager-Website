import assert from "node:assert/strict";
import fs from "node:fs";
import { normalizeContactTopic, validateContact } from "../docs/contact/contact-core.mjs";
import { contactLocalesExtra } from "../docs/contact/contact-extra-i18n.mjs";
const get = path => fs.readFileSync(new URL("../" + path,import.meta.url),"utf8");
const html = get("docs/contact/contact.html");
const support = get("docs/support/support.html");
const home = get("docs/index.html");
const script = get("docs/contact/contact.js");

assert.ok(home.includes('href="contact/contact.html"'),"Homepage must open own contact page");
assert.ok(support.includes('href="../contact/contact.html"'),"Support must link contact");
assert.ok(!html.includes('id="contactName"') && !html.includes('id="contactEmail"'));
assert.ok(!support.includes('id="visitorName"') && !support.includes('id="visitorEmail"'));
assert.ok(!support.includes('id="developerContact"') && !support.includes('<span class="pulse"></span>'));
assert.ok(!html.includes('id="contactEmailFallback"'));
assert.ok(script.includes('getContactBridge') && script.includes('bridge.send('));
assert.ok(!script.includes('https://formspree.io/f/'));
assert.ok(html.includes('value="pl"') && html.includes('value="de"'));
assert.equal(normalizeContactTopic("cooperation"),"cooperation");
assert.equal(normalizeContactTopic("bad"),"question");
const valid = {title:"Developer question",message:"Here is my original question for the developer.",
  reply:"none",reference:"",consent:true,website:""};
assert.equal(validateContact(valid),"valid");
assert.equal(validateContact({...valid,consent:false}),"invalid");
assert.equal(validateContact({...valid,title:"a"}),"invalid");
assert.equal(validateContact({...valid,message:"x"}),"invalid");
assert.equal(validateContact({...valid,reference:"javascript:alert(1)"}),"invalid");
assert.equal(validateContact({...valid,website:"bot"}),"honeypot");

const controls={};const events=new Map();
function el(id=""){
 return {id,hidden:false,disabled:false,value:"",checked:false,dataset:{},placeholder:"",
 textContent:"",href:"",classList:{toggle(){}},attributes:{},
 addEventListener(type,cb){events.set(id+":"+type,cb);},
 setAttribute(k,v){this.attributes[k]=v;},removeAttribute(k){delete this.attributes[k];},
 querySelector(sel){if(sel==='option[value="email"]') return controls.replyEmailOption;
 if(sel==='[data-t=send]') return controls.sendLabel;return null;},
 append(){},focus(){this.focused=true;},replaceChildren(){},reportValidity(){},
 checkValidity(){return true;},
 reset(){["contactTitle","contactMessage","contactReference"].forEach(k=>controls[k].value="");
 controls.contactReply.value="email";controls.contactConsent.checked=false;}}
}
for(const [,id] of html.matchAll(/\bid="([^"]+)"/g)) controls[id]=el(id);
controls.replyEmailOption=el("reply-option");
controls.sendLabel=el("send-label");
controls.contactReply.value="email";
controls.contactForm.hidden=false;
controls.contactSuccess.hidden=true;
const topics=["question","cooperation","feedback","other"].map(topic=>{const e=el("topic-"+topic);e.dataset.topic=topic;return e;});
globalThis.document={documentElement:{lang:""},getElementById:id=>controls[id]||null,
 querySelectorAll:s=>s==="[data-topic]"?topics:[],
 createTextNode:text=>({textContent:text}),createElement:()=>el()};
globalThis.window={location:{origin:"http://localhost:5500",pathname:"/docs/contact/contact.html"}};
Object.defineProperty(globalThis,"navigator",{configurable:true,value:{language:"ru"}});
globalThis.localStorage={getItem:()=> "ru",setItem(){}};
globalThis.contactLocalesExtra=contactLocalesExtra;
globalThis.normalizeContactTopic=normalizeContactTopic;
globalThis.validateContact=validateContact;
let sent=null;let shouldFail=false;
globalThis.getContactBridge=async()=>({
 nickname:"TestPlayer",hasReplyEmail:false,
 async send(payload){sent=payload;if(shouldFail)throw new Error("RATE_LIMIT");return {ok:true};}
});
const stubbed=script.replace(/^import\s+[^\n]+\n/gm,"");
await import("data:text/javascript;base64,"+Buffer.from(stubbed).toString("base64"));
await new Promise(resolve=>setImmediate(resolve));
assert.equal(controls.contactSubmit.disabled,false);
assert.equal(controls.contactIdentityNotice.textContent,"Отправитель из профиля: TestPlayer");
assert.equal(controls.contactReply.value,"none");
events.get("topic-cooperation:click")();
assert.equal(controls.contactTopic.value,"cooperation");
controls.contactTitle.value="Collaboration question";
controls.contactMessage.value="I would like to talk about a collaboration.";
controls.contactConsent.checked=true;
await events.get("contactForm:submit")({preventDefault(){}});
assert.ok(sent);
assert.equal(sent.kind,"contact");
assert.equal(sent.topic,"cooperation");
assert.equal(sent.title,"Collaboration question");
assert.equal(sent.name,undefined);
assert.equal(sent.email,undefined);
assert.equal(controls.contactForm.hidden,true);
assert.equal(controls.contactSuccess.hidden,false);
events.get("contactAgain:click")();
controls.contactTitle.value="Another message";
controls.contactMessage.value="This is a second meaningful message for the developer.";
controls.contactConsent.checked=true;
shouldFail=true;
const realNow=Date.now;
Date.now=()=>realNow()+70000;
try { await events.get("contactForm:submit")({preventDefault(){}}); }
finally {Date.now=realNow;}
assert.equal(controls.contactForm.hidden,false);
assert.equal(controls.contactSuccess.hidden,true);
assert.equal(controls.contactMessage.value,"This is a second meaningful message for the developer.");
assert.equal(controls.contactNotice.textContent,"Слишком много обращений. Попробуй позже.");
console.log("PASS: contact sender from profile, message routing, 5 languages, success and failure retention");
