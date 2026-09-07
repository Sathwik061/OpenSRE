"""
sentinel/knowledge/runbook_knowledge.py
=======================================
Real-Time SRE Runbook Documentation & Knowledge Engine.
Provides sub-millisecond local retrieval, dynamic multi-factor scoring,
BPMN topology-aware guidance, and structured YAML SOP remediation playbooks.
"""

from __future__ import annotations

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

logger = logging.getLogger("sentinel.knowledge.runbook")

RUNBOOKS_DIR = Path(__file__).resolve().parent / "runbooks"
INDEX_FILE = RUNBOOKS_DIR / "_index.json"

# In-memory hot caches for 0.1ms retrieval
_INDEX_CACHE: List[Dict[str, Any]] = []
_CONTENT_CACHE: Dict[str, str] = {}
_YAML_CACHE: Dict[str, Dict[str, Any]] = {}
_LAST_LOAD_TS: float = 0.0


def _load_index() -> List[Dict[str, Any]]:
    """Loads runbook index into memory, auto-refreshing on file modification."""
    global _INDEX_CACHE, _LAST_LOAD_TS
    if not INDEX_FILE.exists():
        logger.warning(f"Runbook index not found at {INDEX_FILE}")
        return []

    mtime = INDEX_FILE.stat().st_mtime
    if not _INDEX_CACHE or mtime > _LAST_LOAD_TS:
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                _INDEX_CACHE = json.load(f)
            _LAST_LOAD_TS = mtime
            logger.info(f"Loaded {len(_INDEX_CACHE)} SRE Runbooks into memory cache.")
        except Exception as e:
            logger.error(f"Error loading {INDEX_FILE}: {e}")
            return []
    return _INDEX_CACHE


def _get_runbook_content(file_name: str, max_chars: int = 4000) -> str:
    """Reads runbook YAML/markdown from disk and caches in memory."""
    if file_name not in _CONTENT_CACHE:
        path = RUNBOOKS_DIR / file_name
        if not path.exists():
            # Try alternate extension if needed (.yml vs .md)
            alt_path = RUNBOOKS_DIR / (Path(file_name).stem + ".yml")
            if alt_path.exists():
                path = alt_path
            else:
                return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                _CONTENT_CACHE[file_name] = f.read()
        except Exception as e:
            logger.warning(f"Failed to read runbook {file_name}: {e}")
            return ""

    text = _CONTENT_CACHE.get(file_name, "")
    return text[:max_chars] if len(text) > max_chars else text


def _get_runbook_parsed(file_name: str) -> Optional[Dict[str, Any]]:
    """Parses runbook YAML file into a structured dictionary."""
    if file_name not in _YAML_CACHE:
        content = _get_runbook_content(file_name)
        if not content:
            return None
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                _YAML_CACHE[file_name] = data
            else:
                _YAML_CACHE[file_name] = {}
        except Exception as e:
            logger.warning(f"Failed to parse YAML runbook {file_name}: {e}")
            _YAML_CACHE[file_name] = {}

    return _YAML_CACHE.get(file_name)


