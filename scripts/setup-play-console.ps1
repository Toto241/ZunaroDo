#Requires -Version 5.1
<#
.SYNOPSIS
  Einmal-Setup vor Play-Console-Ausfuellung: Checks + Exporte + Checkliste.
#>
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "`n=== ZunaroDo Play Console Setup ===" -ForegroundColor Cyan

& "$PSScriptRoot\export-play-console-packet.ps1"
& "$PSScriptRoot\prepare-closed-test.ps1"

$checklist = @"
# Play Console Checkliste (generiert)

## Vor dem Oeffnen der Console
- [ ] ``python -m tools.playstore_check --strict`` gruen
- [ ] ``release/DATA_SAFETY_CONSOLE_ANSWERS.md`` aktuell
- [ ] Privacy URL: https://toto241.github.io/ZunaroDo/privacy/

## In der Console
- [ ] App content -> Data safety (Copy-Paste aus DATA_SAFETY_CONSOLE_ANSWERS.md)
- [ ] App content -> Target audience (>= 13, keine Kinder)
- [ ] Store listing (Texte: ``python -m tools.store_listing --check``)
- [ ] Content rating Fragebogen
- [ ] Testing -> Closed testing (AAB + Tester-Gruppe)
- [ ] Monetization: In-app purchases = Nein (bis Play Billing live)

## Nach Closed Test (14 Tage)
- [ ] Production access beantragen
- [ ] ``release/closed-test-YYYY-MM.md`` mit echten Console-Daten
"@

$checklist | Out-File -Encoding utf8 release\PLAY_CONSOLE_CHECKLIST.md
Write-Host "`nCheckliste: release\PLAY_CONSOLE_CHECKLIST.md" -ForegroundColor Green
