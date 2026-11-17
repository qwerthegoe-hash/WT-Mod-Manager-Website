// Shared profile-backed contact client: browsers never supply sender identity.
// The Edge Function re-reads user/profile from Supabase and is authoritative.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.119.0";
import { COMMUNITY_CONFIG } from "./community-config.js";
import { ensureAuthenticatedUser } from "./supabase-session.mjs";

let instancePromise = null;

async function createBridge() {
  if (!COMMUNITY_CONFIG.supabaseUrl || !COMMUNITY_CONFIG.supabasePublishableKey)
    throw new Error("CONTACT_NOT_CONFIGURED");
  const db = createClient(COMMUNITY_CONFIG.supabaseUrl, COMMUNITY_CONFIG.supabasePublishableKey);
  const user = await ensureAuthenticatedUser(db);
  const {data:profile,error} = await db.from("community_user_profiles")
    .select("nickname").eq("user_id",user.id).maybeSingle();
  if(error) throw error;
  const nickname = typeof profile?.nickname === "string" ? profile.nickname.trim() : "";
  if(nickname.length < 2) throw new Error("PROFILE_REQUIRED");
  const verifiedEmail = user.email_confirmed_at && !user.is_anonymous ? (user.email || "") : "";
  return {
    nickname,
    hasReplyEmail: Boolean(verifiedEmail),
    async send(payload) {
      // No nickname / email / user ID is sent: even a modified browser cannot
      // impersonate another account through this application's API.
      const {data,error} = await db.functions.invoke("contact-message", {
        body: {...payload,consent:true}
      });
      if(error) {
        if(error.context?.status === 429) throw new Error("RATE_LIMIT");
        if(error.context?.status === 403) throw new Error("PROFILE_REQUIRED");
        throw new Error("DELIVERY_FAILED");
      }
      if(!data?.ok) throw new Error("DELIVERY_FAILED");
      return data;
    }
  };
}

export async function getContactBridge() {
  if(!instancePromise) instancePromise = createBridge().catch(error => {
    instancePromise = null;
    throw error;
  });
  return instancePromise;
}
