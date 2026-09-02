# ─────────────────────────────────────────────────────────────────────────────
# test-investigation.ps1
# Run a quick OpenSRE RCA investigation via trigger.py
# ─────────────────────────────────────────────────────────────────────────────

$GraphifyRoot = Split-Path $PSScriptRoot -Parent
Set-Location $GraphifyRoot

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  GRAPHIFY — Phase 1 Test: Direct RCA Investigation" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Running:  python trigger.py -i incidents\test-incident.json" -ForegroundColor Yellow
Write-Host ""

python trigger.py -i incidents\test-incident.json

Write-Host ""
Write-Host "Investigation complete. Check the output above." -ForegroundColor Green
