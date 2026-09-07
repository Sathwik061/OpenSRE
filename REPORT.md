# OpenSRE: Autonomous SRE Incident Investigation & Remediation Platform
## Technical Architecture, Repository Audit, and Comprehensive Component Specification Report

> **Author**: OpenSRE Core Engineering Team  
> **Date**: September 7, 2026  
> **Platform Version**: OpenSRE v2.4 (Enterprise Production Edition)  
> **Target Runtime Stack**: Camunda 8.9 (Self-Managed & Enterprise SaaS), Python 3.11, React 19 / TypeScript 5.6 / Vite 6.0, NVIDIA DGX vLLM (Qwen 3.6 35B NVFP4), PostgreSQL / Supabase, Elasticsearch 8.x  
> **Workspace Root**: `c:\Users\madire sathwik\OneDrive - TRUVIQ SYSTEMS PRIVATE LIMITED\Documents\Open SRE`

---

## 📑 Table of Contents

1. [Executive Summary & Platform Vision](#1-executive-summary--platform-vision)
2. [End-to-End System Architecture & Data Pipelines](#2-end-to-end-system-architecture--data-pipelines)
   - [2.1 High-Level Architecture Diagram](#21-high-level-architecture-diagram)
   - [2.2 Incident Ingestion & Processing Pipeline](#22-incident-ingestion--processing-pipeline)
   - [2.3 Multi-Tier Knowledge & Inference Pipeline](#23-multi-tier-knowledge--inference-pipeline)
3. [Exhaustive File-by-File Codebase Inventory](#3-exhaustive-file-by-file-codebase-inventory)
   - [3.1 Workspace Root Files](#31-workspace-root-files)
   - [3.2 Orchestration & Bridge Layer (`graphify/`)](#32-orchestration--bridge-layer-graphify)
   - [3.3 Sentinel FastAPI Microservice (`graphify/sentinel/`)](#33-sentinel-fastapi-microservice-graphifysentinel)
     - [3.3.1 Microservice Entrypoint & Base Modules](#331-microservice-entrypoint--base-modules)
     - [3.3.2 API Routing Layer (`sentinel/api/`)](#332-api-routing-layer-sentinelapi)
     - [3.3.3 Camunda Integration & Graph Topology (`sentinel/camunda/`)](#333-camunda-integration--graph-topology-sentinelcamunda)
     - [3.3.4 Core Engine, Investigator & State Store (`sentinel/core/`)](#334-core-engine-investigator--state-store-sentinelcore)
     - [3.3.5 DGX AI Inference & Prompt Engine (`sentinel/engine/`)](#335-dgx-ai-inference--prompt-engine-sentinelengine)
     - [3.3.6 Knowledge Base, Kapa MCP & Supabase SOPs (`sentinel/knowledge/`)](#336-knowledge-base-kapa-mcp--supabase-sops-sentinelknowledge)
     - [3.3.7 Local Camunda Documentation Catalog (`sentinel/knowledge/camunda_docs/`)](#337-local-camunda-documentation-catalog-sentinelknowledgecamunda_docs)
     - [3.3.8 Automation Scripts & DDL Schemas (`sentinel/scripts/`, Root Scripts)](#338-automation-scripts--ddl-schemas-sentinelscripts-root-scripts)
   - [3.4 Incident Insights Hub UI (`graphify/Incident Insights Hub/`)](#34-incident-insights-hub-ui-graphifyincident-insights-hub)
     - [3.4.1 Configuration & Project Metadata](#341-configuration--project-metadata)
     - [3.4.2 Application Routes (`src/routes/`)](#342-application-routes-srcroutes)
     - [3.4.3 Custom SRE React Components (`src/components/`)](#343-custom-sre-react-components-srccomponents)
     - [3.4.4 Shadcn UI Primitives Library (`src/components/ui/`)](#344-shadcn-ui-primitives-library-srccomponentsui)
     - [3.4.5 Application State, Hooks & API Client (`src/lib/` & `src/hooks/`)](#345-application-state-hooks--api-client-srclib--srchooks)
   - [3.5 Camunda BPMN Artifacts & Job Worker Mock Services (`graphify/camunda/`)](#35-camunda-bpmn-artifacts--job-worker-mock-services-graphifycamunda)
   - [3.6 Synthetic Incident Datasets & Test Scenarios (`graphify/incidents/`)](#36-synthetic-incident-datasets--test-scenarios-graphifyincidents)
   - [3.7 Shell Scripts & Environment Tooling (`graphify/scripts/`)](#37-shell-scripts--environment-tooling-graphifyscripts)
   - [3.8 Automated Unit & Integration Tests (`graphify/tests/`)](#38-automated-unit--integration-tests-graphifytests)
   - [3.9 Static Graph Analysis Artifacts (`graphify-out/`)](#39-static-graph-analysis-artifacts-graphify-out)
4. [Deep Dive: Core Architectural Subsystems](#4-deep-dive-core-architectural-subsystems)
   - [4.1 Dynamic Version-Aware Resolution Engine (Camunda 8.0 – 8.10+)](#41-dynamic-version-aware-resolution-engine-camunda-80--810)
   - [4.2 BPMN 2.0 Graph Topology & Reachability Engine](#42-bpmn-20-graph-topology--reachability-engine)
   - [4.3 Sub-Millisecond Hybrid Knowledge Retrieval & Kapa MCP Integration](#43-sub-millisecond-hybrid-knowledge-retrieval--kapa-mcp-integration)
   - [4.4 NVIDIA DGX vLLM Qwen 35B Inference Engine & Schema Guardrails](#44-nvidia-dgx-vllm-qwen-35b-inference-engine--schema-guardrails)
   - [4.5 SRE Standard Operating Procedures (SOP) & Supabase Persistence](#45-sre-standard-operating-procedures-sop--supabase-persistence)
5. [Network Topology, Ports & Service Mesh Map](#5-network-topology-ports--service-mesh-map)
6. [Operational Runbooks, Setup & Verification Test Results](#6-operational-runbooks-setup--verification-test-results)
   - [6.1 Platform Bootstrap Runbook](#61-platform-bootstrap-runbook)
   - [6.2 Automated Test Suite Results & Latency Benchmarks](#62-automated-test-suite-results--latency-benchmarks)
   - [6.3 Verification of Deep Multi-Layer Incidents in Ingest Lab](#63-verification-of-deep-multi-layer-incidents-in-ingest-lab)
7. [Conclusion & Strategic Roadmap](#7-conclusion--strategic-roadmap)

---

## 1. Executive Summary & Platform Vision

**OpenSRE** is an autonomous Site Reliability Engineering (SRE) platform engineered to detect, diagnose, explain, and remediate complex incidents occurring within **Camunda 8 (Zeebe / Operate / Tasklist)** orchestration engines and associated distributed microservices.

Modern enterprise workflows orchestrate mission-critical services across polyglot microservice boundaries. When an incident occurs—whether triggered by database connection exhaustion, third-party gateway timeouts, JSON FEEL evaluation errors, unhandled BPMN error events, or parallel gateway deadlocks—traditional observability tools merely surface raw log dumps and stack traces. Engineers are left manually deciphering BPMN XML topologies, cross-referencing version-specific documentation, and guessing root causes under severe MTTR pressure.

### Core Value Propositions
- **Zero-Touch Automated Incident Ingestion**: Continuously polls Camunda Operate REST APIs (`/v1/incidents/search`, `/v2/incidents/search`) and intercepts raw application exceptions via the `@camunda_error_hook` decorator.
- **Structural BPMN 2.0 Graph Intelligence**: Traverses process definitions via Breadth-First Search (BFS) to detect hidden graph hazards such as Parallel Fork/Join token starvation, missing error boundary catch events, and unhandled exclusive gateway branches.
- **Dynamic Engine Version Pinning**: Dynamically resolves target engine versions (`Camunda 8.9`, `8.8`, `8.10+`) from XML definitions and cluster topology headers, ensuring version-accurate documentation URLs and semantic prompt invariants.
- **Sub-Millisecond Knowledge RAG & MCP Integration**: Combines live querying of the official **Camunda Kapa MCP Server** (`https://camunda-docs.mcp.kapa.ai`) with an offline **0.18ms local vector-like index** covering 21 core BPMN engine specifications.
- **Deterministic On-Premises GPU Inference**: Offloads complex reasoning to an NVIDIA DGX system running `vLLM` with **Qwen 3.6 35B NVFP4**, enforced by strict JSON schema validation, evidence citations, and dynamic remediation playbooks.
- **Rich Interactive SRE Workspace**: Provides an intuitive React 19 / Vite single-page application featuring embedded `bpmn-js` interactive viewers, real-time KPI dashboards, an incident Ingest Lab, and one-click incident retry/resolution in Camunda Operate.

---

## 2. End-to-End System Architecture & Data Pipelines

### 2.1 High-Level Architecture Diagram

```
                                  ┌──────────────────────────────────────────────┐
                                  │           Camunda Modeler Desktop            │
                                  │    (Deploys BPMN XML with Version Header)    │
                                  └──────────────────────┬───────────────────────┘
                                                         │ gRPC :26500 / REST :8080
                                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Camunda 8 Self-Managed Stack                                         │
│                                                                                                        │
│  ┌────────────────────────┐          ┌────────────────────────┐          ┌──────────────────────────┐  │
│  │      Zeebe Engine      │ ───────▶ │     Elasticsearch      │ ───────▶ │     Camunda Operate      │  │
│  │ (Executes BPMN Tasks)  │          │      (Port 9200)       │          │   (Web UI & REST :8081)  │  │
│  └───────────┬────────────┘          └────────────────────────┘          └────────────┬─────────────┘  │
│              │                                                                        │                │
│              │ Task Exception / UNHANDLED_ERROR_EVENT                                 │ Polls Active   │
│              ▼                                                                        │ Incidents      │
│       Active Incident                                                                 │ via REST API   │
└───────────────────────────────────────────────────────────────────────────────────────┼────────────────┘
                                                                                        │
                                                                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       Sentinel SRE Backend (:5000)                                     │
│                                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  1. Camunda Bridge Watcher (bridge_watcher.py) & Topology Parser (topology_parser.py)             │  │
│  │     • Reads Incident Key, Flow Node ID, Live Process Variables, and BPMN XML                     │  │
│  │     • Extracts executionPlatformVersion (e.g. 8.9.0 -> 8.9)                                      │  │
│  │     • Analyzes Graph: Parallel Fork/Join Deadlocks, Missing Boundary Catch Events, XOR Defaults  │  │
│  └──────────────────────────────────┬───────────────────────────────────────────────────────────────┘  │
│                                     │                                                                  │
│                                     ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  2. Knowledge Engine & SOP Runbook Resolver (camunda_knowledge.py & supabase_runbook.py)         │  │
│  │     • Dynamic Version-Scoped Queries -> Kapa MCP (https://camunda-docs.mcp.kapa.ai)              │  │
│  │     • Sub-millisecond Local RAG Fallback with Versioned URL Rewriting (/docs/8.9/...)            │  │
│  │     • Predefined Team SOP Guidelines Lookup from Supabase Store                                  │  │
│  └──────────────────────────────────┬───────────────────────────────────────────────────────────────┘  │
│                                     │                                                                  │
│                                     ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  3. NVIDIA DGX AI Engine (dgx_client.py & prompt_builder.py)                                     │  │
│  │     • Injects Strict Camunda 8.9 Semantics Invariant & Topology Findings                         │  │
│  │     • Calls local SSH Tunnel (http://localhost:8000/v1/chat/completions) -> Qwen 3.6 35B         │  │
│  │     • Outputs JSON Schema: Summary, Root Cause, Observed Facts, Evidence, Dynamic Actions       │  │
│  └──────────────────────────────────┬───────────────────────────────────────────────────────────────┘  │
│                                     │                                                                  │
│                                     ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  4. State Store & Supabase Persistence (state_store.py & rca_routes.py)                          │  │
│  │     • In-Memory Thread-Safe Cache + Supabase PostgreSQL Permanent Instance Store                 │  │
│  └──────────────────────────────────┬───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┼──────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              Incident Insights Hub (React 19 / Vite :5173)                             │
│                                                                                                        │
│  • Dashboard: Real-time incident telemetry, severity breakdowns, MTTR metrics                          │
│  • Incidents & RCA: Interactive BPMN viewer, deep incident cards, dynamic Camunda 8.9 badges           │
│  • Ingest Lab: Drag-and-drop custom JSON incident injector & synthetic log generator                  │
│  • History & Processes: Auditable investigation timeline and process definition registry              │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Exhaustive File-by-File Codebase Inventory

### 3.1 Workspace Root Files

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`REPORT.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/REPORT.md) | Markdown | ~850 lines | **Master Platform Report & Complete Codebase Audit**: Exhaustive architectural blueprint, file-by-file inventory, and operational verification guide. |
| [`DOCUMENTATION.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/DOCUMENTATION.md) | Markdown | 251 lines | End-user manual, service port map, prerequisites, environment setup, and incident simulation tutorials. |
| [`PRESENTATION_SCRIPT.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/PRESENTATION_SCRIPT.md) | Markdown | 310 lines | Executive presentation script, slide-by-slide pitch walkthrough, and live demonstration guide for leadership stakeholders. |
| [`run.ps1`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/run.ps1) | PowerShell | 35 lines | Bootstrap orchestration script automating the simultaneous launch of the Sentinel backend, frontend dev server, and DGX SSH tunnel. |
| [`sample_app.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/sample_app.py) | Python | 18 lines | Root-level microservice stub demonstrating exception handling and error forwarding to OpenSRE. |
| [`trigger.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/trigger.py) | Python | 16 lines | Workspace root CLI entry point delegating directly to `graphify/trigger.py` for synthetic incident generation. |
| [`.graphifyignore`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/.graphifyignore) | Config | 7 lines | Exclusion patterns for static code analysis (ignores `node_modules`, `.venv`, `.git`, `.pytest_cache`). |

---

### 3.2 Orchestration & Bridge Layer (`graphify/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`graphify/camunda_bridge.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/camunda_bridge.py) | Python | 65 lines | CLI daemon entry point initiating the automated Camunda Operate polling loop via `bridge_watcher.py`. |
| [`graphify/error_hook.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/error_hook.py) | Python | 195 lines | Universal Python error interception decorator (`@camunda_error_hook`) capturing unhandled exceptions, extracting local variables/stack traces, and dispatching alerts to Sentinel. |
| [`graphify/incident_registry.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/incident_registry.py) | Python | 240 lines | In-memory and disk-persisted incident catalog providing deduplication, incident status tracking, and query filters. |
| [`graphify/log_watcher.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/log_watcher.py) | Python | 245 lines | Real-time file system tailer parsing application logs with regular expressions to detect stack traces and trigger RCA. |
| [`graphify/watcher.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/watcher.py) | Python | 165 lines | Directory monitor scanning `incidents/incoming` for dropped JSON files and automatically feeding them into Sentinel. |
| [`graphify/check_operate_status.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/check_operate_status.py) | Python | 70 lines | Operational utility validating Camunda Operate authentication, cookie sessions, CSRF headers, and active incident counts on port 8081. |
| [`graphify/trigger.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/trigger.py) | Python | 240 lines | Interactive incident inducer CLI allowing users to inject real Camunda 8 incidents (`UNHANDLED_ERROR_EVENT`, `CONDITION_ERROR`, `JOB_NO_RETRIES`, `FORM_NOT_FOUND`). |
| [`graphify/sample_app.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sample_app.py) | Python | 110 lines | Multi-route Flask web service simulating real-world e-commerce payment timeouts, database locks, and validation errors. |
| [`graphify/docker-compose.yml`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/docker-compose.yml) | YAML | 48 lines | Docker Compose configuration defining the Camunda 8.9 stack (Zeebe, Operate, Elasticsearch, Tasklist) for local development. |
| [`graphify/docker-compose-8.6-backup.yml`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/docker-compose-8.6-backup.yml) | YAML | 145 lines | Backup Docker Compose configuration for multi-node legacy Camunda 8.6 clusters. |
| [`graphify/requirements.txt`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/requirements.txt) | Text | 28 lines | Pinned Python dependencies (`fastapi`, `uvicorn`, `pydantic`, `httpx`, `supabase`, `pytest`, `requests`, `pyyaml`). |
| [`graphify/.env.example`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/.env.example) | Config | 35 lines | Master environment variable template declaring port bindings, DGX URLs, Supabase API keys, and Operate credentials. |
| [`graphify/README.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/README.md) | Markdown | 95 lines | Graphify module overview, quickstart instructions, and component interaction guide. |
| [`graphify/camunda_8_9_deep_incident.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/camunda_8_9_deep_incident.json) | JSON | 140 lines | Synthetic production incident payload: PostgreSQL transaction lock + HikariCP exhaustion (50/50) + Stripe 504 + Zeebe Parallel Deadlock. |
| [`graphify/camunda_8_9_deep_dmn_incident.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/camunda_8_9_deep_dmn_incident.json) | JSON | 135 lines | Synthetic production incident payload: `DECISION_EVALUATION_ERROR` with FEEL runtime type mismatch (`"43.5%"` String vs Double) + Kafka Avro schema drift + XOR gateway without default flow. |

---

### 3.3 Sentinel FastAPI Microservice (`graphify/sentinel/`)

#### 3.3.1 Microservice Entrypoint & Base Modules

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`sentinel/main.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/main.py) | Python | 85 lines | FastAPI application bootstrap, CORS middleware initialization, router registrations (`rca_routes`, `camunda_proxy`, `dgx_routes`, `runbook_routes`), and startup warmup hooks. |
| [`sentinel/Dockerfile`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/Dockerfile) | Docker | 15 lines | Container build definition packaging Sentinel with Python 3.11-slim, pre-installing dependencies, and exposing port 5000. |
| [`sentinel/dgx_engine.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/dgx_engine.py) | Python | 22 lines | Compatibility wrapper re-exporting `sentinel.engine.dgx_client` functions for backward compatibility. |
| [`sentinel/investigator.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/investigator.py) | Python | 18 lines | Backward compatibility shim routing investigation calls to `sentinel.core.investigator`. |
| [`sentinel/models.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/models.py) | Python | 15 lines | Compatibility import exporter forwarding Pydantic data schemas from `sentinel.core.models`. |
| [`sentinel/incident_builder.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/incident_builder.py) | Python | 14 lines | Compatibility wrapper re-exporting `sentinel.core.incident_builder`. |
| [`sentinel/supabase_runbook.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/supabase_runbook.py) | Python | 25 lines | Compatibility proxy delegating database operations to `sentinel.knowledge.supabase_runbook`. |
| [`sentinel/camunda_knowledge.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/camunda_knowledge.py) | Python | 25 lines | Compatibility wrapper forwarding calls to `sentinel.knowledge.camunda_knowledge`. |

#### 3.3.2 API Routing Layer (`sentinel/api/`)

| File Link & Path | Type | Lines / Size | Routes & Technical Details |
| :--- | :---: | :---: | :--- |
| [`sentinel/api/rca_routes.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/api/rca_routes.py) | Python | 160 lines | Primary investigation endpoints:<br>• `GET /health`: Service liveness check.<br>• `POST /investigate`: Asynchronously dispatches investigation task to background executor.<br>• `POST /investigate/from-error`: Ingests raw exceptions, converts to `IncidentAlert`, and triggers RCA.<br>• `GET /investigations`: Lists all active and historical investigation records.<br>• `GET /investigations/{inv_id}`: Polls investigation status or retrieves finalized RCA report.<br>• `POST /api/rca/record`: Ingests external RCA reports into in-memory store and Supabase. |
| [`sentinel/api/camunda_proxy.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/api/camunda_proxy.py) | Python | 95 lines | Reverse proxy endpoints solving browser CORS limitations for Camunda Operate:<br>• `POST /api/camunda/incidents/search`: Proxies `/v1/incidents/search`.<br>• `POST /api/camunda/process-instances/search`: Proxies `/v2/process-instances/search`.<br>• `GET /api/camunda/process-definitions/{id}/xml`: Fetches raw BPMN XML from Operate. |
| [`sentinel/api/dgx_routes.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/api/dgx_routes.py) | Python | 30 lines | Hardware diagnostic endpoints:<br>• `GET /api/dgx/status`: Probes local SSH tunnel `:8000` to verify vLLM availability.<br>• `GET /api/dgx/model`: Returns the active model identifier (`nvidia/Qwen3.6-35B-A3B-NVFP4`). |
| [`sentinel/api/runbook_routes.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/api/runbook_routes.py) | Python | 65 lines | SOP knowledge endpoints:<br>• `GET /api/runbooks/{error_type}`: Queries Supabase database for canonical remediation playbooks matching specific Camunda error types. |

#### 3.3.3 Camunda Integration & Graph Topology (`sentinel/camunda/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`sentinel/camunda/client.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/camunda/client.py) | Python | 311 lines | `OperateClient` class managing HTTP cookie sessions, CSRF token negotiation, cluster version discovery (`/v1/topology` -> `8.9.17`), incident search pagination, process variable inspection, and raw BPMN XML downloads. |
| [`sentinel/camunda/topology_parser.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/camunda/topology_parser.py) | Python | 260 lines | `parse_bpmn_topology()`: XML parser and BFS graph traversal engine extracting gateways (Parallel, Exclusive, Inclusive), boundary error events, sequence flows, dynamic `executionPlatformVersion` version attributes, and calculating deadlock hazards with actionable remediation. |
| [`sentinel/camunda/bridge_watcher.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/camunda/bridge_watcher.py) | Python | 302 lines | `start_watcher_loop()`, `build_incident_payload()`, and `push_rca_to_sentinel()`: High-frequency polling daemon querying Operate for unresolved incidents, enriching payloads with live variables and topology, and triggering DGX inference. |

#### 3.3.4 Core Engine, Investigator & State Store (`sentinel/core/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`sentinel/core/models.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/core/models.py) | Python | 85 lines | Pydantic v2 data models: `IncidentAlert`, `ErrorEvent`, `RcaReport`, `DocumentationReference`, `InvestigationResult`. |
| [`sentinel/core/incident_builder.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/core/incident_builder.py) | Python | 45 lines | `build_incident_from_error()`: Normalizes unstructured stack traces, log files, and HTTP webhooks into standardized `IncidentAlert` models. |
| [`sentinel/core/investigator.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/core/investigator.py) | Python | 145 lines | `run_investigation()`: Primary controller coordinating knowledge retrieval, Supabase SOP lookup, DGX LLM inference, and in-memory cache storage. |
| [`sentinel/core/state_store.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/core/state_store.py) | Python | 70 lines | `InvestigationStore`: Thread-safe, multi-indexed in-memory repository mapping `inv_id`, `incident_key`, and `instance_key` to active investigations. |

#### 3.3.5 DGX AI Inference & Prompt Engine (`sentinel/engine/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`sentinel/engine/prompt_builder.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/engine/prompt_builder.py) | Python | 195 lines | `build_sre_system_prompt()` & `build_rca_prompt()`: Constructs version-pinned system prompts enforcing strict Camunda engine semantics, embedding BPMN graph topology warnings, official Camunda documentation citations, and canonical team SOP playbooks. |
| [`sentinel/engine/dgx_client.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/engine/dgx_client.py) | Python | 295 lines | `run_rca_on_dgx()` & `investigate_with_dgx()`: Communicates with DGX vLLM API, parses and validates JSON LLM outputs, dynamically incorporates topology recommendations, and populates documentation references. |

#### 3.3.6 Knowledge Base, Kapa MCP & Supabase SOPs (`sentinel/knowledge/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`sentinel/knowledge/camunda_knowledge.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_knowledge.py) | Python | 316 lines | `retrieve_camunda_context()`, `format_versioned_doc_url()`: 0.18ms local offline vector-like scoring engine matching error types, elements, and topology warnings with dynamic version-pinned URL rewriting (`/docs/{version}/...`). |
| [`sentinel/knowledge/kapa_mcp_client.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/kapa_mcp_client.py) | Python | 162 lines | `query_kapa_mcp()`: Standard Model Context Protocol (MCP) JSON-RPC 2.0 client querying `https://camunda-docs.mcp.kapa.ai` with dynamic version tags (`[Camunda 8.9]`). |
| [`sentinel/knowledge/supabase_runbook.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/supabase_runbook.py) | Python | 307 lines | `lookup_instance_rca()`, `save_instance_rca()`, `lookup_sop_guidelines()`: Connects to Supabase PostgreSQL database for persistent RCA archiving and canonical team runbooks. |

#### 3.3.7 Local Camunda Documentation Catalog (`sentinel/knowledge/camunda_docs/`)

The local offline RAG knowledge base contains 21 core markdown rule specifications and an indexed topic metadata file:

| File Link & Path | Size | Key Camunda Engine Topics Covered |
| :--- | :---: | :--- |
| [`camunda_docs/_index.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/_index.json) | 20.4 KB | Index metadata mapping keywords, error codes, and elements to markdown files. |
| [`camunda_docs/error-events.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/error-events.md) | 6.5 KB | Error Boundary Catch events, Error End events, errorCode scoping, and unhandled errors. |
| [`camunda_docs/incidents.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/incidents.md) | 3.0 KB | Zeebe incident lifecycles, incident states, manual resolution, and retry operations. |
| [`camunda_docs/exclusive-gateways.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/exclusive-gateways.md) | 2.8 KB | XOR gateway evaluation rules, FEEL condition syntax, and default sequence flows. |
| [`camunda_docs/parallel-gateways.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/parallel-gateways.md) | 1.0 KB | Parallel Fork/Join token semantics, token synchronization, and deadlock hazards. |
| [`camunda_docs/inclusive-gateways.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/inclusive-gateways.md) | 3.8 KB | Inclusive OR gateway branching and multi-token merging mechanics. |
| [`camunda_docs/event-based-gateways.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/event-based-gateways.md) | 1.7 KB | Event-driven gateway triggers, message correlation, and timer conditions. |
| [`camunda_docs/service-tasks.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/service-tasks.md) | 3.3 KB | Zeebe Job Workers, job polling intervals, retry exhaustion, and backoff strategies. |
| [`camunda_docs/user-tasks.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/user-tasks.md) | 19.2 KB | Camunda 8 User Tasks, Tasklist integration, form schema bindings, and assignments. |
| [`camunda_docs/variables.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/variables.md) | 24.0 KB | Variable scoping, input/output variable mappings, document payloads, and size limits. |
| [`camunda_docs/expressions.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/expressions.md) | 3.6 KB | Friendly Easy Expression Language (FEEL) syntax, type conversions, and null handling. |
| [`camunda_docs/message-events.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/message-events.md) | 9.1 KB | Message buffering, correlation keys, message catch events, and TTL timeouts. |
| [`camunda_docs/timer-events.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/timer-events.md) | 7.5 KB | ISO 8601 date, duration, and cycle timer event definitions and boundary timers. |
| [`camunda_docs/signal-events.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/signal-events.md) | 5.7 KB | Broadcast signal mechanics, signal throw/catch events across process definitions. |
| [`camunda_docs/call-activities.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/call-activities.md) | 9.1 KB | Child process invocation, variable propagation in/out, and multi-instance child calls. |
| [`camunda_docs/multi-instance.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/multi-instance.md) | 10.8 KB | Parallel and sequential multi-instance loop characteristics and completion conditions. |
| [`camunda_docs/embedded-subprocesses.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/embedded-subprocesses.md) | 3.4 KB | Subprocess variable scoping, boundary error interception, and execution containment. |
| [`camunda_docs/event-subprocesses.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/event-subprocesses.md) | 2.7 KB | Interrupting and non-interrupting event subprocesses triggered by errors or messages. |
| [`camunda_docs/terminate-events.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/terminate-events.md) | 1.8 KB | Process and subprocess token cancellation rules via Terminate End Events. |
| [`camunda_docs/compensation-events.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/compensation-events.md) | 5.0 KB | Saga transaction compensation handlers and backward rollback execution. |
| [`camunda_docs/data-flow.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/data-flow.md) | 3.0 KB | Data object mapping, payload immutability, and Zeebe internal event records. |
| [`camunda_docs/process-instance-modification.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_docs/process-instance-modification.md) | 14.4 KB | Manual token movement, token cancellation, and variable patching in live instances. |

#### 3.3.8 Automation Scripts & DDL Schemas (`sentinel/scripts/`, Root Scripts)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`sentinel/scripts/fetch_camunda_docs.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/scripts/fetch_camunda_docs.py) | Python | 480 lines | Automated crawler scraping the official Camunda documentation repository and rebuilding the local markdown knowledge index. |
| [`sentinel/seed_predefined_runbooks.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/seed_predefined_runbooks.py) | Python | 222 lines | Database migration script seeding canonical SRE runbook playbooks into Supabase PostgreSQL. |
| [`sentinel/runbook_schema.sql`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/runbook_schema.sql) | SQL | 120 lines | PostgreSQL DDL schema definition for the `runbooks` table, indexes, and Row Level Security (RLS) policies. |
| [`sentinel/test_camunda_knowledge_rag.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/test_camunda_knowledge_rag.py) | Python | 188 lines | Automated test suite verifying URL version rewriting, sub-millisecond retrieval latency, and live DGX Qwen inference. |

---

### 3.4 Incident Insights Hub UI (`graphify/Incident Insights Hub/`)

#### 3.4.1 Configuration & Project Metadata

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`package.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/package.json) | JSON | 95 lines | Frontend npm package manifest specifying React 19, Vite 6, `@tanstack/react-router`, `bpmn-js`, `lucide-react`, `tailwindcss`, and `@radix-ui` dependencies. |
| [`vite.config.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/vite.config.ts) | TypeScript | 42 lines | Vite configuration configuring the TanStack Router plugin, path aliases (`@/`), and development server port `5173`. |
| [`tsconfig.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/tsconfig.json) | JSON | 30 lines | TypeScript compiler options enabling strict mode, JSX transforms, and path alias mapping. |
| [`eslint.config.js`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/eslint.config.js) | JS | 40 lines | ESLint configuration declaring rules for React hooks and TypeScript linting. |
| [`components.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/components.json) | JSON | 20 lines | Shadcn UI configuration file declaring design tokens, CSS variables, and component directory paths. |
| [`bunfig.toml`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/bunfig.toml) | TOML | 15 lines | Bun runtime configuration for optional high-speed bundle execution. |
| [`AGENTS.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/AGENTS.md) | Markdown | 20 lines | LLM coding assistant guidelines for the frontend application repository. |
| [`README.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/README.md) | Markdown | 35 lines | Frontend overview and quickstart guide for launching the web dashboard. |
| [`src/styles.css`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/styles.css) | CSS | 280 lines | Global Tailwind stylesheet defining HSL color tokens, dark mode variables, glassmorphic card classes, and bpmn-js diagram styling. |
| [`src/router.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/router.tsx) | TypeScript | 15 lines | TanStack Router instance creation and type-safe router exporting. |
| [`src/routeTree.gen.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/routeTree.gen.ts) | TypeScript | 145 lines | Auto-generated TanStack route tree binding all file-based routes. |
| [`src/start.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/start.ts) | TypeScript | 35 lines | Application startup bootstrapper configuring query client and error boundaries. |
| [`src/server.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/server.ts) | TypeScript | 70 lines | Node/Bun server entry point for server-side rendered deployments. |

#### 3.4.2 Application Routes (`src/routes/`)

| File Link & Path | Type | Lines / Size | Route & Key Features |
| :--- | :---: | :---: | :--- |
| [`src/routes/__root.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/routes/__root.tsx) | TypeScript | 110 lines | Root application shell layout, sidebar navigation, theme switcher, and real-time backend connection status indicators. |
| [`src/routes/index.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/routes/index.tsx) | TypeScript | 285 lines | **Executive Dashboard**: KPI metric cards (Total Incidents, Active Failures, MTTR, DGX Latency), severity distribution charts, and live incident feed. |
| [`src/routes/incidents.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/routes/incidents.tsx) | TypeScript | 195 lines | **Live Incidents & RCA Workspace**: Dual-pane master-detail view with search/filter on active incidents and in-depth RCA analysis. |
| [`src/routes/ingest.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/routes/ingest.tsx) | TypeScript | 423 lines | **Incident & Log Injection Lab**: Interactive payload constructor, drag-and-drop JSON file loader, enterprise test template picker, and instant RCA triggering. |
| [`src/routes/history.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/routes/history.tsx) | TypeScript | 260 lines | **Audit History & Timeline**: Permanent chronological audit log of all investigated incidents with resolution tags and Markdown/JSON export capabilities. |
| [`src/routes/processes.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/routes/processes.tsx) | TypeScript | 210 lines | **Process Definition Catalog**: Visual registry of all deployed Camunda BPMN definitions, active instance counts, and incident heatmaps. |
| [`src/routes/settings.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/routes/settings.tsx) | TypeScript | 180 lines | **Settings & Connectivity**: Endpoint configuration for Camunda Operate (:8081), Sentinel (:5000), and DGX (:8000) with live latency diagnostics. |
| [`src/routes/README.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/routes/README.md) | Markdown | 25 lines | Routing architecture and route tree generation documentation. |

#### 3.4.3 Custom SRE React Components (`src/components/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`src/components/RcaDetail.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/RcaDetail.tsx) | TypeScript | 540 lines | **Core RCA Investigation Presentation Card**: Dynamic Camunda version badge, interactive BPMN viewer embed, WHAT/WHY/HOW sections, topology alerts, cited evidence, official documentation reference chips, and resolution actions. |
| [`src/components/OperateBpmnViewer.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/OperateBpmnViewer.tsx) | TypeScript | 290 lines | Embedded `bpmn-js` interactive diagram viewer rendering BPMN 2.0 XML with red highlight overlays on failing flow nodes and active incident counters. |
| [`src/components/AppShell.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/AppShell.tsx) | TypeScript | 165 lines | Collapsible navigation sidebar wrapper, breadcrumb generator, header bar, and live service mesh connectivity indicators. |
| [`src/components/MetricCard.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/MetricCard.tsx) | TypeScript | 75 lines | KPI card rendering numeric values, trend indicators, percentage deltas, and subtle gradient backgrounds. |
| [`src/components/SeverityBadge.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/SeverityBadge.tsx) | TypeScript | 50 lines | Color-coded severity badge component supporting `critical` (red), `high` (orange), `medium` (yellow), and `low` (blue). |
| [`src/components/StatusDot.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/StatusDot.tsx) | TypeScript | 40 lines | Animated pulsating status dot for service mesh health (Green = Online, Yellow = Checking, Red = Offline). |
| [`src/components/EmptyState.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/EmptyState.tsx) | TypeScript | 30 lines | Empty placeholder state with contextual illustration and call-to-action buttons. |

#### 3.4.4 Shadcn UI Primitives Library (`src/components/ui/`)

The application includes 46 modular, accessible UI primitives built with Radix UI and Tailwind CSS:

| UI Component File Link | Description & Usage |
| :--- | :--- |
| [`accordion.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/accordion.tsx) | Expandable accordion sections for multi-layered stack traces and SOP steps. |
| [`alert.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/alert.tsx) & [`alert-dialog.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/alert-dialog.tsx) | Modal alert dialogs and inline alert callouts for critical system warnings. |
| [`badge.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/badge.tsx) | Styled pill badges for incident status, element types, and engine version tags. |
| [`button.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/button.tsx) | Primary, secondary, outline, destructive, and ghost interactive button variants. |
| [`card.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/card.tsx) | Surface container cards with header, title, description, and footer sections. |
| [`chart.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/chart.tsx) | Recharts integration wrapper for real-time MTTR and incident volume charts. |
| [`dialog.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/dialog.tsx) & [`drawer.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/drawer.tsx) | Accessible modal popups and slide-over side drawers for deep incident payloads. |
| [`dropdown-menu.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/dropdown-menu.tsx) | Dropdown selection menus for filters, exports, and incident action commands. |
| [`input.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/input.tsx) & [`textarea.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/textarea.tsx) | Controlled text inputs and multi-line code textareas with monospace font. |
| [`scroll-area.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/scroll-area.tsx) | Custom scrollable containers with sleek translucent scrollbars. |
| [`select.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/select.tsx) | Styled select dropdown controls for environment switching and template choices. |
| [`sonner.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/sonner.tsx) | Toast notification container reporting background task success or network errors. |
| [`table.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/table.tsx) | Clean data tables for process instance listings, variable maps, and audit logs. |
| [`tabs.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/tabs.tsx) | Tab switching navigation for Investigation Overview, BPMN Diagram, and Raw JSON. |
| [`tooltip.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/components/ui/tooltip.tsx) | Hover tooltips detailing metric descriptions and element properties. |
| *Other Primitives* | `aspect-ratio`, `avatar`, `breadcrumb`, `calendar`, `carousel`, `checkbox`, `collapsible`, `command`, `context-menu`, `form`, `hover-card`, `input-otp`, `label`, `menubar`, `navigation-menu`, `pagination`, `popover`, `progress`, `radio-group`, `resizable`, `separator`, `sheet`, `sidebar`, `skeleton`, `slider`, `switch`, `toggle`, `toggle-group`. |

#### 3.4.5 Application State, Hooks & API Client (`src/lib/` & `src/hooks/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`src/lib/api.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/api.ts) | TypeScript | 225 lines | Centralized API client dispatching requests to Sentinel (:5000), Camunda Operate (:8081 via proxy), and DGX AI engine (:8000). |
| [`src/lib/app-context.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/app-context.tsx) | TypeScript | 110 lines | Global React Context Provider managing service endpoints, theme state, and periodic health check ping loops. |
| [`src/lib/use-incidents.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/use-incidents.ts) | TypeScript | 70 lines | React hook polling live Operate incidents, process definitions, and instances with automatic retry and error backoff. |
| [`src/lib/storage.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/storage.ts) | TypeScript | 125 lines | Browser LocalStorage management layer persisting custom incident templates, saved RCA reports, and user preferences. |
| [`src/lib/types.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/types.ts) | TypeScript | 145 lines | Strict TypeScript interfaces for Camunda entities, `IncidentAlert`, `RcaReport`, `DocumentationReference`, and UI view states. |
| [`src/lib/rca-format.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/rca-format.ts) | TypeScript | 76 lines | Formatter serializing structured RCA JSON objects into professional, clean GitHub-flavored Markdown for clipboard export. |
| [`src/lib/incident-cases.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/incident-cases.ts) | TypeScript | 210 lines | Catalog of curated enterprise test scenarios (Unhandled Error, Gateway Deadlock, DMN Type Collision) for instant loading in Ingest Lab. |
| [`src/lib/error-capture.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/error-capture.ts) | TypeScript | 85 lines | Global client-side unhandled exception and promise rejection listener for frontend self-diagnostics. |
| [`src/lib/error-page.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/error-page.ts) | TypeScript | 45 lines | Fallback error view renderer for unrecoverable routing failures. |
| [`src/lib/lovable-error-reporting.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/lovable-error-reporting.ts) | TypeScript | 55 lines | Telemetry dispatcher reporting client runtime health metrics. |
| [`src/lib/utils.ts`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/lib/utils.ts) | TypeScript | 10 lines | Utility helper merging Tailwind classes with `clsx` and `tailwind-merge`. |
| [`src/hooks/use-mobile.tsx`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/Incident%20Insights%20Hub/src/hooks/use-mobile.tsx) | TypeScript | 25 lines | React media query hook detecting viewport breakpoints for responsive mobile rendering. |

---

### 3.5 Camunda BPMN Artifacts & Job Worker Mock Services (`graphify/camunda/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`camunda/bpmn/rca_investigation.bpmn`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/camunda/bpmn/rca_investigation.bpmn) | XML | 3.5 KB | Camunda BPMN 2.0 definition model containing Parallel Fork gateways, service tasks (`payment-service`, `inventory-service`), Error End events, and boundary catch elements. |
| [`camunda/deploy.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/camunda/deploy.py) | Python | 120 lines | Automated deployment script uploading `rca_investigation.bpmn` to Zeebe via REST API (`POST /v1/deployments`). |
| [`camunda/worker.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/camunda/worker.py) | Python | 250 lines | Mock Camunda 8 Job Worker polling Zeebe service tasks and simulating controlled runtime exceptions (timeouts, errors, null references) for testing. |

---

### 3.6 Synthetic Incident Datasets & Test Scenarios (`graphify/incidents/`)

| File Link & Path | Type | Size | Scenario Description |
| :--- | :---: | :---: | :--- |
| [`incidents/camunda_8_9_deep_incident.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/incidents/camunda_8_9_deep_incident.json) | JSON | 10.1 KB | Deep multi-layered failure: PostgreSQL row lock contention -> HikariCP pool saturation -> Stripe payment gateway 504 -> Zeebe parallel deadlock. |
| [`incidents/camunda_8_9_deep_dmn_incident.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/incidents/camunda_8_9_deep_dmn_incident.json) | JSON | 8.0 KB | Deep DMN failure: FEEL runtime type collision (`"43.5%"` String vs numeric Double) -> Kafka Avro schema drift -> XOR missing default flow. |
| [`incidents/test-incident.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/incidents/test-incident.json) | JSON | 1.0 KB | Baseline single-node test incident payload validating basic Sentinel pipeline ingestion. |

---

### 3.7 Shell Scripts & Environment Tooling (`graphify/scripts/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`scripts/start.ps1`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/scripts/start.ps1) | PowerShell | 185 lines | Interactive full-stack startup script provisioning virtual environments, installing dependencies, validating ports, and launching services. |
| [`scripts/run-all.ps1`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/scripts/run-all.ps1) | PowerShell | 65 lines | Concurrent process launcher spawning background jobs for Sentinel, UI, and DGX tunnel. |
| [`scripts/test-investigation.ps1`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/scripts/test-investigation.ps1) | PowerShell | 35 lines | Automated validation script dispatching test payloads to Sentinel and asserting HTTP 200 responses. |
| [`scripts/fix-temp.ps1`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/scripts/fix-temp.ps1) | PowerShell | 20 lines | Maintenance script cleaning temporary cache files and dangling socket locks. |

---

### 3.8 Automated Unit & Integration Tests (`graphify/tests/`)

| File Link & Path | Type | Lines / Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`tests/test_sentinel.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/tests/test_sentinel.py) | Python | 135 lines | Pytest test suite testing Pydantic model serialization, investigation dispatching, store lookups, and error conversion logic. |

---

### 3.9 Static Graph Analysis Artifacts (`graphify-out/`)

| File Link & Path | Type | Size | Purpose & Technical Description |
| :--- | :---: | :---: | :--- |
| [`graphify-out/GRAPH_REPORT.md`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify-out/GRAPH_REPORT.md) | Markdown | 18.0 KB | Static code analysis report detailing dependency graphs, module couplings, and architectural metrics. |
| [`graphify-out/graph.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify-out/graph.json) | JSON | 1.1 MB | Complete graph dependency dataset modeling all functions, classes, and file import edges. |
| [`graphify-out/graph.html`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify-out/graph.html) | HTML | 923 KB | Interactive D3.js 3D visual graph explorer of the OpenSRE codebase. |
| [`graphify-out/manifest.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify-out/manifest.json) | JSON | 46.6 KB | Manifest tracking file hashes and AST node counts. |
| [`graphify-out/.graphify_analysis.json`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify-out/.graphify_analysis.json) | JSON | 70.2 KB | Raw static analysis metrics and cyclomatic complexity logs. |

---

## 4. Deep Dive: Core Architectural Subsystems

### 4.1 Dynamic Version-Aware Resolution Engine (Camunda 8.0 – 8.10+)

In previous iterations, SRE tooling often suffered from hardcoded engine assumptions (e.g. defaulting to legacy Camunda 8.6), causing documentation links to fail and prompts to misstate engine invariants. OpenSRE implements a dynamic version resolution hierarchy:

```
                  ┌────────────────────────────────────────────────────────┐
                  │ 1. Read BPMN XML Definition Header                     │
                  │    <bpmn:definitions                                   │
                  │      modeler:executionPlatformVersion="8.9.0">         │
                  └───────────────────────────┬────────────────────────────┘
                                              │ (If Found: Pin to "8.9")
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │ 2. Live Cluster Topology Header Query                  │
                  │    GET http://localhost:8080/v1/topology               │
                  │    Response: { "gatewayVersion": "8.9.17" }            │
                  └───────────────────────────┬────────────────────────────┘
                                              │ (If Found: Pin to "8.9")
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │ 3. Fallback Dynamic Default Version                    │
                  │    Target Version: "8.9"                               │
                  └────────────────────────────────────────────────────────┘
```

#### Multi-Tier Version Propagation
1. **BPMN XML Header Parsing** ([`topology_parser.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/camunda/topology_parser.py)): Directly reads `modeler:executionPlatformVersion` from `<bpmn:definitions>` attributes, converting semver strings (e.g., `"8.9.0"`) into major.minor pins (`"8.9"`).
2. **Dynamic Documentation URL Rewriter** ([`camunda_knowledge.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/camunda_knowledge.py)): Dynamically converts canonical URL paths into targeted documentation links:
   `https://docs.camunda.io/docs/{version}/components/modeler/bpmn/error-events/`
3. **Kapa MCP Scoping** ([`kapa_mcp_client.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/kapa_mcp_client.py)): Prepends `[Camunda {version}]` context tags to all Model Context Protocol queries.
4. **Prompt Invariant Binding** ([`prompt_builder.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/engine/prompt_builder.py)): Binds `TARGET ENGINE VERSION: Camunda {version}` directly into the LLM system prompt invariants.

---

### 4.2 BPMN 2.0 Graph Topology & Reachability Engine

The graph topology engine in [`sentinel/camunda/topology_parser.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/camunda/topology_parser.py) performs AST and Breadth-First Search (BFS) reachability traversal to detect structural runtime hazards:

#### 1. Parallel Fork / Join Deadlock Hazard (Token Starvation)
When a process executes concurrent branches spawned by a **Parallel Fork Gateway** (`bpmn:parallelGateway`), every branch must deliver an execution token to the downstream **Parallel Join Gateway** before the process can advance.

If an error boundary event or throw-error event in one branch diverts the token away from the join without terminating the entire process instance, the join gateway waits indefinitely for the missing token. The topology engine detects this condition and automatically outputs:
```text
CRITICAL TOPOLOGY HAZARD: Task '{failing_task}' is in a concurrent branch from Parallel Gateway '{fork_id}' joining at '{join_id}'. Diverting execution via error flow will cause a Parallel Join Deadlock (token starvation).
RECOMMENDATION: Route error flow to a Terminate End Event or attach an interrupting Error Boundary Event to the parent subprocess scope.
```

#### 2. Exclusive Gateway (XOR) Missing Default Flow Hazard
Evaluates all outgoing conditional flows from `bpmn:exclusiveGateway`. If an XOR gateway lacks a default sequence flow (`default="flow_id"`), runtime evaluation of unhandled variable combinations will throw a fatal `CONDITION_ERROR`. The engine detects this and outputs:
```text
CRITICAL TOPOLOGY HAZARD: Exclusive Gateway '{gw_id}' has multiple outgoing conditional flows but NO default sequence flow defined.
RECOMMENDATION: Set a default sequence flow in Camunda Modeler to prevent CONDITION_ERROR incidents when conditions evaluate to false.
```

#### 3. Error Boundary Event Scope Validation
Traverses the parent element hierarchy of the failing flow node to determine whether an `bpmn:boundaryEvent` with a matching `bpmn:errorEventDefinition` is active in the current execution scope.

---

### 4.3 Sub-Millisecond Hybrid Knowledge Retrieval & Kapa MCP Integration

OpenSRE deploys a two-tier knowledge retrieval architecture:

```
                         Incident Occurs (e.g. UNHANDLED_ERROR_EVENT)
                                              │
                                              ▼
                    ┌──────────────────────────────────────────────────┐
                    │ Query Primary: Camunda Kapa MCP Server           │
                    │ Endpoint: https://camunda-docs.mcp.kapa.ai       │
                    │ Protocol: JSON-RPC 2.0 (Tags: [Camunda 8.9])     │
                    └─────────────────────────┬────────────────────────┘
                                              │
                         ┌────────────────────┴────────────────────┐
                         │ MCP Success (<800ms)                    │ MCP Timeout / Offline
                         ▼                                         ▼
           ┌───────────────────────────┐             ┌───────────────────────────┐
           │ Rich Context Injected     │             │ Local Sub-Millisecond RAG │
           │ into Prompt               │             │ (camunda_knowledge.py)    │
           └───────────────────────────┘             └─────────────┬─────────────┘
                                                                   │ 0.18ms Latency
                                                                   ▼
                                                     ┌───────────────────────────┐
                                                     │ 21 Indexed Engine Docs    │
                                                     │ Dynamic URL Rewriting     │
                                                     └───────────────────────────┘
```

#### Performance Benchmarks
In offline benchmark tests across 500 consecutive retrieval queries, the local knowledge engine loaded 21 core topics in **0.43 ms** and executed queries with an average latency of **0.1819 ms** per query.

---

### 4.4 NVIDIA DGX vLLM Qwen 35B Inference Engine & Schema Guardrails

The inference engine in [`sentinel/engine/dgx_client.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/engine/dgx_client.py) connects via SSH tunnel (`http://localhost:8000/v1/chat/completions`) to an on-premise NVIDIA DGX station hosting `nvidia/Qwen3.6-35B-A3B-NVFP4`.

#### Enforced JSON Output Contract
The model is constrained to generate deterministic JSON conforming to:
```json
{
  "summary": "One-line executive problem summary",
  "root_cause": "Deep technical explanation of the failure mechanism",
  "confidence": "HIGH | MEDIUM | LOW",
  "observed_facts": [
    "Fact 1 with element IDs and variable names",
    "Fact 2 with timestamp and error codes"
  ],
  "evidence": [
    "Exact cited stack trace or log excerpt"
  ],
  "recommended_actions": [
    "Immediate operational remediation action",
    "BPMN Modeler structural fix"
  ],
  "topology_warnings": [
    "Hazard warnings extracted by graph analysis"
  ],
  "documentation_references": [
    {
      "section": "Error Events",
      "url": "https://docs.camunda.io/docs/8.9/components/modeler/bpmn/error-events/",
      "relevance": "Camunda 8.9 Error Boundary Catch rules"
    }
  ]
}
```

#### Three-Tier Robust Parser Fallback
1. **Tier 1**: Direct `json.loads()` on sanitized LLM response.
2. **Tier 2**: Unicode quote normalization, trailing comma stripping, and markdown code block extraction (` ```json ... ``` `).
3. **Tier 3**: Regular expression key-value extraction ensuring valid `RcaReport` objects are produced even in partial output conditions.

---

### 4.5 SRE Standard Operating Procedures (SOP) & Supabase Persistence

Located in [`sentinel/knowledge/supabase_runbook.py`](file:///c:/Users/madire%20sathwik/OneDrive%20-%20TRUVIQ%20SYSTEMS%20PRIVATE%20LIMITED/Documents/Open%20SRE/graphify/sentinel/knowledge/supabase_runbook.py):

1. **Instance Deduplication Cache**: Caches verified RCA reports in Supabase PostgreSQL indexed by `instance_key`. Repeat queries for the same incident return in `<5ms` without re-invoking the LLM.
2. **Pre-Seeded Canonical SOPs**: Contains standardized operational playbooks for:
   - `UNHANDLED_ERROR_EVENT`
   - `CONDITION_ERROR`
   - `DECISION_EVALUATION_ERROR`
   - `JOB_NO_RETRIES`
   - `FORM_NOT_FOUND`
   - `CONNECTION_POOL_EXHAUSTED`
   - `KAFKA_TIMEOUT`

---

## 5. Network Topology, Ports & Service Mesh Map

| Service Name | Port | Protocol | Binding | Purpose & Responsibilities | Health Probe URL |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Incident Insights Hub** | `5173` | HTTP | `localhost:5173` | React 19 / Vite SRE Web UI | `http://localhost:5173` |
| **Sentinel SRE Backend** | `5000` | HTTP | `0.0.0.0:5000` | FastAPI Core Engine & Proxy | `http://localhost:5000/health` |
| **NVIDIA DGX vLLM AI** | `8000` | HTTP | `localhost:8000` | Qwen 3.6 35B Inference Tunnel | `http://localhost:8000/v1/models` |
| **Camunda Zeebe REST** | `8080` | HTTP | `localhost:8080` | Deployments, Topology, Instances | `http://localhost:8080/v1/topology` |
| **Camunda Operate UI/REST**| `8081` | HTTP | `localhost:8081` | Incident Management & Auditing | `http://localhost:8081/actuator/info` |
| **Camunda Tasklist** | `8082` | HTTP | `localhost:8082` | Human Task Management | `http://localhost:8082` |
| **Elasticsearch** | `9200` | HTTP | `localhost:9200` | Incident Log Indexing | `http://localhost:9200` |
| **Zeebe gRPC Broker** | `26500`| gRPC | `localhost:26500`| High-throughput Job Polling | `localhost:26500` |

---

## 6. Operational Runbooks, Setup & Verification Test Results

### 6.1 Platform Bootstrap Runbook

To launch the complete OpenSRE platform in local development mode:

```powershell
# In workspace root:
.\run.ps1
```

Or execute in dedicated terminal sessions:

```powershell
# Terminal 1: Sentinel FastAPI Backend
cd "graphify\sentinel"
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload

# Terminal 2: NVIDIA DGX SSH Tunnel
ssh -L 8000:localhost:8000 truviq_domain@192.168.0.143

# Terminal 3: Incident Insights Hub Frontend
cd "graphify\Incident Insights Hub"
npm run dev
```

---

### 6.2 Automated Test Suite Results & Latency Benchmarks

All test suites pass with 100% compliance:

```text
============================================================
TEST SUITE 1: Camunda Knowledge RAG & Latency (test_camunda_knowledge_rag.py)
============================================================
--- 1. Testing Dynamic Version Pinning in Doc URLs ---
  Target 8.5 -> https://docs.camunda.io/docs/8.5/components/modeler/bpmn/error-events/
  Target 8.9 -> https://docs.camunda.io/docs/8.9/components/modeler/bpmn/error-events/
  [PASS] All version URLs dynamically formatted correctly!

--- 2. Testing Retrieval Latency & Throughput ---
  Index loaded 21 topics in 0.43 ms
  Executed 500 retrieval queries in 90.95 ms -> Average latency per query: 0.1819 ms (Sub-Millisecond: True)

--- 3. Testing Version-Aware Retrieval Scenarios ---
  [PASS] Unhandled Error Event: Top Match = 'Error Events'
  [PASS] Condition Error on XOR Gateway: Top Match = 'Exclusive Gateways (XOR)'
  [PASS] Service Task Retries Exhausted: Top Match = 'Service Tasks & Job Workers'

--- 4. Testing DGX Qwen 35B Inference with Version-Pinned Camunda 8.9 RCA ---
  DGX vLLM is CONNECTED. Active model: nvidia/Qwen3.6-35B-A3B-NVFP4
  [PASS] DGX RCA received in 6.04s!
  [SUCCESS] ALL CAMUNDA KNOWLEDGE & DYNAMIC VERSION PINNING TESTS PASSED!
```

```text
============================================================
TEST SUITE 2: Multi-Topology Dynamic Recommendations Test
============================================================
=== SCENARIO 1: Parallel Fork/Join Deadlock ===
  [PASS] Parallel Deadlock Warning Detected
  [PASS] Actionable Recommendation: Route to Terminate End Event

=== SCENARIO 2: Exclusive Gateway without Default Flow ===
  [PASS] XOR Missing Default Flow Warning Detected
  [PASS] Actionable Recommendation: Designate Default Flow in Camunda Modeler
  [PASS] Terminate End Event omitted (No false positive)

=== SCENARIO 3: Simple Linear Task Failure ===
  [PASS] Standard Job Worker retry and network remediation generated
  [PASS] Gateway deadlock warnings omitted (No false positive)

[SUCCESS] ALL MULTI-TOPOLOGY DYNAMIC RECOMMENDATION TESTS PASSED!
```

---

### 6.3 Verification of Deep Multi-Layer Incidents in Ingest Lab

Two production-grade synthetic incident datasets are available for end-to-end evaluation in the **Ingest Lab** (`http://localhost:5173/ingest`):

1. **`camunda_8_9_deep_incident.json`**:
   - **Trigger Mechanism**: PostgreSQL lock contention -> HikariCP pool saturation (50/50 active) -> Stripe 504 gateway timeout -> Zeebe `UNHANDLED_ERROR_EVENT` in Parallel Fork.
   - **Verification Result**: DGX correctly identifies the database pool saturation as the primary root cause, cites the exact timeout exception string, and generates the parallel deadlock remediation.

2. **`camunda_8_9_deep_dmn_incident.json`**:
   - **Trigger Mechanism**: `DECISION_EVALUATION_ERROR` with FEEL type collision (`"43.5%"` String passed into numeric Double calculation) -> Kafka Avro schema drift -> XOR gateway with no default flow.
   - **Verification Result**: DGX pinpoints the FEEL type mismatch, references `https://docs.camunda.io/docs/8.9/components/modeler/bpmn/expressions/`, and recommends adding a default sequence flow on the XOR gateway.

---

## 7. Conclusion & Strategic Roadmap

The **OpenSRE** platform provides an end-to-end autonomous incident investigation and remediation platform designed for modern enterprise Camunda 8 deployments. By integrating static BPMN 2.0 graph topology traversal, sub-millisecond local RAG, live Kapa MCP documentation retrieval, on-premise NVIDIA DGX GPU inference, and a React 19 visual workspace, OpenSRE slashes Mean Time to Resolution (MTTR) from hours of manual log parsing to seconds of automated analysis.

### Future Roadmap Highlights
- **Active Remediation Execution**: Automated execution of Camunda instance modifications (token moves, payload variable patches) via Zeebe REST API with human-in-the-loop approval.
- **Predictive Failure Forecasting**: Real-time graph simulation detecting token bottlenecking and deadlocks prior to runtime deployment.
- **Multi-Tenant Cluster Federation**: Centralized management across heterogeneous Camunda 8 clusters across hybrid on-prem and SaaS clouds.
