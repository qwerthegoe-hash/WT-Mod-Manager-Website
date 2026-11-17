
-- ============================================================
-- WT MOD MANAGER — WT GUARDIAN 2.0
-- PostgreSQL / Supabase
--
-- Install AFTER:
--   1. community.sql (version 3.0)
--   2. media_upgrade.sql
--
-- IMPORTANT:
-- Back up the database before running migrations.
-- The client must use guardian_send_message RPC after this.
-- ============================================================

begin;

-- ============================================================
-- 1. ADMINISTRATOR-CONTROLLED SETTINGS
-- ============================================================

create table if not exists public.guardian_settings (
    id integer primary key default 1
        check (id = 1),

    enabled boolean not null default true,

    block_links boolean not null default true,

    detect_obfuscation boolean not null default true,

    detect_spam boolean not null default true,

    detect_duplicates boolean not null default true,

    detect_flood boolean not null default true,

    issue_warnings boolean not null default true,

    min_delay_seconds integer not null default 3
        check (min_delay_seconds between 1 and 60),

    hourly_limit integer not null default 40
        check (hourly_limit between 5 and 500),

    duplicate_window_minutes integer not null default 10
        check (duplicate_window_minutes between 1 and 120),

    warning_limit integer not null default 3
        check (warning_limit between 1 and 10),

    mute_minutes integer not null default 15
        check (mute_minutes between 1 and 10080),

    updated_at timestamptz not null default now()
);

insert into public.guardian_settings (id)
values (1)
on conflict (id) do nothing;


-- ============================================================
-- 2. USER MODERATION STATE
-- ============================================================

create table if not exists public.guardian_user_state (
    user_id uuid primary key,

    warning_count integer not null default 0
        check (warning_count >= 0),

    last_warning_at timestamptz,

    muted_until timestamptz,

    updated_at timestamptz not null default now()
);


-- ============================================================
-- 3. MODERATION EVENT LOG
-- ============================================================

create table if not exists public.guardian_events (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null,

    event_type text not null,

    details text not null default '',

    warning_count integer not null default 0,

    created_at timestamptz not null default now(),

    constraint guardian_event_details_limit
        check (char_length(details) <= 300)
);

create index if not exists guardian_events_recent
on public.guardian_events(created_at desc);

create index if not exists guardian_events_user
on public.guardian_events(user_id, created_at desc);


-- ============================================================
-- 4. TRUSTED GUARDIAN NOTIFICATIONS
-- ============================================================

-- These are separate from player messages.
-- A player cannot create or impersonate a Guardian notice.

create table if not exists public.guardian_notices (
    id uuid primary key default gen_random_uuid(),

    recipient_id uuid,

    notice_type text not null default 'info',

    body text not null,

    created_at timestamptz not null default now(),

    created_by uuid,

    constraint guardian_notice_length
        check (char_length(body) between 1 and 1000)
);

create index if not exists guardian_notices_recipient
on public.guardian_notices(
    recipient_id,
    created_at desc
);


-- ============================================================
-- 5. PERMISSIONS AND RLS
-- ============================================================

alter table public.guardian_settings
enable row level security;

alter table public.guardian_user_state
enable row level security;

alter table public.guardian_events
enable row level security;

alter table public.guardian_notices
enable row level security;

revoke all on public.guardian_settings
from anon, authenticated;

revoke all on public.guardian_user_state
from anon, authenticated;

revoke all on public.guardian_events
from anon, authenticated;

revoke all on public.guardian_notices
from anon, authenticated;

grant select on public.guardian_settings
to authenticated;

grant select on public.guardian_user_state
to authenticated;

grant select on public.guardian_events
to authenticated;

grant select on public.guardian_notices
to authenticated;


drop policy if exists
    "Guardian settings read"
on public.guardian_settings;

create policy "Guardian settings read"
on public.guardian_settings
for select to authenticated
using (true);


drop policy if exists
    "Guardian state read"
on public.guardian_user_state;

create policy "Guardian state read"
on public.guardian_user_state
for select to authenticated
using (
    user_id = (select auth.uid())
    or (select public.community_is_admin())
);


drop policy if exists
    "Guardian events admin read"
on public.guardian_events;

create policy "Guardian events admin read"
on public.guardian_events
for select to authenticated
using (
    (select public.community_is_admin())
);


