/**
 * One ZIP per invocation. pg_cron calls this once a minute with a Vault-only
 * internal token. Claims are atomic and globally serialized by PostgreSQL.
 * No public upload/approval path and no file execution.
 */
import { createClient } from "npm:@supabase/supabase-js@2.119.0";
import { inspectZip, ScanReject, MAX_ZIP_BYTES } from "./zip.ts";

const URL_BASE = Deno.env.get("SUPABASE_URL") ?? "";
function serverKey() {
  try {
    const fromBundle=JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") || "{}")?.default;
    if(typeof fromBundle==="string" && fromBundle.length>15) return fromBundle;
  } catch { /* legacy key */ }
  return Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
}
const KEY=serverKey();
if (!URL_BASE || !KEY) throw new Error("Server configuration is missing.");
const db=createClient(URL_BASE,KEY,{auth:{persistSession:false,autoRefreshToken:false}});
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
const STORAGE_PATH=/^[a-f0-9-]{36}\/[a-f0-9-]{36}\/[a-f0-9-]{36}\.zip$/i;
// Update on EVERY ZIP scanner rules change, invalidating earlier cache entries.
const SCANNER_VERSION="zip-20261119-r4";

function result(body:Record<string,unknown>,status=200) {
  return new Response(JSON.stringify(body),{
    status,headers:{"Content-Type":"application/json;charset=utf-8",
      "Cache-Control":"no-store","X-Content-Type-Options":"nosniff"}
  });
}
type Job={id:string,file_path:string,started_at:string};
Deno.serve(async req=>{
  if(req.method!=="POST") return result({error:"method_not_allowed"},405);
  // Supabase Edge gateway has verify_jwt=false only because cron uses a
  // separate randomly generated Vault secret, not a client-accessible key.
  const provided=req.headers.get("x-wtmm-internal-token") ?? "";
  if(!/^[a-f0-9]{64}$/.test(provided)) return result({error:"forbidden"},403);
  const {data:authorized,error:authError}=await db.rpc("wtmm_scan_authorized",
    {p_token:provided});
  if(authError || authorized!==true) return result({error:"forbidden"},403);

  const {data,error}=await db.rpc("wtmm_scan_claim");
  if(error) return result({error:"queue_unavailable"},503);
  if(!data) return result({processed:0,reason:"idle"});
  const job=data as Job;
  if(!UUID.test(job.id) || !STORAGE_PATH.test(job.file_path) ||
      typeof job.started_at!=="string")
    return result({error:"invalid_queue_record"},503);

  let stage:"checked"|"review"|"blocked"|"error"="error";
  let note="Temporary scanner error";
  let sha256:string|null=null;
  let files:number|null=null;
  try {
    const {data:file,error:storageError}=await db.storage
      .from("wtmm-mod-packages").download(job.file_path);
    if(storageError || !file) throw new Error("Storage unavailable");
    if(file.size<=0 || file.size>MAX_ZIP_BYTES)
      throw new ScanReject("ZIP превышает лимит 20 МБ");
    const raw=new Uint8Array(await file.arrayBuffer());
    const hashed=await crypto.subtle.digest("SHA-256",new Uint8Array(raw).buffer);
    sha256=Array.from(new Uint8Array(hashed),n=>n.toString(16).padStart(2,"0")).join("");
    // Cached result is for identical bytes and *this exact* scan ruleset.
    // It is never an antivirus clearance or automatic publishing permission.
    const {data:cached,error:cacheError}=await db.rpc("wtmm_scan_cache_get",{
      p_sha256:sha256,p_engine_version:SCANNER_VERSION
    });
    if(!cacheError && cached &&
      (cached.verdict==="checked" || cached.verdict==="review") &&
      Number.isSafeInteger(cached.files) && cached.files>0 && cached.files<=250 &&
      typeof cached.note==="string" && cached.note.length<=180
    ) {
      stage=cached.verdict; files=cached.files;
      note=cached.note;
    } else {
      const report=await inspectZip(raw);
      if(report.sha256!==sha256) throw new Error("Scan hash mismatch");
      files=report.files;
      stage=report.verdict;
      note=stage==="review"
        ? "Структура ZIP и CRC верны, нужна дополнительная проверка: " +
          report.reviewReasons.slice(0,2).join("; ").slice(0,110)
        : "Структура ZIP и CRC проверены. Требуется ручная модерация.";
      // Cache only completed structural checks; scanner errors and malware
      // investigations are never cached as "safe".
      await db.rpc("wtmm_scan_cache_put",{
        p_sha256:sha256,p_engine_version:SCANNER_VERSION,
        p_verdict:stage,p_files:files,p_note:note
      });
    }
  } catch(e) {
    if(e instanceof ScanReject) {
      stage="blocked"; note=e.message.slice(0,160);
    } else {
      // Infrastructure failures are retried. Never expose storage credentials,
      // raw URLs, paths or detailed exceptions to clients.
      stage="error"; note="Temporary scanner error";
    }
  }
  const {data:finished,error:finishError}=await db.rpc("wtmm_scan_finish",{
    p_id:job.id,p_started_at:job.started_at,p_state:stage,
    p_note:note,p_sha256:sha256,p_file_count:files
  });
  if(finishError || finished!==true)
    return result({error:"completion_unavailable"},503);
  return result({processed:1,status:stage});
});
