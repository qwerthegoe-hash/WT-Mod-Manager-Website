
-- ============================================================
-- WT MOD MANAGER COMMUNITY DATABASE
-- VERSION 3.0
-- PostgreSQL / Supabase
-- ============================================================
--
-- FEATURES
-- Persistent message history
-- Five community channels
-- Anonymous Supabase Auth support
-- Administrator permissions
-- Moderation and soft hiding
-- Message reports
-- Temporary mutes
-- Anti-spam restrictions
-- Link and email filtering
-- Protected image references
-- Supabase Realtime
-- Row Level Security
--
-- Run in Supabase SQL Editor.
--
-- Do not put SQL editor credentials or secret keys
-- into public website files.
--
-- ============================================================

begin;

-- ============================================================
-- 1. EXTENSIONS
-- ============================================================

create extension if not exists pgcrypto;


-- ============================================================
-- 2. ADMINISTRATORS
-- ============================================================

create table if not exists public.community_admins (
    user_id uuid primary key
        references auth.users(id)
        on delete cascade,

    created_at timestamptz
        not null default now()
);


-- ============================================================
-- 3. CHAT MESSAGES
-- ============================================================

create table if not exists public.community_messages (

    id uuid primary key
        default gen_random_uuid(),

    -- Keep message history even after account removal.
    user_id uuid not null,

    nickname text not null,

    channel text not null,

    body text not null default '',

    attachment_path text,

    created_at timestamptz
        not null default now(),

    -- Moderation without destroying message history.
    is_hidden boolean
        not null default false,

    hidden_at timestamptz,

    constraint community_valid_channel check (
        channel in (
            'general',
            'updates',
            'news',
            'ideas',
            'help'
        )
    ),

    constraint community_valid_nickname check (
        char_length(btrim(nickname))
        between 2 and 24
    ),

    constraint community_valid_body check (
        char_length(body) <= 1500
        and (
            char_length(btrim(body)) > 0
            or attachment_path is not null
        )
    ),

    constraint community_valid_attachment check (
        attachment_path is null
        or attachment_path ~
        '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(jpg|png|webp|gif)$'
    )
);


-- ============================================================
-- 4. MIGRATION FROM VERSION 2.0
-- ============================================================

-- Add moderation columns to existing tables.

alter table public.community_messages
    add column if not exists
    is_hidden boolean not null default false;

alter table public.community_messages
    add column if not exists
    hidden_at timestamptz;

-- Original version 1.0 connected messages to auth.users
-- with ON DELETE CASCADE.
--
-- Remove only that original known constraint.
-- Existing messages remain in the database.

alter table public.community_messages
    drop constraint if exists
    community_messages_user_id_fkey;


-- ============================================================
-- 5. TEMPORARY USER RESTRICTIONS
-- ============================================================

create table if not exists public.community_mutes (

    user_id uuid primary key,

    reason text not null
        default 'Community rule violation',

    muted_until timestamptz not null,

    created_at timestamptz
        not null default now()
);


-- ============================================================
-- 6. REPORTS
-- ============================================================

create table if not exists public.community_reports (

    id uuid primary key
        default gen_random_uuid(),

    message_id uuid not null
        references public.community_messages(id)
        on delete restrict,

    reporter_id uuid not null
        references auth.users(id)
        on delete cascade,

    reason text not null,

    details text not null default '',

    status text not null default 'pending',

    created_at timestamptz
        not null default now(),

    reviewed_at timestamptz,

    constraint community_report_reason check (
        reason in (
            'spam',
            'harassment',
            'scam',
            'unsafe_content',
            'other'
        )
    ),

    constraint community_report_status check (
        status in (
            'pending',
            'reviewed',
            'dismissed'
        )
    ),

    constraint community_report_details check (
        char_length(details) <= 1000
    ),

    constraint community_one_report_per_message unique (
        message_id,
        reporter_id
    )
);


-- ============================================================
-- 7. INDEXES
-- ============================================================

create index if not exists
    community_messages_recent

on public.community_messages (
    channel,
    created_at desc,
    id desc
);


create index if not exists
    community_messages_user_recent

on public.community_messages (
    user_id,
    created_at desc
);


create index if not exists
    community_messages_hidden

on public.community_messages (
    is_hidden,
    created_at desc
);


