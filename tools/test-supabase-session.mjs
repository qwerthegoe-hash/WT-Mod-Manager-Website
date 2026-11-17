import assert from "node:assert/strict";
import { ensureAuthenticatedUser } from "../docs/js/supabase-session.mjs";

let anonCalls = 0, getUserCalls = 0;
const client = { auth: {
  getSession: async () => ({ data: { session: null }, error: null }),
  signInAnonymously: async () => { anonCalls++; return { error: null }; },
  getUser: async () => { getUserCalls++; return { data: { user: { id: "u1" } }, error: null }; }
}};
const [a,b] = await Promise.all([ensureAuthenticatedUser(client), ensureAuthenticatedUser(client)]);
assert.equal(a.id,"u1");
assert.equal(b.id,"u1");
assert.equal(anonCalls,1);
assert.equal(getUserCalls,1);
const currentSession = { auth: {
  getSession: async () => ({ data: { session: { access_token: "t" } }, error: null }),
  signInAnonymously: async () => { throw Error("Unexpected anonymous login"); },
  getUser: async () => ({ data: { user: { id: "u2" } }, error: null })
}};
assert.equal((await ensureAuthenticatedUser(currentSession)).id,"u2");
const failing = { auth: {
  getSession: async () => ({ data: null, error: new Error("Bad session") }),
  signInAnonymously: async () => ({ error: null }),
  getUser: async () => ({ data: { user: { id: "u1" } }, error: null })
}};
await assert.rejects(() => ensureAuthenticatedUser(failing), /Bad session/);
console.log("PASS: verified Supabase sessions, anonymous access and race safety");
