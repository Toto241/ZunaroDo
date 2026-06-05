#Requires -Version 5.1
<#
.SYNOPSIS
  Vorbereitung Closed Test (12 Tester / 14 Tage) fuer ZunaroDo.
#>
[CmdletBinding()]
param(
    [string] $Owner = "Toto241",
    [string] $Repo = "ZunaroDo"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

Write-Step "Closed-Test-Konfiguration (playstore.yml)"
Select-String -Path playstore.yml -Pattern "min_testers|min_days|zunarodo-closed" | ForEach-Object { $_.Line }

Write-Step "Release-Gate pruefen"
python -m tools.playstore_check --strict 2>&1 | Select-String -Pattern "closed_test|PASS|FAIL"

Write-Step "Google Group"
Write-Host "Tester-Gruppe: zunarodo-closed-testers@googlegroups.com"
Write-Host "Gruppe pflegen: https://groups.google.com/"

Write-Step "Play Console"
Write-Host "Closed testing: https://play.google.com/console"
Write-Host "1. Testing -> Closed testing -> Release mit AAB"
Write-Host "2. Testers -> Google Group zuweisen"
Write-Host "3. Opt-in-Link kopieren (siehe SecBrain: zunarodo-closed-test-playbook)"

$evidence = Get-ChildItem release\closed-test-*.md -ErrorAction SilentlyContinue
if ($evidence) {
    Write-Host "Nachweis-Datei(en): $($evidence.Name -join ', ')" -ForegroundColor Green
} else {
    Write-Warning "Kein release\closed-test-*.md — nach Test aus Vorlage anlegen."
}

Write-Step "Optional: AAB-Workflow"
Write-Host "gh workflow run `"Android Release (AAB)`" --repo $Owner/$Repo"

Write-Host "`nEinladungstext: docs/ENABLE_CLOSED_TEST.md oder SecBrain zunarodo-closed-test-playbook" -ForegroundColor DarkGray
