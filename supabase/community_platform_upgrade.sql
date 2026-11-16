-- WT Mod Manager — profiles + moderated mod library (stage 2)
-- IMPORTANT: First run supabase/profile_upgrade.sql (if not already applied).
-- Then run this complete script once in Supabase SQL Editor.
-- No service-role keys or secrets belong in this repository.
begin;

-- 1) Extend the existing account records without losing current data.
alter table public.community_user_profiles
    add column if not exists bio text not null default '',
    add column if not exists banner_path text,
    add column if not exists is_public boolean not null default false;

alter table public.community_user_profiles
    drop constraint if exists wtmm_profile_bio_length;
alter table public.community_user_profiles
    add constraint wtmm_profile_bio_length check (char_length(bio) <= 320);

alter table public.community_user_profiles
    drop constraint if exists wtmm_profile_banner_path;
alter table public.community_user_profiles
    add constraint wtmm_profile_banner_path check (
       banner_path is null or banner_path ~
       ('^' || user_id::text || '/[0-9a-f-]{36}[.](png|jpg|webp|gif)$')
    );

-- Public profiles are readable only when the owner explicitly enables them.
drop policy if exists "wtmm_profiles_public_read" on public.community_user_profiles;
create policy "wtmm_profiles_public_read" on public.community_user_profiles
  for select to authenticated using (is_public = true);

-- Keep avatar/banner files in private Supabase buckets and serve them
-- only to their owner or to viewers of an explicitly public profile.
insert into storage.buckets (id,name,public,file_size_limit,allowed_mime_types)
values ('community-banners','community-banners',false,5242880,
        array['image/jpeg','image/png','image/webp','image/gif'])
on conflict (id) do update set
  public=false, file_size_limit=excluded.file_size_limit,
  allowed_mime_types=excluded.allowed_mime_types;

drop policy if exists "wtmm_banners_read" on storage.objects;
create policy "wtmm_banners_read" on storage.objects for select to authenticated
using (
  bucket_id='community-banners' and (
    (storage.foldername(name))[1]=(select auth.uid())::text or
    exists(select 1 from public.community_user_profiles p
      where p.banner_path=name and p.is_public)
  )
);
drop policy if exists "wtmm_banners_upload" on storage.objects;
create policy "wtmm_banners_upload" on storage.objects for insert to authenticated
with check (bucket_id='community-banners' and
  (storage.foldername(name))[1]=(select auth.uid())::text);
drop policy if exists "wtmm_banners_remove" on storage.objects;
create policy "wtmm_banners_remove" on storage.objects for delete to authenticated
using (bucket_id='community-banners' and
  (storage.foldername(name))[1]=(select auth.uid())::text);

drop policy if exists "wtmm_avatars_public_read" on storage.objects;
create policy "wtmm_avatars_public_read" on storage.objects for select to authenticated
using (
  bucket_id='community-avatars' and
  exists (select 1 from public.community_user_profiles p
    where p.avatar_path=name and p.is_public=true)
);

-- 2) A fixed, server-authorized admin check; no exposed admin credentials.
create or replace function public.wtmm_is_admin()
returns boolean language sql stable security definer set search_path = public
as $$
  select exists (
    select 1 from public.community_admins a where a.user_id = (select auth.uid())
  );
$$;
revoke all on function public.wtmm_is_admin() from public;
grant execute on function public.wtmm_is_admin() to authenticated;

-- 3) Mod releases. A user can submit but cannot approve their own submission.
create table if not exists public.wtmm_mods (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  description text not null default '',
  category text not null,
  version text not null default '1.0',
  status text not null default 'pending',
  file_path text not null,
  cover_path text,
  rejection_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  reviewed_at timestamptz,
  constraint wtmm_mods_title check (char_length(btrim(title)) between 3 and 90),
  constraint wtmm_mods_description check (char_length(description) <= 2500),
  constraint wtmm_mods_version check (char_length(version) between 1 and 32),
  constraint wtmm_mods_category check
    (category in ('sights','camouflage','sounds','interface','other')),
  constraint wtmm_mods_status check
    (status in ('pending','approved','rejected')),
  constraint wtmm_mods_file_path check
    (file_path ~ ('^' || owner_id::text || '/' || id::text ||
         '/[0-9a-f-]{36}[.]zip$')),
  constraint wtmm_mods_cover_path check
    (cover_path is null or cover_path ~ ('^' || owner_id::text || '/' ||
         id::text || '/[0-9a-f-]{36}[.](jpg|png|webp|gif)$'))
);
create index if not exists wtmm_mods_public_catalog on public.wtmm_mods(status,created_at desc);
create index if not exists wtmm_mods_author on public.wtmm_mods(owner_id,created_at desc);
alter table public.wtmm_mods enable row level security;
revoke all on public.wtmm_mods from anon,public;
grant select,insert,update,delete on public.wtmm_mods to authenticated;

