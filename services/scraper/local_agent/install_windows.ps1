# Lumora Scraper — local agent installer for Windows
# Run from PowerShell:  iex (Get-Content .\install_windows.ps1 -Raw)
# Or: .\install_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "[install] checking python..." -ForegroundColor Cyan
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Python is not in PATH. Install from https://www.python.org/downloads/ first." -ForegroundColor Red
    exit 1
}

Push-Location $PSScriptRoot
try {
    Write-Host "[install] pip install local agent deps..." -ForegroundColor Cyan
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

    Write-Host "[install] playwright install chrome..." -ForegroundColor Cyan
    python -m playwright install chrome

    $envPath = Join-Path $PSScriptRoot "..\.env"
    if (-not (Test-Path $envPath)) {
        Write-Host "[install] generating local agent token..." -ForegroundColor Cyan
        $token = python -c "import secrets; print(secrets.token_urlsafe(32))"
        Write-Host ""
        Write-Host "Generated LOCAL_AGENT_TOKEN: $token" -ForegroundColor Yellow
        Write-Host "Add this same value to your GitHub repo secret + Railway service vars." -ForegroundColor Yellow
        Write-Host ""

        $serverUrl = Read-Host "Enter SCRAPER_SERVER_URL (e.g. wss://scraper-production.up.railway.app)"
        $agentId = Read-Host "Enter AGENT_ID (default: $env:COMPUTERNAME)"
        if (-not $agentId) { $agentId = $env:COMPUTERNAME }

        $envContent = "SCRAPER_SERVER_URL=$serverUrl`r`nLOCAL_AGENT_TOKEN=$token`r`nAGENT_ID=$agentId`r`n"
        Set-Content -Path $envPath -Value $envContent -NoNewline
        Write-Host "[install] wrote $envPath" -ForegroundColor Green
    } else {
        Write-Host "[install] $envPath already exists, skipping." -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "[install] DONE. To run the agent:" -ForegroundColor Green
    Write-Host "  cd $((Get-Item $PSScriptRoot).Parent.FullName)" -ForegroundColor White
    Write-Host "  python -m local_agent.agent" -ForegroundColor White
} finally {
    Pop-Location
}
