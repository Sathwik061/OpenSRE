# ─────────────────────────────────────────────────────────────────────────────
# run-all.ps1
# Starts the full Graphify stack:
#   1. Docker (Camunda)
#   2. Sentinel FastAPI service
#   3. Camunda external task worker
#
# Run this AFTER Phase 1 is verified (trigger.py works).
# ─────────────────────────────────────────────────────────────────────────────

$GraphifyRoot = Split-Path $PSScriptRoot -Parent
Set-Location $GraphifyRoot

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  GRAPHIFY — Full Stack Startup" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Install Python deps ────────────────────────────────────────────────────
Write-Host "[1/4] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# ── 2. Start Camunda + Sentinel via Docker Compose ───────────────────────────
Write-Host "[2/4] Starting Camunda + Sentinel (Docker Compose)..." -ForegroundColor Yellow
docker compose up -d

Write-Host "      Waiting for Camunda to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 20

# ── 3. Deploy BPMN to Camunda ────────────────────────────────────────────────
Write-Host "[3/4] Deploying BPMN workflow to Camunda..." -ForegroundColor Yellow
python camunda\deploy.py

# ── 4. Start the Camunda worker (foreground) ─────────────────────────────────
Write-Host "[4/4] Starting Camunda external task worker..." -ForegroundColor Yellow
Write-Host ""
Write-Host "------------------------------------------------------" -ForegroundColor Green
Write-Host "  Camunda UI  : http://localhost:8080/camunda" -ForegroundColor Green
Write-Host "  Sentinel API: http://localhost:5000/docs" -ForegroundColor Green
Write-Host "  Worker      : running (Ctrl+C to stop)" -ForegroundColor Green
Write-Host "------------------------------------------------------" -ForegroundColor Green
Write-Host ""

python camunda\worker.py
