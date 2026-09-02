# ─────────────────────────────────────────────────────────────────────────────
# run.ps1  —  Graphify Launcher (run from ANYWHERE)
# Place this in the Open SRE root or Desktop for convenience.
# It automatically navigates to the graphify folder and starts everything.
# ─────────────────────────────────────────────────────────────────────────────

$GraphifyRoot = Join-Path $PSScriptRoot "graphify"

if (-not (Test-Path $GraphifyRoot)) {
    Write-Host "[ERROR] graphify folder not found at: $GraphifyRoot" -ForegroundColor Red
    Write-Host "        Make sure this file is in the 'Open SRE' folder." -ForegroundColor Red
    exit 1
}

Set-Location $GraphifyRoot
Write-Host "Working directory: $GraphifyRoot" -ForegroundColor Gray
Write-Host ""

powershell -ExecutionPolicy Bypass -File "scripts\start.ps1"
