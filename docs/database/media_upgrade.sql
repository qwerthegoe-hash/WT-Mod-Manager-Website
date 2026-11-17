-- WTMM Media Quarantine migration. Run AFTER community SQL v3.
begin;

-- Approved images stay public; uploads first enter a PRIVATE bucket.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('community-pending','community-pending',false,5242880,
        array['image/jpeg','image/png','image/webp','image/gif'])
on conflict (id) do update set public=false, file_size_limit=5242880,
 allowed_mime_types=excluded.allowed_mime_types;

-- Approved bucket is served through public URLs, but public users cannot upload there.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('community-media','community-media',true,5242880,
        array['image/jpeg','image/png','image/webp','image/gif'])
on conflict (id) do update set public=true, file_size_limit=5242880,
 allowed_mime_types=excluded.allowed_mime_types;

-- Limit direct quarantine uploads, including files not submitted to the queue.
create or replace function public.community_pending_upload_allowed()
returns boolean language sql stable security definer set search_path='' as $$
 select (select count(*) from storage.objects
  where bucket_id='community-pending'
    and owner_id=(select auth.uid())::text
    and created_at>now()-interval '1 hour') < 15;
$$;
revoke all on function public.community_pending_upload_allowed() from public,anon,authenticated;
grant execute on function public.community_pending_upload_allowed() to authenticated;

drop policy if exists "Upload own community images" on storage.objects;
drop policy if exists "Upload pending community images" on storage.objects;
create policy "Upload pending community images" on storage.objects
for insert to authenticated with check (
 bucket_id='community-pending'
 and (storage.foldername(name))[1]=(select auth.uid())::text
 and name ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png|webp|gif)$'
 and lower(storage.extension(name)) in ('jpg','png','webp','gif')
 and (select public.community_pending_upload_allowed())
);

create table if not exists public.community_media_jobs (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null,
 pending_path text not null unique,
 published_path text unique,
 status text not null default 'pending' check (status in ('pending','approved','rejected')),
 reason text,
 created_at timestamptz not null default now(),
 reviewed_at timestamptz,
 constraint community_media_path_check check (
  pending_path ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png|webp|gif)$'
 )
);
create index if not exists community_media_jobs_queue on public.community_media_jobs(status,created_at);
alter table public.community_media_jobs enable row level security;
revoke all on public.community_media_jobs from anon,authenticated;
grant select on public.community_media_jobs to authenticated;
drop policy if exists "Read own media jobs" on public.community_media_jobs;
create policy "Read own media jobs" on public.community_media_jobs
for select to authenticated using (user_id=(select auth.uid()) or (select public.community_is_admin()));

create or replace function public.queue_community_media(p_path text)
returns uuid language plpgsql security definer set search_path='' as $$
declare sender uuid := auth.uid(); result uuid;
begin
 if sender is null then raise exception 'Login required'; end if;
 if p_path !~ '^[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png|webp|gif)$'
    or split_part(p_path,'/',1) <> sender::text
 then raise exception 'Invalid media path'; end if;
 if not exists(select 1 from storage.objects
   where bucket_id='community-pending' and name=p_path and owner_id=sender::text)
 then raise exception 'Upload not found'; end if;
 if (select count(*) from public.community_media_jobs
     where user_id=sender and created_at > now()-interval '1 hour') >= 15
 then raise exception 'Hourly image limit reached'; end if;
 insert into public.community_media_jobs(user_id,pending_path)
 values(sender,p_path) on conflict (pending_path) do update
 set pending_path=excluded.pending_path
 returning id into result;
 return result;
end $$;
revoke all on function public.queue_community_media(text) from public,anon,authenticated;
grant execute on function public.queue_community_media(text) to authenticated;

-- Replace v3 guard: its old Storage owner_id check is incompatible with
-- service-role publication (service uploads may have NULL owner_id).
create or replace function public.check_community_message()
returns trigger language plpgsql security definer set search_path='' as $$
declare sender uuid:=auth.uid(); is_admin boolean; n integer;
begin
 if sender is null or new.user_id is distinct from sender then
   raise exception 'Authentication required'; end if;
 new.id:=gen_random_uuid(); new.created_at:=now();
 new.nickname:=btrim(coalesce(new.nickname,''));
 new.body:=btrim(coalesce(new.body,''));
 new.is_hidden:=false; new.hidden_at:=null;
 if length(new.nickname) not between 2 and 24 then
   raise exception 'Invalid nickname'; end if;
 if length(new.body)>1500 or (new.body='' and new.attachment_path is null) then
   raise exception 'Invalid message'; end if;
 select exists(select 1 from public.community_admins where user_id=sender)
 into is_admin;
 if not is_admin and lower(new.nickname) in
 ('admin','administrator','developer','moderator','system','system bot','wt guardian','wt mod manager')
 then raise exception 'Reserved nickname'; end if;
 if new.channel='news' and not is_admin then
   raise exception 'Only administrators publish news'; end if;
 if exists(select 1 from public.community_mutes
   where user_id=sender and muted_until>now()) then
   raise exception 'Messaging temporarily restricted'; end if;
 if new.body ~* '(https?://|www\.|discord\.gg/|discord\.com/invite/|t\.me/|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|[a-z0-9-]+\.(com|net|org|io|gg|ru|ua|me|xyz|app|dev|site|link|click|top)(/|[[:space:]]|$))'
 then raise exception 'Links are not allowed'; end if;
 if new.attachment_path is not null and not exists(
    select 1 from public.community_media_jobs
    where user_id=sender and published_path=new.attachment_path
      and status='approved'
 ) then raise exception 'Image not approved'; end if;
 perform pg_advisory_xact_lock(92141,hashtext(sender::text));
 if exists(select 1 from public.community_messages where user_id=sender
  and created_at>now()-interval '3 seconds') then
  raise exception 'Please wait before sending'; end if;
 select count(*) into n from public.community_messages
 where user_id=sender and created_at>now()-interval '1 hour';
 if n>=40 then raise exception 'Hourly message limit reached'; end if;
 if length(new.body)>=12 and exists(select 1 from public.community_messages
   where user_id=sender and lower(btrim(body))=lower(new.body)
   and created_at>now()-interval '10 minutes') then
   raise exception 'Duplicate message'; end if;
 return new;
end $$;
revoke all on function public.check_community_message() from public,anon,authenticated;

-- A pending image cannot be attached to a public message.
-- Only the server's approved media jobs authorize newly inserted attachments.
create or replace function public.check_approved_community_media()
returns trigger language plpgsql security definer set search_path='' as $$
begin
 if new.attachment_path is not null and not exists (
  select 1 from public.community_media_jobs j
  where j.user_id=new.user_id and j.status='approved'
   and j.published_path=new.attachment_path
 ) then raise exception 'Image is awaiting approval'; end if;
 return new;
end $$;
revoke all on function public.check_approved_community_media() from public,anon,authenticated;
drop trigger if exists community_approved_media_guard on public.community_messages;
create trigger community_approved_media_guard
before insert on public.community_messages for each row
execute function public.check_approved_community_media();

-- One approved image may be attached only once.
create unique index if not exists community_message_one_media
on public.community_messages(attachment_path) where attachment_path is not null;
commit;
