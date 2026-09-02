# =============================================================================
#  scripts/start.ps1  --  Graphify Full Stack Launcher (Camunda 8 + DGX SRE)
#
#  Run from the graphify\ folder:
#    .\scripts\start.ps1
#
#  Services started:
#    1. Camunda 8 (Zeebe + Operate + Tasklist) via Docker
#    2. Sentinel RCA API (FastAPI, port 5000)
#    3. Camunda Bridge (real-time incident poller → DGX Qwen 35B)
#
#  Prerequisites:
#    - Docker Desktop running
#    - SSH tunnel open: ssh -L 8000:localhost:8000 truviq_domain@192.168.0.143
# =============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

# ── Environment: DGX vLLM (company GPU, NO OpenRouter) ───────────────────────
$env:TEMP                    = "C:\Temp"
$env:TMP                     = "C:\Temp"
$env:ZEEBE_HOST              = "localhost"
$env:ZEEBE_PORT              = "26500"
$env:SENTINEL_URL            = "http://localhost:5000"
$env:OPERATE_URL             = "http://localhost:8080"
$env:OPERATE_USER            = "demo"
$env:OPERATE_PASS            = "demo"
$env:DGX_URL                 = "http://localhost:8000/v1"
$env:DGX_MODEL               = "nvidia/Qwen3.6-35B-A3B-NVFP4"
# Force opensre (CLI fallback) to also use DGX, not OpenRouter
$env:LLM_PROVIDER            = "custom-openai"
$env:CUSTOM_OPENAI_API_KEY   = "dummy-not-needed-local-vllm"
$env:CUSTOM_OPENAI_API_BASE  = "http://localhost:8000/v1"
$env:CUSTOM_OPENAI_MODEL     = "nvidia/Qwen3.6-35B-A3B-NVFP4"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  GRAPHIFY  --  Real-Time Camunda 8 + DGX SRE Stack" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  AI Engine : DGX vLLM -> localhost:8000 (Qwen 35B, on-prem GPU)"
Write-Host "  Camunda 8 : localhost:8080  (Zeebe gRPC: :26500)"
Write-Host "  Operate   : localhost:8080/operate"
Write-Host "  Tasklist  : localhost:8080/tasklist"
Write-Host "  Sentinel  : localhost:5000"
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# ── Ensure C:\Temp exists ─────────────────────────────────────────────────────
if (-not (Test-Path "C:\Temp")) {
    New-Item -ItemType Directory -Path "C:\Temp" -Force | Out-Null
    Write-Host "[SETUP] Created C:\Temp"
}

# ── Check DGX SSH tunnel ──────────────────────────────────────────────────────
Write-Host "[CHECK] DGX vLLM tunnel (localhost:8000)..." -NoNewline
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/v1/models" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  OK" -ForegroundColor Green
} catch {
    Write-Host "  DOWN" -ForegroundColor Red
    Write-Host "[WARN] Open SSH tunnel first:" -ForegroundColor Yellow
    Write-Host "       ssh -L 8000:localhost:8000 truviq_domain@192.168.0.143" -ForegroundColor Yellow
    Write-Host ""
}

# ── Step 1: Start Camunda 8 (Docker) ─────────────────────────────────────────
Write-Host "[1/3] Checking Camunda 8 (Zeebe + Operate + Tasklist)..."
$alreadyUp = $false
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8080/v2/topology" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($r.StatusCode -eq 200) { $alreadyUp = $true }
} catch { }

if ($alreadyUp) {
    Write-Host "[1/3] Camunda 8 is already UP -> http://localhost:8080" -ForegroundColor Green
} else {
    Write-Host "[1/3] Starting Camunda 8 via Docker..."
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] docker compose failed. Is Docker Desktop running?" -ForegroundColor Red
        exit 1
    }
    Write-Host "[1/4] Waiting for Camunda 8 Zeebe REST to be ready..."
    $ready = $false
    for ($i = 1; $i -le 36; $i++) {
        Start-Sleep -Seconds 5
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8080/v2/topology" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
        Write-Host "       ...waiting ($($i*5)s elapsed)"
    }
    if (-not $ready) { Write-Host "[WARN] Zeebe REST health check timed out. Proceeding..." -ForegroundColor Yellow }
    else             { Write-Host "[1/4] Camunda 8 UP -> http://localhost:8080" -ForegroundColor Green }
}
Write-Host ""