drop policy if exists
    "Guardian notices read"
on public.guardian_notices;

create policy "Guardian notices read"
on public.guardian_notices
for select to authenticated
using (
    recipient_id is null
    or recipient_id = (select auth.uid())
);


-- ============================================================
-- 6. MESSAGE INSPECTION ENGINE
-- ============================================================

create or replace function public.guardian_inspect(
    p_user uuid,
    p_channel text,
    p_nickname text,
    p_body text,
    p_attachment text
)
returns text

language plpgsql
security definer
set search_path = ''

as $$
declare
    cfg public.guardian_settings%rowtype;

    body_text text := btrim(coalesce(p_body, ''));
    name_text text := btrim(coalesce(p_nickname, ''));

    compact_text text;
    simplified_text text;
    letter_text text;

    message_count integer;

begin

    select *
    into cfg
    from public.guardian_settings
    where id = 1;

    if not found then
        return 'configuration';
    end if;

    if p_user is null
       or p_user is distinct from auth.uid()
    then
        return 'authentication';
    end if;

    -- General validation remains enabled even when
    -- optional moderation rules are switched off.

    if p_channel not in (
        'general', 'updates', 'news', 'ideas', 'help'
    ) then
        return 'invalid_channel';
    end if;

    if char_length(name_text) not between 2 and 24 then
        return 'invalid_nickname';
    end if;

    if char_length(body_text) > 1500 then
        return 'message_too_long';
    end if;

    if body_text = '' and p_attachment is null then
        return 'empty_message';
    end if;

    if not exists (
        select 1
        from public.community_admins
        where user_id = p_user
    ) then

        if p_channel = 'news' then
            return 'admin_only';
        end if;

        if lower(name_text) in (
            'admin',
            'administrator',
            'developer',
            'moderator',
            'system',
            'system bot',
            'wt guardian',
            'wt mod manager'
        ) then
            return 'reserved_nickname';
        end if;
    end if;

    -- Respect existing administrator restrictions.

    if exists (
        select 1
        from public.community_mutes
        where user_id = p_user
          and muted_until > now()
    ) then
        return 'muted';
    end if;

    if exists (
        select 1
        from public.guardian_user_state
        where user_id = p_user
          and muted_until > now()
    ) then
        return 'muted';
    end if;

    -- Only approved media owned by this user
    -- may be attached to a message.

    if p_attachment is not null then
        if not exists (
            select 1
            from public.community_media_jobs
            where user_id = p_user
              and published_path = p_attachment
              and status = 'approved'
        ) then
            return 'unapproved_media';
        end if;
    end if;

    if not cfg.enabled then
        return 'ok';
    end if;

    -- Remove whitespace and common invisible characters
    -- for approximate obfuscation detection.

    compact_text := lower(body_text);

    compact_text := replace(
        compact_text, chr(8203), ''
    );

    compact_text := replace(
        compact_text, chr(8204), ''
    );

    compact_text := replace(
        compact_text, chr(8205), ''
    );

    compact_text := replace(
        compact_text, chr(8288), ''
    );

    compact_text := regexp_replace(
        compact_text,
        '[[:space:]]+',
        '',
        'g'
    );

    -- Replace several Cyrillic look-alike characters.
    -- This is a heuristic, not full Unicode protection.

    simplified_text := translate(
        compact_text,
        'аеорсухі',
        'aeopcyxi'
    );

    -- Standard link detection.

    if cfg.block_links then

        if body_text ~* (
            '(https?://|www\.|discord\.gg/|' ||
            'discord\.com/invite/|t\.me/|' ||
            '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|' ||
            '[a-z0-9_-]+\.(com|net|org|io|gg|ru|ua|' ||
            'me|xyz|app|dev|site|link|click|top)' ||
            '(/|[[:space:]]|$))'
        ) then
            return 'blocked_link';
        end if;

        if cfg.detect_obfuscation then

            if simplified_text ~* (
                '(https?://|www\.|discord\.gg|' ||
                'discord\.com/invite|t\.me)'
            ) then
                return 'obfuscated_link';
            end if;

            if simplified_text ~* (
                '[a-z0-9_-]+\.(com|net|org|io|gg|' ||
                'ru|ua|me|xyz|app|dev|site|link|' ||
                'click|top)(/|$)'
            ) then
                return 'obfuscated_link';
            end if;

        end if;
    end if;

    -- Flooding with repeated characters.

    if cfg.detect_flood then

        if body_text ~ '(.)\1{15,}' then
            return 'character_flood';
        end if;

        letter_text := regexp_replace(
            body_text,
            '[^[:alpha:]]',
            '',
            'g'
        );

        -- Repeated all-caps text is flagged only
        -- when the message is substantial.
        if char_length(letter_text) >= 40
           and letter_text = upper(letter_text)
           and letter_text <> lower(letter_text)
        then
            return 'caps_flood';
        end if;

    end if;

    -- Server-side rate limits.

    if cfg.detect_spam then

        if exists (
            select 1
            from public.community_messages
            where user_id = p_user
              and created_at > (
                  now() -
                  make_interval(
                      secs => cfg.min_delay_seconds
                  )
              )
        ) then
            return 'sending_too_fast';
        end if;

        select count(*)
        into message_count
        from public.community_messages
        where user_id = p_user
          and created_at > now() - interval '1 hour';

        if message_count >= cfg.hourly_limit then
            return 'hourly_limit';
        end if;
    end if;

    -- Detect repeat messages over the configured window.

    if cfg.detect_duplicates
       and char_length(body_text) >= 12
    then

        if exists (
            select 1
            from public.community_messages
            where user_id = p_user
              and lower(btrim(body)) = lower(body_text)
              and created_at > (
                  now() -
                  make_interval(
                      mins => cfg.duplicate_window_minutes
                  )
              )
        ) then
            return 'duplicate_message';
        end if;

    end if;

    -- Profanity by itself is not considered a violation.
    return 'ok';

