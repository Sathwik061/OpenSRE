# OpenSRE (Graphify) — Product Presentation & Demo Script

> **A Complete Guide & Speaking Script for Presenting OpenSRE to Managers, Technical Leads, and Clients.**  
> *Written in simple, clear English with deep technical accuracy.*

---

## 📋 Table of Contents

1. [Executive Summary (The 30-Second Elevator Pitch)](#1-executive-summary-the-30-second-elevator-pitch)
2. [The Real-World Problem We Solve](#2-the-real-world-problem-we-solve)
3. [How the System Works (In Plain English)](#3-how-the-system-works-in-plain-english)
4. [Complete Feature Breakdown & Implementation](#4-complete-feature-breakdown--implementation)
5. [Step-by-Step Live Demo Script (Word-for-Word Walkthrough)](#5-step-by-step-live-demo-script)
6. [Architecture & Technical Highlights](#6-architecture--technical-highlights)
7. [Business Value, Security & ROI for Clients](#7-business-value-security--roi-for-clients)
8. [Technical Glossary (Simplified Terms for Non-Tech Stakeholders)](#8-technical-glossary-simplified-terms)

---

## 1. Executive Summary (The 30-Second Elevator Pitch)

> *"When mission-critical software or automated business workflows crash, engineers typically spend hours digging through thousands of log lines to find out what went wrong. **OpenSRE** is an automated AI Site Reliability Engineer that detects outages the exact second they occur, diagnoses the root cause, and hands your on-call engineers the exact, step-by-step fix in real time — completely on-premise without exposing sensitive company data to public clouds."*

---

## 2. The Real-World Problem We Solve

In modern enterprise applications and automated workflows (like Camunda 8):
1. **Downtime is Expensive:** Every minute an incident goes uninvestigated costs revenue and damages user trust.
2. **Log Fatigue:** A single server failure generates thousands of cryptic log lines across multiple microservices. Engineers waste 80% of their incident response time just finding the right error message.
3. **Data Privacy Concerns:** Companies cannot send proprietary workflow data or customer logs to public AI providers like OpenAI/OpenRouter due to compliance and security rules.

**Our Solution:**
OpenSRE connects directly to enterprise workflow engines (Camunda 8) and backend microservices, feeds runtime errors directly to an **on-premise NVIDIA DGX GPU (Qwen 35B)**, and produces an instant **WHAT / WHY / HOW TO FIX** report.

---

## 3. How the System Works (In Plain English)

Think of OpenSRE like an automated doctor for your software:

```
┌───────────────────────────┐
│  1. An Error Happens      │  A business workflow fails (e.g., bank transfer, leave approval, DB crash)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│  2. Sensor Catches It     │  Our bridge captures: Error message, timestamp, variables, flow node
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│  3. AI Brain Diagnoses    │  On-prem GPU (Qwen 35B) analyzes evidence with strict zero-hallucination rules
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│  4. Actionable Report     │  Terminal outputs: WHAT broke, WHY it broke, and the EXACT 3-step fix
└───────────────────────────┘
```

---

## 4. Complete Feature Breakdown & Implementation

Our platform is divided into **4 Core Ingestion Channels** and **2 AI Reasoning Engines**:

### 🎯 Feature 1: Real-Time Camunda 8 Incident Bridge (`camunda_bridge.py`)
* **What it does:** Automatically monitors Camunda 8 Self-Managed (Zeebe + Operate) for any broken workflow diagram without needing code changes in the BPMN.
* **How it is implemented:**
  * Uses cookie-based session authentication with CSRF token validation against Camunda Operate (`http://localhost:8081`).
  * Continuously polls `/v1/incidents/search` for `ACTIVE` incidents.
  * When an incident occurs, it queries `/v1/process-instances/`, `/v1/variables/search`, and `/v1/flownode-instances/search` to extract:
    * Human-readable Process Name (e.g., `final-test`)
    * Failed Step / Element (e.g., `Gateway_17l8d9w`, `Send leave request`)
    * All live process variables at the exact millisecond of failure.
  * Sends the enriched incident payload to the on-premise DGX GPU.

---

### 🎯 Feature 2: Zero-Code Application Error Interceptor (`error_hook.py`)
* **What it does:** Automatically catches unhandled exceptions in *any* Python backend microservice and sends them for investigation.
* **How it is implemented:**
  * Developers add just **2 lines of code**:
    ```python
    from error_hook import GraphifyHook
    GraphifyHook.install(service="payment-service")
    ```
  * It intercepts `sys.excepthook`, captures the stack trace, extracts the last 5 critical frames, and asynchronously posts the incident to the Sentinel API without crashing the running process.

---

### 🎯 Feature 3: Live File Log Tailing Watcher (`log_watcher.py`)
* **What it does:** Tails live production log files (similar to Linux `tail -f`) and detects errors as they are written to disk.
* **How it is implemented:**
  * Uses a high-performance regex engine scanning for keywords like `ERROR`, `CRITICAL`, `OOMKilled`, `Connection Refused`, `NullPointerException`, and HTTP `500`.
  * Implements a **5-second batching window** so multiple related error lines occurring in the same second are grouped into a single unified incident rather than triggering duplicate alerts.

---

### 🎯 Feature 4: Automated File-Drop Watcher (`watcher.py`)
* **What it does:** Allows external monitoring systems (Datadog, Prometheus, Grafana, CloudWatch) to drop raw JSON incident alerts into an `incidents/incoming/` directory.
* **How it is implemented:**
  * Uses the Python `watchdog` filesystem event listener.
  * Detects new files, routes them to DGX AI, archives the report in `incidents/history/`, and moves the processed file to `incidents/processed/`.

---

### 🎯 Feature 5: On-Premise GPU SRE Engine (`dgx_engine.py`)
* **What it does:** Powers all intelligence using your company’s private NVIDIA DGX server hosting the `Qwen3.6-35B` model.
* **How it is implemented:**
  * Connects over a secure SSH port-forward tunnel (`http://localhost:8000/v1`).
  * Features a **Strict SRE System Prompt** enforcing:
    * Separation of observed facts from inferences.
    * No hallucinations — claims must cite specific log evidence.
    * Concrete remediation steps.
  * Employs `enable_thinking: false` for low-latency JSON delivery and a **3-tier resilient JSON parser** (`_parse_llm_json`) with regex fallback to guarantee 100% crash-free operation.

---

### 🎯 Feature 6: Sentinel Microservice (`sentinel/main.py`)
* **What it does:** A FastAPI asynchronous microservice providing REST endpoints for third-party integrations.
* **Endpoints:**
  * `POST /investigate` — Run RCA on structured alerts (returns `202 Accepted` immediately with an investigation ID).
  * `POST /investigate/from-error` — Ingest raw error events.
  * `GET /investigations/{id}` — Poll status and retrieve results.
  * `GET /health` — Service liveness and active investigation count.

---

## 5. Step-by-Step Live Demo Script

Use this exact script when presenting the project live to your manager or clients.

---

### 🎙️ Phase 1: Introduction (Slide / Screen 1)
> **You say:**  
> *"Good morning/afternoon everyone. Today I am demonstrating **OpenSRE**, our automated AI platform for Site Reliability Engineering and workflow remediation.*  
> *In production systems, when an automated workflow fails, diagnosing the issue usually takes 30 to 60 minutes of manual log searching. With OpenSRE, diagnosis happens in under 5 seconds.*  
> *Let me show you our live setup."*

---

### 🎙️ Phase 2: Show the Infrastructure (Ports & Dashboards)
> **You say:**  
> *"Here on my screen, we have a complete enterprise stack running:*  
> *1. **Camunda 8 Self-Managed** on port `8080` (Zeebe Engine) and `8081` (Camunda Operate dashboard).*  
> *2. **Company NVIDIA DGX Server** running Qwen 35B connected securely via an SSH tunnel on port `8000`.*  
> *3. **OpenSRE Bridge** running in my terminal, listening for incidents in real time.*  
> *Notice that no public cloud AI is used — everything is 100% private and on-premise."*

---

### 🎙️ Phase 3: Triggering the Failure (Live Action)
> **You say:**  
> *"Now let's simulate a real enterprise failure. I have a BPMN process diagram called `leave_approval.bpmn` in Camunda Modeler.*  
> *I am deploying this workflow and launching an instance where a critical step contains an unhandled data error.*  
> *Let's watch what happens in Camunda Operate and our OpenSRE terminal."*

*(Action: Click Deploy 🚀 and Start Instance ▶️ in Camunda Modeler, or run `python test_leave_approval.py --error`)*

---

### 🎙️ Phase 4: Show the Real-Time Diagnosis
> **You say:**  
> *"Look at the terminal window. Within 3 seconds of the workflow failing in Camunda:*  
> *1. The OpenSRE bridge detected the active incident via REST API.*  
> *2. It extracted the failed element `Gateway_17l8d9w`, the process ID, and the exact variables.*  
> *3. It consulted our DGX Qwen 35B model and produced this structured report:*  
>  
> * **WHAT is the error:** Missing `approved` variable in `final-test` process.*  
> * **WHY it occurred:** The gateway expression `=not(approved)` evaluated to NULL because the variable was never initialized in previous tasks.*  
> * **HOW to fix it:**  
>    *1. Ensure the start event or manager approval task passes `approved`.*  
>    *2. Update the FEEL expression to handle null values gracefully.*  
>    *3. Add a default fallback mapping in the gateway.*  
>  
> *Instead of an on-call engineer waking up at 2 AM to read raw stack traces, OpenSRE delivers the diagnosis and the exact fix instantly."*

---

## 6. Architecture & Technical Highlights

```
                               ┌─────────────────────────────┐
                               │  Ingress Sources            │
                               │  - Camunda 8 Operate REST   │
                               │  - Python App ExceptionHook │
                               │  - Log File Tailer (Regex)  │
                               │  - Drop Folder (Watchdog)   │
                               └──────────────┬──────────────┘
                                              │ Enriched JSON
                                              ▼
                               ┌─────────────────────────────┐
                               │    camunda_bridge.py /      │
                               │     Sentinel FastAPI        │
                               └──────────────┬──────────────┘
                                              │ HTTP POST /v1/chat/completions
                                              │ (enable_thinking: false)
                                              ▼
                               ┌─────────────────────────────┐
                               │    Company NVIDIA DGX       │
                               │    vLLM Server (:8000)      │
                               │  nvidia/Qwen3.6-35B-NVFP4   │
                               └──────────────┬──────────────┘
                                              │ Robust JSON Parse
                                              ▼
                               ┌─────────────────────────────┐
                               │    Structured SRE Report    │
                               │    WHAT / WHY / HOW FIX     │
                               └─────────────────────────────┘
```

### Key Technical Innovations:
1. **Zero BPMN Hardcoding:** The bridge queries live metadata from Operate at runtime. It works on *any* BPMN diagram deployed now or in the future.
2. **Session Resilience:** Automatically manages cookie authentication and handles token expiration gracefully.
3. **Fault-Tolerant JSON Parsing:** Employs a multi-tier fallback mechanism (direct parse ➔ quote/comma cleanup ➔ regex field isolation) to guarantee that slight LLM syntax quirks never break the pipeline.

---

## 7. Business Value, Security & ROI for Clients

| Dimension | Traditional Manual SRE | OpenSRE Platform |
| :--- | :--- | :--- |
| **Mean Time to Detect (MTTD)** | 5 – 15 Minutes | **< 5 Seconds** |
| **Mean Time to Diagnose (MTTR)**| 30 – 60 Minutes | **< 10 Seconds** |
| **Data Privacy & Compliance** | Cloud AI risks data leaks | **100% On-Premise GPU (DGX)** |
| **Operating Cost** | Recurring cloud token fees | **$0 Ongoing AI API Cost** |
| **Developer Onboarding** | Steep learning curve | **2-line drop-in code hook** |

---

## 8. Technical Glossary (Simplified Terms)

When speaking with non-technical managers or business clients, use these simple analogies:

* **BPMN (Business Process Model and Notation):**  
  *Simple explanation:* A visual flowchart that software executes automatically (e.g., "Step 1: Submit Form ➔ Step 2: Manager Approves ➔ Step 3: Send Email").
* **Camunda 8 (Zeebe):**  
  *Simple explanation:* The high-speed automation engine that runs and tracks those visual flowcharts.
* **Operate:**  
  *Simple explanation:* The control dashboard where managers and engineers see which processes are running and which ones have errors.
* **Incident:**  
  *Simple explanation:* A red alert raised when a workflow gets stuck or encounters an error it doesn't know how to handle.
* **FEEL Expression (Friendly Enough Expression Language):**  
  *Simple explanation:* Simple formula rules inside Camunda (like Excel formulas, e.g., `=approved == true`).
* **Root Cause Analysis (RCA):**  
  *Simple explanation:* Finding the real root reason why a problem happened, not just looking at the surface symptoms.
* **NVIDIA DGX & vLLM:**  
  *Simple explanation:* The company's private supercomputer hosting the AI model locally so no confidential data ever leaves our building.
* **REST API:**  
  *Simple explanation:* The standard communication bridge that allows our SRE script to talk directly to Camunda and the AI engine.
