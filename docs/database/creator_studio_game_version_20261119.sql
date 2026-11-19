-- Creator Studio metadata: declared game compatibility (not verified by WTMM).
-- Additive migration; keeps existing mods/permissions/approvals untouched.
alter table public.wtmm_mods
  add column if not exists game_version text;

alter table public.wtmm_mods
  drop constraint if exists wtmm_mods_game_version_format;

alter table public.wtmm_mods
  add constraint wtmm_mods_game_version_format
    check (
      game_version is null or
      (length(game_version) between 3 and 24 and
       game_version ~ '^[0-9]+([.][0-9]+){1,3})
    );

comment on column public.wtmm_mods.game_version is
  'Optional version claimed by mod author; not a verified compatibility certification.';
-- Original ownership RLS, MFA and server moderation protections remain active.
)
    );

comment on column public.wtmm_mods.game_version is
  'Optional version claimed by mod author; not a verified compatibility certification.';
-- Original ownership RLS, MFA and server moderation protections remain active.
