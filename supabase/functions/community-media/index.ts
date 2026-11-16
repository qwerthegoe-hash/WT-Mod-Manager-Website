// WT Mod Manager Community — secure photo review Edge Function.
// Server-side authorization and manual moderation; NOT an automatic malware scanner.
// Never place secret keys in the repository or frontend files.
import { createClient } from "npm:@supabase/supabase-js@2";

const PROJECT_URL = Deno.env.get("SUPABASE_URL") || "";
const MAX_BYTES = 5 * 1024 * 1024;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const MEDIA_PATH = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(jpg|png|webp|gif)$/i;
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-cleanup-token, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Max-Age": "600",
};
const response = (body: Record<string, unknown>, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });

function serverKey(): string {
  const keys = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (keys) {
    try {
      const candidate = JSON.parse(keys)?.default;
      if (typeof candidate === "string" && candidate.length > 15) return candidate;
    } catch {
      // Fall back only for legacy/self-hosted installations.
    }
  }
  return Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
}
const key = serverKey();
if (!PROJECT_URL || !key) {
  throw new Error("Missing Supabase server configuration");
}
const admin = createClient(PROJECT_URL, key, {
  auth: { persistSession: false, autoRefreshToken: false },
});

function imageType(path: string, bytes: Uint8Array): string | null {
  const extension = path.split(".").at(-1)?.toLowerCase();
  const signature = (...b: number[]) => b.every((v, i) => bytes[i] === v);
  const text = (from: number, length: number) =>
    String.fromCharCode(...bytes.subarray(from, from + length));
  if (extension === "jpg" && bytes.length >= 3 && signature(255, 216, 255))
    return "image/jpeg";
  if (extension === "png" && bytes.length >= 8 && signature(137, 80, 78, 71, 13, 10, 26, 10))
    return "image/png";
  if (extension === "gif" && bytes.length >= 6 &&
      (text(0, 6) === "GIF87a" || text(0, 6) === "GIF89a"))
    return "image/gif";
  if (extension === "webp" && bytes.length >= 12 &&
      text(0, 4) === "RIFF" && text(8, 4) === "WEBP")
    return "image/webp";
  return null;
}

async function cleanOldMedia(): Promise<number> {
  const expired = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const { data: jobs, error } = await admin.from("community_media_jobs")
    .select("id,pending_path,published_path,status")
    .lt("created_at", expired)
    .order("created_at", { ascending: true })
    .limit(100);
  if (error) throw error;
  let cleaned = 0;
  for (const job of jobs || []) {
    if (!UUID.test(String(job.id))) continue;
    if ((job.status === "pending" || job.status === "rejected") &&
        MEDIA_PATH.test(String(job.pending_path))) {
      const { error: removeError } = await admin.storage
        .from("community-pending").remove([job.pending_path]);
      if (removeError) continue;
      if (job.status === "pending") {
        const { error: updateError } = await admin.from("community_media_jobs")
          .update({ status: "rejected", reason: "Review expired", reviewed_at: new Date().toISOString() })
          .eq("id", job.id).eq("status", "pending");
        if (updateError) continue;
      }
      cleaned++;
    }
    // Approved media stays available to its owner until submitted in a message.
    // This prevents silently deleting a recently approved image.
  }
  return cleaned;
}

async function authenticatedAdmin(request: Request) {
  const bearer = request.headers.get("authorization")?.match(/^Bearer\s+(.+)$/i)?.[1];
  if (!bearer || !bearer.includes(".") || bearer.startsWith("sb_"))
    return { error: response({ error: "Необходим вход в чат" }, 401) };
  const { data, error } = await admin.auth.getUser(bearer);
  if (error || !data.user) return { error: response({ error: "Сессия недействительна" }, 401) };
  const { data: role, error: roleError } = await admin.from("community_admins")
    .select("user_id").eq("user_id", data.user.id).maybeSingle();
  if (roleError) throw roleError;
  if (!role) return { error: response({ error: "Только администратор" }, 403) };
  return { userId: data.user.id };
}

