#Requires -Version 5.1
<#
.SYNOPSIS
    Erstellt den Upload-Keystore fuer die Play-Store-Signierung von ZunaroDo.

.DESCRIPTION
    Wrapper um `keytool` (Teil des JDK). Erzeugt einen RSA-2048-Schluessel mit
    10000 Tagen Gueltigkeit - so verlangt es Google fuer Upload-Keys.

    WICHTIG - Sicherheit:
      * Die abgefragten Passwoerter werden NICHT in einer Datei gespeichert.
        Bewahre sie in einem Passwort-Manager auf. Gehen sie verloren,
        kann (bei Play App Signing) nur ueber den Upload-Key-Reset wieder
        hochgeladen werden - ohne Play App Signing ist die App-Linie verloren.
      * Die erzeugte .jks-Datei NIEMALS ins Git committen. Sie ist in
        .gitignore ausgeschlossen; trotzdem vor jedem Commit pruefen.
      * Fuer CI: .jks base64-kodieren und zusammen mit den Passwoertern als
        GitHub-Secrets hinterlegen (siehe docs/android/07_CICD.md).

.EXAMPLE
    pwsh ./release/create_upload_keystore.ps1
#>
[CmdletBinding()]
param(
    [string]$KeystorePath = "$PSScriptRoot/keystore/alltagshelfer-upload.jks",
    [string]$Alias        = "alltagshelfer-upload",
    [int]$ValidityDays    = 10000
)

$ErrorActionPreference = "Stop"

# keytool finden (JAVA_HOME oder PATH). Kein ?.-Operator, damit das Skript
# auch unter Windows PowerShell 5.1 (Win11-Default) laeuft, nicht nur pwsh 7+.
$keytoolCmd = Get-Command keytool -ErrorAction SilentlyContinue
$keytool = if ($keytoolCmd) { $keytoolCmd.Source } else { $null }
if (-not $keytool -and $env:JAVA_HOME) {
    $cand = Join-Path $env:JAVA_HOME "bin/keytool.exe"
    if (Test-Path $cand) { $keytool = $cand }
}
if (-not $keytool) {
    Write-Error "keytool nicht gefunden. JDK 17 installieren (z. B. Temurin) und JAVA_HOME setzen."
    return
}

$dir = Split-Path -Parent $KeystorePath
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

if (Test-Path $KeystorePath) {
    Write-Error "Keystore existiert bereits: $KeystorePath - Abbruch (nicht ueberschreiben!)."
    return
}

Write-Host "Erzeuge Upload-Keystore:" -ForegroundColor Cyan
Write-Host "  Datei : $KeystorePath"
Write-Host "  Alias : $Alias"
Write-Host "  Gueltig: $ValidityDays Tage"
Write-Host "keytool fragt gleich nach Keystore- und Key-Passwort (merken!)." -ForegroundColor Yellow

& $keytool -genkeypair -v `
    -keystore $KeystorePath `
    -alias $Alias `
    -keyalg RSA -keysize 2048 `
    -validity $ValidityDays `
    -storetype JKS

if ($LASTEXITCODE -ne 0) { Write-Error "keytool fehlgeschlagen (Exit $LASTEXITCODE)."; return }

Write-Host ""
Write-Host "Fertig. Naechste Schritte:" -ForegroundColor Green
Write-Host "  1. Passwoerter im Passwort-Manager sichern."
Write-Host "  2. Fuer lokalen Release-Build die Env-Vars setzen:"
Write-Host '       $env:P4A_RELEASE_KEYSTORE        = "' -NoNewline; Write-Host "$KeystorePath`""
Write-Host '       $env:P4A_RELEASE_KEYSTORE_PASSWD = "<keystore-passwort>"'
Write-Host "       `$env:P4A_RELEASE_KEYALIAS        = `"$Alias`""
Write-Host '       $env:P4A_RELEASE_KEYALIAS_PASSWD = "<key-passwort>"'
Write-Host "  3. Fuer den GitHub-Release-Workflow (.github/workflows/android-release.yml)"
Write-Host "     diese vier Repo-Secrets setzen (Settings -> Secrets and variables -> Actions):"
Write-Host "       ANDROID_KEYSTORE_BASE64     = Base64 der .jks   (PowerShell:"
Write-Host "                                     [Convert]::ToBase64String([IO.File]::ReadAllBytes('$KeystorePath')) )"
Write-Host "       ANDROID_KEYSTORE_PASSWORD   = <keystore-passwort>"
Write-Host "       ANDROID_KEY_ALIAS           = $Alias"
Write-Host "       ANDROID_KEY_ALIAS_PASSWORD  = <key-passwort>"
Write-Host "  4. .jks NIEMALS committen."