# ── Step 2: Start Sentinel FastAPI ───────────────────────────────────────────
Write-Host "[2/4] Starting Sentinel RCA API on port 5000..."
$sentinelArgs = @(
    "-NoExit", "-Command",
    "cd '$Root\sentinel'; " +
    "`$env:TEMP='C:\Temp'; `$env:TMP='C:\Temp'; " +
    "`$env:DGX_URL='http://localhost:8000/v1'; " +
    "`$env:DGX_MODEL='nvidia/Qwen3.6-35B-A3B-NVFP4'; " +
    "python -m uvicorn main:app --host 0.0.0.0 --port 5000"
)
Start-Process powershell -ArgumentList $sentinelArgs -WindowStyle Normal
Start-Sleep -Seconds 4
try {
    $r = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[2/4] Sentinel UP  -> http://localhost:5000/docs" -ForegroundColor Green
} catch {
    Write-Host "[2/4] Sentinel starting... (check its window)" -ForegroundColor Yellow
}
Write-Host ""

# ── Step 3: Start Real-Time Camunda Bridge (Operate poller → DGX) ─────────────
Write-Host "[3/4] Starting Real-Time Camunda Bridge (polls Operate every 10s)..."
$bridgeArgs = @(
    "-NoExit", "-Command",
    "cd '$Root'; " +
    "`$env:TEMP='C:\Temp'; `$env:TMP='C:\Temp'; " +
    "`$env:OPERATE_URL='http://localhost:8080'; " +
    "`$env:OPERATE_USER='demo'; `$env:OPERATE_PASS='demo'; " +
    "`$env:DGX_URL='http://localhost:8000/v1'; " +
    "`$env:DGX_MODEL='nvidia/Qwen3.6-35B-A3B-NVFP4'; " +
    "python camunda_bridge.py --interval 10"
)
Start-Process powershell -ArgumentList $bridgeArgs -WindowStyle Normal
Start-Sleep -Seconds 2
Write-Host "[3/4] Camunda Bridge started (watch its window for live incidents)" -ForegroundColor Green
Write-Host ""

# ── Step 4: Start Frontend Web Dashboard ───────────────────────────────────────
Write-Host "[4/4] Starting Incident Insights Hub Frontend (Port 5173)..."
$frontendDir = Join-Path $Root "Incident Insights Hub"
if (Test-Path $frontendDir) {
    $frontendArgs = @(
        "-NoExit", "-Command",
        "cd '$frontendDir'; " +
        "npm run dev"
    )
    Start-Process powershell -ArgumentList $frontendArgs -WindowStyle Normal
    Write-Host "[4/4] Frontend Dashboard UP -> http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "[WARN] Frontend directory not found at $frontendDir" -ForegroundColor Yellow
}
Write-Host ""

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  STACK IS READY" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  BROWSER INTERFACES:"
Write-Host "    🌟 OpenSRE Dashboard : http://localhost:5173" -ForegroundColor Green
Write-Host "    Camunda Operate      : http://localhost:8080/operate  (demo/demo)"
Write-Host "    Camunda Tasklist     : http://localhost:8080/tasklist (demo/demo)"
Write-Host "    Sentinel API Docs    : http://localhost:5000/docs"
Write-Host ""
Write-Host "  AI ENGINE:"
Write-Host "    DGX vLLM         : http://localhost:8000/v1 (SSH tunnel)"
Write-Host "    Model            : nvidia/Qwen3.6-35B-A3B-NVFP4"
Write-Host "    OpenRouter       : NOT used (all inference on-prem GPU)"
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