Deno.serve(async (request: Request) => {
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (request.method !== "POST") return response({ error: "Method not allowed" }, 405);

  try {
    if (!request.headers.get("content-type")?.toLowerCase().includes("application/json"))
      return response({ error: "Expected JSON" }, 415);
    const length = Number(request.headers.get("content-length") || 0);
    if (length > 8192) return response({ error: "Request too large" }, 413);

    const input: unknown = await request.json().catch(() => null);
    if (!input || typeof input !== "object" || Array.isArray(input))
      return response({ error: "Invalid JSON body" }, 400);
    const data = input as Record<string, unknown>;
    if (JSON.stringify(data).length > 8192) return response({ error: "Request too large" }, 413);
    const action = data.action;

    if (action === "cleanup") {
      const token = Deno.env.get("COMMUNITY_CLEANUP_TOKEN");
      if (!token || token.length < 24 ||
          request.headers.get("x-cleanup-token") !== token)
        return response({ error: "Unauthorized" }, 401);
      return response({ ok: true, cleaned: await cleanOldMedia() });
    }

    const session = await authenticatedAdmin(request);
    if ("error" in session) return session.error!;

    if (action === "list") {
      const { data: jobs, error } = await admin.from("community_media_jobs")
        .select("id,user_id,pending_path,created_at")
        .eq("status", "pending").order("created_at", { ascending: true }).limit(50);
      if (error) throw error;
      return response({ ok: true, jobs: jobs ?? [] });
    }

    const jobId = typeof data.jobId === "string" ? data.jobId : "";
    if (!UUID.test(jobId)) return response({ error: "Неверный ID заявки" }, 400);
    if (action !== "preview" && action !== "approve" && action !== "reject")
      return response({ error: "Unknown action" }, 400);

    const { data: job, error: jobError } = await admin.from("community_media_jobs")
      .select("id,pending_path,status")
      .eq("id", jobId).eq("status", "pending").maybeSingle();
    if (jobError) throw jobError;
    if (!job) return response({ error: "Заявка уже обработана или не найдена" }, 404);
    if (!MEDIA_PATH.test(String(job.pending_path)))
      return response({ error: "Некорректный путь файла" }, 400);

    if (action === "preview") {
      const { data: link, error } = await admin.storage.from("community-pending")
        .createSignedUrl(job.pending_path, 120);
      if (error || !link?.signedUrl) throw error ?? new Error("Signed URL unavailable");
      return response({ ok: true, url: link.signedUrl });
    }

    if (action === "reject") {
      const { data: updated, error } = await admin.from("community_media_jobs")
        .update({ status: "rejected", reason: "Rejected by moderator", reviewed_at: new Date().toISOString() })
        .eq("id", job.id).eq("status", "pending").select("id").maybeSingle();
      if (error) throw error;
      if (!updated) return response({ error: "Заявка уже обработана" }, 409);
      // Deletion errors are logged; rejection remains authoritative in the DB.
      const { error: removeError } = await admin.storage.from("community-pending")
        .remove([job.pending_path]);
      if (removeError) console.warn("Rejected file cleanup failed", removeError.message);
      return response({ ok: true, status: "rejected" });
    }

    // Human moderator must inspect the image before approval in the UI.
    // Magic bytes are a basic file-type check, NOT malware/content scanning.
    const { data: blob, error: downloadError } = await admin.storage
      .from("community-pending").download(job.pending_path);
    if (downloadError || !blob) return response({ error: "Файл не найден в карантине" }, 404);
    if (blob.size < 16 || blob.size > MAX_BYTES)
      return response({ error: "Недопустимый размер изображения" }, 400);
    const bytes = new Uint8Array(await blob.arrayBuffer());
    const mime = imageType(job.pending_path, bytes);
    if (!mime) return response({ error: "Формат файла не совпадает с его содержимым" }, 400);

    const { error: uploadError } = await admin.storage.from("community-media")
      .upload(job.pending_path, bytes, { contentType: mime, upsert: false });
    if (uploadError) {
      // Two moderators approving at once must not overwrite the same file.
      if (/already exists|duplicate|conflict/i.test(uploadError.message))
        return response({ error: "Файл уже обрабатывается" }, 409);
      throw uploadError;
    }
    const { data: updated, error: updateError } = await admin.from("community_media_jobs")
      .update({
        status: "approved", published_path: job.pending_path,
        reviewed_at: new Date().toISOString(), reason: null,
      })
      .eq("id", job.id).eq("status", "pending").select("id").maybeSingle();
    if (updateError || !updated) {
      await admin.storage.from("community-media").remove([job.pending_path]);
      if (updateError) throw updateError;
      return response({ error: "Заявка уже обработана" }, 409);
    }
    const { error: removeError } = await admin.storage.from("community-pending")
      .remove([job.pending_path]);
    if (removeError) console.warn("Approved file cleanup failed", removeError.message);
    return response({ ok: true, status: "approved", publishedPath: job.pending_path });
  } catch (error) {
    console.error("community-media:", error instanceof Error ? error.message : String(error));
    return response({ error: "Ошибка модерации на сервере" }, 500);
  }
});
