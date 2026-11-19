// WT Mod Manager: account-scoped, explicit desktop transfer bridge.
// Never return service credentials or user JWTs to a Windows client.
import { createClient } from "npm:@supabase/supabase-js@2.119.0";

const URL_BASE = Deno.env.get("SUPABASE_URL") || "";
function serverKey(): string {
  const bundle = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (bundle) {
    try {
      const value = JSON.parse(bundle)?.default;
      if (typeof value === "string" && value.length > 15) return value;
    } catch { /* Legacy fallback */ }
  }
  return Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
}
const ADMIN_KEY = serverKey();
if (!URL_BASE || !ADMIN_KEY) throw new Error("Server configuration missing");
const admin = createClient(URL_BASE, ADMIN_KEY, {
  auth:{persistSession:false,autoRefreshToken:false}
});
const OFFICIAL_ORIGIN = "https://qwerthegoe-hash.github.io";
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const DEVICE_TOKEN=/^[A-Za-z0-9_-]{40,80}$/;
const PAIR_CODE=/^[0-9a-f]{36}$/;
const SUPPORTED=new Set(["sights","camouflage","sounds"]);

function cors(origin: string | null) {
  return {
    ...(origin===OFFICIAL_ORIGIN ? {"Access-Control-Allow-Origin":OFFICIAL_ORIGIN} : {}),
    "Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info",
    "Access-Control-Allow-Methods":"POST,OPTIONS",
    "Access-Control-Max-Age":"600",
    "Content-Type":"application/json; charset=utf-8",
    "Cache-Control":"no-store","X-Content-Type-Options":"nosniff",
    "Vary":"Origin"
  };
}
function result(body:Record<string,unknown>,status=200,origin:string|null=null) {
  return new Response(JSON.stringify(body),{status,headers:cors(origin)});
}
async function payload(req:Request) {
  if (!req.body) return null;
  const reader=req.body.getReader();const chunks:Uint8Array[]=[];let total=0;
  try{
    while(true){
      const {done,value}=await reader.read();if(done)break;
      total+=value.byteLength;
      if(total>4096){await reader.cancel();return null;}
      chunks.push(value);
    }
  }finally{reader.releaseLock();}
  const bytes=new Uint8Array(total);let offset=0;
  for(const part of chunks){bytes.set(part,offset);offset+=part.length;}
  try{
    const v=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
    return v && typeof v==="object" && !Array.isArray(v) ? v as Record<string,unknown>:null;
  }catch{return null;}
}
async function digest(text:string) {
  const hash=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(text));
  return Array.from(new Uint8Array(hash),n=>n.toString(16).padStart(2,"0")).join("");
}
function randomHex(length:number) {
  return Array.from(crypto.getRandomValues(new Uint8Array(length)),n=>n.toString(16).padStart(2,"0")).join("");
}
async function deviceFrom(body:Record<string,unknown>) {
  const token=body.device_token;
  if(typeof token!=="string" || !DEVICE_TOKEN.test(token))return null;
  const {data,error}=await admin.from("wtmm_desktop_devices")
    .select("id,user_id,revoked_at")
    .eq("token_hash",await digest(token)).maybeSingle();
  if(error || !data || data.revoked_at)return null;
  return data;
}
async function websiteUser(request:Request) {
  const jwt=request.headers.get("authorization")?.match(/^Bearer\s+([^\s]+)$/i)?.[1];
  if(!jwt || !jwt.includes(".") || jwt.startsWith("sb_"))return null;
  const {data,error}=await admin.auth.getUser(jwt);
  return !error && data?.user?.id ? data.user : null;
}
Deno.serve(async req=>{
  const origin=req.headers.get("origin");
  if(origin && origin!==OFFICIAL_ORIGIN)return result({error:"Origin not allowed"},403,origin);
  if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors(origin)});
  if(req.method!=="POST")return result({error:"Method not allowed"},405,origin);
  const body=await payload(req);
  if(!body)return result({error:"Invalid request"},400,origin);
  const action=body.action;
  try{
    if(action==="register"){
      // Device secret stays on the Windows machine; only its digest is stored.
      const token=body.device_token;
      if(typeof token!=="string"||!DEVICE_TOKEN.test(token))
        return result({error:"Invalid device token"},400,origin);
      const {count}=await admin.from("wtmm_desktop_devices")
        .select("id",{head:true,count:"exact"}).is("user_id",null)
        .gt("created_at",new Date(Date.now()-10*60*1000).toISOString());
      if((count||0)>1000)return result({error:"Pairing temporarily limited"},429,origin);
      const code=randomHex(18);
      const {data,error}=await admin.from("wtmm_desktop_devices").insert({
        token_hash:await digest(token),pair_code_hash:await digest(code),
        pair_expires_at:new Date(Date.now()+5*60*1000).toISOString()
      }).select("id").single();
      if(error || !data?.id)return result({error:"Pairing registration failed"},409,origin);
      return result({pair_id:data.id,pair_code:code,expires_in:300},200,origin);
    }
    if(action==="claim"){
      const user=await websiteUser(req);
      if(!user)return result({error:"Sign in to the website first"},401,origin);
      const id=String(body.pair_id||"");
      const code=String(body.pair_code||"");
      if(!UUID.test(id)||!PAIR_CODE.test(code))return result({error:"Invalid pairing code"},400,origin);
      const {data,error}=await admin.from("wtmm_desktop_devices")
        .update({user_id:user.id,pair_code_hash:null,pair_expires_at:null})
        .eq("id",id).eq("pair_code_hash",await digest(code))
        .gt("pair_expires_at",new Date().toISOString())
        .is("user_id",null).is("revoked_at",null)
        .select("id").maybeSingle();
      if(error || !data?.id)return result({error:"Pairing expired or already used"},409,origin);
      return result({paired:true},200,origin);
    }
    const device=await deviceFrom(body);
    if(!device)return result({error:"Device not recognized"},401,origin);
    if(action==="revoke"){
      await admin.from("wtmm_desktop_devices")
        .update({revoked_at:new Date().toISOString()}).eq("id",device.id);
      return result({revoked:true},200,origin);
    }
    if(!device.user_id)return result({paired:false},200,origin);
    if(action==="status"){
      return result({paired:true,user_id:device.user_id},200,origin);
    }
    if(action==="notifications"){
      const {data,error}=await admin.from("wtmm_notifications")
        .select("id,kind,title,body,url,created_at,read_at")
        .eq("user_id",device.user_id)
        .order("created_at",{ascending:false})
        .limit(60);
      if(error)throw error;
      return result({items:(data||[]).map(n=>({
        id:n.id,kind:n.kind,title:String(n.title||"").slice(0,120),
        body:String(n.body||"").slice(0,340),
        url:String(n.url||"").slice(0,180),
        created_at:n.created_at,read_at:n.read_at
      }))},200,origin);
    }
    if(action==="notifications_read"){
      const {error}=await admin.from("wtmm_notifications")
        .update({read_at:new Date().toISOString()})
        .eq("user_id",device.user_id)
        .is("read_at",null);
      if(error)throw error;
      return result({read:true},200,origin);
    }

    if(action==="catalog"){
      // Metadata only. No storage path or signed ZIP URL is disclosed here.
      // The user must explicitly download and request transfer on the site.
      const {data,error}=await admin.from("wtmm_mods")
        .select("id,title,category,version,game_version,description,created_at")
        .eq("status","approved")
        .order("created_at",{ascending:false})
        .limit(100);
      if(error)throw error;
      return result({user_id:device.user_id,items:(data||[]).map(mod=>({
        id:mod.id,title:mod.title,category:mod.category,version:mod.version,
        game_version:mod.game_version,
        description:String(mod.description||"").slice(0,180),
        created_at:mod.created_at
      }))},200,origin);
    }
    if(action==="poll"){
      const {data,error}=await admin.from("wtmm_app_transfer_queue")
        .select("id,mod_id,requested_at").eq("user_id",device.user_id)
        .eq("state","pending").order("requested_at",{ascending:true}).limit(10);
      if(error)throw error;
      const list=data||[];
      if(!list.length)return result({user_id:device.user_id,items:[]},200,origin);
      const {data:mods,error:modError}=await admin.from("wtmm_mods")
        .select("id,title,category,version,game_version,status")
        .in("id",list.map(x=>x.mod_id)).eq("status","approved");
      if(modError)throw modError;
      const index=new Map((mods||[]).map(mod=>[mod.id,mod]));
      return result({user_id:device.user_id,items:list
        .map(queue=>({transfer_id:queue.id,mod:index.get(queue.mod_id)}))
        .filter(item=>item.mod && SUPPORTED.has(item.mod.category))},200,origin);
    }
    if(action==="package" || action==="ack"){
      const transfer=String(body.transfer_id||"");
      if(!UUID.test(transfer))return result({error:"Invalid transfer"},400,origin);
      const {data:row,error}=await admin.from("wtmm_app_transfer_queue")
        .select("id,mod_id,state")
        .eq("id",transfer).eq("user_id",device.user_id).maybeSingle();
      if(error || !row || row.state!=="pending")
        return result({error:"Transfer not pending for this account"},409,origin);
      if(action==="ack"){
        const state=body.state;
        if(state!=="applied"&&state!=="failed")return result({error:"Invalid state"},400,origin);
        const message=state==="failed"?String(body.error||"").slice(0,200):null;
        const update=await admin.from("wtmm_app_transfer_queue")
          .update({state,processed_at:new Date().toISOString(),error_message:message})
          .eq("id",row.id).eq("user_id",device.user_id).eq("state","pending");
        if(update.error)throw update.error;
        return result({acknowledged:true},200,origin);
      }
      const {data:mod,error:modError}=await admin.from("wtmm_mods")
        .select("id,title,category,version,game_version,file_path,status")
        .eq("id",row.mod_id).eq("status","approved").maybeSingle();
      if(modError || !mod || !SUPPORTED.has(mod.category))
        return result({error:"Mod is unavailable or incompatible"},409,origin);
      const signed=await admin.storage.from("wtmm-mod-packages")
        .createSignedUrl(mod.file_path,90);
      if(signed.error || !signed.data?.signedUrl)
        return result({error:"Package temporarily unavailable"},503,origin);
      return result({mod_id:mod.id,title:mod.title,category:mod.category,
        version:mod.version,game_version:mod.game_version,
        signed_url:signed.data.signedUrl},200,origin);
    }
    return result({error:"Unknown action"},400,origin);
  }catch(err){
    console.error("Desktop bridge request failed:", err instanceof Error?err.name:"Unknown error");
    return result({error:"Server error"},500,origin);
  }
});
