#!/usr/bin/env python3
"""
sentinel/scripts/fetch_camunda_docs.py
======================================
Downloads official Camunda 8 documentation markdown files directly from GitHub
(https://github.com/camunda/camunda-docs) and compiles a search index for
local sub-millisecond RAG retrieval during SRE Root Cause Analysis.

Usage:
  python sentinel/scripts/fetch_camunda_docs.py
"""

import os
import re
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fetch_docs")

BASE_RAW_URL = "https://raw.githubusercontent.com/camunda/camunda-docs/main"

# Destination directory
DOCS_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "camunda_docs"
INDEX_FILE = DOCS_DIR / "_index.json"

# Master catalog of target docs with mapped error types and BPMN element tags
DOC_CATALOG = [
    {
        "id": "error-events",
        "file": "error-events.md",
        "title": "Error Events",
        "github_path": "docs/components/modeler/bpmn/error-events/error-events.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/error-events/",
        "error_types": ["UNHANDLED_ERROR_EVENT", "ERROR_EVENT", "ERROR_CODE_UNHANDLED"],
        "element_types": ["boundaryEvent", "endEvent", "subProcess", "errorEventDefinition"],
        "tags": [
            "UNHANDLED_ERROR_EVENT", "error boundary", "error catch", "error throw", "errorCode",
            "error event subprocess", "unhandled error", "error code", "boundaryEvent", "catch error",
            "scope escalation", "error propagation"
        ],
        "priority": "critical",
        "summary": "Explains how Camunda 8 handles BPMN error throw/catch events, error boundaries, and unhandled error event incidents."
    },
    {
        "id": "exclusive-gateways",
        "file": "exclusive-gateways.md",
        "title": "Exclusive Gateways (XOR)",
        "github_path": "docs/components/modeler/bpmn/exclusive-gateways/exclusive-gateways.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/exclusive-gateways/",
        "error_types": ["CONDITION_ERROR", "EXTRACT_VALUE_ERROR", "NO_MATCHING_CONDITION"],
        "element_types": ["exclusiveGateway", "sequenceFlow"],
        "tags": [
            "CONDITION_ERROR", "exclusiveGateway", "XOR", "default flow", "condition expression",
            "FEEL expression", "outgoing sequence flow", "no condition evaluated to true",
            "boolean condition", "gateway routing"
        ],
        "priority": "critical",
        "summary": "Explains exclusive gateway conditional evaluation, default sequence flows, and CONDITION_ERROR when no branch matches."
    },
    {
        "id": "parallel-gateways",
        "file": "parallel-gateways.md",
        "title": "Parallel Gateways (Fork & Join)",
        "github_path": "docs/components/modeler/bpmn/parallel-gateways/parallel-gateways.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/parallel-gateways/",
        "error_types": ["PARALLEL_DEADLOCK", "TOKEN_STARVATION", "DEADLOCK"],
        "element_types": ["parallelGateway"],
        "tags": [
            "parallelGateway", "fork", "join", "deadlock", "token starvation", "concurrent branches",
            "synchronization", "incoming tokens", "bypassed join", "token waiting", "parallel join"
        ],
        "priority": "critical",
        "summary": "Explains parallel fork and join token mechanics, synchronization rules, and deadlock risks when one branch is bypassed."
    },
    {
        "id": "inclusive-gateways",
        "file": "inclusive-gateways.md",
        "title": "Inclusive Gateways (OR)",
        "github_path": "docs/components/modeler/bpmn/inclusive-gateways/inclusive-gateways.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/inclusive-gateways/",
        "error_types": ["CONDITION_ERROR", "INCLUSIVE_GATEWAY_ERROR"],
        "element_types": ["inclusiveGateway"],
        "tags": [
            "inclusiveGateway", "OR", "default flow", "condition evaluation", "split", "join", "synchronization"
        ],
        "priority": "high",
        "summary": "Rules for inclusive gateways (OR splits/joins) evaluating multiple concurrent conditional outgoing sequence flows."
    },
    {
        "id": "event-based-gateways",
        "file": "event-based-gateways.md",
        "title": "Event-Based Gateways",
        "github_path": "docs/components/modeler/bpmn/event-based-gateways/event-based-gateways.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/event-based-gateways/",
        "error_types": ["EVENT_BASED_GATEWAY_ERROR", "RACE_CONDITION"],
        "element_types": ["eventBasedGateway"],
        "tags": [
            "eventBasedGateway", "race condition", "message event", "timer event", "signal event", "branch selection"
        ],
        "priority": "high",
        "summary": "Rules governing event-based gateways waiting for competing intermediate catch events or receive tasks."
    },
    {
        "id": "service-tasks",
        "file": "service-tasks.md",
        "title": "Service Tasks & Job Workers",
        "github_path": "docs/components/modeler/bpmn/service-tasks/service-tasks.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/service-tasks/",
        "error_types": ["JOB_NO_RETRIES", "JOB_WORKER_ERROR", "CONNECTOR_ERROR", "TASK_TIMEOUT"],
        "element_types": ["serviceTask"],
        "tags": [
            "serviceTask", "jobType", "job worker", "retries", "headers", "zeebe:taskDefinition",
            "zeebe:taskHeaders", "worker timeout", "backoff", "incident on zero retries"
        ],
        "priority": "critical",
        "summary": "Explains service task job definitions, job polling by workers, retry counters, and incident generation on zero retries."
    },
    {
        "id": "user-tasks",
        "file": "user-tasks.md",
        "title": "User Tasks & Form Binding",
        "github_path": "docs/components/modeler/bpmn/user-tasks/user-tasks.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/user-tasks/",
        "error_types": ["USER_TASK_ERROR", "FORM_NOT_FOUND", "ASSIGNMENT_ERROR"],
        "element_types": ["userTask"],
        "tags": [
            "userTask", "formId", "formKey", "formBinding", "assignee", "candidateGroups",
            "candidateUsers", "user task completion", "FORM_NOT_FOUND", "camunda form"
        ],
        "priority": "critical",
        "summary": "Explains user task lifecycle, form binding (formId vs formKey), assignee expressions, and FORM_NOT_FOUND errors."
    },
    {
        "id": "call-activities",
        "file": "call-activities.md",
        "title": "Call Activities (Sub-Processes)",
        "github_path": "docs/components/modeler/bpmn/call-activities/call-activities.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/call-activities/",
        "error_types": ["CALLED_ELEMENT_ERROR", "CALLED_PROCESS_NOT_FOUND", "VARIABLE_MAPPING_ERROR"],
        "element_types": ["callActivity"],
        "tags": [
            "callActivity", "calledElement", "processId", "in mapping", "out mapping",
            "sub-process instance", "CALLED_ELEMENT_ERROR", "process definition key"
        ],
        "priority": "critical",
        "summary": "Explains call activity invocation, calledElement process definitions, variable input/output propagation, and missing process errors."
    },
    {
        "id": "timer-events",
        "file": "timer-events.md",
        "title": "Timer Events",
        "github_path": "docs/components/modeler/bpmn/timer-events/timer-events.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/timer-events/",
        "error_types": ["TIMER_ERROR", "INVALID_DATE_TIME", "TIMER_EXPRESSION_ERROR"],
        "element_types": ["timerEventDefinition", "intermediateCatchEvent", "boundaryEvent", "startEvent"],
        "tags": [
            "timer", "timeDuration", "timeDate", "timeCycle", "ISO 8601", "timer boundary event",
            "timer catch event", "timer expression", "PT1H"
        ],
        "priority": "high",
        "summary": "Timer event specifications (date, duration, cycle in ISO 8601 or FEEL), interrupting and non-interrupting boundary timers."
    },
    {
        "id": "message-events",
        "file": "message-events.md",
        "title": "Message Events & Correlation",
        "github_path": "docs/components/modeler/bpmn/message-events/message-events.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/message-events/",
        "error_types": ["MESSAGE_CORRELATION_ERROR", "MESSAGE_NAME_MISSING", "CORRELATION_KEY_ERROR"],
        "element_types": ["messageEventDefinition", "intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent", "receiveTask"],
        "tags": [
            "message", "correlationKey", "message correlation", "message name", "ttl",
            "time-to-live", "subscription", "publish message", "message buffer"
        ],
        "priority": "critical",
        "summary": "Message subscriptions, correlation keys, TTL buffering, and correlation failure troubleshooting."
    },
    {
        "id": "signal-events",
        "file": "signal-events.md",
        "title": "Signal Events",
        "github_path": "docs/components/modeler/bpmn/signal-events/signal-events.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/signal-events/",
        "error_types": ["SIGNAL_ERROR", "SIGNAL_BROADCAST_ERROR"],
        "element_types": ["signalEventDefinition", "intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent"],
        "tags": [
            "signal", "broadcast", "signal catch", "signal throw", "signal name", "global broadcast"
        ],
        "priority": "medium",
        "summary": "Signal event broadcast semantics across all active process instances."
    },
    {
        "id": "terminate-events",
        "file": "terminate-events.md",
        "title": "Terminate End Events",
        "github_path": "docs/components/modeler/bpmn/terminate-events/terminate-events.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/terminate-events/",
        "error_types": ["TERMINATE_END_EVENT", "SCOPE_TERMINATION"],
        "element_types": ["terminateEventDefinition", "endEvent"],
        "tags": [
            "terminate end event", "scope termination", "cancel tokens", "process termination",
            "parallel termination", "deadlock resolution"
        ],
        "priority": "high",
        "summary": "Behavior of terminate end events terminating the current scope and consuming all active concurrent tokens."
    },
    {
        "id": "compensation-events",
        "file": "compensation-events.md",
        "title": "Compensation Events",
        "github_path": "docs/components/modeler/bpmn/compensation-events/compensation-events.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/compensation-events/",
        "error_types": ["COMPENSATION_ERROR"],
        "element_types": ["compensateEventDefinition", "boundaryEvent", "intermediateThrowEvent"],
        "tags": [
            "compensation", "undo", "compensation boundary event", "compensation handler", "activityRef"
        ],
        "priority": "medium",
        "summary": "Compensation handling and undo mechanisms for completed activities."
    },
    {
        "id": "multi-instance",
        "file": "multi-instance.md",
        "title": "Multi-Instance Activities",
        "github_path": "docs/components/modeler/bpmn/multi-instance/multi-instance.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/multi-instance/",
        "error_types": ["MULTI_INSTANCE_ERROR", "INPUT_COLLECTION_ERROR", "OUTPUT_COLLECTION_ERROR"],
        "element_types": ["multiInstanceLoopCharacteristics"],
        "tags": [
            "multi-instance", "inputCollection", "inputElement", "outputCollection", "outputElement",
            "completionCondition", "parallel multi-instance", "sequential multi-instance", "loopCardinality"
        ],
        "priority": "high",
        "summary": "Parallel and sequential multi-instance loop execution, collection variable binding, and completion conditions."
    },
    {
        "id": "embedded-subprocesses",
        "file": "embedded-subprocesses.md",
        "title": "Embedded Subprocesses",
        "github_path": "docs/components/modeler/bpmn/embedded-subprocesses/embedded-subprocesses.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/embedded-subprocesses/",
        "error_types": ["SUBPROCESS_ERROR", "VARIABLE_SCOPE_ERROR"],
        "element_types": ["subProcess"],
        "tags": [
            "subProcess", "embedded subprocess", "variable scope", "start event", "end event",
            "boundary events on subprocess"
        ],
        "priority": "high",
        "summary": "Embedded subprocess scoping rules, local variables, and boundary catch event handling on subprocess containers."
    },
    {
        "id": "event-subprocesses",
        "file": "event-subprocesses.md",
        "title": "Event Subprocesses",
        "github_path": "docs/components/modeler/bpmn/event-subprocesses/event-subprocesses.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/event-subprocesses/",
        "error_types": ["EVENT_SUBPROCESS_ERROR", "UNHANDLED_ERROR_EVENT"],
        "element_types": ["subProcess"],
        "tags": [
            "event subprocess", "triggeredByEvent", "error event subprocess", "message event subprocess",
            "timer event subprocess", "interrupting vs non-interrupting"
        ],
        "priority": "high",
        "summary": "Event subprocess triggers, interrupting and non-interrupting event start behavior, and error catch scoping."
    },
    {
        "id": "data-flow",
        "file": "data-flow.md",
        "title": "Data Flow & Variable Mapping",
        "github_path": "docs/components/modeler/bpmn/data-flow.md",
        "doc_url": "https://docs.camunda.io/docs/components/modeler/bpmn/data-flow/",
        "error_types": ["VARIABLE_MAPPING_ERROR", "IO_MAPPING_ERROR", "EXTRACT_VALUE_ERROR"],
        "element_types": ["ioMapping", "inputOutput", "zeebe:ioMapping"],
        "tags": [
            "data flow", "ioMapping", "input mapping", "output mapping", "variable scope",
            "FEEL expression", "target variable", "source expression"
        ],
        "priority": "critical",
        "summary": "Zeebe variable scoping, input mappings, output mappings, and FEEL data transformations."
    },
    {
        "id": "expressions",
        "file": "expressions.md",
        "title": "FEEL Expressions & Evaluation",
        "github_path": "docs/components/concepts/expressions.md",
        "doc_url": "https://docs.camunda.io/docs/components/concepts/expressions/",
        "error_types": ["FEEL_EVALUATION_ERROR", "CONDITION_ERROR", "EXTRACT_VALUE_ERROR"],
        "element_types": ["conditionExpression"],
        "tags": [
            "FEEL", "expressions", "null check", "list operators", "string functions",
            "boolean logic", "feel evaluation error", "expression syntax", "unary test"
        ],
        "priority": "critical",
        "summary": "Friendly Enterprise Exception Language (FEEL) expression syntax, null-handling, type conversions, and evaluation rules."
    },
    {
        "id": "variables",
        "file": "variables.md",
        "title": "Variables & Scoping",
        "github_path": "docs/components/concepts/variables.md",
        "doc_url": "https://docs.camunda.io/docs/components/concepts/variables/",
        "error_types": ["VARIABLE_NOT_FOUND", "VARIABLE_SCOPE_ERROR", "TYPE_MISMATCH"],
        "element_types": ["process", "subProcess", "task"],
        "tags": [
            "variables", "variable scope", "local variable", "root scope", "JSON variables",
            "variable propagation", "variable shadowing"
        ],
        "priority": "critical",
        "summary": "Camunda 8 variable scopes, payload sizes, shadowing rules, and instance variable visibility."
    },
    {
        "id": "incidents",
        "file": "incidents.md",
        "title": "Incidents & Error Lifecycle",
        "github_path": "docs/components/concepts/incidents.md",
        "doc_url": "https://docs.camunda.io/docs/components/concepts/incidents/",
        "error_types": ["INCIDENT", "UNHANDLED_ERROR_EVENT", "CONDITION_ERROR", "EXTRACT_VALUE_ERROR", "CALLED_ELEMENT_ERROR", "JOB_NO_RETRIES"],
        "element_types": ["processInstance"],
        "tags": [
            "incidents", "incident types", "resolve incident", "retry", "incident lifecycle",
            "Zeebe incident", "Operate incident", "incident resolution"
        ],
        "priority": "critical",
        "summary": "Incident creation triggers, incident types, automatic retries vs manual resolution, and Operate incident handling."
    },
    {
        "id": "process-instance-modification",
        "file": "process-instance-modification.md",
        "title": "Process Instance Modification",
        "github_path": "docs/components/concepts/process-instance-modification.md",
        "doc_url": "https://docs.camunda.io/docs/components/concepts/process-instance-modification/",
        "error_types": ["MODIFICATION_ERROR", "STUCK_INSTANCE", "REPAIR_INSTANCE"],
        "element_types": ["processInstance"],
        "tags": [
            "process instance modification", "activate token", "cancel token", "move token",
            "instance repair", "Operate modification", "remediation"
        ],
        "priority": "high",
        "summary": "How to repair stuck or failing process instances by activating or cancelling tokens at specific flow nodes via Operate / Zeebe API."
    }
]


