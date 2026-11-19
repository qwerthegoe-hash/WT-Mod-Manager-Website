// Shared WT Mod Manager VirusTotal proxy.
// The user's personal VirusTotal key is held only in encrypted Supabase Vault.
// A registered, paired desktop device is required; this is NEVER a public proxy.
// Only a SHA-256 digest is sent to VirusTotal. No sample uploads or secrets in replies.
import { createClient } from "npm:@supabase/supabase-js@2.119.0";

const ORIGIN = "https://qwerthegoe-hash.github.io";
const HASH = /^[0-9a-f]{64}$/;
const TOKEN = /^[A-Za-z0-9_-]{40,80}$/;
const URL = Deno.env.get("SUPABASE_URL") || "";
function serverKey(): string {
  try {
    const value = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") || "{}")?.default;
    if (typeof value === "string" && value.length > 15) return value;
  } catch { /* Backward-compatible legacy fallback. */ }
  return Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
}
const secret = serverKey();
if (!URL || !secret) throw new Error("Internal server configuration missing");
const db = createClient(URL, secret, {
  auth: {persistSession: false, autoRefreshToken: false},
});

function headers(origin: string | null): HeadersInit {
  return {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Vary": "Origin",
    ...(origin === ORIGIN ? {"Access-Control-Allow-Origin": ORIGIN} : {}),
    "Access-Control-Allow-Headers": "content-type,apikey",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
  };
}
function reply(body: Record<string, unknown>, status=200, origin: string | null=null) {
  return new Response(JSON.stringify(body), { status, headers: headers(origin) });
}
async function smallBody(req: Request): Promise<Record<string, unknown> | null> {
  if (!req.body) return null;
  const reader=req.body.getReader(); const chunks: Uint8Array[]=[]; let size=0;
  try {
    while (true) {
      const {done,value}=await reader.read(); if (done) break;
      size+=value.byteLength;
      if (size>2048) { await reader.cancel(); return null; }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const merged = new Uint8Array(size); let offset=0;
  for (const x of chunks) {merged.set(x,offset); offset+=x.length;}
  try {
    const obj=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(merged));
    return obj && typeof obj==="object" && !Array.isArray(obj) ? obj : null;
  } catch {return null;}
}
async function digestToken(token: string): Promise<string> {
  const data=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(token));
  return Array.from(new Uint8Array(data),x=>x.toString(16).padStart(2,"0")).join("");
}
function count(value: unknown): number {
  return typeof value==="number" && Number.isSafeInteger(value) && value>=0 ? value : 0;
}
Deno.serve(async req => {
  const origin=req.headers.get("origin");
  if (origin && origin!==ORIGIN) return reply({error:"origin_forbidden"},403,origin);
  if (req.method==="OPTIONS") return new Response(null,{status:204,headers:headers(origin)});
  if (req.method!=="POST") return reply({error:"method_not_allowed"},405,origin);
  try {
    const body=await smallBody(req);
    if (!body || typeof body.sha256!=="string" || !HASH.test(body.sha256) ||
        typeof body.device_token!=="string" || !TOKEN.test(body.device_token))
      return reply({error:"invalid_input"},400,origin);

    const tokenHash=await digestToken(body.device_token);
    const {data:device,error:deviceError}=await db.from("wtmm_desktop_devices")
      .select("user_id,revoked_at")
      .eq("token_hash",tokenHash).maybeSingle();
    if (deviceError) return reply({error:"temporarily_unavailable"},503,origin);
    if (!device || device.revoked_at || !device.user_id)
      return reply({error:"account_not_linked"},401,origin);

    // The RPC is invoker-secured and granted ONLY to database service_role.
    // It atomically reserves one request under project-wide and per-user quotas.
    const {data:permit,error:permitError}=await db.rpc(
      "wtmm_vt_permit",{p_user_id:device.user_id}
    );
    if (permitError || !permit || typeof permit!=="object")
      return reply({error:"temporarily_unavailable"},503,origin);
    if (permit.ok!==true) {
      if (permit.error==="rate_limit")
        return reply({error:"rate_limit"},429,origin);
      return reply({error:"temporarily_unavailable"},503,origin);
    }
    const apiKey=permit.api_key;
    if (typeof apiKey!=="string" || !/^[a-zA-Z0-9_-]{32,128}$/.test(apiKey))
      return reply({error:"temporarily_unavailable"},503,origin);

    // User input is restricted to 64 lowercase SHA-256 hex characters.
    // Never request arbitrary URLs, use redirects, or upload files.
    const vt = await fetch("https://www.virustotal.com/api/v3/files/"+body.sha256,{
      method:"GET",
      headers:{"x-apikey":apiKey,"Accept":"application/json"},
      redirect:"error",
      signal:AbortSignal.timeout(12000)
    });
    if (vt.status===404) return reply({known:false,sha256:body.sha256},200,origin);
    if (vt.status===429) return reply({error:"rate_limit"},429,origin);
    if (vt.status===401 || vt.status===403)
      return reply({error:"vt_credentials_rejected"},503,origin);
    if (!vt.ok) return reply({error:"vt_unavailable"},503,origin);

    const raw=await vt.text();
    if (raw.length>1024*1024) return reply({error:"invalid_report"},502,origin);
    let parsed: unknown;
    try { parsed=JSON.parse(raw); } catch { return reply({error:"invalid_report"},502,origin); }
    const attrs=(parsed as {data?:{attributes?:{last_analysis_stats?:Record<string,unknown>}}})
      ?.data?.attributes?.last_analysis_stats;
    if (!attrs || typeof attrs!=="object")
      return reply({error:"invalid_report"},502,origin);

    return reply({
      known:true,
      sha256:body.sha256,
      malicious:count(attrs.malicious),
      suspicious:count(attrs.suspicious),
      harmless:count(attrs.harmless),
      undetected:count(attrs.undetected),
    },200,origin);
  } catch {
    // Deliberately omit request details/headers/secrets from logs and replies.
    return reply({error:"temporarily_unavailable"},503,origin);
  }
});