create index if not exists
    community_mutes_expiration

on public.community_mutes (
    muted_until
);


create index if not exists
    community_reports_pending

on public.community_reports (
    status,
    created_at desc
);


create index if not exists
    community_reports_user_recent

on public.community_reports (
    reporter_id,
    created_at desc
);


-- ============================================================
-- 8. ENABLE ROW LEVEL SECURITY
-- ============================================================

alter table public.community_admins
    enable row level security;

alter table public.community_messages
    enable row level security;

alter table public.community_mutes
    enable row level security;

alter table public.community_reports
    enable row level security;


-- ============================================================
-- 9. DATABASE PERMISSIONS
-- ============================================================

revoke all on public.community_admins
from anon, authenticated;

revoke all on public.community_messages
from anon, authenticated;

revoke all on public.community_mutes
from anon, authenticated;

revoke all on public.community_reports
from anon, authenticated;


grant select on public.community_admins
to authenticated;

grant select, insert on public.community_messages
to authenticated;

grant select, insert on public.community_reports
to authenticated;

-- No client UPDATE or DELETE on messages.
-- No client writes to admin roles.
-- No client writes to temporary restrictions.


-- ============================================================
-- 10. ADMINISTRATOR CHECK
-- ============================================================

create or replace function
public.community_is_admin()

returns boolean

language sql
stable
security definer
set search_path = ''

as $$
    select exists (
        select 1
        from public.community_admins
        where user_id = (select auth.uid())
    );
$$;


revoke all
on function public.community_is_admin()
from public, anon, authenticated;

grant execute
on function public.community_is_admin()
to authenticated;


-- ============================================================
-- 11. ADMIN ROLE POLICY
-- ============================================================

drop policy if exists
    "Read own admin status"
on public.community_admins;


create policy "Read own admin status"
on public.community_admins

for select
to authenticated

using (
    user_id = (select auth.uid())
);


-- ============================================================
-- 12. MESSAGE READ POLICY
-- ============================================================

drop policy if exists
    "Authenticated users read chat"
on public.community_messages;


create policy "Authenticated users read chat"
on public.community_messages

for select
to authenticated

using (
    is_hidden = false
    or (select public.community_is_admin())
);


-- ============================================================
-- 13. MESSAGE INSERT POLICY
-- ============================================================

drop policy if exists
    "Authenticated users create messages"
on public.community_messages;


create policy "Authenticated users create messages"
on public.community_messages

for insert
to authenticated

with check (
    user_id = (select auth.uid())
);


-- ============================================================
-- 14. REPORT READ POLICY
-- ============================================================

drop policy if exists
    "Read community reports"
on public.community_reports;


create policy "Read community reports"
on public.community_reports

for select
to authenticated

using (
    reporter_id = (select auth.uid())
    or (select public.community_is_admin())
);


-- ============================================================
-- 15. REPORT INSERT POLICY
-- ============================================================

drop policy if exists
    "Create community reports"
on public.community_reports;


create policy "Create community reports"
on public.community_reports

for insert
to authenticated

with check (
    reporter_id = (select auth.uid())
);


-- ============================================================
-- 16. MESSAGE MODERATION FUNCTION
-- ============================================================

create or replace function
public.check_community_message()

returns trigger

language plpgsql
security definer
set search_path = ''

as $$
declare
    sender_id uuid;
    sender_is_admin boolean := false;
    hourly_count integer := 0;
    normalized_body text;