def clean_markdown_content(raw_text: str) -> str:
    """
    Strips YAML frontmatter, removes doc HTML comments, collapses excessive newlines,
    and cleans image badges while keeping code snippets and text intact.
    """
    text = raw_text.strip()
    
    # Strip YAML frontmatter (--- ... ---)
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2].strip()

    # Remove Docusaurus / Markdown import statements (e.g. import ... from '...')
    text = re.sub(r"^import\s+.*?from\s+['\"].*?['\"];?\s*$", "", text, flags=re.MULTILINE)
    
    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    
    # Remove image tags like ![image](...)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    
    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip()


def fetch_and_save_docs() -> None:
    """Downloads all catalog docs from GitHub and writes them to DOCS_DIR."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Target docs directory: {DOCS_DIR}")

    index_entries = []
    success_count = 0
    total_words = 0

    headers = {
        "User-Agent": "OpenSRE-Camunda-Knowledge-Ingester/1.0"
    }

    for item in DOC_CATALOG:
        file_name = item["file"]
        github_path = item["github_path"]
        raw_url = f"{BASE_RAW_URL}/{github_path}"
        dest_file = DOCS_DIR / file_name

        logger.info(f"Fetching: {item['title']} -> {raw_url}")
        content = ""
        try:
            req = urllib.request.Request(raw_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_bytes = resp.read()
                raw_text = raw_bytes.decode("utf-8", errors="replace")
                content = clean_markdown_content(raw_text)
                dest_file.write_text(content, encoding="utf-8")
                words = len(content.split())
                total_words += words
                success_count += 1
                logger.info(f"  ✓ Saved {file_name} ({words} words)")
        except urllib.error.HTTPError as http_err:
            logger.warning(f"  ✗ HTTP {http_err.code} for {raw_url}")
            # If a specific doc path fails, fallback to creating a high-quality summary markdown
            content = f"# {item['title']}\n\n{item['summary']}\n\nTags: {', '.join(item['tags'])}"
            dest_file.write_text(content, encoding="utf-8")
            logger.info(f"  ⚠ Wrote catalog fallback for {file_name}")
        except Exception as err:
            logger.warning(f"  ✗ Error downloading {raw_url}: {err}")
            content = f"# {item['title']}\n\n{item['summary']}\n\nTags: {', '.join(item['tags'])}"
            dest_file.write_text(content, encoding="utf-8")

        # Prepare index record
        entry = {
            "id": item["id"],
            "file": item["file"],
            "title": item["title"],
            "doc_url": item["doc_url"],
            "github_url": raw_url,
            "error_types": item["error_types"],
            "element_types": item["element_types"],
            "tags": item["tags"],
            "priority": item["priority"],
            "summary": item["summary"],
            "last_fetched": datetime.now(timezone.utc).isoformat(),
        }
        index_entries.append(entry)

    # Save _index.json
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_entries, f, indent=2)

    logger.info("============================================================")
    logger.info(f"Successfully processed {len(index_entries)} documentation entries.")
    logger.info(f"Direct downloads: {success_count}/{len(DOC_CATALOG)} | Total words: ~{total_words:,}")
    logger.info(f"Index written to: {INDEX_FILE}")
    logger.info("============================================================")


if __name__ == "__main__":
    fetch_and_save_docs()
