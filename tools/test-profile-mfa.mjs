import assert from "node:assert/strict";
import { setupProfileMfa } from "../docs/js/profile-mfa.mjs";

// Simulate the live Supabase MFA API and DOM without touching real user accounts.
const ids = [
  "mfaBegin", "mfaCancel", "mfaSetup", "mfaQr", "mfaSecret",
  "mfaSetupCode", "mfaConfirm", "mfaChallenge", "mfaLoginCode",
  "mfaVerify", "mfaRemove", "mfaStatus", "mfaNotice"
];
const events = new Map();
const controls = Object.fromEntries(ids.map(id => [id, {
  hidden: id === "mfaSetup" || id === "mfaChallenge" || id === "mfaRemove",
  value: "", textContent: "", disabled: false, src: "",
  classList: { toggle() {} },
  addEventListener(event, fn) { events.set(id + ":" + event, fn); },
  removeAttribute(attr) { if (attr === "src") this.src = ""; }
}]));
const root = { getElementById(id) { return controls[id] ?? null; } };
let pagehide = null;
globalThis.window = {
  addEventListener(name, fn) { if (name === "pagehide") pagehide = fn; },
  confirm() { return true; }
};
let enrolled = false;
let assured = false;
let enrollCalls = 0, verifyCalls = 0, unEnrollCalls = 0;
const auth = {
  async getUser() { return { data: { user: { id:"sample", email:"a@example.test", is_anonymous: false } }, error:null }; },
  mfa: {
    async listFactors() { return { data:{ totp: enrolled ? [{id:"fac-1", status:"verified"}] : [] },error:null }; },
    async getAuthenticatorAssuranceLevel() {
      return { data:{currentLevel:assured ? "aal2" : "aal1", nextLevel:enrolled ? "aal2" : "aal1"},error:null };
    },
    async enroll() {
      enrollCalls++;
      return {data:{id:"fac-1",totp:{qr_code:"data:image/svg+xml;utf8,<svg></svg>",secret:"ONLY_IN_MEMORY"}},error:null};
    },
    async challenge({factorId}) { assert.equal(factorId,"fac-1"); return {data:{id:"c-1"},error:null}; },
    async verify({factorId,challengeId,code}) {
      assert.equal(factorId,"fac-1"); assert.equal(challengeId,"c-1"); assert.equal(code,"123456");
      verifyCalls++; enrolled = true; assured = true;
      return {data:{},error:null};
    },
    async unenroll({factorId}) { assert.equal(factorId,"fac-1"); unEnrollCalls++; enrolled=false; assured=false; return {data:{},error:null}; }
  }
};
const ui = setupProfileMfa(auth, root);
await ui.refresh();
assert.equal(controls.mfaBegin.hidden, false);
await events.get("mfaBegin:click")();
assert.equal(enrollCalls,1);
assert.equal(controls.mfaSetup.hidden,false);
assert.equal(controls.mfaSecret.textContent,"ONLY_IN_MEMORY");
controls.mfaSetupCode.value="123456";
await events.get("mfaConfirm:click")();
assert.equal(verifyCalls,1);
assert.equal(controls.mfaSetup.hidden,true);
assert.equal(controls.mfaSecret.textContent,"");
assert.equal(controls.mfaStatus.textContent,"Двухфакторная защита подключена.");

assured=false;
await ui.refresh();
assert.equal(controls.mfaChallenge.hidden,false);
assert.equal(controls.mfaRemove.hidden,true);
controls.mfaLoginCode.value="123456";
await events.get("mfaVerify:click")();
assert.equal(verifyCalls,2);
assert.equal(controls.mfaChallenge.hidden,true);
assert.equal(controls.mfaLoginCode.value,"");
assert.equal(controls.mfaRemove.hidden,false);
await events.get("mfaRemove:click")();
assert.equal(unEnrollCalls,1);
assert.equal(controls.mfaBegin.hidden,false);
assert.equal(controls.mfaStatus.textContent,"Двухфакторная защита ещё не подключена.");
assert.equal(typeof pagehide,"function");
pagehide();
assert.equal(controls.mfaSecret.textContent,"");
console.log("PASS: MFA setup, challenge, cleanup and reenrollment transitions");
