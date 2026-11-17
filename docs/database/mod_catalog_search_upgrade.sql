-- WT Mod Manager: RLS-preserving global catalog search.
-- Additive: keeps existing client queries and all existing tables/policies.
-- SECURITY INVOKER means the caller only sees rows already allowed by RLS.
begin;

create or replace function public.wtmm_search_mods(
  p_view text default 'catalog',
  p_status text default 'pending',
  p_category text default 'all',
  p_text text default '',
  p_sort text default 'new',
  p_offset integer default 0,
  p_limit integer default 150
)
returns table (
  id uuid, owner_id uuid, title text, description text, category text,
  version text, status text, file_path text, cover_path text,
  rejection_reason text, created_at timestamptz
)
language sql stable security invoker
set search_path = ''
as $$
  select
    m.id, m.owner_id, m.title, m.description, m.category,
    m.version, m.status, m.file_path, m.cover_path,
    m.rejection_reason, m.created_at
  from public.wtmm_mods m
  left join public.community_user_profiles p on p.user_id = m.owner_id
  where
    (
      (p_view = 'catalog' and m.status = 'approved')
      or (p_view = 'mine' and m.owner_id = (select auth.uid()))
      or (
        p_view = 'moderation'
        and (select public.wtmm_is_admin())
        and m.status = p_status
        and p_status in ('pending','approved','rejected')
      )
    )
    and (p_category = 'all' or m.category = p_category)
    and (
      nullif(btrim(p_text), '') is null
      or m.title ilike ('%' || left(btrim(p_text), 90) || '%')
      or m.description ilike ('%' || left(btrim(p_text), 90) || '%')
      or p.nickname ilike ('%' || left(btrim(p_text), 90) || '%')
    )
  order by
    case when p_sort = 'name' then lower(m.title) end asc nulls last,
    case when p_sort = 'old' then m.created_at end asc nulls last,
    case when p_sort not in ('name','old') then m.created_at end desc nulls last,
    m.id desc
  limit least(greatest(coalesce(p_limit,150),1),150)
  offset least(greatest(coalesce(p_offset,0),0),100000)
$$;

revoke all on function public.wtmm_search_mods(text,text,text,text,text,integer,integer)
  from public, anon;
grant execute on function public.wtmm_search_mods(text,text,text,text,text,integer,integer)
  to authenticated;

commit;
