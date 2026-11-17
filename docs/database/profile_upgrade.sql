-- WT Mod Manager: per-user profiles and PRIVATE avatar uploads.
-- Run once in Supabase SQL Editor (or via Supabase migrations).
-- Uploads are user-owned; avatars are not publicly accessible without a signed URL.
begin;

create table if not exists public.community_user_profiles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    nickname text not null,
    avatar_path text,
    accent text not null default 'blue',
    updated_at timestamptz not null default now(),
    constraint community_profile_nickname_length check (char_length(btrim(nickname)) between 2 and 24),
    constraint community_profile_accent_allowed check (accent in ('blue', 'teal', 'purple')),
    constraint community_profile_avatar_path check (
        avatar_path is null or
        avatar_path ~ ('^' || user_id::text || '/[a-f0-9-]{36}[.](png|jpg|webp|gif)$')
    )
);
alter table public.community_user_profiles enable row level security;
revoke all on public.community_user_profiles from public, anon;
grant select, insert, update on public.community_user_profiles to authenticated;
drop policy if exists "community_profile_select_self" on public.community_user_profiles;
create policy "community_profile_select_self" on public.community_user_profiles
    for select to authenticated using (user_id = (select auth.uid()));
drop policy if exists "community_profile_insert_self" on public.community_user_profiles;
create policy "community_profile_insert_self" on public.community_user_profiles
    for insert to authenticated with check (user_id = (select auth.uid()));
drop policy if exists "community_profile_update_self" on public.community_user_profiles;
create policy "community_profile_update_self" on public.community_user_profiles
    for update to authenticated using (user_id = (select auth.uid()))
    with check (user_id = (select auth.uid()));

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('community-avatars', 'community-avatars', false, 5242880,
    array['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
on conflict (id) do update set
    public = false,
    file_size_limit = 5242880,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "community_avatars_select_self" on storage.objects;
create policy "community_avatars_select_self" on storage.objects
    for select to authenticated
    using (bucket_id = 'community-avatars' and
           (storage.foldername(name))[1] = (select auth.uid())::text);

drop policy if exists "community_avatars_insert_self" on storage.objects;
create policy "community_avatars_insert_self" on storage.objects
    for insert to authenticated
    with check (bucket_id = 'community-avatars' and
                (storage.foldername(name))[1] = (select auth.uid())::text);

drop policy if exists "community_avatars_delete_self" on storage.objects;
create policy "community_avatars_delete_self" on storage.objects
    for delete to authenticated
    using (bucket_id = 'community-avatars' and
           (storage.foldername(name))[1] = (select auth.uid())::text);

commit;