end;
$$;

revoke all
on function public.guardian_inspect(
    uuid, text, text, text, text
)
from public, anon, authenticated;


-- ============================================================
-- 7. RECORD WARNING WITHOUT THROWING EXCEPTIONS
-- ============================================================

create or replace function public.guardian_warn(
    p_user uuid,
    p_code text
)
returns jsonb

language plpgsql
security definer
set search_path = ''

as $$
declare
    cfg public.guardian_settings%rowtype;

    warnings integer;
    mute_end timestamptz;
    last_warn timestamptz;

begin

    if p_user is distinct from auth.uid() then
        raise exception 'Invalid sender';
    end if;

    select *
    into cfg
    from public.guardian_settings
    where id = 1;

    -- Avoid unbounded logs from repeated invalid requests.

    if (
        select count(*)
        from public.guardian_events
        where user_id = p_user
          and created_at > now() - interval '10 minutes'
    ) >= 12 then

        return jsonb_build_object(
            'ok', false,
            'code', p_code,
            'rate_limited', true
        );

    end if;

    if not cfg.issue_warnings then
        return jsonb_build_object(
            'ok', false,
            'code', p_code,
            'warning_count', 0
        );
    end if;

    insert into public.guardian_user_state (
        user_id,
        warning_count,
        last_warning_at,
        updated_at
    )
    values (
        p_user, 1, now(), now()
    )
    on conflict (user_id)
    do update set
        warning_count = case
            when guardian_user_state.last_warning_at
                 < now() - interval '7 days'
              or guardian_user_state.last_warning_at is null
            then 1
            else guardian_user_state.warning_count + 1
        end,
        last_warning_at = now(),
        updated_at = now()
    returning
        warning_count,
        muted_until,
        last_warning_at
    into warnings, mute_end, last_warn;

    if warnings >= cfg.warning_limit then

        mute_end := now() + make_interval(
            mins => cfg.mute_minutes
        );

        update public.guardian_user_state
        set
            muted_until = mute_end,
            warning_count = 0,
            updated_at = now()
        where user_id = p_user;

        insert into public.community_mutes (
            user_id,
            reason,
            muted_until
        )
        values (
            p_user,
            'WT Guardian: automatic moderation',
            mute_end
        )
        on conflict (user_id)
        do update set
            reason = excluded.reason,
            muted_until = greatest(
                community_mutes.muted_until,
                excluded.muted_until
            );

    end if;

    insert into public.guardian_events (
        user_id,
        event_type,
        details,
        warning_count
    )
    values (
        p_user,
        case
            when mute_end is not null
             and mute_end > now()
            then 'automatic_mute'
            else 'warning'
        end,
        left(p_code, 300),
        warnings
    );

    insert into public.guardian_notices (
        recipient_id,
        notice_type,
        body
    )
    values (
        p_user,
        case
            when mute_end is not null
             and mute_end > now()
            then 'mute'
            else 'warning'
        end,
        case
            when mute_end is not null
             and mute_end > now()
            then
                'WT Guardian: отправка сообщений временно ' ||
                'ограничена из-за повторных нарушений.'
            else
                'WT Guardian: сообщение отклонено. ' ||
                'Причина: ' || left(p_code, 100)
        end
    );

    return jsonb_build_object(
        'ok', false,
        'code', p_code,
        'warning_count', warnings,
        'muted_until', mute_end
    );

