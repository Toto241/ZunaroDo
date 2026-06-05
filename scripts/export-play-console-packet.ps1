#Requires -Version 5.1
<#
.SYNOPSIS
  Exportiert Play-Console-Artefakte (Data Safety, Checks) nach release/.
#>
[CmdletBinding()]
param(
    [switch] $SkipStrictCheck
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

Write-Step "Data Safety Markdown"
python -m tools.data_safety --markdown | Out-File -Encoding utf8 release\DATA_SAFETY_CONSOLE_ANSWERS.md
python -m tools.data_safety --check
if ($LASTEXITCODE -ne 0) { throw "data_safety --check fehlgeschlagen." }

if (-not $SkipStrictCheck) {
    Write-Step "Playstore strict check"
    python -m tools.playstore_check --strict
    if ($LASTEXITCODE -ne 0) { throw "playstore_check --strict fehlgeschlagen." }
}

Write-Step "Store listing check"
python -m tools.store_listing --check

Write-Host "`nFertig. Console-Copy-Paste: release\DATA_SAFETY_CONSOLE_ANSWERS.md" -ForegroundColor Green