def score_runbook(
    entry: Dict[str, Any],
    error_type: str = "",
    service: str = "",
    error_message: str = "",
    logs: Optional[List[str]] = None,
    topology_ctx: Optional[Dict[str, Any]] = None,
) -> Tuple[float, List[str]]:
    """
    Computes dynamic multi-factor relevance score for a runbook entry.
    """
    score = 0.0
    reasons = []

    err_type_clean = (error_type or "").upper().strip()
    service_clean = (service or "").lower().strip()
    err_msg_lower = (error_message or "").lower()
    log_text_lower = " ".join(logs or []).lower() if logs else ""

    # 1. Error Type match (+50 exact, +30 partial)
    entry_err_types = [e.upper() for e in entry.get("error_types", [])]
    if err_type_clean and err_type_clean in entry_err_types:
        score += 50.0
        reasons.append(f"Direct error type match '{err_type_clean}'")
    elif any(e in err_type_clean or err_type_clean in e for e in entry_err_types if len(e) > 3):
        score += 30.0
        reasons.append(f"Partial error type match with {entry_err_types}")

    # 2. Service match (+20 exact, +10 wildcard)
    entry_services = [s.lower() for s in entry.get("services", [])]
    if service_clean and service_clean in entry_services:
        score += 20.0
        reasons.append(f"Direct service match '{service_clean}'")
    elif "*" in entry_services:
        score += 10.0
        reasons.append("Applicable across all services (*)")

    # 3. Keyword / Tag matching in error message & logs (+5 per match)
    tags = [t.lower() for t in entry.get("tags", [])]
    matched_tags = []
    for tag in tags:
        if len(tag) > 3:
            if tag in err_msg_lower or tag in log_text_lower:
                matched_tags.append(tag)
                score += 6.0

    if matched_tags:
        reasons.append(f"Matched incident keywords: {', '.join(matched_tags[:3])}")

    # 4. BPMN Topology hazards (+25)
    if topology_ctx:
        if topology_ctx.get("inside_parallel_branch") and entry["id"] == "unhandled-error-event":
            score += 35.0
            reasons.append("Active parallel branch deadlock risk detected")
        if topology_ctx.get("has_error_boundary_event") is False and entry["id"] == "unhandled-error-event":
            score += 25.0
            reasons.append("Missing error boundary event confirmed by topology")

    # 5. Base Priority weighting
    priority = entry.get("priority", "medium").lower()
    if priority == "critical":
        score += 5.0
    elif priority == "high":
        score += 2.0

    return score, reasons


def interpolate_template(text: str, context: Dict[str, Any]) -> str:
    """Dynamically replaces placeholders like {task_name}, {error_code}, etc."""
    if not text or not isinstance(text, str):
        return text

    t_name = context.get("task_name") or "failing task"
    e_id = context.get("element_id") or "Activity_Current"

    replacements = {
        "{task_name}": t_name,
        "{element_id}": e_id,
        "{error_code}": context.get("error_code") or context.get("error_type") or "PROCESS_ERROR",
        "{service}": context.get("service") or "service",
        "{gateway_name}": context.get("gateway_name") or "Gateway",
        "{form_id}": context.get("form_id") or "form-schema",
        "{topic_name}": context.get("topic_name") or "event-topic",
        "{status_code}": str(context.get("status_code") or "500"),
        "{timeout_ms}": str(context.get("timeout_ms") or "30000"),
        "{property_name}": context.get("property_name") or "variable",
        "{redis_host}": context.get("redis_host") or "redis-cluster",
        "{redis_port}": str(context.get("redis_port") or "6379"),
        "{topology_hazard}": context.get("topology_hazard") or "",
    }

    result = text
    for key, val in replacements.items():
        if key in result:
            result = result.replace(key, str(val))

    # Clean up duplicate task naming like Task 'Activity_0luysxt' (Activity_0luysxt)
    if t_name == e_id and t_name != "failing task":
        result = result.replace(f"Task '{t_name}' ({e_id})", f"Task '{e_id}'")
        result = result.replace(f"'{t_name}' ({e_id})", f"'{e_id}'")

    return result