end;
$$;

revoke all
on function public.guardian_warn(uuid, text)
from public, anon, authenticated;


-- ============================================================
-- 8. PROTECT DIRECT TABLE INSERTS
-- ============================================================

-- Keep the existing trigger name so that the earlier
-- community schema remains compatible.
--
-- Direct inserts cannot bypass Guardian.
-- Rejected requests must use the RPC to record warnings.

create or replace function public.check_community_message()
returns trigger

language plpgsql
security definer
set search_path = ''

as $$
declare
    result_code text;
begin

    if auth.uid() is null
       or new.user_id is distinct from auth.uid()
    then
        raise exception 'Authentication required';
    end if;

    new.id := gen_random_uuid();
    new.created_at := now();
    new.nickname := btrim(coalesce(new.nickname, ''));
    new.body := btrim(coalesce(new.body, ''));
    new.is_hidden := false;
    new.hidden_at := null;

    perform pg_advisory_xact_lock(
        92141,
        hashtext(new.user_id::text)
    );

    result_code := public.guardian_inspect(
        new.user_id,
        new.channel,
        new.nickname,
        new.body,
        new.attachment_path
    );

    if result_code <> 'ok' then
        raise exception 'WT Guardian: %', result_code;
    end if;

    return new;
end;
$$;

revoke all
on function public.check_community_message()
from public, anon, authenticated;

-- Remove browser permission to insert directly.
-- Authenticated players can now send through RPC only.

revoke insert
on public.community_messages
from authenticated;

-- Keep SELECT permissions and RLS read policies unchanged.


-- ============================================================
-- 9. TRUSTED MESSAGE-SENDING API
-- ============================================================

create or replace function public.guardian_send_message(
    p_channel text,
    p_nickname text,
    p_body text,
    p_attachment_path text default null
)
returns jsonb

language plpgsql
security definer
set search_path = ''

as $$
declare
    sender uuid := auth.uid();
    result_code text;

    inserted_id uuid;
    warning_result jsonb;

begin

    if sender is null then
        raise exception 'Authentication required';
    end if;

    -- Serialize requests from the same user.

    perform pg_advisory_xact_lock(
        92141,
        hashtext(sender::text)
    );

    result_code := public.guardian_inspect(
        sender,
        p_channel,
        p_nickname,
        p_body,
        p_attachment_path
    );

    if result_code <> 'ok' then

        -- Input errors and access errors do not
        -- automatically count as warnings.

        if result_code in (
            'invalid_channel',
            'invalid_nickname',
            'message_too_long',
            'empty_message',
            'admin_only',
            'reserved_nickname',
            'unapproved_media',
            'authentication',
            'configuration',
            'muted'
        ) then

            return jsonb_build_object(
                'ok', false,
                'code', result_code,
                'warning_count', 0
            );

        end if;

        warning_result := public.guardian_warn(
            sender,
            result_code
        );

        return warning_result;
    end if;

    insert into public.community_messages (
        user_id,
        nickname,
        channel,
        body,
        attachment_path
    )
    values (
        sender,
        btrim(p_nickname),
        p_channel,
        btrim(coalesce(p_body, '')),
        p_attachment_path
    )
    returning id into inserted_id;

    return jsonb_build_object(
        'ok', true,
        'message_id', inserted_id
    );

end;
$$;

revoke all
on function public.guardian_send_message(
    text, text, text, text
)
from public, anon, authenticated;

