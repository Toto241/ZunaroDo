#Requires -Version 5.1
<#
.SYNOPSIS
  Aktiviert GitHub Pages (Actions), deployed die Privacy-Policy und prueft die URL.

.DESCRIPTION
  Ersetzt die manuellen Schritte aus docs/ENABLE_GITHUB_PAGES.md:
  - Pages-Site per GitHub REST API (build_type: workflow)
  - Repository-Variable PRIVACY_POLICY_URL
  - Lokales Rendern (tools.privacy_policy --build)
  - Workflow "Privacy-Policy Pages" starten und abwarten
  - HTTP-HEAD auf die Privacy-URL

  Platzhalter in legal/DATENSCHUTZ.md werden NICHT automatisch ausgefuellt
  (keine erfundenen Anbieterdaten). Optional: -LegalConfigJson mit Werten.

.PARAMETER Owner
  GitHub-Owner (Default: Toto241).

.PARAMETER Repo
  Repository-Name (Default: ZunaroDo).

.PARAMETER PrivacyUrl
  Ziel-URL fuer die Datenschutzerklaerung.

.PARAMETER Branch
  Branch fuer Pages-Source-Metadaten (Default: main).

.PARAMETER SkipWorkflow
  Nur API/Variable/Build, kein Workflow-Deploy.

.PARAMETER LegalConfigJson
  JSON-Datei mit Ersetzungen fuer Platzhalter, z.B.:
  { "ANBIETER_NAME": "Max Mustermann", "EMAIL": "kontakt@example.de", ... }

.EXAMPLE
  .\scripts\setup-github-pages.ps1

.EXAMPLE
  .\scripts\setup-github-pages.ps1 -LegalConfigJson .\config\legal-publisher.json
#>
[CmdletBinding()]
param(
    [string] $Owner = "Toto241",
    [string] $Repo = "ZunaroDo",
    [string] $PrivacyUrl = "https://toto241.github.io/ZunaroDo/privacy/",
    [string] $Branch = "main",
    [switch] $SkipWorkflow,
    [string] $LegalConfigJson = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Ensure-GhAuth {
    Write-Step "GitHub CLI pruefen"
    $null = Get-Command gh -ErrorAction Stop
    gh auth status 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "gh nicht eingeloggt. Bitte: gh auth login" }
}

function Enable-PagesWorkflow {
    Write-Step "GitHub Pages aktivieren (build_type=workflow)"
    $endpoint = "repos/$Owner/$Repo/pages"
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    $existing = gh api $endpoint 2>&1
    if ($LASTEXITCODE -eq 0 -and ($existing -match '"build_type"\s*:\s*"workflow"')) {
        Write-Host "Pages bereits aktiv (workflow)."
        $ErrorActionPreference = $prevEap
        return
    }

    $null = gh api -X POST $endpoint `
        -f build_type=workflow `
        -f "source[branch]=$Branch" `
        -f "source[path]=/" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $null = gh api -X PUT $endpoint `
            -f build_type=workflow `
            -f "source[branch]=$Branch" `
            -f "source[path]=/" 2>&1
        if ($LASTEXITCODE -ne 0) {
            $ErrorActionPreference = $prevEap
            throw "Pages konnte nicht konfiguriert werden (POST/PUT fehlgeschlagen)."
        }
        Write-Host "Pages-Site aktualisiert (PUT)."
    } else {
        Write-Host "Pages-Site erstellt (POST)."
    }

    $info = gh api $endpoint 2>&1
    Write-Host "Pages-Status: $info"
    $ErrorActionPreference = $prevEap
}

function Set-PrivacyVariable {
    Write-Step "Repository-Variable PRIVACY_POLICY_URL setzen"
    gh variable set PRIVACY_POLICY_URL --repo "$Owner/$Repo" --body $PrivacyUrl 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Variable konnte nicht gesetzt werden." }
}

