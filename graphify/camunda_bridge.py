"""
camunda_bridge.py — Real-Time Camunda 8 → SRE Agent Bridge
===========================================================
Polls the Camunda 8 Operate REST API for ANY live incident across
ALL running BPMN processes — no BPMN file required, no hardcoding.

When a real incident appears in Operate:
  1. Fetches: process name, instance ID, element, error message, variables
  2. Sends to Sentinel → DGX Qwen 35B (via your SSH tunnel at localhost:8000)
  3. Prints structured RCA: WHAT / WHY / HOW TO FIX

Architecture:
  Camunda Operate :8081  →  camunda_bridge.py  →  DGX vLLM :8000
       (REST API poll)            (this file)       (Qwen 35B GPU)

Usage:
    python camunda_bridge.py
    python camunda_bridge.py --interval 5   # poll every 5 seconds
    python camunda_bridge.py --once         # run once and exit
"""
import sys
import os
os.environ["PYTHONUNBUFFERED"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import argparse
import json
import logging
import time
import urllib.request
import urllib.error
import http.cookiejar
from datetime import datetime, timezone
from typing import Optional

# ── Configuration — all overridable via environment variables ─────────────────
OPERATE_URL  = os.getenv("OPERATE_URL",  "http://localhost:8080")   # Camunda 8.9 Unified (Operate + Zeebe)
OPERATE_USER = os.getenv("OPERATE_USER", "demo")
OPERATE_PASS = os.getenv("OPERATE_PASS", "demo")
ZEEBE_REST   = os.getenv("ZEEBE_REST",  "http://localhost:8080")    # Zeebe REST
DGX_URL      = os.getenv("DGX_URL",     "http://localhost:8000/v1") # DGX vLLM (SSH tunnel)
DGX_MODEL    = os.getenv("DGX_MODEL",   "nvidia/Qwen3.6-35B-A3B-NVFP4")
POLL_INTERVAL= int(os.getenv("POLL_INTERVAL", "10"))               # seconds

# ── Supabase Runbook & Instance Store ──────────────────────────────────────────
# Stores instance-specific RCAs so repeated executions of the SAME instance
# always return the exact same result, while DIFFERENT instances get fresh analysis.
import sys as _sys
_sentinel_dir = os.path.join(os.path.dirname(__file__), "sentinel")
if _sentinel_dir not in _sys.path:
    _sys.path.insert(0, _sentinel_dir)
try:
    from supabase_runbook import (
        lookup_instance_rca,
        save_instance_rca,
        lookup_sop_guidelines,
        lookup_runbook,
        save_runbook,
        health_check as sb_health,
    )
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False
    def lookup_instance_rca(*a, **kw): return None  # type: ignore
    def save_instance_rca(*a, **kw): return None    # type: ignore
    def lookup_sop_guidelines(*a, **kw): return None  # type: ignore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("camunda.bridge")

# ── SRE system prompt — BPMN Topology-Aware RCA ──────────────────────────────
_SYSTEM_PROMPT = """\
You are a senior SRE engineer and BPMN 2.0 specialist performing Root Cause Analysis on a Camunda 8 BPMN incident.

You have access to:
  1. The live incident error (type, message, element, variables)
  2. The BPMN process flow TOPOLOGY (gateways, branches, boundary events, sequence flows)

Rules:
- Base EVERY claim on the supplied evidence only.
- Never invent variable values, process names, or infrastructure facts not in the data.
- If cause is unclear, say UNKNOWN.
- Provide concrete, actionable fix steps.

BPMN Topology Analysis Rules (CRITICAL — always check if topology is provided):
  A. PARALLEL GATEWAY DEADLOCK: If the failing element is inside a Parallel Fork (+) branch,
     check if a Parallel Join (+) gateway exists downstream. If YES, and the error path bypasses
     the normal token flow into that join, the join will wait forever (Token Starvation).
     You MUST warn about this deadlock and recommend Terminate End Event or sequential flow.
  B. EXCLUSIVE GATEWAY (X): If failing at a gateway with conditions, check if a default flow
     is configured. If not, CONDITION_ERROR means no condition evaluated to true.
  C. ERROR BOUNDARY EVENTS: If error type is UNHANDLED_ERROR_EVENT, check the topology for
     any Error Boundary Catch Events on the failing task. If none exist, that is the root cause.
  D. MESSAGE/TIMER BOUNDARY: Check if hanging tasks have Boundary Events they depend on.
  E. SUB-PROCESS SCOPE: If the failing element is inside a sub-process, errors thrown inside
     may not propagate to the parent scope — check boundary events on the sub-process container.

Return ONLY valid JSON (no markdown fences):
{
  "summary": "one-line summary",
  "root_cause": "precise root cause from evidence and topology",
  "confidence": "HIGH"|"MEDIUM"|"LOW",
  "topology_warnings": ["e.g. PARALLEL_DEADLOCK: Parallel Join X waits for token from branch Y which is bypassed by error flow"],
  "observed_facts": ["fact from data"],
  "evidence": ["exact error message or log line cited from evidence"],
  "recommended_actions": ["concrete step 1", "step 2"]
}"""


# ── Operate Session (cookie-based auth) ──────────────────────────────────────
# Operate uses POST /api/login → returns Set-Cookie: OPERATE-SESSION
# Subsequent calls must carry that session cookie.

class _OperateSession:
    """Manages a persistent Camunda Operate login session."""

    def __init__(self):
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener     = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar)
        )
        self._csrf_token: str = ""
        self._logged_in: bool = False

    def login(self) -> bool:
        """Authenticate with Camunda Operate (supports 8.9 /login and 8.6 /api/login)."""
        # Try Camunda 8.9 form login first
        try:
            import urllib.parse
            data = urllib.parse.urlencode({"username": OPERATE_USER, "password": OPERATE_PASS}).encode()
            req = urllib.request.Request(f"{OPERATE_URL}/login", data=data, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            with self._opener.open(req, timeout=5) as r:
                csrf = r.getheader("X-CSRF-TOKEN", "")
                if csrf:
                    self._csrf_token = csrf
                self._logged_in = r.status in (200, 204)
                if self._logged_in:
                    return True
        except Exception:
            pass

        # Fallback to Camunda 8.6 /api/login
        url = f"{OPERATE_URL}/api/login?username={OPERATE_USER}&password={OPERATE_PASS}"
        try:
            req = urllib.request.Request(url, data=b"", method="POST")
            with self._opener.open(req, timeout=5) as r:
                csrf = r.getheader("X-CSRF-TOKEN", "")
                if csrf:
                    self._csrf_token = csrf
                self._logged_in = r.status in (200, 204)
                return self._logged_in
        except Exception as e:
            # In local Camunda 8.9 without auth, v2 endpoints might work directly
            self._logged_in = True
            return True

    def get(self, url: str, timeout: int = 8) -> Optional[dict]:
        """Authenticated GET via session cookie returning parsed JSON."""
        if not self._logged_in:
            self.login()
        try:
            req = urllib.request.Request(url)
            if self._csrf_token:
                req.add_header("X-CSRF-TOKEN", self._csrf_token)
            with self._opener.open(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                self._logged_in = False
                if self.login():
                    return self.get(url, timeout)
            log.debug(f"GET {url} → HTTP {e.code}")
            return None
        except Exception as e:
            log.debug(f"GET {url} failed: {e}")
            return None

    def get_raw(self, url: str, timeout: int = 8) -> Optional[str]:
        """Authenticated GET returning raw text (handles XML, plaintext, or JSON strings)."""
        if not self._logged_in:
            self.login()
        try:
            req = urllib.request.Request(url)
            if self._csrf_token:
                req.add_header("X-CSRF-TOKEN", self._csrf_token)
            with self._opener.open(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                self._logged_in = False
                if self.login():
                    return self.get_raw(url, timeout)
            log.debug(f"GET_RAW {url} → HTTP {e.code}")
            return None
        except Exception as e:
            log.debug(f"GET_RAW {url} failed: {e}")
            return None

    def post(self, url: str, body: dict, timeout: int = 8) -> Optional[dict]:
        """Authenticated POST via session cookie."""
        if not self._logged_in:
            self.login()
        try:
            data = json.dumps(body).encode()
            req  = urllib.request.Request(url, data=data)
            req.add_header("Content-Type", "application/json")
            if self._csrf_token:
                req.add_header("X-CSRF-TOKEN", self._csrf_token)
            with self._opener.open(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                self._logged_in = False
                if self.login():
                    return self.post(url, body, timeout)
            log.debug(f"POST {url} → HTTP {e.code}: {e.read().decode()[:200]}")
            return None
        except Exception as e:
            log.debug(f"POST {url} failed: {e}")
            return None


# Module-level session singleton
_session = _OperateSession()


# ── Camunda Operate API ───────────────────────────────────────────────────────

def check_operate_alive() -> bool:
    """Return True if Camunda Operate is reachable and healthy."""
    # Test v2 incidents endpoint or login
    res = _session.post(f"{OPERATE_URL}/v2/incidents/search", {"page": {"limit": 1}})
    if res is not None:
        return True
    return _session.login()


def fetch_live_incidents(size: int = 50) -> list[dict]:
    """
    Query Operate / Zeebe for all currently ACTIVE incidents (state=ACTIVE).
    Supports Camunda 8.9 (/v2/incidents/search) and 8.6 (/v1/incidents/search).
    """
    # 1. Try Camunda 8.9 unified v2 API
    v2_body = {
        "filter": {"state": "ACTIVE"},
        "page": {"limit": size},
    }
    result = _session.post(f"{OPERATE_URL}/v2/incidents/search", v2_body)
    if result and "items" in result:
        # Standardize key names for 8.9 -> bridge schema
        items = []
        for it in result.get("items", []):
            item = dict(it)
            if "incidentKey" in item and "key" not in item:
                item["key"] = item["incidentKey"]
            if "processDefinitionId" in item and "processDefinitionKey" not in item:
                item["processDefinitionKey"] = item.get("processDefinitionKey")
            items.append(item)
        return items

    # 2. Fallback to Camunda 8.6 v1 API
    v1_body = {
        "filter": {"state": "ACTIVE"},
        "size": size,
        "sort": [{"field": "creationTime", "order": "DESC"}],
    }
    result = _session.post(f"{OPERATE_URL}/v1/incidents/search", v1_body)
    if result:
        return result.get("items", [])
    return []


def fetch_process_instance(instance_key: str) -> dict:
    """Fetch a single process instance by key for context."""
    res = _session.get(f"{OPERATE_URL}/v2/process-instances/{instance_key}")
    if res:
        return res
    return _session.get(f"{OPERATE_URL}/v1/process-instances/{instance_key}") or {}


def fetch_instance_variables(instance_key: str) -> dict:
    """Fetch all variables of a process instance (for RCA context). Includes retry for exporter lag."""
    body_v2 = {
        "filter": {"processInstanceKey": str(instance_key)},
        "page": {"limit": 100},
    }
    result = _session.post(f"{OPERATE_URL}/v2/variables/search", body_v2)
    if not result or not result.get("items"):
        # Brief retry to handle Operate Elasticsearch exporter indexing lag
        time.sleep(0.5)
        result = _session.post(f"{OPERATE_URL}/v2/variables/search", body_v2)

    if not result or "items" not in result:
        # Fallback to v1 variables search
        body_v1 = {
            "filter": {"processInstanceKey": int(instance_key) if str(instance_key).isdigit() else instance_key},
            "size": 100,
        }
        result = _session.post(f"{OPERATE_URL}/v1/variables/search", body_v1)
    
    if not result:
        return {}
    variables = {}
    for var in result.get("items", []):
        name = var.get("name", "")
        val  = var.get("value", "")
        try:
            variables[name] = json.loads(val)
        except (json.JSONDecodeError, TypeError):
            variables[name] = val
    return variables


def fetch_flow_node_name(instance_key: str, flow_node_id: str) -> str:
    """Try to resolve the human-readable flow node name from Operate."""
    # Try v2 element instances search
    body_v2 = {
        "filter": {
            "processInstanceKey": str(instance_key),
            "elementId": flow_node_id,
        },
        "page": {"limit": 1},
    }
    result = _session.post(f"{OPERATE_URL}/v2/element-instances/search", body_v2)
    if result and result.get("items"):
        item = result["items"][0]
        return item.get("elementName") or item.get("elementId") or flow_node_id

    # Fallback to v1 flownode-instances search
    body_v1 = {
        "filter": {
            "processInstanceKey": int(instance_key) if str(instance_key).isdigit() else instance_key,
            "flowNodeId": flow_node_id,
        },
        "size": 1,
    }
    result = _session.post(f"{OPERATE_URL}/v1/flownode-instances/search", body_v1)
    if result and result.get("items"):
        return result["items"][0].get("flowNodeName") or result["items"][0].get("flowNodeId") or flow_node_id
    return flow_node_id


# ── BPMN XML Topology Parser ──────────────────────────────────────────────────

def fetch_bpmn_xml(proc_def_key: str) -> Optional[str]:
    """Fetch the raw BPMN 2.0 XML for a process definition from Camunda Operate."""
    for endpoint in [
        f"{OPERATE_URL}/v2/process-definitions/{proc_def_key}/xml",
        f"{OPERATE_URL}/v1/process-definitions/{proc_def_key}/xml",
        f"{OPERATE_URL}/api/process-definitions/{proc_def_key}/xml",
    ]:
        raw = _session.get_raw(endpoint)
        if raw:
            raw_s = raw.strip()
            if raw_s.startswith("{"):
                try:
                    data = json.loads(raw_s)
                    if isinstance(data, dict):
                        xml = data.get("bpmnXml") or data.get("xml") or data.get("content")
                        if xml:
                            return xml
                except Exception:
                    pass
            elif "<" in raw_s and ("process" in raw_s or "definitions" in raw_s):
                return raw_s

    return None


def parse_bpmn_topology(xml_content: str, incident_element_id: str = "") -> dict:
    """
    Parse BPMN 2.0 XML and extract the process flow topology relevant for RCA.
    Robustly handles all namespaces and prefixes.
    Returns a structured dict describing:
      - gateways (type, id, name, incoming/outgoing flows)
      - boundary_events (type, attached to which task)
      - parallel_branches (which tasks share a parallel fork)
      - incident_element_context (what gateway/scope the failing element is in)
      - warnings (critical deadlock / missing boundary warnings)
    """
    try:
        import xml.etree.ElementTree as ET

        def _local_tag(elem) -> str:
            return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        root = ET.fromstring(xml_content)

        # Find the process element
        process_el = None
        for el in root.iter():
            if _local_tag(el) == "process":
                process_el = el
                break
        if process_el is None:
            process_el = root

        topology = {
            "gateways": [],
            "boundary_events": [],
            "sequence_flows": [],
            "tasks": [],
            "incident_element_context": {},
            "parallel_fork_branches": [],
            "warnings": [],
        }

        # Collect all sequence flows: {flow_id: {sourceRef, targetRef}}
        flow_map: dict = {}
        for el in process_el.iter():
            if _local_tag(el) == "sequenceFlow":
                fid = el.get("id", "")
                has_cond = any(_local_tag(c) == "conditionExpression" for c in el)
                flow_map[fid] = {
                    "id": fid,
                    "name": el.get("name", ""),
                    "source": el.get("sourceRef", ""),
                    "target": el.get("targetRef", ""),
                    "condition": "yes" if has_cond else "no",
                }
                topology["sequence_flows"].append(flow_map[fid])

        # Build adjacency: element_id -> list of target element_ids
        outgoing_map: dict = {}
        incoming_map: dict = {}
        for sf in flow_map.values():
            outgoing_map.setdefault(sf["source"], []).append(sf["target"])
            incoming_map.setdefault(sf["target"], []).append(sf["source"])

        # Collect gateways
        gw_types = {
            "parallelGateway": "PARALLEL",
            "exclusiveGateway": "EXCLUSIVE",
            "inclusiveGateway": "INCLUSIVE",
            "eventBasedGateway": "EVENT_BASED",
            "complexGateway": "COMPLEX",
        }
        for el in process_el.iter():
            lt = _local_tag(el)
            if lt in gw_types:
                gw_id   = el.get("id", "")
                gw_name = el.get("name", gw_id)
                out_targets = outgoing_map.get(gw_id, [])
                in_sources  = incoming_map.get(gw_id, [])
                role = "FORK" if len(out_targets) > 1 else ("JOIN" if len(in_sources) > 1 else "PASS-THROUGH")

                entry = {
                    "id": gw_id,
                    "name": gw_name,
                    "type": gw_types[lt],
                    "role": role,
                    "outgoing_targets": out_targets,
                    "incoming_sources": in_sources,
                }
                topology["gateways"].append(entry)

                if gw_types[lt] == "PARALLEL" and role == "FORK":
                    topology["parallel_fork_branches"].append({
                        "fork_id": gw_id,
                        "fork_name": gw_name,
                        "branch_entry_elements": out_targets,
                        "description": f"Parallel Fork '{gw_name}' splits into {len(out_targets)} concurrent branches: {out_targets}",
                    })

        # Collect boundary events (error, timer, message, signal)
        boundary_event_types = {
            "errorEventDefinition": "ERROR",
            "timerEventDefinition": "TIMER",
            "messageEventDefinition": "MESSAGE",
            "signalEventDefinition": "SIGNAL",
            "escalationEventDefinition": "ESCALATION",
        }
        for el in process_el.iter():
            if _local_tag(el) == "boundaryEvent":
                be_id     = el.get("id", "")
                be_name   = el.get("name", be_id)
                attached  = el.get("attachedToRef", "")
                cancel    = el.get("cancelActivity", "true")
                be_types  = []
                for child in el:
                    c_lt = _local_tag(child)
                    if c_lt in boundary_event_types:
                        err_ref = child.get("errorRef", "")
                        label = boundary_event_types[c_lt]
                        if err_ref:
                            for err_el in root.iter():
                                if _local_tag(err_el) == "error" and err_el.get("id") == err_ref:
                                    err_code = err_el.get("errorCode", "")
                                    if err_code:
                                        label = f"{label}(code={err_code})"
                                    break
                        be_types.append(label)

                topology["boundary_events"].append({
                    "id": be_id,
                    "name": be_name,
                    "attached_to": attached,
                    "type": ",".join(be_types) if be_types else "UNKNOWN",
                    "interrupting": cancel != "false",
                    "outgoing_targets": outgoing_map.get(be_id, []),
                })

        # Collect tasks/service tasks
        task_tags = {
            "serviceTask", "userTask", "sendTask", "receiveTask",
            "manualTask", "scriptTask", "businessRuleTask", "callActivity", "task",
        }
        for el in process_el.iter():
            lt = _local_tag(el)
            if lt in task_tags:
                t_id   = el.get("id", "")
                t_name = el.get("name", t_id)
                attached_bes = [
                    be for be in topology["boundary_events"]
                    if be["attached_to"] == t_id
                ]
                topology["tasks"].append({
                    "id": t_id,
                    "name": t_name,
                    "type": lt,
                    "boundary_events": [be["type"] for be in attached_bes],
                    "incoming": incoming_map.get(t_id, []),
                    "outgoing": outgoing_map.get(t_id, []),
                })

        # Analyze incident element context
        if incident_element_id:
            # Check if incident element is inside a parallel branch
            for branch_info in topology["parallel_fork_branches"]:
                branch_entries = branch_info["branch_entry_elements"]
                # BFS from branch entry to find if incident_element_id is reachable
                reachable = set()
                queue = list(branch_entries)
                while queue:
                    curr = queue.pop(0)
                    if curr in reachable:
                        continue
                    reachable.add(curr)
                    queue.extend(outgoing_map.get(curr, []))

                if incident_element_id in reachable:
                    parallel_joins = [
                        g for g in topology["gateways"]
                        if g["type"] == "PARALLEL" and g["role"] == "JOIN"
                    ]
                    join_info = parallel_joins[0] if parallel_joins else {}
                    elem_name = incident_element_id
                    for t in topology["tasks"]:
                        if t["id"] == incident_element_id:
                            elem_name = t["name"] or incident_element_id
                            break

                    deadlock_msg = (
                        f"CRITICAL: '{elem_name}' ({incident_element_id}) is inside Parallel Fork '{branch_info['fork_name']}'. "
                        f"If its token is redirected by an error/boundary event, "
                        f"the Parallel Join '{join_info.get('name', 'downstream')}' will WAIT FOREVER "
                        f"(Token Starvation Deadlock). Recommend using a Terminate End Event or sequential flow."
                    )
                    topology["incident_element_context"] = {
                        "inside_parallel_branch": True,
                        "fork_gateway": branch_info["fork_id"],
                        "fork_name": branch_info["fork_name"],
                        "concurrent_branches": branch_entries,
                        "parallel_join": join_info.get("id", "unknown"),
                        "parallel_join_name": join_info.get("name", "unknown"),
                        "deadlock_risk": deadlock_msg,
                    }
                    topology["warnings"].append(deadlock_msg)
                    break

            # Check if incident element has an error boundary event
            task_matches = [t for t in topology["tasks"] if t["id"] == incident_element_id]
            if task_matches:
                task_info = task_matches[0]
                has_error_boundary = any("ERROR" in be_type for be_type in task_info["boundary_events"])
                topology["incident_element_context"]["has_error_boundary_event"] = has_error_boundary
                if not has_error_boundary:
                    missing_msg = (
                        f"ERROR_BOUNDARY_MISSING: Task '{task_info['name']}' ({incident_element_id}) has NO Error Boundary Catch Event. "
                        f"Any BPMN error thrown here will cause an UNHANDLED_ERROR_EVENT incident."
                    )
                    topology["incident_element_context"]["missing_boundary_warning"] = missing_msg
                    topology["warnings"].append(missing_msg)

        return topology

    except Exception as e:
        log.warning(f"BPMN topology parse failed: {e}")
        return {"parse_error": str(e), "warnings": []}


    except Exception as e:
        log.warning(f"BPMN topology parse failed: {e}")
        return {"parse_error": str(e), "warnings": []}


# ── DGX vLLM RCA ─────────────────────────────────────────────────────────────

def check_dgx_alive() -> bool:
    """Return True if the DGX vLLM SSH tunnel is active on :8000."""
    try:
        req = urllib.request.Request(f"{DGX_URL}/models")
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False

def _parse_llm_json(raw: str) -> Optional[dict]:
    """
    Robustly parse JSON from LLM output.
    Strategy 1: Standard json.loads (fastest)
    Strategy 2: Strip trailing comma issues and retry
    Strategy 3: Regex-extract individual fields (graceful degradation)
    """
    # Strategy 1: direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strategy 2: clean common LLM JSON mistakes and retry
    import re
    cleaned = raw
    # Remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    # Replace smart quotes
    cleaned = cleaned.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: regex field extraction (graceful degradation)
    log.warning("JSON parse failed — extracting fields via regex")
    result = {}

    def _extract(field: str) -> str:
        # Match "field": "value" or "field": ["item1", "item2"]
        m = re.search(rf'"{field}"\s*:\s*"([^"]*)"', raw, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1)
        return ""

    def _extract_list(field: str) -> list:
        m = re.search(rf'"{field}"\s*:\s*\[([^\]]*)\]', raw, re.IGNORECASE | re.DOTALL)
        if m:
            items = re.findall(r'"([^"]*)"', m.group(1))
            return items
        return []

    result["summary"]             = _extract("summary")
    result["root_cause"]          = _extract("root_cause")
    result["confidence"]          = _extract("confidence") or "LOW"
    result["observed_facts"]      = _extract_list("observed_facts")
    result["recommended_actions"] = _extract_list("recommended_actions")

    if result["summary"] or result["root_cause"]:
        return result

    return None


def get_active_model() -> str:
    """Auto-detect the model name served by vLLM."""
    try:
        req = urllib.request.Request(f"{DGX_URL}/models")
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read().decode())
            models = data.get("data", [])
            if models:
                return models[0].get("id", DGX_MODEL)
    except Exception:
        pass
    return DGX_MODEL


def run_rca_on_dgx(incident_payload: dict, sop_runbook: Optional[dict] = None) -> Optional[dict]:
    """
    Send a structured Camunda incident payload to DGX Qwen 35B and get back
    a JSON RCA. If a predefined SOP Runbook is provided, it instructs the model
    to strictly apply the predefined SRE instructions to the incident's variables.
    """
    model = get_active_model()

    sop_instructions = ""
    if sop_runbook:
        sop_instructions = (
            "\n\n============================================================\n"
            "📖 PREDEFINED SRE RUNBOOK INSTRUCTIONS FOR THIS SCENARIO:\n"
            "============================================================\n"
            f"Guidance Root Cause: {sop_runbook.get('root_cause', '')}\n"
            "Standard Recommended Remediation Steps:\n"
            + "\n".join(f"  - {s}" for s in sop_runbook.get("recommended_actions", []))
            + "\n\nApply these exact predefined instructions and steps tailored to the instance variables."
        )

    # Build topology section separately for clear prompt injection
    topology = incident_payload.get("bpmn_topology", {})
    topology_section = ""
    if topology and not topology.get("parse_error"):
        # Summarise key topology facts concisely for the model
        lines = []
        lines.append("\n\n============================================================")
        lines.append("🗺️  BPMN PROCESS TOPOLOGY (use for structural analysis)")
        lines.append("============================================================")

        # Incident element context (most important)
        ctx = topology.get("incident_element_context", {})
        if ctx:
            lines.append("\n📍 Incident Element Context:")
            if ctx.get("inside_parallel_branch"):
                lines.append(f"  ⚠️  INSIDE PARALLEL BRANCH: Fork='{ctx.get('fork_name')}' Join='{ctx.get('parallel_join_name')}'")
                lines.append(f"  🔴 DEADLOCK RISK: {ctx.get('deadlock_risk', '')}")
            if ctx.get("missing_boundary_warning"):
                lines.append(f"  ⚠️  {ctx['missing_boundary_warning']}")
            if ctx.get("has_error_boundary_event") is False:
                lines.append("  ❌ No Error Boundary Event found on this task.")
            elif ctx.get("has_error_boundary_event"):
                lines.append("  ✅ Error Boundary Event IS configured on this task.")

        # Gateways summary
        gateways = topology.get("gateways", [])
        if gateways:
            lines.append("\n🔀 Gateways:")
            for gw in gateways:
                lines.append(
                    f"  [{gw['type']} {gw['role']}] id={gw['id']} name='{gw['name']}' "
                    f"in={len(gw['incoming_sources'])} out={len(gw['outgoing_targets'])}"
                )

        # Boundary events summary
        boundary_events = topology.get("boundary_events", [])
        if boundary_events:
            lines.append("\n🔔 Boundary Events:")
            for be in boundary_events:
                lines.append(
                    f"  [{be['type']}] id={be['id']} attached_to={be['attached_to']} "
                    f"interrupting={be['interrupting']}"
                )

        # Parallel branch info
        parallel_branches = topology.get("parallel_fork_branches", [])
        if parallel_branches:
            lines.append("\n⚡ Parallel Fork Branches:")
            for pb in parallel_branches:
                lines.append(f"  Fork '{pb['fork_name']}' → branches: {pb['branch_entry_elements']}")

        # Top-level topology warnings
        warnings = topology.get("warnings", [])
        if warnings:
            lines.append("\n🚨 Topology Warnings:")
            for w in warnings:
                lines.append(f"  ⚠️  {w}")

        topology_section = "\n".join(lines)

    # Strip bpmn_topology from the JSON payload to avoid sending raw XML parsed dict (already summarised above)
    payload_for_prompt = {k: v for k, v in incident_payload.items() if k != "bpmn_topology"}

    user_content = (
        "Camunda 8 BPMN Incident — Perform Root Cause Analysis:\n\n"
        + json.dumps(payload_for_prompt, indent=2)
        + topology_section
        + sop_instructions
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system",  "content": _SYSTEM_PROMPT},
            {"role": "user",    "content": user_content},
        ],
        "max_tokens": 2000,
        "temperature": 0.0,  # deterministic — required for runbook consistency
        # Disable internal chain-of-thought so content field is always populated
        "chat_template_kwargs": {"enable_thinking": False},
    }

    try:
        data = json.dumps(body).encode()
        req  = urllib.request.Request(
            f"{DGX_URL}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read().decode())

        choice  = resp.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = (message.get("content") or "").strip()

        # Fallback: if content empty, check reasoning (some model configs differ)
        if not content:
            reasoning = (message.get("reasoning") or "").strip()
            # Extract JSON block from reasoning if present
            start_r = reasoning.find("{")
            end_r   = reasoning.rfind("}") + 1
            if start_r != -1 and end_r > start_r:
                content = reasoning[start_r:end_r]

        if not content:
            log.warning("DGX returned empty content. Full response: %s", json.dumps(resp)[:500])
            return None

        # Strip markdown fences if present
        if content.startswith("```"):
            lines = content.splitlines()
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()

        # Extract the JSON object (handles any leading/trailing text)
        start = content.find("{")
        end   = content.rfind("}") + 1
        if start != -1 and end > start:
            content = content[start:end]

        parsed = json.loads(content)
        if not parsed.get("evidence"):
            err_msg = incident_payload.get("error_message")
            if err_msg:
                parsed["evidence"] = [err_msg]

        # ── Merge pre-computed topology warnings into DGX output ──────────────
        # Our BFS parser already detected structural issues (Parallel Gateway
        # Deadlock, missing Boundary Event, etc.) stored in bpmn_topology["warnings"].
        # DGX may or may not echo them back in topology_warnings[].
        # We ALWAYS merge our pre-computed warnings to guarantee they appear.
        bpmn_topology  = incident_payload.get("bpmn_topology", {})
        pre_computed   = bpmn_topology.get("warnings", [])
        dgx_warnings   = parsed.get("topology_warnings") or []

        if pre_computed:
            # Pre-computed warnings always come first (BFS-guaranteed structural facts)
            merged = list(pre_computed)
            seen = {w.lower()[:60] for w in merged}
            for w in dgx_warnings:
                if w.lower()[:60] not in seen:
                    merged.append(w)
                    seen.add(w.lower()[:60])
            parsed["topology_warnings"] = merged
            log.info(
                f"  \U0001f5fa\ufe0f  topology_warnings merged: {len(pre_computed)} pre-computed "
                f"+ {len(dgx_warnings)} DGX \u2192 {len(merged)} total"
            )
        elif dgx_warnings:
            parsed["topology_warnings"] = dgx_warnings

        return parsed

    except Exception as exc:
        log.warning(f"DGX RCA failed: {exc}")
        return None


# ── Pretty printer ────────────────────────────────────────────────────────────

def print_rca(incident: dict, rca: Optional[dict]) -> None:
    thick = "=" * 70
    thin  = "-" * 70
    now   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"\n{thick}")
    print(f"  🔴  CAMUNDA INCIDENT — SRE ROOT CAUSE ANALYSIS")
    print(f"  Detected : {now}")
    print(thick)
    print(f"  Process  : {incident.get('process_id', 'unknown')}")
    print(f"  Instance : {incident.get('instance_key', 'unknown')}")
    print(f"  Element  : {incident.get('element_name', incident.get('element_id', 'unknown'))}")
    print(f"  Error    : {incident.get('error_type', 'unknown')}")
    print(f"  Message  : {incident.get('error_message', '')}")

    if incident.get("variables"):
        print(f"\n  📦 Process Variables at Failure:")
        for k, v in incident["variables"].items():
            print(f"     {k} = {v!r}")

    if rca:
        conf   = rca.get("confidence", "?")
        emoji  = "🟢" if conf == "HIGH" else "🟡" if conf == "MEDIUM" else "🔴"
        print(f"\n  {thick}")
        print(f"  🤖 AI Engine : DGX Qwen 35B  (localhost:8000 via SSH tunnel)")
        print(f"  Confidence  : {emoji} {conf}")
        print(thin)

        print(f"\n  ❓ WHAT is the error?")
        print(f"     {rca.get('summary', 'See error message above')}")

        print(f"\n  🔍 WHY did it occur?  (Root Cause)")
        print(thin)
        rc = rca.get("root_cause", "")
        for line in rc.splitlines():
            print(f"     {line}")

        if rca.get("observed_facts"):
            print(f"\n  📋 Observed Facts:")
            for fact in rca["observed_facts"]:
                print(f"     • {fact}")

        print(f"\n  🛠️  HOW to fix it?")
        print(thin)
        for i, step in enumerate(rca.get("recommended_actions", []), 1):
            print(f"     {i}. {step}")
    else:
        print(f"\n  ⚠️  DGX RCA unavailable — check SSH tunnel (localhost:8000)")

    print(f"\n{thick}\n")


# ── Main polling loop ─────────────────────────────────────────────────────────

def build_incident_payload(raw: dict) -> dict:
    """
    Build a rich, dynamic incident payload from a raw Operate incident object.
    Fetches bpmnProcessId, variables, flow node names, and BPMN topology from Operate REST API.
    Zero hardcoding — every field comes from the live Camunda 8 API.

    Raw Operate incident fields:
      key, processDefinitionKey, processInstanceKey, type, message, creationTime, state
    """
    incident_key  = str(raw.get("key", ""))
    instance_key  = str(raw.get("processInstanceKey", ""))
    proc_def_key  = str(raw.get("processDefinitionKey", ""))

    # 'type' is the Operate field name (not 'errorType')
    error_type    = raw.get("type", raw.get("errorType", "UNSPECIFIED"))
    error_message = raw.get("message", raw.get("errorMessage", "Unknown error"))
    creation_time = raw.get("creationTime", datetime.now(timezone.utc).isoformat())

    # Operate incidents don't include bpmnProcessId — fetch from process instance
    instance_data = fetch_process_instance(instance_key) if instance_key else {}
    process_id    = (
        instance_data.get("bpmnProcessId")
        or proc_def_key
        or "unknown-process"
    )

    # Incidents don't have flowNodeId at top level — fetch from flownode-instances
    element_id   = ""
    element_name = ""
    if instance_key:
        fn_body   = {"filter": {"processInstanceKey": int(instance_key), "incident": True}, "size": 1}
        fn_result = _session.post(f"{OPERATE_URL}/v1/flownode-instances/search", fn_body)
        if fn_result and fn_result.get("items"):
            fn_item      = fn_result["items"][0]
            element_id   = fn_item.get("flowNodeId", "")
            element_name = fn_item.get("flowNodeName") or element_id

    # Fetch live process variables
    variables = fetch_instance_variables(instance_key) if instance_key else {}

    # ── BPMN Topology Analysis ───────────────────────────────────────────────
    bpmn_topology: dict = {}
    if proc_def_key:
        log.info(f"  🗺️  Fetching BPMN XML topology for process def {proc_def_key}...")
        bpmn_xml = fetch_bpmn_xml(proc_def_key)
        if bpmn_xml:
            bpmn_topology = parse_bpmn_topology(bpmn_xml, element_id)
            warnings = bpmn_topology.get("warnings", [])
            if warnings:
                for w in warnings:
                    log.warning(f"  ⚠️  TOPOLOGY: {w}")
            gw_count   = len(bpmn_topology.get("gateways", []))
            task_count = len(bpmn_topology.get("tasks", []))
            log.info(f"  🗺️  Topology parsed: {gw_count} gateways, {task_count} tasks")
        else:
            log.debug(f"  ⚠️  BPMN XML not available for proc_def_key={proc_def_key}")

    return {
        "incident_key":   incident_key,
        "process_id":     process_id,
        "instance_key":   instance_key,
        "element_id":     element_id,
        "element_name":   element_name,
        "error_type":     error_type,
        "error_message":  error_message,
        "creation_time":  creation_time,
        "variables":      variables,
        "bpmn_topology":  bpmn_topology,
    }


def _post_rca_to_sentinel(incident: dict, rca: Optional[dict]) -> None:
    """Send completed RCA to Sentinel service so frontend displays it immediately."""
    if not rca:
        return
    try:
        inst_key = str(incident.get("instance_key", ""))
        inc_key  = str(incident.get("incident_key", ""))
        record = {
            "status": "success",
            "incident": incident.get("error_type", "INCIDENT"),
            "incident_key": inc_key,
            "incidentKey": inc_key,
            "process_id": incident.get("process_id"),
            "instance_key": inst_key,
            "processInstanceKey": inst_key,
            "element_id": incident.get("element_id"),
            "variables": incident.get("variables", {}),
            "rca": rca,
            "raw_output": rca.get("root_cause", ""),
        }
        data = json.dumps(record).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:5000/api/rca/record",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3):
            log.info(f"✅ Synced RCA for incident {inc_key} (Instance {inst_key}) to Sentinel")
    except Exception as e:
        log.warning(f"⚠️ Could not push RCA to Sentinel: {e}")



def run_bridge(poll_interval: int = POLL_INTERVAL, run_once: bool = False) -> None:
    """
    Main loop: polls Camunda Operate for live incidents, runs DGX RCA on each new one.
    """
    thick = "=" * 70

    # ── Startup banner ────────────────────────────────────────────────────────
    print(f"\n{thick}")
    print("  GRAPHIFY  —  Real-Time Camunda 8 → SRE Agent Bridge")
    print(thick)

    # Check Operate
    if check_operate_alive():
        print("  ✅ Camunda Operate  :8081  [CONNECTED]")
    else:
        print("  ❌ Camunda Operate  :8081  [DOWN] — start with: docker compose up -d operate")

    # Check DGX
    if check_dgx_alive():
        model = get_active_model()
        print(f"  ✅ DGX vLLM         :8000  [CONNECTED] — {model}")
    else:
        print("  ❌ DGX vLLM         :8000  [DOWN] — run: ssh -L 8000:localhost:8000 truviq_domain@192.168.0.143")

    print(f"\n  Polling every {poll_interval}s for ACTIVE incidents in ALL BPMN processes.")
    print("  No BPMN file needed — watches everything running in Camunda 8.")
    print(f"{thick}\n")

    seen_incident_keys: set[str] = set()

    while True:
        try:
            incidents = fetch_live_incidents()

            new_count = 0
            for raw_incident in incidents:
                inc_key = str(raw_incident.get("key", ""))

                if not inc_key or inc_key in seen_incident_keys:
                    continue  # already processed

                seen_incident_keys.add(inc_key)
                new_count += 1

                # Build dynamic payload from live Operate data
                payload = build_incident_payload(raw_incident)

                log.info(
                    f"NEW INCIDENT [{inc_key}] "
                    f"process={payload['process_id']} "
                    f"element={payload['element_name']} "
                    f"error={payload['error_type']}"
                )

                inst_key   = str(payload.get("instance_key", ""))
                inc_key    = str(payload.get("incident_key", ""))
                error_type = payload.get("error_type", "UNSPECIFIED")
                process_id = payload.get("process_id", "*")

                # 1. Check if THIS SPECIFIC INSTANCE already has an RCA in Supabase
                rca = lookup_instance_rca(inst_key, inc_key) if _SUPABASE_AVAILABLE else None

                if rca:
                    log.info(
                        f"  🔁 INSTANCE MATCH: Re-using existing RCA for Instance [{inst_key}] "
                        f"— 100% consistent story for this instance."
                    )
                else:
                    # 2. Different / New instance: Fetch predefined SOP Runbook for this error scenario
                    sop = lookup_sop_guidelines(error_type, process_id) if _SUPABASE_AVAILABLE else None
                    if sop:
                        log.info(f"  📖 SOP RUNBOOK [{error_type}] (process: {process_id}) loaded with predefined instructions")

                    log.info(f"  🤖 NEW INSTANCE [{inst_key}]: Running DGX analysis on its specific variables with predefined SOP...")
                    rca = run_rca_on_dgx(payload, sop) if check_dgx_alive() else None

                    # 3. Persist this instance's RCA into Supabase tagged by its instance_key
                    if rca and _SUPABASE_AVAILABLE:
                        save_instance_rca(inst_key, inc_key, error_type, process_id, rca, payload)

                print_rca(payload, rca)
                _post_rca_to_sentinel(payload, rca)

            if not incidents:
                log.info("No active incidents. Watching...")
            elif new_count == 0:
                log.info(f"{len(incidents)} known incident(s) — no new ones. Watching...")

        except KeyboardInterrupt:
            print("\n\n  [Bridge] Stopped. Goodbye!\n")
            break
        except Exception as exc:
            log.error(f"Poll loop error: {exc}")

        if run_once:
            break

        try:
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n\n  [Bridge] Stopped. Goodbye!\n")
            break


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real-time Camunda 8 → SRE Agent bridge (polls Operate REST API)"
    )
    parser.add_argument(
        "--interval", type=int, default=POLL_INTERVAL,
        help=f"Polling interval in seconds (default: {POLL_INTERVAL})",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run one poll cycle and exit (useful for testing)",
    )
    parser.add_argument(
        "--operate-url", default=OPERATE_URL,
        help=f"Camunda Operate base URL (default: {OPERATE_URL})",
    )
    parser.add_argument(
        "--dgx-url", default=DGX_URL,
        help=f"DGX vLLM base URL (default: {DGX_URL})",
    )
    args = parser.parse_args()

    # Allow CLI overrides via global module variables
    if args.operate_url != OPERATE_URL:
        os.environ["OPERATE_URL"] = args.operate_url
    if args.dgx_url != DGX_URL:
        os.environ["DGX_URL"] = args.dgx_url

    run_bridge(poll_interval=args.interval, run_once=args.once)


if __name__ == "__main__":
    main()
