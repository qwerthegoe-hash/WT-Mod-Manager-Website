-- WT Mod Manager Community 2.0
-- Additive schema: personal favorites, private collections, author subscriptions,
-- owner-only notifications and support-ticket history; public search remains
-- subject to the existing wtmm_mods and profile RLS.
begin;

alter table public.wtmm_mods
  add column if not exists before_image_path text,
  add column if not exists after_image_path text;

-- Only storage paths within the author's own preview directory are accepted,
-- including when a browser tries to submit another player's path.
create or replace function wtmm_security.validate_comparison_paths()
returns trigger language plpgsql set search_path = '' as $$
declare path text;
begin
  foreach path in array array[new.before_image_path,new.after_image_path] loop
    if path is not null and (
        char_length(path) > 250
        or left(path, length(new.owner_id::text)+1) <> new.owner_id::text || '/'
        or path !~ '^[a-f0-9-]+/[a-f0-9-]+/[a-f0-9-]+\.(png|jpg|webp|gif)$'
      ) then
      raise exception 'Invalid comparison image path' using errcode='22023';
    end if;
  end loop;
  return new;
end; $$;
revoke all on function wtmm_security.validate_comparison_paths() from public,anon,authenticated;
drop trigger if exists wtmm_comparison_image_paths on public.wtmm_mods;
create trigger wtmm_comparison_image_paths before insert or update
on public.wtmm_mods for each row
execute function wtmm_security.validate_comparison_paths();

create table if not exists public.wtmm_mod_favorites (
  user_id uuid not null references auth.users(id) on delete cascade,
  mod_id uuid not null references public.wtmm_mods(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id,mod_id)
);
create index if not exists wtmm_favorites_mod_idx on public.wtmm_mod_favorites(mod_id);

create table if not exists public.wtmm_collections (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (length(btrim(name)) between 2 and 60),
  description text not null default '' check (char_length(description) <= 400),
  created_at timestamptz not null default now()
);
create index if not exists wtmm_collections_owner_idx on public.wtmm_collections(owner_id,created_at desc);

create table if not exists public.wtmm_collection_items (
  collection_id uuid not null references public.wtmm_collections(id) on delete cascade,
  mod_id uuid not null references public.wtmm_mods(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (collection_id,mod_id)
);
create index if not exists wtmm_collection_items_mod_idx on public.wtmm_collection_items(mod_id);

create table if not exists public.wtmm_author_follows (
  follower_id uuid not null references auth.users(id) on delete cascade,
  author_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (follower_id,author_id),
  constraint wtmm_no_self_follow check (follower_id <> author_id)
);
create index if not exists wtmm_follows_author_idx on public.wtmm_author_follows(author_id);

create table if not exists public.wtmm_notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (kind in ('author_mod','mod_approved','mod_rejected','support_status')),
  title text not null check (char_length(title) between 1 and 180),
  body text not null default '' check (char_length(body) <= 350),
  url text not null default '' check (char_length(url) <= 300),
  source_id uuid,
  created_at timestamptz not null default now(),
  read_at timestamptz
);
create index if not exists wtmm_notification_owner_idx
  on public.wtmm_notifications(user_id,created_at desc);
create unique index if not exists wtmm_notification_event_unique
  on public.wtmm_notifications(user_id,kind,source_id)
  where source_id is not null;