begin

    -- Verify authenticated sender.

    sender_id := auth.uid();

    if sender_id is null then
        raise exception
            'Authentication required';
    end if;

    if new.user_id <> sender_id then
        raise exception
            'Cannot send as another user';
    end if;


    -- Normalize and protect server-owned fields.

    new.id := gen_random_uuid();
    new.created_at := now();

    new.nickname :=
        btrim(coalesce(new.nickname, ''));

    new.body :=
        btrim(coalesce(new.body, ''));

    new.is_hidden := false;
    new.hidden_at := null;

    normalized_body := new.body;


    -- Check administrative role.

    select exists (
        select 1
        from public.community_admins
        where user_id = sender_id
    )
    into sender_is_admin;


    -- Disallow impersonation of system accounts.

    if not sender_is_admin and
       lower(new.nickname) in (
           'admin',
           'administrator',
           'developer',
           'moderator',
           'system',
           'system bot',
           'wt guardian',
           'wt mod manager'
       )
    then
        raise exception
            'This nickname is reserved';
    end if;


    -- Verify that the user is not muted.

    if exists (
        select 1
        from public.community_mutes
        where user_id = sender_id
          and muted_until > now()
    ) then
        raise exception
            'Messaging temporarily restricted';
    end if;


    -- Protect official news channel.

    if new.channel = 'news'
       and not sender_is_admin
    then
        raise exception
            'Only administrators can publish news';
    end if;


    -- Validate nickname.

    if char_length(new.nickname) < 2
       or char_length(new.nickname) > 24
    then
        raise exception
            'Invalid nickname';
    end if;


    -- Validate message length.

    if char_length(new.body) > 1500 then
        raise exception
            'Message too long';
    end if;


    -- Block links, common invitations and email addresses.
    --
    -- This is a first-line filter.
    -- It does not guarantee detection of every disguised URL.

    if normalized_body ~*
        '(https?://|www\.|discord\.gg/|discord\.com/invite/|t\.me/|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|[a-z0-9-]+\.(com|net|org|io|gg|ru|ua|me|xyz|app|dev|site|link|click|top)(/|[[:space:]]|$))'
    then
        raise exception
            'Links and email addresses are not allowed';
    end if;


    -- Validate optional media.

    if new.attachment_path is not null then

        if new.attachment_path !~
            '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(jpg|png|webp|gif)$'
        then
            raise exception
                'Invalid attachment path';
        end if;


        -- The attachment must belong to the sender.

        if split_part(
            new.attachment_path,
            '/',
            1
        ) <> sender_id::text
        then
            raise exception
                'Attachment belongs to another user';
        end if;


        -- Confirm that the object exists.

        if not exists (
            select 1
            from storage.objects
            where bucket_id = 'community-media'
              and name = new.attachment_path
              and owner_id = sender_id::text
        ) then
            raise exception
                'Attachment not found or not owned by sender';
        end if;

    end if;


    -- Require message text or image.

    if char_length(new.body) = 0
       and new.attachment_path is null
    then
        raise exception
            'Empty message';
    end if;


    -- Prevent concurrent requests from bypassing
    -- per-user message limits.

    perform pg_advisory_xact_lock(
        92141,
        hashtext(sender_id::text)
    );


    -- Minimum time between messages.

    if exists (
        select 1
        from public.community_messages
        where user_id = sender_id
          and created_at >
              now() - interval '3 seconds'
    ) then
        raise exception
            'Please wait before sending another message';
    end if;


    -- Hourly message limit.

    select count(*)
    into hourly_count
    from public.community_messages
    where user_id = sender_id
      and created_at >
          now() - interval '1 hour';


    if hourly_count >= 40 then
        raise exception
            'Hourly message limit reached';
    end if;


    -- Detect repeated messages.
    --
    -- Does not ban the user, only rejects duplicates.
    -- Apply only to substantial messages.

    if char_length(new.body) >= 12
       and exists (
           select 1
           from public.community_messages
           where user_id = sender_id
             and lower(btrim(body)) =
                 lower(new.body)
             and created_at >
                 now() - interval '10 minutes'
       )
    then
        raise exception
            'Duplicate message detected';
    end if;


    -- Ordinary language and emojis are allowed.
    -- No automatic profanity-based bans.

    return new;

end;
$$;


-- ============================================================
-- 17. MESSAGE TRIGGER
-- ============================================================

revoke all
on function public.check_community_message()
from public, anon, authenticated;


drop trigger if exists
    community_message_guard
on public.community_messages;


create trigger community_message_guard

before insert
on public.community_messages

for each row

execute function public.check_community_message();


-- ============================================================
-- 18. REPORT VALIDATION FUNCTION
-- ============================================================

create or replace function
public.check_community_report()

returns trigger

language plpgsql
security definer
set search_path = ''

as $$
declare
    sender_id uuid;