function Apply-LegalPlaceholders {
    if (-not $LegalConfigJson) { return }
    Write-Step "Legal-Platzhalter aus $LegalConfigJson"
    if (-not (Test-Path $LegalConfigJson)) {
        throw "LegalConfigJson nicht gefunden: $LegalConfigJson"
    }
    $map = Get-Content $LegalConfigJson -Raw -Encoding UTF8 | ConvertFrom-Json
    $files = @(
        "legal/DATENSCHUTZ.md",
        "legal/IMPRESSUM.md",
        "legal/AGB.md",
        "legal/WIDERRUF.md"
    )
    foreach ($rel in $files) {
        $path = Join-Path $RepoRoot $rel
        if (-not (Test-Path $path)) { continue }
        $text = Get-Content $path -Raw -Encoding UTF8
        foreach ($prop in $map.PSObject.Properties) {
            $key = "[{0}]" -f $prop.Name
            $text = $text.Replace($key, [string]$prop.Value)
        }
        Set-Content -Path $path -Value $text -Encoding UTF8 -NoNewline
        Write-Host "Aktualisiert: $rel"
    }
}

function Build-PrivacyHtml {
    Write-Step "Privacy-HTML lokal bauen"
    python -m tools.privacy_policy --build
    if ($LASTEXITCODE -ne 0) { throw "privacy_policy --build fehlgeschlagen." }
    python -m tools.privacy_policy --list-placeholders 2>&1 | ForEach-Object {
        if ($_ -match '^\[') {
            Write-Warning "Offener Platzhalter: $_ (vor Production ausfuellen oder -LegalConfigJson nutzen)"
        }
    }
}

function Invoke-PrivacyWorkflow {
    Write-Step "Workflow 'Privacy-Policy Pages' starten"
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $null = gh workflow run "Privacy-Policy Pages" --repo "$Owner/$Repo" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $ErrorActionPreference = $prevEap
        throw "Workflow-Start fehlgeschlagen."
    }
    Start-Sleep -Seconds 5
    $runId = gh run list --repo "$Owner/$Repo" --workflow "pages.yml" --limit 1 --json databaseId --jq ".[0].databaseId" 2>&1
    if (-not $runId -or $runId -match "error|failed") {
        $runId = gh run list --repo "$Owner/$Repo" --limit 3 --json databaseId,displayTitle --jq '.[] | select(.displayTitle|test("Privacy|Pages")) | .databaseId' 2>&1 | Select-Object -First 1
    }
    if (-not $runId) {
        $ErrorActionPreference = $prevEap
        throw "Run-ID nicht gefunden."
    }
    Write-Host "Run-ID: $runId - warte auf Abschluss ..."
    gh run watch $runId --repo "$Owner/$Repo" --exit-status 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        $ErrorActionPreference = $prevEap
        throw "Pages-Workflow fehlgeschlagen."
    }
    $ErrorActionPreference = $prevEap
}

function Test-PrivacyUrl {
    Write-Step "Privacy-URL pruefen ($PrivacyUrl)"
    $max = 12
    for ($i = 1; $i -le $max; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri $PrivacyUrl -Method Head -UseBasicParsing -TimeoutSec 30
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) {
                Write-Host "OK HTTP $($resp.StatusCode)" -ForegroundColor Green
                return
            }
        } catch {
            Write-Host "Versuch $i/$max : $($_.Exception.Message)"
        }
        Start-Sleep -Seconds 10
    }
    throw "Privacy-URL nach $max Versuchen nicht erreichbar."
}

# --- Main ---
Ensure-GhAuth
Enable-PagesWorkflow
Set-PrivacyVariable
Apply-LegalPlaceholders
Build-PrivacyHtml

if (-not $SkipWorkflow) {
    Invoke-PrivacyWorkflow
    Test-PrivacyUrl
} else {
    Write-Host "SkipWorkflow: Deploy uebersprungen." -ForegroundColor Yellow
}

Write-Host "`nFertig. Privacy-URL: $PrivacyUrl" -ForegroundColor Green