create table if not exists public.wtmm_support_tickets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (kind in ('bug','idea','contact')),
  title text not null check (char_length(title) between 5 and 120),
  message text not null check (char_length(message) between 15 and 5000),
  details text not null default '' check (char_length(details) <= 2500),
  reference_url text not null default '' check (char_length(reference_url) <= 500),
  language text not null default 'ru' check (language in ('ru','uk','en','pl','de')),
  status text not null default 'sending'
    check (status in ('sending','received','delivery_failed','in_review','resolved','closed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists wtmm_tickets_owner_idx
  on public.wtmm_support_tickets(user_id,created_at desc);

-- Explicit privileges, with row policies additionally filtering individual
-- records. Client users may not impersonate notifications or submitted tickets.
revoke all on public.wtmm_mod_favorites, public.wtmm_collections,
  public.wtmm_collection_items,public.wtmm_author_follows,
  public.wtmm_notifications, public.wtmm_support_tickets
from public,anon,authenticated;
grant select,insert,delete on public.wtmm_mod_favorites to authenticated;
grant select,insert,delete on public.wtmm_collections to authenticated;
grant select,insert,delete on public.wtmm_collection_items to authenticated;
grant select,insert,delete on public.wtmm_author_follows to authenticated;
grant select,update(read_at) on public.wtmm_notifications to authenticated;
grant select on public.wtmm_support_tickets to authenticated;
grant update(status,updated_at) on public.wtmm_support_tickets to authenticated;
grant all on public.wtmm_mod_favorites,public.wtmm_collections,
  public.wtmm_collection_items,public.wtmm_author_follows,
  public.wtmm_notifications,public.wtmm_support_tickets to service_role;

alter table public.wtmm_mod_favorites enable row level security;
alter table public.wtmm_collections enable row level security;
alter table public.wtmm_collection_items enable row level security;
alter table public.wtmm_author_follows enable row level security;
alter table public.wtmm_notifications enable row level security;
alter table public.wtmm_support_tickets enable row level security;

create policy "favorites owner read" on public.wtmm_mod_favorites
for select to authenticated using (user_id = (select auth.uid()));
create policy "favorites owner add published mod" on public.wtmm_mod_favorites
for insert to authenticated with check (
 user_id = (select auth.uid()) and exists(
  select 1 from public.wtmm_mods m where m.id=mod_id and m.status='approved'
 )
);
create policy "favorites owner remove" on public.wtmm_mod_favorites
for delete to authenticated using (user_id = (select auth.uid()));

create policy "collections owner read" on public.wtmm_collections
for select to authenticated using (owner_id = (select auth.uid()));
create policy "collections owner create" on public.wtmm_collections
for insert to authenticated with check (owner_id = (select auth.uid()));
create policy "collections owner remove" on public.wtmm_collections
for delete to authenticated using (owner_id = (select auth.uid()));

create policy "collection items owner read" on public.wtmm_collection_items
for select to authenticated using (
 exists(select 1 from public.wtmm_collections c
  where c.id=collection_id and c.owner_id=(select auth.uid()))
);
create policy "collection items owner add published" on public.wtmm_collection_items
for insert to authenticated with check (
 exists(select 1 from public.wtmm_collections c
  where c.id=collection_id and c.owner_id=(select auth.uid()))
 and exists(select 1 from public.wtmm_mods m where m.id=mod_id and m.status='approved')
);
create policy "collection items owner remove" on public.wtmm_collection_items
for delete to authenticated using (
 exists(select 1 from public.wtmm_collections c
  where c.id=collection_id and c.owner_id=(select auth.uid()))
);

create policy "follows only self read" on public.wtmm_author_follows
for select to authenticated using (follower_id=(select auth.uid()));
create policy "follows only published authors" on public.wtmm_author_follows
for insert to authenticated with check (
 follower_id=(select auth.uid()) and follower_id<>author_id
 and exists(select 1 from public.community_user_profiles p
  where p.user_id=author_id and p.is_public=true)
);
create policy "follows owner remove" on public.wtmm_author_follows
for delete to authenticated using (follower_id=(select auth.uid()));

create policy "notifications owner read" on public.wtmm_notifications
for select to authenticated using (user_id=(select auth.uid()));
create policy "notifications owner mark read" on public.wtmm_notifications
for update to authenticated using (user_id=(select auth.uid()))
with check (user_id=(select auth.uid()));

create policy "tickets private to owner/admin" on public.wtmm_support_tickets
for select to authenticated using (
 user_id=(select auth.uid()) or (select public.community_is_admin())
);
create policy "tickets admin status update" on public.wtmm_support_tickets
for update to authenticated using ((select public.community_is_admin()))
with check ((select public.community_is_admin()));

-- Enforce collection/follow caps even for parallel browser requests.
create or replace function wtmm_security.limit_social_rows()
returns trigger language plpgsql set search_path='' as $$
declare maximum integer; actual integer; subject_id uuid; tab text;
begin
 tab := tg_table_name;
 if tab='wtmm_collections' then
  maximum:=30;subject_id:=new.owner_id;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('wtmm-coll:'||subject_id::text,0));
  select count(*) into actual from public.wtmm_collections where owner_id=subject_id;
 elsif tab='wtmm_collection_items' then
  maximum:=200;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('wtmm-items:'||new.collection_id::text,0));
  select count(*) into actual from public.wtmm_collection_items where collection_id=new.collection_id;
 elsif tab='wtmm_author_follows' then
  maximum:=300;subject_id:=new.follower_id;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('wtmm-follow:'||subject_id::text,0));
  select count(*) into actual from public.wtmm_author_follows where follower_id=subject_id;
 else return new;
 end if;
 if actual>=maximum then raise exception 'Community collection/follow limit reached' using errcode='P0001';end if;
 return new;
end; $$;
revoke all on function wtmm_security.limit_social_rows() from public,anon,authenticated;
create trigger wtmm_coll_limit before insert on public.wtmm_collections
for each row execute function wtmm_security.limit_social_rows();
create trigger wtmm_coll_items_limit before insert on public.wtmm_collection_items
for each row execute function wtmm_security.limit_social_rows();
create trigger wtmm_follow_limit before insert on public.wtmm_author_follows
for each row execute function wtmm_security.limit_social_rows();

-- Internal-only trigger functions: never grant API EXECUTE. Notifications are
-- produced from *database-confirmed* moderation and support updates.
create or replace function wtmm_security.notify_mod_event()
returns trigger language plpgsql security definer set search_path='' as $$
begin
 if new.status is not distinct from old.status then return new; end if;
 if new.status='approved' then
  insert into public.wtmm_notifications(user_id,kind,title,body,url,source_id)
  values(new.owner_id,'mod_approved','Мод одобрен',left(new.title,180),'../mods/mods.html?mod='||new.id::text,new.id)
  on conflict do nothing;
  insert into public.wtmm_notifications(user_id,kind,title,body,url,source_id)
  select f.follower_id,'author_mod','Новый мод от автора',left(new.title,350),
         '../mods/mods.html?mod='||new.id::text,new.id
  from public.wtmm_author_follows f where f.author_id=new.owner_id
  limit 2000 on conflict do nothing;
 elsif new.status='rejected' then
  insert into public.wtmm_notifications(user_id,kind,title,body,url,source_id)
  values(new.owner_id,'mod_rejected','Мод отклонён',left(new.title,350),'../mods/mods.html?mine=1',new.id)
  on conflict do nothing;
 end if;
 return new;