grant execute
on function public.guardian_send_message(
    text, text, text, text
)
to authenticated;


-- ============================================================
-- 10. ADMINISTRATOR SETTINGS API
-- ============================================================

create or replace function public.guardian_set_settings(
    p_settings jsonb
)
returns jsonb

language plpgsql
security definer
set search_path = ''

as $$
declare
    setting_name text;
    updated public.guardian_settings%rowtype;
begin

    if auth.uid() is null
       or not public.community_is_admin()
    then
        raise exception 'Administrator access required';
    end if;

    if p_settings is null
       or jsonb_typeof(p_settings) <> 'object'
    then
        raise exception 'Invalid settings object';
    end if;

    -- Do not accept arbitrary column names.

    for setting_name in
        select jsonb_object_keys(p_settings)
    loop
        if setting_name not in (
            'enabled',
            'block_links',
            'detect_obfuscation',
            'detect_spam',
            'detect_duplicates',
            'detect_flood',
            'issue_warnings',
            'min_delay_seconds',
            'hourly_limit',
            'duplicate_window_minutes',
            'warning_limit',
            'mute_minutes'
        ) then
            raise exception
                'Unknown setting: %', setting_name;
        end if;
    end loop;

    update public.guardian_settings
    set
        enabled = coalesce(
            (p_settings->>'enabled')::boolean,
            enabled
        ),
        block_links = coalesce(
            (p_settings->>'block_links')::boolean,
            block_links
        ),
        detect_obfuscation = coalesce(
            (p_settings->>'detect_obfuscation')::boolean,
            detect_obfuscation
        ),
        detect_spam = coalesce(
            (p_settings->>'detect_spam')::boolean,
            detect_spam
        ),
        detect_duplicates = coalesce(
            (p_settings->>'detect_duplicates')::boolean,
            detect_duplicates
        ),
        detect_flood = coalesce(
            (p_settings->>'detect_flood')::boolean,
            detect_flood
        ),
        issue_warnings = coalesce(
            (p_settings->>'issue_warnings')::boolean,
            issue_warnings
        ),
        min_delay_seconds = coalesce(
            (p_settings->>'min_delay_seconds')::integer,
            min_delay_seconds
        ),
        hourly_limit = coalesce(
            (p_settings->>'hourly_limit')::integer,
            hourly_limit
        ),
        duplicate_window_minutes = coalesce(
            (p_settings->>'duplicate_window_minutes')::integer,
            duplicate_window_minutes
        ),
        warning_limit = coalesce(
            (p_settings->>'warning_limit')::integer,
            warning_limit
        ),
        mute_minutes = coalesce(
            (p_settings->>'mute_minutes')::integer,
            mute_minutes
        ),
        updated_at = now()
    where id = 1
    returning * into updated;

    insert into public.guardian_events (
        user_id,
        event_type,
        details
    )
    values (
        auth.uid(),
        'settings_updated',
        'Guardian settings updated by administrator'
    );

    return to_jsonb(updated);

end;
$$;

revoke all
on function public.guardian_set_settings(jsonb)
from public, anon, authenticated;

grant execute
on function public.guardian_set_settings(jsonb)
to authenticated;


-- ============================================================
-- 11. TRUSTED GUARDIAN ANNOUNCEMENTS
-- ============================================================

create or replace function public.guardian_announce(
    p_body text
)
returns uuid

language plpgsql
security definer
set search_path = ''

as $$
declare
    new_id uuid;
begin

    if auth.uid() is null
       or not public.community_is_admin()
    then
        raise exception 'Administrator access required';
    end if;

    if char_length(btrim(coalesce(p_body, '')))
       not between 1 and 1000
    then
        raise exception 'Invalid announcement length';
    end if;

    insert into public.guardian_notices (
        recipient_id,
        notice_type,
        body,
        created_by
    )
    values (
        null,
        'announcement',
        btrim(p_body),
        auth.uid()
    )
    returning id into new_id;

    return new_id;

end;
$$;

revoke all
on function public.guardian_announce(text)
from public, anon, authenticated;

grant execute
on function public.guardian_announce(text)
to authenticated;


-- ============================================================
-- 12. FINISH
-- ============================================================

commit;

-- ============================================================
-- END — WT GUARDIAN 2.0
-- ============================================================
