# WTMM: optional safe Windows background synchronization

This is an improvement for the *user's Windows computer*, not a browser feature.
Nothing in this folder changes Windows Task Scheduler automatically.

## What this solves

- A scheduled task starting PowerShell every minute can interrupt full-screen games.
- Git refuses to merge when an untracked `README.md` would be overwritten.
- Never fix that by deleting the README or running `git reset --hard`.

## Safe migration

1. Open Task Scheduler (`taskschd.msc`).
2. Locate the existing `WT-Mod-Manager-GitHub-Sync` task and **disable** it.
   Do not delete the current script or any local files.
3. Review the local working-tree conflicts manually (especially `README.md`).
   The new script deliberately **skips** syncing whenever it sees *any*
   changed or untracked files.
4. If you want silent updates, create a replacement task running
   `wscript.exe` and pass the full path to `tools\windows-sync\launch-hidden.vbs`
   as its argument. Choose a cadence such as 15 minutes instead of one minute.
5. Check `%LOCALAPPDATA%\WTModManagerGitSync\sync-safe.log` for results.

The worker skips selected games (process names configurable in PowerShell)
and only runs `git fetch` plus `git merge --ff-only` on a clean `main`
branch. It cannot make the local folder conflict-free automatically,
which is intentional: local data is more important than forced updates.

**Note:** Task Scheduler can create tasks from a local administrator session.
Setting up or disabling your existing Windows task requires action on the PC;
changing files in GitHub cannot do it for you.
