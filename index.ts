// WTMM Community Media: human-review publication and scheduled cleanup.
// Deploy as Supabase Edge Function; NEVER put service role key in docs/.
import { createClient } from 'npm:@supabase/supabase-js@2';

const url = Deno.env.get('SUPABASE_URL')!;
const secret = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const admin = createClient(url, secret, { auth: { persistSession: false } });
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, apikey, content-type, x-cleanup-token',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};
const reply = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status, headers: { ...CORS, 'Content-Type': 'application/json' } });

function contentType(path: string, bytes: Uint8Array): string | null {
  const ext = path.split('.').at(-1);
  const eq = (...b: number[]) => b.every((x, i) => bytes[i] === x);
  const str = (start: number, length: number) =>
    String.fromCharCode(...bytes.slice(start, start + length));
  if (ext === 'jpg' && eq(255, 216, 255)) return 'image/jpeg';
  if (ext === 'png' && eq(137, 80, 78, 71, 13, 10, 26, 10)) return 'image/png';
  if (ext === 'gif' && ['GIF87a','GIF89a'].includes(str(0, 6))) return 'image/gif';
  if (ext === 'webp' && str(0, 4) === 'RIFF' && str(8, 4) === 'WEBP') return 'image/webp';
  return null;
}

async function cleanup() {
  const expired = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const { data: jobs, error } = await admin.from('community_media_jobs')
    .select('id,pending_path,published_path,status')
    .lt('created_at', expired).limit(100);
  if (error) throw error;
  let count = 0;
  for (const job of jobs ?? []) {
    if (job.status === 'pending' || job.status === 'rejected') {
      const { error: deleteError } = await admin.storage.from('community-pending').remove([job.pending_path]);
      if (deleteError) continue;
      if (job.status === 'pending') {
        await admin.from('community_media_jobs').update({status:'rejected',reason:'Review expired',reviewed_at:new Date().toISOString()}).eq('id',job.id).eq('status','pending');
      }
      count++;
    }
    if (job.status === 'approved' && job.published_path) {
      const { data: used, error: checkError } = await admin.from('community_messages')
        .select('id').eq('attachment_path',job.published_path).limit(1);
      if (checkError || (used?.length ?? 0) > 0) continue;
      const { error: removeError } = await admin.storage.from('community-media').remove([job.published_path]);
      if (removeError) continue;
      await admin.from('community_media_jobs').update({status:'rejected',reason:'Unused attachment',published_path:null,reviewed_at:new Date().toISOString()}).eq('id',job.id).eq('status','approved');
      count++;
    }
  }
  return count;
}

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') return new Response(null, {headers:CORS});
  if (request.method !== 'POST') return reply({error:'Method not allowed'},405);
  try {
    const input = await request.json();
    if (input?.action === 'cleanup') {
      const expected = Deno.env.get('COMMUNITY_CLEANUP_TOKEN');
      if (!expected || request.headers.get('x-cleanup-token') !== expected)
        return reply({error:'Unauthorized'},401);
      return reply({ok:true,cleaned:await cleanup()});
    }

    const jwt = request.headers.get('Authorization')?.replace(/^Bearer\s+/i,'');
    if (!jwt) return reply({error:'Login required'},401);
    const { data: identity, error: authError } = await admin.auth.getUser(jwt);
    if (authError || !identity.user) return reply({error:'Invalid session'},401);
    const { data: role } = await admin.from('community_admins').select('user_id')
      .eq('user_id',identity.user.id).maybeSingle();
    if (!role) return reply({error:'Admin only'},403);
    if (input?.action === 'list') {
      const {data,error} = await admin.from('community_media_jobs')
        .select('id,user_id,pending_path,created_at')
        .eq('status','pending').order('created_at',{ascending:true}).limit(50);
      if (error) throw error;
      return reply({ok:true,jobs:data ?? []});
    }
    if (input?.action === 'preview' && typeof input.jobId === 'string') {
      const {data: job} = await admin.from('community_media_jobs')
        .select('pending_path').eq('id',input.jobId).eq('status','pending').maybeSingle();
      if (!job) return reply({error:'Not found'},404);
      const {data,error} = await admin.storage.from('community-pending')
        .createSignedUrl(job.pending_path,120);
      if (error) throw error;
      return reply({ok:true,url:data.signedUrl});
    }
    if (!['approve','reject'].includes(input?.action) ||
        typeof input.jobId !== 'string' || !/^[0-9a-f-]{36}$/i.test(input.jobId))
      return reply({error:'Invalid request'},400);
    const { data: job, error } = await admin.from('community_media_jobs')
      .select('*').eq('id',input.jobId).eq('status','pending').maybeSingle();
    if (error || !job) return reply({error:'Pending job not found'},404);

    if (input.action === 'reject') {
      const { error: updateError } = await admin.from('community_media_jobs')
        .update({status:'rejected',reason:'Rejected by moderator',reviewed_at:new Date().toISOString()})
        .eq('id',job.id).eq('status','pending');
      if (updateError) throw updateError;
      await admin.storage.from('community-pending').remove([job.pending_path]);
      return reply({ok:true,status:'rejected'});
    }

    // Approval REQUIRES manual inspection in the private Storage dashboard.
    // Magic bytes are an additional type check, NOT a malware scanner.
    const { data: blob, error: downloadError } = await admin.storage
      .from('community-pending').download(job.pending_path);
    if (downloadError || !blob) return reply({error:'File missing'},404);
    if (blob.size < 16 || blob.size > 5 * 1024 * 1024)
      return reply({error:'Invalid image size'},400);
    const bytes = new Uint8Array(await blob.arrayBuffer());
    const mime = contentType(job.pending_path, bytes);
    if (!mime) return reply({error:'Invalid image signature'},400);
    const { error: uploadError } = await admin.storage.from('community-media')
      .upload(job.pending_path, bytes, {contentType:mime,upsert:false});
    if (uploadError) throw uploadError;
    const { data: updated, error: updateError } = await admin.from('community_media_jobs')
      .update({status:'approved',published_path:job.pending_path,
        reviewed_at:new Date().toISOString(),reason:null})
      .eq('id',job.id).eq('status','pending').select('id').maybeSingle();
    if (updateError || !updated) {
      await admin.storage.from('community-media').remove([job.pending_path]);
      throw updateError ?? new Error('Concurrent review');
    }
    await admin.storage.from('community-pending').remove([job.pending_path]);
    return reply({ok:true,status:'approved',publishedPath:job.pending_path});
  } catch (error) {
    console.error(error);
    return reply({error:'Media operation failed'},500);
  }
});
