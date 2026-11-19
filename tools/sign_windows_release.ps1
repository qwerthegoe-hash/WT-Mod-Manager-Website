param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("payload", "installer")]
  [string]$Stage
)
$ErrorActionPreference = "Stop"

# Code-signing keys are ONLY provided by the owner in GitHub Actions secrets.
# If none are configured, do not pretend that the release is signed.
$encoded = $env:WTMM_SIGN_PFX_BASE64
$password = $env:WTMM_SIGN_PFX_PASSWORD
if (-not $encoded -and -not $password) {
  Write-Output "No code-signing certificate configured: release remains unsigned."
  exit 0
}
if (-not $encoded -or -not $password) {
  throw "Both code-signing secrets must be configured together."
}

$exe = Get-Command signtool.exe -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty Source -First 1
if (-not $exe) {
  $candidates = Get-ChildItem -Path "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Filter signtool.exe -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -like "*\x64\signtool.exe" } |
    Sort-Object FullName -Descending
  if ($candidates) { $exe = $candidates[0].FullName }
}
if (-not $exe) { throw "Windows SDK SignTool was not found." }

$privateKeyPath = Join-Path $env:RUNNER_TEMP ([Guid]::NewGuid().ToString() + ".pfx")
try {
  [IO.File]::WriteAllBytes($privateKeyPath, [Convert]::FromBase64String($encoded))
  if ($Stage -eq "payload") {
    $paths = @(
      "build\wtmm_taskbar.dll",
      "dist\WTModManager.exe",
      "dist\WTModManager\WTModManager.exe"
    )
  } else {
    $paths = @("dist\WTModManager-Setup.exe")
  }
  foreach ($path in $paths) {
    if (-not (Test-Path $path)) { throw "Missing file for signing: $path" }
    & $exe sign /f $privateKeyPath /p $password /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $path
    if ($LASTEXITCODE -ne 0) { throw "Authenticode signing failed for $path" }
    & $exe verify /pa /v $path
    if ($LASTEXITCODE -ne 0) { throw "Signature verification failed for $path" }
    Write-Output "Verified Authenticode signature: $path"
  }
}
finally {
  Remove-Item -LiteralPath $privateKeyPath -Force -ErrorAction SilentlyContinue
}
