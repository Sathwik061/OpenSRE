# OpenSRE — The Universal, Platform-Agnostic Site Reliability Intelligence Platform

> **"Any Platform. Any Project. Any Log. Any Runbook Format. Instant, Actionable Root Cause Analysis."**
> 
> OpenSRE is an open, universal, AI-powered Site Reliability Engineering (SRE) and Incident Intelligence platform. It breaks vendor lock-in by capturing deep **Project Context & Business Intent** (what the project is, why it was built, its architecture, and platform), ingesting logs and telemetry from **any system** (Camunda, Pega, Kubernetes, Kafka, Spring Boot, Microservices, Databases, Cloud, or Custom Apps), searching across **multi-format enterprise runbooks (PDF, Word, Markdown, YAML)**, official framework documentations, and **live web intelligence**, and delivering precise, prescriptive Root Cause Analysis (RCA) with step-by-step remediation.

---

## 📑 Table of Contents

1. [Executive Summary & Core Philosophy](#1-executive-summary--core-philosophy)
2. [The Project Intake & Context Profiling Framework ("Project Passport")](#2-the-project-intake--context-profiling-framework-project-passport)
3. [High-Level System Architecture](#3-high-level-system-architecture)
4. [Universal Multi-Format Runbook Ingestion Engine (PDF, Word, Markdown, YAML)](#4-universal-multi-format-runbook-ingestion-engine-pdf-word-markdown-yaml)
5. [Deep Log Scanning & Incident Intelligence Pipeline](#5-deep-log-scanning--incident-intelligence-pipeline)
6. [Multi-Layer Hybrid Investigation Engine (RAG + Live Web Search)](#6-multi-layer-hybrid-investigation-engine-rag--live-web-search)
7. [Standardized RCA Output: The 4-Pillar Incident Report](#7-standardized-rca-output-the-4-pillar-incident-report)
8. [Zero-Leakage Privacy & Sensitive Data Masking Engine](#8-zero-leakage-privacy--sensitive-data-masking-engine)
9. [Enterprise Notification & Auto-Remediation Hub](#9-enterprise-notification--auto-remediation-hub)
10. [End-to-End Incident Lifecycle Walkthrough](#10-end-to-end-incident-lifecycle-walkthrough)
11. [Extensibility & Platform Expansion Guide](#11-extensibility--platform-expansion-guide)

---

## 1. Executive Summary & Core Philosophy

### 1.1 The Core Motto
Traditional APM and SRE tools are often siloed, vendor-specific, or require proprietary log agents. If an enterprise runs Camunda for workflow orchestration, Pega for customer decisioning, Kubernetes for microservices, and PostgreSQL for storage, engineers are forced to context-switch across multiple dashboards and manually dig through fragmented documentation.

Furthermore, traditional log analyzers only look at raw error text in a vacuum—without knowing **what the project is**, **why it was built**, or **what business operations it performs**.

**OpenSRE is built on two foundational principles:**

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   THE OPENSRE CORE PRINCIPLES                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  1. Deep Project Context First ("Understand the Moto & Intent"):                                 │
│     Before investigating, OpenSRE captures the full identity of the project—its name, business   │
│     purpose, why it was built, target platform (Camunda, Pega, K8s, etc.), and architecture.     │
│     This context guides every log scan, runbook search, and AI reasoning step.                   │
│                                                                                                  │
│  2. Universal, Platform-Agnostic Intelligence:                                                   │
│     OpenSRE is not restricted to any single engine. It accepts any logs, indexes runbooks in     │
│     any format (PDF, Word .docx, Markdown, YAML), searches live web intelligence when needed,    │
│     and produces deterministic, actionable fixes in seconds.                                     │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Project Intake & Context Profiling Framework ("Project Passport")

Just as an enterprise application collects user registration and profile details during signup, OpenSRE captures a comprehensive **Project Profile / Passport** for every workload it monitors.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   THE OPENSRE PROJECT PASSPORT                                   │
├──────────────────────────┬───────────────────────────────────────┬───────────────────────────────┤
│ Dimension                │ Questions Answered                    │ Example Configuration         │
├──────────────────────────┼───────────────────────────────────────┼───────────────────────────────┤
│ **1. Project Identity**  │ What is the project name & service?   │ `Global-Payment-Gateway`,     │
│                          │                                       │ `orderFulfillmentProcess`     │
├──────────────────────────┼───────────────────────────────────────┼───────────────────────────────┤
│ **2. Purpose & Moto**    │ Why was it built? What does it do?    │ "Processes B2B customer       │
│                          │ What is the expected business flow?   │ checkout, validates credit    │
│                          │                                       │ cards, reserves inventory"    │
├──────────────────────────┼───────────────────────────────────────┼───────────────────────────────┤
│ **3. Platform & Version**│ What execution engine/stack is used?  │ `Camunda 8.9`, `Camunda 7.20`,│
│                          │                                       │ `Pega 8.8`, `Kubernetes`,     │
│                          │                                       │ `Spring Boot 3`, `Kafka`      │
├──────────────────────────┼───────────────────────────────────────┼───────────────────────────────┤
│ **4. Architecture Graph**│ What are the upstream/downstream      │ Upstream: Stripe Gateway API  │
│                          │ dependencies, DBs, and queues?        │ Downstream: Redis Cluster, DB │
├──────────────────────────┼───────────────────────────────────────┼───────────────────────────────┤
│ **5. Environment**       │ Where is this running?                │ `Production`, `Staging`, `DR` │
├──────────────────────────┼───────────────────────────────────────┼───────────────────────────────┤
│ **6. Runbooks / SOPs**   │ What company SOPs govern this project?│ `Payment_SOP_v3.pdf`,         │
│                          │ (PDF, Word, Markdown, YAML)           │ `Deadlock_Runbook.docx`       │
├──────────────────────────┼───────────────────────────────────────┼───────────────────────────────┤
│ **7. Logs & Telemetry**  │ What logs and traces were generated?  │ Raw log files, Zeebe events,  │
│                          │                                       │ microservice stdout streams   │
└──────────────────────────┴───────────────────────────────────────┴───────────────────────────────┘
```

### 2.1 Why Project Context Transforms RCA Accuracy
When OpenSRE receives an error like `LettuceConnectionException: Unable to connect to redis-cluster:6379`:

- **Without Project Context (Traditional Tool):**
  > *"Error: Redis connection timeout. Recommendation: Check Redis service."* (Generic and unhelpful).

- **WITH OpenSRE Project Profile Intelligence:**
  > *"Incident in **`orderFulfillmentProcess`** (Production on **Camunda 8.9**).  
  > **Business Impact:** Customer checkout is stalled at step **`Activity_ProcessPayment`**.  
  > **Root Cause:** Upstream Redis session cache connection pool exhausted (auth timeout) while authorizing credit transaction for order checkout.  
  > **Resolution (from attached `Payment_SOP_v3.pdf` & Camunda 8.9 Rules):**  
  > 1. Scale Lettuce connection pool max-active in Redis configuration.  
  > 2. Attach an interrupting Error Boundary Catch Event with code `PAYMENT_FAILED` on `Activity_ProcessPayment` in Camunda Modeler to prevent token starvation deadlocks."*

---

## 3. High-Level System Architecture

```
                                  ┌─────────────────────────────────────────┐
                                  │      1. USER INTAKE & PROJECT DATA      │
                                  │  • Project Name & Business Purpose/Moto │
                                  │  • Target Platform (Camunda, Pega, K8s) │
                                  │  • Multi-Format Runbooks (PDF/Word/YAML)│
                                  │  • Raw Incident Logs, Traces & Variables│
                                  └────────────────────┬────────────────────┘
                                                       │
                                                       ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                2. SCANNER ENGINE                              │
│                                                                                                   │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  ┌─────────────────────────┐  │
│  │   Zero-Leakage Masking       │  │   Minute Detail Scanner      │  │  Universal Error Parser │  │
│  │   (Clean Asterisks: ******)  │  │   (Timelines, Variables, IDs)│  │  (Class, Pattern, Code)│  │
│  └──────────────────────────────┘  └──────────────────────────────┘  └─────────────────────────┘  │
└──────────────────────────────────────────────────────┬────────────────────────────────────────────┘
                                                       │ Context-Enriched & Masked Payload
                                                       ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               3. SEARCHING ENGINE                          │
│                                                                                                   │
│  ┌─────────────────────────────────┐  ┌────────────────────────────────┐  ┌────────────────────┐  │
│  │  Layer 1: Enterprise Runbooks   │  │ Layer 2: Official Platform KB  │  │ Layer 3: Live Web  │  │
│  │  (PDF, Word, Markdown, YAML)    │  │ (Camunda, Pega, K8s, Spring)   │  │ Search Intelligence│  │
│  └────────────────┬────────────────┘  └───────────────┬────────────────┘  └─────────┬──────────┘  │
│                   │                                   │                             │             │
│                   └───────────────────────────┬───────┴─────────────────────────────┘             │
│                                               ▼                                                   │
│                        ┌──────────────────────────────────────────────┐                           │
│                        │       On-Prem NVIDIA DGX AI (Qwen 35B)       │                           │
│                        │      Deterministic SRE Reasoning Engine      │                           │
│                        └──────────────────────┬───────────────────────┘                           │
└───────────────────────────────────────────────┼───────────────────────────────────────────────────┘
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                4. REPORTING ENGINE                             │
│                                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  ❓ WHAT: Precise incident summary, failing component & business impact                      │  │
│  │  🔍 WHY:  Root cause analysis linked to project purpose with cited evidence                │  │
│  │  🛠️ HOW:  Prescriptive resolution steps directly from uploaded SOPs, docs, or web search    │  │
│  │  📚 DOCS: Verified citations to uploaded runbook sections or official documentation         │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                               │                                                   │
│                                               ▼                                                   │
│  ┌──────────────────────┐  ┌───────────────────────┐  ┌───────────────────┐  ┌────────────────┐  │
│  │ Incident Insights Hub│  │ Slack / Teams Alert   │  │ Jira / ServiceNow │  │ Auto-Retry &   │  │
│  │ (Interactive UI)     │  │ Webhook Notification  │  │ Ticket Generation │  │ Self-Healing   │  │
│  └──────────────────────┘  └───────────────────────┘  └───────────────────┘  └────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Universal Multi-Format Runbook Ingestion Engine (PDF, Word)

In enterprise environments, Standard Operating Procedures (SOPs) and runbooks exist in multiple formats:
- **Operations & SRE Teams:** PDF runbooks (`.pdf`).
- **Architects & Developers:** Word documents (`.docx`, `.doc`).


OpenSRE implements an **Omni-Format Document Ingestor** that extracts, vectors, and indexes any format.

### 4.1 Supported Runbook Formats

| Format | Extensions | Ingestion & Extraction Mechanism |
| :--- | :--- | :--- |
| **Adobe PDF** | `.pdf` | Structure-aware text extraction, table parsing, heading hierarchy mapping |
| **Microsoft Word** | `.docx`, `.doc` | Paragraph, numbered action lists, and table extraction |


### 4.2 Runbook Ingestion & Vector Storage Pipeline

```
  Uploaded SOP (PDF / DOCX)
                   │
                   ▼
  ┌─────────────────────────────────┐
  │   Document Parser & Extractor   │ ──▶ Strips boilerplate, extracts headings, tables & code
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │   Intelligent Text Chunking     │ ──▶ Keeps remediation steps & code commands grouped
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │   Embedding Generator (Vector)  │ ──▶ High-density vector embedding generation
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │   Hybrid Runbook Knowledge Base │ ──▶ Vector similarity + Full-text keyword search index
  └─────────────────────────────────┘
```

---

## 5. Deep Log Scanning & Incident Intelligence Pipeline

OpenSRE performs a **forensic, minute-level log scan** to extract operational telemetry without losing contextual fidelity.

### 5.1 Telemetry Extracted During Scanning

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 AUTOMATICALLY EXTRACTED LOG ENTITIES                             │
├──────────────────────────┬───────────────────────────────────────┬───────────────────────────────┤
│ Entity                   │ Example Extracted Value               │ SRE Diagnostic Value          │
├──────────────────────────┼───────────────────────────────────────┼───────────────────────────────┤
│ **Microsecond Timelines**│ `2026-09-07 10:14:06.340`             │ Event causality & sequencing  │
│ **Log Severity Level**   │ `[FATAL]`, `[ERROR]`, `[WARN]`        │ Impact severity scoring       │
│ **Worker / Pod Thread**  │ `[payment-gateway-worker-3]`          │ Concurrency & thread isolation│
│ **Service & Module**     │ `orderFulfillmentProcess`, `auth-svc` │ Blast radius identification   │
│ **Error Classification** │ `PaymentGatewayException`, `504`      │ Root cause categorization     │
│ **Instance / Flow Node** │ `Activity_ProcessPayment`             │ Exact BPMN/Code failure point │
│ **Process Variables**    │ `orderId: 874c310`, `amount: $1450`   │ Business transaction context  │
└──────────────────────────┴───────────────────────────────────────┴───────────────────────────────┘
```

---

## 6. Multi-Layer Hybrid Investigation Engine (RAG + Live Web Search)

When an incident is ingested, OpenSRE executes a 5-layer intelligence pipeline:

```mermaid
graph TD
    A["Project Context + Incident Logs"] --> B["Dual-Tier Sanitization & Masking"]
    B --> C{"Layer 1: Enterprise Runbooks<br/>(PDF, Word, MD, YAML for this Project)"}
    C -- "Match Found" --> G["Synthesize High-Confidence RCA"]
    C -- "Partial / No Match" --> D{"Layer 2: Platform Knowledge Base<br/>(Camunda, Pega, K8s, Spring Official Docs)"}
    D -- "Match Found" --> G
    D -- "Novel / Unknown Error" --> E{"Layer 3: Live Web Search & External Intelligence<br/>(Official Vendor Portals, GitHub Issues, CVEs)"}
    E --> F["Layer 4: Static Topology & Deadlock Analyzer"]
    F --> H["Layer 5: NVIDIA DGX AI Reasoning Engine (Qwen 35B)"]
    H --> G
    G --> I["Incident Insights Hub + Slack + Auto-Remediation"]
```

### 6.1 The 5 Investigation Layers

1. **Layer 1: Enterprise Runbooks & SOPs (Project-Specific)**
   - Searches uploaded PDF, Word, Markdown, and YAML runbooks matching the project and error pattern.
   - Provides internal procedures, team escalation paths, and company-specific recovery scripts.

2. **Layer 2: Official Platform Documentation Bases (Version-Aware)**
   - Built-in rules for major enterprise stacks:
     - **Camunda 8 / 7:** Zeebe broker errors, FEEL syntax collisions, boundary catch event rules, parallel token starvation deadlocks, DMN evaluation failures.
     - **Pega Systems:** PRPC clipboard exceptions, Data Page SLA timeouts, Rule Resolution errors.
     - **Kubernetes / Cloud:** OOMKilled, CrashLoopBackOff, Ingress 502/504, PVC storage exhaustion.
     - **Databases & Messaging:** HikariCP connection pool timeouts, Kafka rebalances, Redis timeouts.

3. **Layer 3: Live Web Search & Global Tech Intelligence**
   - Triggered when encountering unseen stack traces, zero-day library bugs, or proprietary vendor errors.
   - Searches authoritative sources: official vendor portals (`docs.camunda.io`, `docs.pega.com`, `kubernetes.io`), GitHub issues, CVE databases, and StackOverflow verified resolutions.

4. **Layer 4: Static Architecture & Topology Analysis**
   - Analyzes workflow definitions (BPMN 2.0 XML, process trees, Kubernetes service graphs).
   - Detects structural bottlenecks: missing error boundary events, parallel fork deadlocks, token starvation.

5. **Layer 5: NVIDIA DGX On-Prem AI Reasoning Engine**
   - Powered by **Qwen 35B** running on-premise on NVIDIA DGX GPUs.
   - Delivers sub-second SRE synthesis with zero operational data leaving the enterprise boundary.

---

## 7. Standardized RCA Output: The 4-Pillar Incident Report

Every incident processed by OpenSRE generates a structured report:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 OPENSRE 4-PILLAR INCIDENT REPORT                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ❓ 1. WHAT is the error?                                                                        │
│     Clear summary of the failure, affected service, project name, and platform version.         │
│                                                                                                  │
│  🔍 2. WHY did it occur? (Root Cause & Evidence)                                                 │
│     Causal explanation grounded in the project's purpose, with cited log evidence lines.         │
│                                                                                                  │
│  🛠️ 3. HOW to fix it? (Prescriptive Remediation)                                                 │
│     Step-by-step resolution instructions derived from matching runbooks, platform rules, or     │
│     web search recommendations.                                                                  │
│                                                                                                  │
│  📚 4. Official Citations & Documentation References                                             │
│     Verified links to official platform docs, uploaded SOP runbook sections, or web articles.    │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Zero-Leakage Privacy & Sensitive Data Masking Engine

Enterprise compliance (PCI-DSS, GDPR, HIPAA, SOC 2) strictly prohibits exposing raw credentials, customer payment data, or tokens.

OpenSRE enforces clean, non-descriptive asterisk masking across all logs, variables, and evidence:

| Data Category | Target Pattern Detected | Clean Masked Output |
| :--- | :--- | :--- |
| **API Keys & Cloud Secrets** | `AIzaSyD-894729487294829472948294829` | `********` |
| **Database URI Passwords** | `postgres://admin:SuperSecret99@redis:6379` | `postgres://admin:********@redis:6379` |
| **Bearer & JWT Tokens** | `Bearer eyJhbGciOiJIUzI1NiIsInR5c...` | `Bearer ********` |
| **Basic Auth Headers** | `Basic dXNlcm5hbWU6cGFzc3dvcmQ=` | `Basic ********` |
| **Credit & Debit Cards** | `4532-1488-1234-5678` (Luhn Validated) | `****-****-****-5678` |
| **Social Security Numbers** | `123-45-6789` | `***-**-6789` |
| **Indian Aadhaar Numbers** | `9876 5432 1098` | `****-****-1098` |
| **CVVs / Security PINs** | `452` | `***` |
| **Safe Business Variables** | `orderId: 874c310`, `price: 46.48`, `status: PENDING` | **100% Preserved (Untouched)** |

---

## 9. Enterprise Notification & Auto-Remediation Hub

Once an RCA is generated, OpenSRE dispatches actionable notifications and executes self-healing workflows:

### 9.1 Slack & Teams SRE Alert Dispatch
- Sends a rich incident card directly into designated SRE channels with severity, project name, WHAT/WHY summary, step 1 & 2 actions, and deep links.

### 9.2 ITSM & Ticketing Integration
- Opens and updates tickets in **Jira Service Management** or **ServiceNow** with the complete RCA markdown and reproduction logs.

### 9.3 Camunda & Cloud Auto-Remediation
- **Camunda Operate Integration:** SREs can click **"Resolve in Camunda"** directly from OpenSRE to retry failing tasks or update variables.
- **Kubernetes Pod Restarts:** Dispatches automated worker restarts if a worker deadlock is diagnosed.

---

## 10. End-to-End Incident Lifecycle Walkthrough

```
[Step 1: User Intake & Project Profiling]
   Operator provides Project Name ("orderFulfillmentProcess"), Business Purpose ("E-commerce checkout & payment authorization"),
   Target Platform ("Camunda 8.9"), Environment ("Production"), and drops raw incident logs & SOPs (PDF/Word).
        │
        ▼
[Step 2: Mask & Scan]
   Masking engine converts all API keys, DB passwords, and Card numbers to clean '********' / '****-****-****-5678'.
   Scanner extracts timeline, service name, failing task ('Activity_ProcessPayment'), error code ('PAYMENT_FAILED').
        │
        ▼
[Step 3: Multi-Source Investigation]
   • Matches internal PDF/Word/YAML runbooks for 'PAYMENT_FAILED' & 'UNHANDLED_ERROR_EVENT'.
   • Pulls Camunda 8.9 official rules on Error Boundary Events & Token Starvation.
   • Executes web search if a novel upstream gateway exception is observed.
        │
        ▼
[Step 4: DGX AI Synthesis]
   On-prem Qwen 35B synthesizes the 4-Pillar RCA Report in <800ms, linking findings directly to the project's business intent.
        │
        ▼
[Step 5: Action & Resolution]
   • Report renders in Incident Insights Hub with process variables table.
   • Instant Slack alert dispatched to #sre-incidents.
   • SRE clicks "Resolve in Camunda" or applies model fix in Camunda Modeler.
```

---

## 11. Extensibility & Platform Expansion Guide

OpenSRE is designed with a modular plugin architecture to easily support new platforms and runbook formats:

### 11.1 Adding a New Platform Adapter (e.g., Pega / Temporal / Kafka)
1. Create a platform knowledge profile in `sentinel/knowledge/platforms/<platform_name>.py`.
2. Define common error signatures, official documentation mappings, and default SOP guidelines.
3. Register the platform in `sentinel/core/investigator.py` and the Frontend Ingest Lab selector.

### 11.2 Adding a New Runbook Parser (e.g., Notion / Confluence Live API)
1. Add parser utility in `sentinel/knowledge/parsers/`.
2. Extract text and metadata into the unified `RunbookItem` schema.
3. Upload via the Runbook Management API (`POST /runbooks/upload`).

---

## 12. Summary

OpenSRE transforms incident management from stressful, manual firefighting into an **automated, intelligent, and platform-agnostic SRE workflow**. By uniting **deep Project Context & Business Intent**, multi-format enterprise runbooks (PDF, Word, Markdown, YAML), live web intelligence, deep log scanning, and on-premise AI reasoning, OpenSRE ensures that any incident, on any platform, is diagnosed accurately and remediated rapidly.

