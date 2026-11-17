# WTMM opt-in safe local GitHub sync. Never deletes or overwrites local edits.
param(
    [Parameter(Mandatory = $true)][string]$RepositoryPath,
    [string[]]$GameProcessNames = @("aces", "cs2", "RobloxPlayerBeta", "Game")
)
$ErrorActionPreference = "Stop"
$logFolder = Join-Path $env:LOCALAPPDATA "WTModManagerGitSync"
$logFile = Join-Path $logFolder "sync-safe.log"
New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
function Write-LocalLog([string]$Text) {
    Add-Content -LiteralPath $logFile -Value ("{0:u} {1}" -f (Get-Date), $Text) -Encoding UTF8
}
try {
    if (-not (Test-Path -LiteralPath $RepositoryPath -PathType Container)) {
        Write-LocalLog "SKIP: repository folder missing"
        exit 0
    }
    foreach ($processName in $GameProcessNames) {
        if (Get-Process -Name $processName -ErrorAction SilentlyContinue) {
            Write-LocalLog "SKIP: game currently running"
            exit 0
        }
    }
    $gitDir = Join-Path $RepositoryPath ".git"
    if (-not (Test-Path -LiteralPath $gitDir)) {
        Write-LocalLog "SKIP: local folder is not a Git working tree"
        exit 0
    }
    $branchName = (& git -C $RepositoryPath branch --show-current 2>$null)
    if ($LASTEXITCODE -ne 0 -or $branchName.Trim() -ne "main") {
        Write-LocalLog "SKIP: expected current branch main"
        exit 0
    }
    # Respect untracked files as well as tracked changes (including README.md).
    $changes = @(& git -C $RepositoryPath status --porcelain --untracked-files=all)
    if ($LASTEXITCODE -ne 0 -or $changes.Count -gt 0) {
        Write-LocalLog "SKIP: local changes or untracked files require manual review"
        exit 0
    }
    & git -C $RepositoryPath fetch --quiet origin main 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Fetch failed" }
    & git -C $RepositoryPath merge --ff-only --quiet origin/main 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Fast-forward merge refused" }
    Write-LocalLog "OK: clean working tree fast-forwarded safely"
} catch {
    Write-LocalLog "ERROR: sync failed; no local files forcibly changed"
    exit 1
}