drop policy if exists "wtmm_mods_visible" on public.wtmm_mods;
create policy "wtmm_mods_visible" on public.wtmm_mods for select to authenticated
using (status='approved' or owner_id=(select auth.uid()) or (select public.wtmm_is_admin()));

drop policy if exists "wtmm_mods_owner_submit" on public.wtmm_mods;
create policy "wtmm_mods_owner_submit" on public.wtmm_mods for insert to authenticated
with check (owner_id=(select auth.uid()) and status='pending'
  and reviewed_at is null and rejection_reason is null);

drop policy if exists "wtmm_mods_owner_edit" on public.wtmm_mods;
create policy "wtmm_mods_owner_edit" on public.wtmm_mods for update to authenticated
using (owner_id=(select auth.uid()) and status in ('pending','rejected'))
with check (owner_id=(select auth.uid()) and status='pending'
  and reviewed_at is null and rejection_reason is null);

drop policy if exists "wtmm_mods_admin_review" on public.wtmm_mods;
create policy "wtmm_mods_admin_review" on public.wtmm_mods for update to authenticated
using ((select public.wtmm_is_admin()))
with check ((select public.wtmm_is_admin()));

drop policy if exists "wtmm_mods_owner_remove" on public.wtmm_mods;
create policy "wtmm_mods_owner_remove" on public.wtmm_mods for delete to authenticated
using ((owner_id=(select auth.uid()) and status in ('pending','rejected'))
  or (select public.wtmm_is_admin()));

-- Private packages: users upload only into their own folder.
-- Download/read is possible only by the owner, administrator, or for approved mods.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values ('wtmm-mod-packages','wtmm-mod-packages',false,20971520,array['application/zip'])
on conflict (id) do update set
  public=false,file_size_limit=excluded.file_size_limit,
  allowed_mime_types=excluded.allowed_mime_types;

drop policy if exists "wtmm_packages_upload" on storage.objects;
create policy "wtmm_packages_upload" on storage.objects for insert to authenticated
with check (bucket_id='wtmm-mod-packages'
  and (storage.foldername(name))[1]=(select auth.uid())::text);

drop policy if exists "wtmm_packages_read" on storage.objects;
create policy "wtmm_packages_read" on storage.objects for select to authenticated
using (
  bucket_id='wtmm-mod-packages' and (
    (storage.foldername(name))[1]=(select auth.uid())::text or
    (select public.wtmm_is_admin()) or
    exists(select 1 from public.wtmm_mods m
      where m.file_path=name and m.status='approved')
  )
);

drop policy if exists "wtmm_packages_remove" on storage.objects;
create policy "wtmm_packages_remove" on storage.objects for delete to authenticated
using (bucket_id='wtmm-mod-packages'
  and (storage.foldername(name))[1]=(select auth.uid())::text
  and not exists(select 1 from public.wtmm_mods m
    where m.file_path=name and m.status='approved'));

-- Private previews: only owner/admin before approval, visible to signed-in
-- visitors after the associated mod has been approved.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values ('wtmm-mod-previews','wtmm-mod-previews',false,5242880,
       array['image/jpeg','image/png','image/webp','image/gif'])
on conflict (id) do update set
  public=false,file_size_limit=excluded.file_size_limit,
  allowed_mime_types=excluded.allowed_mime_types;

drop policy if exists "wtmm_previews_upload" on storage.objects;
create policy "wtmm_previews_upload" on storage.objects for insert to authenticated
with check (bucket_id='wtmm-mod-previews'
  and (storage.foldername(name))[1]=(select auth.uid())::text);

drop policy if exists "wtmm_previews_read" on storage.objects;
create policy "wtmm_previews_read" on storage.objects for select to authenticated
using (
  bucket_id='wtmm-mod-previews' and (
    (storage.foldername(name))[1]=(select auth.uid())::text or
    (select public.wtmm_is_admin()) or
    exists(select 1 from public.wtmm_mods m
      where m.cover_path=name and m.status='approved')
  )
);

drop policy if exists "wtmm_previews_remove" on storage.objects;
create policy "wtmm_previews_remove" on storage.objects for delete to authenticated
using (bucket_id='wtmm-mod-previews'
  and (storage.foldername(name))[1]=(select auth.uid())::text
  and not exists(select 1 from public.wtmm_mods m
    where m.cover_path=name and m.status='approved'));

commit;
