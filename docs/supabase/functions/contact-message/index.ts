// WT Mod Manager contact delivery gateway.
// Authenticated Supabase accounts only. Sender nickname and email are read
// server-side. Never accept identity fields from an untrusted browser.
// Formspree form ID identifies the already configured developer inbox.
import { createClient } from "npm:@supabase/supabase-js@2.119.0";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
const KEYS = Deno.env.get("SUPABASE_SECRET_KEYS") || "";
const keyFromJson = (() => {
  try {
    const keys = JSON.parse(KEYS);
    return typeof keys.default === "string" ? keys.default : "";
  } catch { return ""; }
})();
const SUPABASE_ADMIN_KEY = keyFromJson || Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const FORMSPREE_ID = Deno.env.get("WTMM_FORMSPREE_FORM_ID") || "xoedeyva";
const MAX_BODY_BYTES = 12288;
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Max-Age": "600"
};
function reply(body: Record<string, unknown>, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type":"application/json; charset=utf-8",
      "Cache-Control":"no-store", "X-Content-Type-Options":"nosniff" }
  });
}
const admin = createClient(SUPABASE_URL, SUPABASE_ADMIN_KEY, {
  auth: {persistSession:false,autoRefreshToken:false}
});
async function readJsonLimited(request: Request): Promise<Record<string, unknown> | null> {
  if (!request.body) return null;
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = []; let size = 0;
  try {
    while(true) {
      const { done, value } = await reader.read();
      if(done) break;
      size += value.byteLength;
      if(size > MAX_BODY_BYTES) {
        await reader.cancel();
        throw new Error("REQUEST_TOO_LARGE");
      }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const all = new Uint8Array(size); let offset=0;
  for(const chunk of chunks) { all.set(chunk, offset); offset += chunk.length; }
  let parsed:unknown;
  try { parsed = JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(all)); }
  catch { return null; }
  return parsed && typeof parsed === "object" && !Array.isArray(parsed)
    ? parsed as Record<string, unknown> : null;
}
function textField(value: unknown, limit: number): string | null {
  return typeof value === "string" && value.length <= limit ? value.trim() : null;
}
function validReference(value: string): boolean {
  if (!value) return true;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {return false;}
}
function validPayload(body: Record<string,unknown>) {
  const kind = textField(body.kind, 16);
  const title = textField(body.title, 120);
  const message = textField(body.message, 5000);
  const details = textField(body.details ?? "", 2500);
  const version = textField(body.version ?? "", 40);
  const reference = textField(body.reference ?? "", 500);
  const replyPreference = body.reply === "none" ? "none" : "email";
  const topic = textField(body.topic ?? "question", 24);
  const lang = textField(body.language ?? "ru", 2);
  if (!kind || !["bug","idea","contact"].includes(kind) ||
      !title || title.length < 5 || !message || message.length < 15 ||
      details === null || version === null || reference === null ||
      !validReference(reference || "") ||
      !topic || !["question","cooperation","feedback","other"].includes(topic) ||
      !lang || !["en","ru","uk","pl","de"].includes(lang) ||
      body.consent !== true || (body.website && String(body.website).trim())) return null;
  return {kind,title,message,details,version,reference,replyPreference,topic,lang};
}
Deno.serve(async (request: Request) => {
  if(request.method === "OPTIONS") return new Response(null,{status:204,headers:cors});
  if(request.method !== "POST") return reply({error:"METHOD_NOT_ALLOWED"},405);
  try {
    if (!SUPABASE_URL || !SUPABASE_ADMIN_KEY || !/^[A-Za-z0-9]{4,30}$/.test(FORMSPREE_ID)) {
      return reply({error:"CONTACT_NOT_CONFIGURED"},503);
    }
    if(!request.headers.get("content-type")?.toLowerCase().includes("application/json")) {
      return reply({error:"INVALID_CONTENT_TYPE"},415);
    }
    const raw = request.headers.get("authorization")?.match(/^Bearer\s+(.+)$/i)?.[1];
    if(!raw || !raw.includes(".") || raw.startsWith("sb_")) {
      return reply({error:"AUTH_REQUIRED"},401);
    }
    const {data:authenticated,error:authError} = await admin.auth.getUser(raw);
    if(authError || !authenticated?.user?.id) {
      return reply({error:"AUTH_REQUIRED"},401);
    }
    const {data:profile,error:profileError} = await admin
      .from("community_user_profiles").select("nickname")
      .eq("user_id", authenticated.user.id).maybeSingle();
    if(profileError) throw new Error("PROFILE_LOOKUP_FAILED");
    const nickname = typeof profile?.nickname === "string" ? profile.nickname.trim() : "";
    if(nickname.length < 2 || nickname.length > 24) {
      return reply({error:"PROFILE_REQUIRED"},403);
    }
    const body = await readJsonLimited(request);
    if(!body) return reply({error:"INVALID_REQUEST"},400);
    const payload = validPayload(body);
    if(!payload) return reply({error:"INVALID_FIELDS"},400);

    // The DB trigger serializes requests per user and limits to four hourly
    // / fifteen daily. No browser IP or message contents are retained.
    const {error:rateError} = await admin.from("wtmm_contact_attempts")
      .insert({user_id: authenticated.user.id});
    if(rateError) {
      if(/CONTACT_RATE_LIMIT/i.test(rateError.message)) {
        return reply({error:"RATE_LIMIT"},429);
      }
      throw new Error("CONTACT_RATE_CHECK_FAILED");
    }
    const email = authenticated.user.email_confirmed_at &&
      !authenticated.user.is_anonymous ? authenticated.user.email || "" : "";

    // Save the support ticket under the verified account before contacting the
    // external email service. Only its owner and authorized moderators can read
    // private message content; the public browser cannot insert or forge tickets.
    const {data:ticket,error:ticketError}=await admin
      .from("wtmm_support_tickets")
      .insert({
        user_id:authenticated.user.id,kind:payload.kind,title:payload.title,
        message:payload.message,details:payload.details,
        reference_url:payload.reference,language:payload.lang,status:"sending"
      }).select("id").single();
    if(ticketError || !ticket?.id) {
      console.error("Support history creation failed",ticketError?.code || "missing-ticket");
      return reply({error:"TICKET_NOT_SAVED"},503);
    }
    const markDelivery=async(status:"received"|"delivery_failed")=>{
      const {error}=await admin.from("wtmm_support_tickets")
        .update({status,updated_at:new Date().toISOString()})
        .eq("id",ticket.id).eq("user_id",authenticated.user.id);
      if(error)console.error("Support ticket status update failed",error.code);
      return !error;
    };
    const data = new FormData();
    const typeLabels:Record<string,string> = {
      bug:"Bug report",idea:"Feature request",contact:"Developer contact"
    };
    data.set("_subject", "WT Mod Manager — " + typeLabels[payload.kind] + " — " + payload.title);
    data.set("ticket_id",ticket.id);
    data.set("request_type",typeLabels[payload.kind]);
    data.set("name",nickname);
    if(email) data.set("email",email);
    data.set("sender_nickname",nickname);
    data.set("sender_account_id",authenticated.user.id);
    data.set("account_email_verified",email ? "yes":"no");
    data.set("title",payload.title);
    data.set("message",payload.message);
    data.set("language",payload.lang);
    if(payload.kind === "contact") {
      data.set("topic",payload.topic);
      data.set("reply_preference",payload.replyPreference);
    } else {
      if(payload.version) data.set("version",payload.version);
      if(payload.details) data.set("steps_to_reproduce",payload.details);
    }
    if(payload.reference) data.set("reference_url",payload.reference);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch("https://formspree.io/f/" + FORMSPREE_ID, {
        method:"POST",body:data,signal:controller.signal,
        headers:{Accept:"application/json"}
      });
      if (!response.ok) {
        console.warn("Formspree rejected contact request, status",response.status);
        await markDelivery("delivery_failed");
        return reply({error:"DELIVERY_FAILED",ticket_id:ticket.id},502);
      }
      const historyUpdated=await markDelivery("received");
      // If delivery succeeded but status update failed, avoid sending a second
      // email on retry. Client sees success and history can be reconciled.
      return reply({ok:true,status:"accepted",ticket_id:ticket.id,
        history_updated:historyUpdated},200);
    } catch(error) {
      await markDelivery("delivery_failed");
      throw error;
    } finally { clearTimeout(timeout); }
  } catch(error) {
    if(error instanceof Error && error.message === "REQUEST_TOO_LARGE")
      return reply({error:"REQUEST_TOO_LARGE"},413);
    console.error("Contact gateway failed",error instanceof Error ? error.message : "unknown");
    return reply({error:"CONTACT_FAILED"},503);
  }
});