def lookup_sop_guidelines(
    error_type: str,
    service: str = "*",
    error_message: str = "",
    logs: Optional[List[str]] = None,
    bpmn_topology: Optional[Dict[str, Any]] = None,
    element_id: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Returns tailored, authoritative SOP guidelines dynamically populated for this incident.
    """
    catalog = _load_index()
    if not catalog:
        return None

    topology_ctx = (bpmn_topology or {}).get("incident_element_context", {})

    # Extract dynamic variables from error message & logs
    all_text = f"{error_message or ''} {' '.join(logs or [])}"

    # Extract element_id / task name from logs or error message if not explicitly supplied
    if not element_id:
        elem_match = re.search(r"(?:elementId|scope of|task)\s*[:=\s]*([a-zA-Z0-9_\-]+(?:Task|Activity|Service|Gateway)[a-zA-Z0-9_\-]*)", all_text, re.IGNORECASE) or re.search(r"\b(Activity_[a-zA-Z0-9_\-]+)\b", all_text)
        if elem_match:
            element_id = elem_match.group(1)

    # Extract error_code
    err_code_match = re.search(r"(?:errorCode|code)\s*['\":=\s]+([A-Z0-9_\-]+)", all_text, re.IGNORECASE)
    error_code = err_code_match.group(1) if err_code_match else (error_type or "PROCESS_ERROR")
    if error_code.lower() in ("the", "with", "is", "a", "an"):
        error_code = error_type or "PROCESS_ERROR"

    elem_name = topology_ctx.get("incident_element_name") if topology_ctx else ""
    task_name = elem_name or element_id or "failing task"
    elem_id_val = element_id or "Activity_Current"
    
    topology_hazard = ""
    if topology_ctx.get("inside_parallel_branch"):
        topology_hazard = "Failing task is inside a Parallel Fork leading to a downstream Parallel Join deadlock."

    context = {
        "task_name": task_name,
        "element_id": elem_id_val,
        "error_code": error_code,
        "service": service or "service",
        "gateway_name": element_id if "gateway" in (element_id or "").lower() else "Gateway_Decision",
        "form_id": "form-definition",
        "topic_name": "order-events",
        "status_code": "500",
        "timeout_ms": "30000",
        "property_name": "targetProperty",
        "redis_host": "redis-cluster",
        "redis_port": "6379",
        "topology_hazard": topology_hazard,
    }

    scored = []
    for entry in catalog:
        score, reasons = score_runbook(
            entry=entry,
            error_type=error_type,
            service=service,
            error_message=error_message,
            logs=logs,
            topology_ctx=topology_ctx,
        )
        if score > 0:
            scored.append((score, reasons, entry))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_reasons, best_entry = scored[0]

    raw_actions = best_entry.get("recommended_actions", [])
    
    # If YAML has automated_actions, also incorporate their descriptions
    parsed_yaml = _get_runbook_parsed(best_entry.get("file", ""))
    if parsed_yaml and "remediation" in parsed_yaml:
        auto_actions = parsed_yaml["remediation"].get("automated_actions", [])
        if auto_actions and not raw_actions:
            raw_actions = [a.get("description", a.get("action", "")) for a in auto_actions if a.get("description")]

    interpolated_actions = [interpolate_template(a, context) for a in raw_actions]

    root_cause_tmpl = best_entry.get("root_cause_template") or best_entry.get("summary") or ""
    interpolated_root_cause = interpolate_template(root_cause_tmpl, context)

    return {
        "id": best_entry["id"],
        "title": best_entry["title"],
        "error_type": error_type,
        "service": service,
        "summary": best_entry.get("summary", ""),
        "root_cause": interpolated_root_cause,
        "recommended_actions": interpolated_actions,
        "observed_facts": [
            f"Incident error type: {error_type}",
            f"Active service: {service}",
            f"Matched SRE Runbook: {best_entry['title']}",
        ],
        "confidence": "HIGH",
        "reasons": best_reasons,
        "file": best_entry.get("file"),
        "source": "sre_runbook_engine",
        "automation_schema": parsed_yaml.get("remediation") if parsed_yaml else None,
    }


def retrieve_runbook_context(
    error_type: str = "",
    service: str = "",
    error_message: str = "",
    logs: Optional[List[str]] = None,
    bpmn_topology: Optional[Dict[str, Any]] = None,
    top_k: int = 1,
) -> Dict[str, Any]:
    """
    Builds a formatted YAML prompt section for DGX / vLLM from the best matching SRE runbooks.
    """
    catalog = _load_index()
    if not catalog:
        return {"runbooks": [], "prompt_section": "", "sop_guidelines": None}

    topology_ctx = (bpmn_topology or {}).get("incident_element_context", {})

    scored = []
    for entry in catalog:
        score, reasons = score_runbook(
            entry=entry,
            error_type=error_type,
            service=service,
            error_message=error_message,
            logs=logs,
            topology_ctx=topology_ctx,
        )
        if score > 0:
            scored.append((score, reasons, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = scored[:top_k]

    if not selected:
        return {"runbooks": [], "prompt_section": "", "sop_guidelines": None}

    prompt_lines = [
        "\n============================================================",
        "📖 SRE STANDARD OPERATING PROCEDURE (SOP) RUNBOOK INSTRUCTIONS (.YML)",
        "============================================================",
    ]

    runbooks_out = []
    for score, reasons, entry in selected:
        content = _get_runbook_content(entry["file"])
        parsed = _get_runbook_parsed(entry["file"])
        runbooks_out.append({
            "id": entry["id"],
            "title": entry["title"],
            "score": score,
            "reasons": reasons,
            "summary": entry.get("summary", ""),
            "content": content,
            "yaml_data": parsed,
        })
        prompt_lines.append(f"### 📋 {entry['title']} ({entry['file']})")
        prompt_lines.append(f"Summary: {entry.get('summary', '')}")
        prompt_lines.append(f"Runbook YAML Content:\n```yaml\n{content}\n```")
        prompt_lines.append("\n" + "-" * 50 + "\n")

    sop_guidelines = lookup_sop_guidelines(
        error_type=error_type,
        service=service,
        error_message=error_message,
        logs=logs,
        bpmn_topology=bpmn_topology,
    )

    return {
        "runbooks": runbooks_out,
        "prompt_section": "\n".join(prompt_lines),
        "sop_guidelines": sop_guidelines,
    }


def list_all_runbooks() -> List[Dict[str, Any]]:
    """Returns all available runbook summaries from the index."""
    return _load_index()


def get_runbook(runbook_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single runbook with its full YAML content and parsed data."""
    catalog = _load_index()
    for entry in catalog:
        if entry["id"] == runbook_id:
            content = _get_runbook_content(entry["file"])
            parsed = _get_runbook_parsed(entry["file"])
            return {**entry, "content": content, "yaml_data": parsed}
    return None


def save_runbook(runbook_data: Dict[str, Any]) -> bool:
    """Saves or updates a runbook in the local YAML runbook catalog."""
    global _INDEX_CACHE, _CONTENT_CACHE, _YAML_CACHE
    catalog = _load_index()

    rb_id = runbook_data.get("id") or re.sub(r"[^a-z0-9\-]", "-", (runbook_data.get("title") or "runbook").lower())
    file_name = f"{rb_id}.yml"

    # Save YAML content if provided
    path = RUNBOOKS_DIR / file_name
    try:
        if "content" in runbook_data and isinstance(runbook_data["content"], str):
            content_str = runbook_data["content"]
            with open(path, "w", encoding="utf-8") as f:
                f.write(content_str)
            _CONTENT_CACHE[file_name] = content_str
            try:
                _YAML_CACHE[file_name] = yaml.safe_load(content_str)
            except Exception:
                pass
        elif "yaml_data" in runbook_data and isinstance(runbook_data["yaml_data"], dict):
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(runbook_data["yaml_data"], f, sort_keys=False)
            _YAML_CACHE[file_name] = runbook_data["yaml_data"]
            with open(path, "r", encoding="utf-8") as f:
                _CONTENT_CACHE[file_name] = f.read()
    except Exception as e:
        logger.error(f"Failed to write runbook file {path}: {e}")
        return False

    # Update index
    updated = False
    for i, entry in enumerate(catalog):
        if entry["id"] == rb_id:
            catalog[i] = {
                **entry,
                "file": file_name,
                "title": runbook_data.get("title", entry.get("title")),
                "error_types": runbook_data.get("error_types", entry.get("error_types")),
                "services": runbook_data.get("services", entry.get("services")),
                "tags": runbook_data.get("tags", entry.get("tags")),
                "summary": runbook_data.get("summary", entry.get("summary")),
                "recommended_actions": runbook_data.get("recommended_actions", entry.get("recommended_actions")),
            }
            updated = True
            break

    if not updated:
        catalog.append({
            "id": rb_id,
            "file": file_name,
            "title": runbook_data.get("title", rb_id.replace("-", " ").title()),
            "error_types": [runbook_data.get("error_type")] if "error_type" in runbook_data else runbook_data.get("error_types", []),
            "services": [runbook_data.get("service", "*")] if "service" in runbook_data else runbook_data.get("services", ["*"]),
            "tags": runbook_data.get("tags", []),
            "priority": runbook_data.get("priority", "high"),
            "summary": runbook_data.get("summary", ""),
            "recommended_actions": runbook_data.get("recommended_actions", []),
        })

    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)
        _INDEX_CACHE = catalog
        logger.info(f"Saved runbook [{rb_id}] to local YAML documentation catalog.")
        return True
    except Exception as e:
        logger.error(f"Failed to update {INDEX_FILE}: {e}")
        return False