begin

    sender_id := auth.uid();

    if sender_id is null
       or new.reporter_id <> sender_id
    then
        raise exception
            'Authentication required';
    end if;


    -- Users cannot set their own report status.

    new.id := gen_random_uuid();
    new.created_at := now();
    new.reviewed_at := null;
    new.status := 'pending';

    new.details :=
        btrim(coalesce(new.details, ''));


    -- Verify that the message exists and is visible.

    if not exists (
        select 1
        from public.community_messages
        where id = new.message_id
          and is_hidden = false
    ) then
        raise exception
            'Message not found';
    end if;


    -- Do not allow reporting your own message.

    if exists (
        select 1
        from public.community_messages
        where id = new.message_id
          and user_id = sender_id
    ) then
        raise exception
            'Cannot report your own message';
    end if;


    -- Prevent rapid report spam.

    perform pg_advisory_xact_lock(
        92142,
        hashtext(sender_id::text)
    );

    if exists (
        select 1
        from public.community_reports
        where reporter_id = sender_id
          and created_at >
              now() - interval '30 seconds'
    ) then
        raise exception
            'Please wait before sending another report';
    end if;


    return new;

end;
$$;


-- ============================================================
-- 19. REPORT TRIGGER
-- ============================================================

revoke all
on function public.check_community_report()
from public, anon, authenticated;


drop trigger if exists
    community_report_guard
on public.community_reports;


create trigger community_report_guard

before insert
on public.community_reports

for each row

execute function public.check_community_report();


-- ============================================================
-- 20. STORAGE POLICIES
-- ============================================================

-- Create the community-media bucket in the Storage UI.
--
-- Required settings:
--
-- Public bucket: enabled
-- Maximum file size: 5 MB
--
-- Allowed MIME types:
-- image/jpeg
-- image/png
-- image/webp
-- image/gif
--
-- No videos, documents, archives or executables.
--
-- This policy allows inserting objects only
-- under the authenticated user's UUID folder.

drop policy if exists
    "Upload own community images"
on storage.objects;


create policy "Upload own community images"

on storage.objects

for insert
to authenticated

with check (

    bucket_id = 'community-media'

    and
    (storage.foldername(name))[1] =
        (select auth.uid())::text

    and
    name ~
        '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(jpg|png|webp|gif)$'

    and
    lower(storage.extension(name))
        in ('jpg', 'png', 'webp', 'gif')

);

-- No user UPDATE or DELETE policy for images.
-- Public image URLs are readable by design.
-- They are not private uploads.


-- ============================================================
-- 21. REALTIME
-- ============================================================

do $$
begin
    if not exists (
        select 1
        from pg_publication_tables
        where pubname = 'supabase_realtime'
          and schemaname = 'public'
          and tablename = 'community_messages'
    ) then

        alter publication supabase_realtime
        add table public.community_messages;

    end if;
end;
$$;


-- ============================================================
-- 22. FINISH
-- ============================================================

commit;


-- ============================================================
-- ADMINISTRATION EXAMPLES
-- ============================================================
--
-- These examples are commented out intentionally.
-- Run them separately in the trusted SQL Editor.
--
-- Never put these commands in public JavaScript.
--
-- ============================================================

-- GRANT ADMINISTRATOR
--
-- insert into public.community_admins (user_id)
-- values ('YOUR-AUTH-USER-UUID')
-- on conflict (user_id) do nothing;


-- TEMPORARILY MUTE A USER FOR ONE HOUR
--
-- insert into public.community_mutes (
--     user_id,
--     reason,
--     muted_until
-- )
-- values (
--     'USER-UUID',
--     'Repeated spam',
--     now() + interval '1 hour'
-- )
-- on conflict (user_id)
-- do update set
--     reason = excluded.reason,
--     muted_until = excluded.muted_until;


-- REMOVE A MUTE
--
-- delete from public.community_mutes
-- where user_id = 'USER-UUID';


-- HIDE A MESSAGE WITHOUT DELETING IT
--
-- update public.community_messages
-- set
--     is_hidden = true,
--     hidden_at = now()
-- where id = 'MESSAGE-UUID';


-- RESTORE A HIDDEN MESSAGE
--
-- update public.community_messages
-- set
--     is_hidden = false,
--     hidden_at = null
-- where id = 'MESSAGE-UUID';


-- MARK A REPORT AS REVIEWED
--
-- update public.community_reports
-- set
--     status = 'reviewed',
--     reviewed_at = now()
-- where id = 'REPORT-UUID';


-- ============================================================
-- END WT MOD MANAGER COMMUNITY DATABASE 3.0
-- ============================================================
