# WT Mod Manager — existing-feature upgrade, 2026-11-17

This batch **extends existing features** without deleting pages, channels, mod
submission, moderation, profiles, support, styling or existing user data.

## Included in this GitHub upgrade

| Existing section | New improvement | Safety note |
| --- | --- | --- |
| Community | Per-channel chat drafts in sessionStorage, unread count while the tab is hidden | Draft text stays in the current browser tab; no account keys or media bytes are saved |
| Community | Reuse unchanged message DOM nodes; reconnect Realtime after an error with bounded backoff | Server remains the authority; keep existing 30-second refresh fallback |
| WT Guardian | Search and type filter for the existing moderation log | Only existing administrator-authorized events are queried |
| Images | Refresh user image-review statuses and recognize processing states | Never re-upload an image automatically |
| Mod library | Stable server pagination with “Load more” instead of a hard cap at the first 150 records | Existing local search/sort/categories retained; current search covers loaded records |
| Mod library | Show other approved submissions by the same author under the same exact mod title | No private records or unapproved versions exposed; server RLS applies |
| Mod administration | Clickable summary filters for pending, approved and rejected loaded submissions | Existing pending-only approval flow remains unchanged |
| Profiles | Tab-session recovery for unsaved nickname, bio, public setting and accent color | No passwords, emails or image file bytes are saved |
| Support | Tab-session recovery of unfinished report text; no draft after successful submission | Name/email are deliberately excluded from saved drafts |
| Diagnostics | Opt-in report copy with error categories/counters, no full stack traces or tokens | Nothing uploaded automatically |
| Windows sync | Optional hidden, game-aware, clean-worktree-only local synchronization | Does not alter Task Scheduler on the user's PC |
| Testing | JavaScript unit tests, static feature checks, PowerShell parser check | Does not replace real browser/account QA |

## Important limitations and follow-up work

- **ClamAV for mod ZIPs:** the repository contains an opt-in server-side worker,
  but the workflow requires encrypted GitHub Secrets, an initial successful scan
  and a reviewed Supabase scan-gate migration before production activation.
  Never describe it as active without a successful worker run and verification.
- **Search:** existing client-side author/title/description search is preserved.
  Full global indexed search across all records will need a dedicated filtered
  Supabase query and further QA.
- **Versions:** history is inferred from approved submissions with the same
  title and author, not from a newly introduced mod-version table.
- **Unread badge:** counts new messages while the current chat tab is hidden,
  not unseen messages in every channel without an active subscription.
- **Media:** refresh status is supported; automatic server cleanup of expired
  quarantined media needs scheduled backend handling and storage retention rules.
- **Windows:** a GitHub commit cannot disable a local Windows scheduled task.
  See `tools/windows-sync/README.md` for safe opt-in migration.
- Automated tests cover syntax and regressions, but do not prove correct layout,
  actual email delivery or every Supabase RLS flow. Use normal, administrator
  and signed-out test sessions before declaring a complete launch.

## Verification

GitHub Actions `Website security and regression checks` runs on pull
requests and `main` pushes. Changes are introduced by PR and merged only
after automated checks pass. The original support form, chat and profile
functionality should also be manually smoke-tested.
