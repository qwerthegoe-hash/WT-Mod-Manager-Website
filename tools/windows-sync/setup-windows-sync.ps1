# User-run Task Scheduler setup for WT Mod Manager GitHub synchronization.
# Default action DISABLE stops the old popping console without deleting any files.
# Run this on your own Windows computer, not on the GitHub server.
param(
    [ValidateSet("Disable", "InstallSafe", "Status")][string]$Mode = "Disable",
    [string]$OldTaskName = "WT-Mod-Manager-GitHub-Sync",
    [string]$SafeTaskName = "WT-Mod-Manager-GitHub-Sync-Safe"
)
$ErrorActionPreference = "Stop"

function Try-GetTask([string]$Name) {
    Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
}
function Disable-OldTask {
    $old = Try-GetTask $OldTaskName
    if (-not $old) {
        Write-Output "Old task not found; nothing to disable."
        return
    }
    if ($old.State -eq "Running") {
        Stop-ScheduledTask -TaskName $OldTaskName -ErrorAction Stop
    }
    Disable-ScheduledTask -TaskName $OldTaskName -ErrorAction Stop | Out-Null
    Write-Output "Old 1-minute task disabled. Local files were not touched."
}
if ($Mode -eq "Status") {
    foreach ($name in @($OldTaskName,$SafeTaskName)) {
        $task = Try-GetTask $name
        if ($task) { Write-Output ("{0}: {1}" -f $name, $task.State) }
        else { Write-Output ("{0}: not installed" -f $name) }
    }
    exit 0
}
if ($Mode -eq "Disable") {
    Disable-OldTask
    exit 0
}

# Optional silent replacement, once per user logon. The worker itself
# refuses to sync during detected games or when the worktree is not clean.
$launcher = Join-Path $PSScriptRoot "launch-hidden.vbs"
$worker = Join-Path $PSScriptRoot "sync-github-safe.ps1"
if (!(Test-Path -LiteralPath $launcher) -or !(Test-Path -LiteralPath $worker)) {
    throw "The safe sync scripts are missing from tools/windows-sync."
}
Disable-OldTask
$action = New-ScheduledTaskAction -Execute (Join-Path $env:WINDIR "System32\wscript.exe") -Argument ('"' + $launcher + '"')
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -StartWhenAvailable
Register-ScheduledTask -TaskName $SafeTaskName -Action $action -Trigger $trigger -Settings $settings -Description "Safe background WTMM git sync: skip games, dirty files, non-main branches" -Force | Out-Null
Write-Output "Safe task installed. It runs at user logon with a hidden window."
Write-Output "This does not silently overwrite untracked README.md or local edits."