end; $$;
revoke all on function wtmm_security.notify_mod_event() from public,anon,authenticated;
create trigger wtmm_notify_mod_approval after update of status on public.wtmm_mods
for each row execute function wtmm_security.notify_mod_event();

create or replace function wtmm_security.notify_ticket_status()
returns trigger language plpgsql security definer set search_path='' as $$
begin
 if new.status in ('in_review','resolved','closed') and new.status is distinct from old.status then
  insert into public.wtmm_notifications(user_id,kind,title,body,url,source_id)
  values(new.user_id,'support_status','Статус обращения изменён',left(new.title,350),
   '../profile/profile.html#supportHistory',null)
  on conflict do nothing;
 end if;
 new.updated_at:=now();
 return new;
end; $$;
revoke all on function wtmm_security.notify_ticket_status() from public,anon,authenticated;
create trigger wtmm_ticket_status_changed before update on public.wtmm_support_tickets
for each row execute function wtmm_security.notify_ticket_status();

-- Aggregate approved-mod popularity without exposing other users' favorite rows.
-- This private definer function returns only a count for an approved mod.
create or replace function wtmm_security.approved_favorite_count(p_mod_id uuid)
returns bigint language sql stable security definer set search_path='' as $
select case when exists(
 select 1 from public.wtmm_mods m where m.id=p_mod_id and m.status='approved'
) then (select count(*) from public.wtmm_mod_favorites f where f.mod_id=p_mod_id)
else 0 end;
$;
revoke all on function wtmm_security.approved_favorite_count(uuid) from public,anon;
grant execute on function wtmm_security.approved_favorite_count(uuid) to authenticated;

-- Server-side discovery with favorites count and optional author/favorite filters.
-- SECURITY INVOKER and table RLS ensure unpublished files cannot leak.
create or replace function public.wtmm_discover_mods(
  p_text text default '', p_category text default 'all', p_sort text default 'new',
  p_author uuid default null, p_favorites_only boolean default false,
  p_limit integer default 50, p_offset integer default 0
)
returns table(
  id uuid,owner_id uuid,title text,description text,category text,
  version text,status text,file_path text,cover_path text,
  before_image_path text,after_image_path text,
  created_at timestamptz,favorites_count bigint,is_favorite boolean
)
language sql stable security invoker set search_path=''
as $$
select m.id,m.owner_id,m.title,m.description,m.category,m.version,m.status,
       m.file_path,m.cover_path,m.before_image_path,m.after_image_path,
       m.created_at,
       wtmm_security.approved_favorite_count(m.id) as favorites_count,
       exists(select 1 from public.wtmm_mod_favorites fav where fav.mod_id=m.id
         and fav.user_id=(select auth.uid())) as is_favorite
from public.wtmm_mods m
left join public.community_user_profiles p on p.user_id=m.owner_id
where m.status='approved'
 and (p_author is null or m.owner_id=p_author)
 and (p_category='all' or m.category=p_category)
 and (not p_favorites_only or exists (
   select 1 from public.wtmm_mod_favorites fav where fav.mod_id=m.id
     and fav.user_id=(select auth.uid())))
 and (btrim(coalesce(p_text,''))='' or
   m.title ilike '%'||left(btrim(p_text),90)||'%' or
   m.description ilike '%'||left(btrim(p_text),90)||'%' or
   p.nickname ilike '%'||left(btrim(p_text),90)||'%')
order by
  case when p_sort='popular' then wtmm_security.approved_favorite_count(m.id) end desc nulls last,
  case when p_sort='name' then lower(m.title) end asc nulls last,
  case when p_sort='old' then m.created_at end asc nulls last,
  case when p_sort='relevance' and btrim(coalesce(p_text,''))<>'' then
    case when lower(m.title)=lower(btrim(p_text)) then 4
         when m.title ilike left(btrim(p_text),90)||'%' then 3
         when m.title ilike '%'||left(btrim(p_text),90)||'%' then 2
         else 1 end end desc nulls last,
  case when p_sort in ('new','popular','relevance') or p_sort not in ('name','old') then m.created_at end desc nulls last,
  m.id desc
limit least(greatest(coalesce(p_limit,50),1),150)
offset least(greatest(coalesce(p_offset,0),0),100000)
$$;
revoke all on function public.wtmm_discover_mods(text,text,text,uuid,boolean,integer,integer)
from public,anon;
grant execute on function public.wtmm_discover_mods(text,text,text,uuid,boolean,integer,integer)
to authenticated;
commit;
