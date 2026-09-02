# OpenSRE + Camunda 8 + DGX AI Agent — Complete Documentation

> **AI-Driven Site Reliability Engineering (SRE) & Incident Remediation Platform**  
> Connects **Camunda 8 Self-Managed** with an on-prem **NVIDIA DGX GPU (Qwen 35B)** to automatically detect, analyze, and remediate BPMN workflow failures in real time.

---

## 📑 Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Port & Service Map](#2-port--service-map)
3. [Prerequisites & Setup](#3-prerequisites--setup)
4. [Quick Start Guide](#4-quick-start-guide)
5. [How Real-Time Incident Detection Works](#5-how-real-time-incident-detection-works)
6. [Testing & Inducing Real BPMN Incidents](#6-testing--inducing-real-bpmn-incidents)
7. [Component Deep Dive](#7-component-deep-dive)
8. [Environment Variables Reference](#8-environment-variables-reference)
9. [Troubleshooting & FAQs](#9-troubleshooting--faqs)

---

## 1. System Architecture

```
                                  ┌─────────────────────────────────────────┐
                                  │       Camunda Modeler / Desktop         │
                                  │      (Deploys & Starts BPMN Flow)       │
                                  └────────────────────┬────────────────────┘
                                                       │ gRPC :26500 / REST :8080
                                                       ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Camunda 8 Self-Managed Stack                                         │
│                                                                                                        │
│  ┌───────────────────────┐          ┌───────────────────────┐          ┌───────────────────────────┐  │
│  │     Zeebe Engine      │ ───────▶ │     Elasticsearch     │ ───────▶ │      Camunda Operate      │  │
│  │ (Executes BPMN Tasks) │          │       (Port 9200)     │          │    (Web UI & REST :8081)  │  │
│  └──────────┬────────────┘          └───────────────────────┘          └─────────────┬─────────────┘  │
│             │                                                                        │                │
│             │ Failure / Expression Error                                             │ Polls Active   │
│             ▼                                                                        │ Incidents      │
│      Active Incident                                                                 │ via REST API   │
└──────────────────────────────────────────────────────────────────────────────────────┼────────────────┘
                                                                                       │
                                                                                       ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       SRE Agent Core                                                   │
│                                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                 camunda_bridge.py (Real-Time Bridge)                             │  │
│  │  • Authenticates to Operate (/api/login session cookie)                                          │  │
│  │  • Polls /v1/incidents/search for ACTIVE incidents                                               │  │
│  │  • Enriches payload: Process ID, Instance ID, Flow Node Name, Live Variables                     │  │
│  └──────────────────────────────────────────────────┬───────────────────────────────────────────────┘  │
│                                                     │                                                  │
│                                                     │ Sends Structured Incident Payload                │
│                                                     ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                          Company NVIDIA DGX Server (Local SSH Tunnel)                            │  │
│  │                          Endpoint: http://localhost:8000/v1                                      │  │
│  │                          Model: nvidia/Qwen3.6-35B-A3B-NVFP4                                     │  │
│  │                          Task: Strict SRE Root Cause Analysis (RCA)                              │  │
│  └──────────────────────────────────────────────────┬───────────────────────────────────────────────┘  │
│                                                     │                                                  │
│                                                     │ Structured RCA Output:                           │
│                                                     │  - WHAT is the error?                            │
│                                                     │  - WHY did it occur? (Evidence & Root Cause)     │
│                                                     │  - HOW to fix it? (Actionable steps)             │
│                                                     ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                              Terminal Output & SRE Dashboard                                     │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Port & Service Map

| Service | Host Port | Protocol | Purpose | Authentication |
| :--- | :---: | :---: | :--- | :--- |
| **Camunda Operate** | `8081` | HTTP / REST | Incident management UI & REST API for incident querying | `demo` / `demo` (Session Cookie) |
| **Camunda Tasklist** | `8082` | HTTP | Human workflow user task interface | `demo` / `demo` |
| **Zeebe REST API** | `8080` | HTTP / REST | Camunda 8 REST interface (deployments, instances) | None |
| **Zeebe gRPC Engine**| `26500`| gRPC | High-throughput broker engine for BPMN execution | Plaintext |
| **Elasticsearch** | `9200` | HTTP | Data store for Zeebe process history and incidents | None |
| **Company DGX AI** | `8000` | HTTP / OpenAI | On-prem NVIDIA GPU vLLM serving Qwen 35B | SSH Tunnel to DGX Box |
| **Sentinel SRE API**| `5000` | HTTP / REST | FastAPI background RCA orchestration service | None |

---

## 3. Prerequisites & Setup

### 3.1 Software Requirements
- **Windows 10/11** or **Linux**
- **Docker Desktop** (running with Docker Compose v2)
- **Python 3.10+**
- **Camunda Desktop Modeler** (v5.20+)

### 3.2 Python Dependencies
Install required packages in your Python environment:
```powershell
pip install fastapi uvicorn pydantic pyzeebe watchdog requests
```

### 3.3 DGX Server SSH Tunnel
Open an SSH tunnel to forward the DGX vLLM service to your local machine:
```powershell
ssh -L 8000:localhost:8000 truviq_domain@192.168.0.143
```
> **Keep this terminal window running.** It routes all AI inference to your on-prem NVIDIA GPU at zero cost.

---

## 4. Quick Start Guide

### Option A: One-Click Full Stack Launcher (Recommended)
From PowerShell inside the `graphify/` directory, run:
```powershell
.\scripts\start.ps1
```

This automatically:
1. Verifies the DGX SSH tunnel on `:8000`.
2. Starts the Docker containers (`elasticsearch`, `camunda8`, `operate`, `tasklist`).
3. Starts the **Sentinel RCA API** on port `5000`.
4. Starts the **Real-Time Camunda Bridge** (`camunda_bridge.py`) in polling mode.

---

### Option B: Individual Service Launch

#### 1. Start Docker Infrastructure
```powershell
cd graphify
docker compose up -d
```

#### 2. Start Real-Time SRE Bridge
```powershell
cd graphify
python camunda_bridge.py --interval 5
```

#### 3. (Optional) Start Sentinel FastAPI API
```powershell
cd graphify\sentinel
python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

---

## 5. How Real-Time Incident Detection Works

`camunda_bridge.py` operates 100% dynamically without requiring any static BPMN diagrams:

1. **Authentication:** Authenticates to Camunda Operate via `POST /api/login` and captures session cookies and CSRF tokens.
2. **Polling:** Every 5–10 seconds, queries `POST /v1/incidents/search` for items with `"state": "ACTIVE"`.
3. **Context Enrichment:**
   - Queries `GET /v1/process-instances/{id}` to fetch human-readable process definition names (`bpmnProcessId`).
   - Queries `POST /v1/flownode-instances/search` to find the exact BPMN activity/element where execution failed.
   - Queries `POST /v1/variables/search` to inspect all process variables at the moment of failure.
4. **AI Reasoning:** Sends the complete context to DGX Qwen 35B via `http://localhost:8000/v1/chat/completions` with chain-of-thought suppression (`enable_thinking: false`) for fast, clean JSON generation.
5. **RCA Output:** Prints a structured, color-coded report to the terminal.

---

## 6. Testing & Inducing Real BPMN Incidents

You can test the SRE agent on any BPMN diagram in Camunda Modeler.

### Scenario 1: FEEL Expression Assertion Failure
1. In Camunda Modeler, select any Task.
2. In the right Properties panel, under **Input Mappings**, add:
   - **Local variable:** `myresult`
   - **Variable assignment value:** `= assert(false, "Database connection timeout in Leave Service")`
3. Click **Deploy (Rocket 🚀)** ➔ Click **Start Instance (Play ▶️)**.
4. The instance fails instantly with a red incident in Operate, and the SRE Agent prints the investigation in the bridge terminal.

### Scenario 2: Missing Variable in Exclusive (XOR) Gateway
1. Create a gateway with sequence flow condition `= approved == true` and `= not(approved)`.
2. Start the process without providing the `approved` variable.
3. Zeebe raises an `EXTRACT_VALUE_ERROR` incident.

### Scenario 3: Programmatic Execution via Python
```powershell
python test_leave_approval.py --error
```

---

## 7. Component Deep Dive

### `camunda_bridge.py`
The central orchestrator connecting Camunda 8 Operate REST API to DGX Qwen 35B.
- **Dynamic Field Resolution:** Resolves IDs into readable flow node names and variable dictionaries.
- **Multi-Strategy JSON Parser:** Implements standard JSON decoding, smart-quote sanitization, trailing-comma correction, and regex fallback extraction to ensure zero crashes from LLM output quirks.
- **Session Auto-Refresh:** Re-authenticates automatically if the session cookie expires.

### `sentinel/dgx_engine.py`
Direct client to the DGX vLLM OpenAI-compatible server.
- Contains the strict SRE system prompt requiring evidence-based reasoning.
- Configured with `temperature: 0.1` and `max_tokens: 4000` for deterministic root cause analysis.

### `scripts/start.ps1`
PowerShell automation script that sets safe Windows temporary paths (`C:\Temp`), validates the GPU tunnel, checks Docker container readiness, and launches background workers.

---

## 8. Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `OPERATE_URL` | `http://localhost:8081` | URL for Camunda Operate Web/REST API |
| `OPERATE_USER` | `demo` | Operate login username |
| `OPERATE_PASS` | `demo` | Operate login password |
| `ZEEBE_REST` | `http://localhost:8080` | Zeebe REST API endpoint |
| `ZEEBE_HOST` | `localhost` | Zeebe gRPC hostname |
| `ZEEBE_PORT` | `26500` | Zeebe gRPC broker port |
| `DGX_URL` | `http://localhost:8000/v1` | DGX vLLM OpenAI-compatible API base |
| `DGX_MODEL` | `nvidia/Qwen3.6-35B-A3B-NVFP4` | Active LLM model ID on DGX GPU |
| `SENTINEL_URL` | `http://localhost:5000` | Sentinel FastAPI service URL |
| `POLL_INTERVAL`| `10` | Incident polling frequency (in seconds) |

---

## 9. Troubleshooting & FAQs

### Q1: `camunda_bridge.py` says "Camunda Operate :8081 [DOWN]"
- Check if the Operate container is running:
  ```powershell
  docker compose ps
  ```
- If not running, start it:
  ```powershell
  docker compose up -d operate
  ```
- Wait 30 seconds for Elasticsearch indices to initialize.

### Q2: "DGX vLLM :8000 [DOWN]"
- Your SSH tunnel to the company DGX server has closed. Reopen it:
  ```powershell
  ssh -L 8000:localhost:8000 truviq_domain@192.168.0.143
  ```

### Q3: Why does Operate show "0 Running Instances"?
- Deploying a BPMN diagram (**Rocket 🚀**) only registers the diagram template.
- You must click the **Play icon ▶️ (Start instance)** next to the rocket to execute a run.

### Q4: Are OpenRouter or cloud API credits needed?
- **No.** All reasoning runs locally on your company's on-prem **NVIDIA DGX GPU** via the port 8000 SSH tunnel. No cloud credits or external APIs are used.
