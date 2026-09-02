# Graphify — Real-Time Camunda 8 SRE Incident Remediation

> **Camunda 8 Self-Managed + Company NVIDIA DGX (Qwen 35B GPU) + SRE Agent**  
> When ANY incident or workflow error occurs in Camunda 8, the SRE Agent automatically detects it in real time via REST API, investigates root cause, and prints actionable fixes to your terminal.

---

## Architecture Overview

```
Camunda 8 BPMN Workflow (Any Process)
       │  (Incident / Failure Occurs)
       ▼
Camunda Operate REST API (:8081)
       │  (Polled by camunda_bridge.py)
       ▼
Dynamic Incident Enrichment (Variables + Flow Nodes)
       │
       ▼
Company NVIDIA DGX Server (:8000 SSH Tunnel)
       │  Model: nvidia/Qwen3.6-35B-A3B-NVFP4
       ▼
SRE Root Cause Analysis Report in Terminal
  ✅ WHAT failed
  ✅ WHY it occurred (Evidence & Root Cause)
  ✅ HOW to fix it (Remediation steps)
```

See [DOCUMENTATION.md](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/DOCUMENTATION.md) for the complete manual.

```
graphify/
├── trigger.py                  ← Phase 1: run RCA directly (no Camunda needed)
├── requirements.txt
├── docker-compose.yml          ← Camunda + Sentinel
├── .env.example
│
├── incidents/
│   └── test-incident.json      ← test payload for opensre investigate
│
├── sentinel/                   ← FastAPI RCA service
│   ├── main.py                 ← API endpoints
│   ├── investigator.py         ← calls opensre investigate
│   ├── incident_builder.py     ← builds IncidentAlert from raw ErrorEvent
│   ├── models.py               ← Pydantic data models
│   └── Dockerfile
│
├── camunda/
│   ├── worker.py               ← external task worker (polls Camunda)
│   ├── deploy.py               ← deploys BPMN to Camunda
│   └── bpmn/
│       └── rca_investigation.bpmn
│
├── scripts/
│   ├── test-investigation.ps1  ← quick test (Phase 1)
│   └── run-all.ps1             ← full stack start (Phase 2)
│
└── tests/
    └── test_sentinel.py        ← pytest smoke tests
```

---

## Quick Start

### Phase 1 — Test OpenSRE directly (no Docker needed)

> You're here right now based on the ChatGPT conversation.

```powershell
# From the graphify folder:
python trigger.py
```

This runs `opensre investigate -i incidents\test-incident.json` and prints the RCA.

You can also run a custom incident:
```powershell
python trigger.py -s payment-service -e "HTTP 500" -m "DB connection refused"
```

---

### Phase 2 — Full stack (Camunda + Sentinel)

**Prerequisites:** Docker Desktop running.

```powershell
# Install Python deps
pip install -r requirements.txt

# Start Camunda + Sentinel
docker compose up -d

# Deploy the BPMN workflow
python camunda\deploy.py

# Start the worker (polls Camunda for tasks)
python camunda\worker.py
```

**Camunda UI:** http://localhost:8080/camunda (admin / admin)  
**Sentinel API:** http://localhost:5000/docs

To trigger a full end-to-end investigation via Camunda:
```powershell
python camunda\deploy.py --trigger
```

---

### Run Tests

```powershell
pip install -r requirements.txt
pytest tests/ -v
```

---

## How It Works

| Phase | Component | What it does |
|-------|-----------|--------------|
| 1 | `trigger.py` | Direct CLI → opensre → RCA in terminal |
| 2 | `sentinel/` | FastAPI service that wraps opensre |
| 2 | `camunda/worker.py` | Polls Camunda, calls Sentinel |
| 2 | `camunda/bpmn/` | BPMN workflow orchestration |
| 3 | *(future)* | Grafana/Prometheus evidence collection |

---

## OpenSRE Commands Reference

```powershell
opensre health                                    # verify OpenSRE is working
opensre investigate -i incidents\test-incident.json  # manual investigation
opensre --help
```
