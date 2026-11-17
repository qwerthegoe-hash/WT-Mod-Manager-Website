# Validate a published WT Mod Manager Windows asset against SHA256SUMS.txt.
# Supply both downloaded files from the same verified GitHub Release page.
param(
    [Parameter(Mandatory = $true)][string]$Asset,
    [Parameter(Mandatory = $true)][string]$Manifest
)
$ErrorActionPreference = "Stop"
$assetPath = (Resolve-Path -LiteralPath $Asset -ErrorAction Stop).Path
$manifestPath = (Resolve-Path -LiteralPath $Manifest -ErrorAction Stop).Path
$name = [IO.Path]::GetFileName($assetPath)
$expected = $null

foreach ($line in Get-Content -LiteralPath $manifestPath -ErrorAction Stop) {
    if ($line -match '^([a-fA-F0-9]{64})  [*]?(.+)$') {
        if ($Matches[2] -ceq $name) {
            $expected = $Matches[1].ToLowerInvariant()
            break
        }
    }
}
if (-not $expected) {
    throw "SHA256SUMS.txt contains no checksum for the selected asset name."
}
$actual = (Get-FileHash -LiteralPath $assetPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -cne $expected) {
    throw "CHECKSUM MISMATCH: the file differs from the published checksum. Do not run it."
}
Write-Output ("PASS: SHA-256 matches published checksum for {0}" -f $name)
