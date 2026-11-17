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

The worker detects War Thunder using `aces.exe`, `aces_BE.exe`, or
`aces-min-cpu.exe`, and also skips a few other configured game processes.
It checks at startup, before fetching, and immediately before merging, so a
game opened during a fetch will prevent the update from being applied.
It only runs `git fetch` plus `git merge --ff-only` on a clean `main`
branch. It cannot make the local folder conflict-free automatically,
which is intentional: local data is more important than forced updates.

**Note:** Task Scheduler can create tasks from a local administrator session.
Setting up or disabling your existing Windows task requires action on the PC;
changing files in GitHub cannot do it for you.


## One-command setup on your Windows computer

After updating this repository on the PC, open PowerShell **on your own
computer** in the repository folder. The safe setup does not delete files.

Disable the original task immediately (recommended when the console appears
during games):

```powershell
powershell -NoProfile -File ".\\tools\\windows-sync\\setup-windows-sync.ps1" -Mode Disable
```

Show task states without changing anything:

```powershell
powershell -NoProfile -File ".\\tools\\windows-sync\\setup-windows-sync.ps1" -Mode Status
```

Only if you want a replacement, install a hidden, **logon-only** task (no
per-minute popups; the worker skips known games and dirty working trees):

```powershell
powershell -NoProfile -File ".\\tools\\windows-sync\\setup-windows-sync.ps1" -Mode InstallSafe
```

Task Scheduler permissions might require opening PowerShell as an
administrator. `InstallSafe` also disables the old task before registering
the new one; it never runs `git reset --hard` or `git clean`.

Important: a GitHub commit cannot operate Task Scheduler on the PC remotely.
These commands must be executed locally by the Windows account owner.

## Check the War Thunder pause rule

While War Thunder is open, run:

```powershell
Get-Process -Name aces,aces_BE,aces-min-cpu -ErrorAction SilentlyContinue | Select-Object ProcessName, Id
```

If Windows reports one of these processes, the background sync worker will
skip its Git operations. Its decisions are logged to
`%LOCALAPPDATA%\WTModManagerGitSync\sync-safe.log`.

After pulling these script updates into the existing local repository, the
already-installed scheduled task uses the updated worker and launcher via
its existing file paths. There is no need to reinstall the task.
The launcher starts local PowerShell using a process-scoped
`-ExecutionPolicy RemoteSigned` option; it does not modify system policies.
