"""
sentinel/camunda/bridge_watcher.py
==================================
Real-time incident polling loop that monitors Camunda Operate for ACTIVE incidents,
builds dynamic topology-aware payloads, triggers DGX Qwen 35B RCA, and synchronizes
investigations with Supabase and Sentinel.
"""

import os
import time
import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Set

from sentinel.camunda.client import OperateClient, default_client
from sentinel.camunda.topology_parser import parse_bpmn_topology
from sentinel.core.masking import mask_variables

logger = logging.getLogger("sentinel.camunda.watcher")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
SENTINEL_URL  = os.getenv("SENTINEL_URL",  "http://localhost:5000").rstrip("/")


def build_incident_payload(raw: Dict[str, Any], client: Optional[OperateClient] = None) -> Dict[str, Any]:
    """
    Build a rich, dynamic incident payload from a raw Operate incident object.
    Fetches bpmnProcessId, variables, flow node names, and BPMN topology from Operate REST API.
    """
    c = client or default_client
    incident_key  = str(raw.get("key", ""))
    instance_key  = str(raw.get("processInstanceKey", ""))
    proc_def_key  = str(raw.get("processDefinitionKey", ""))

    error_type    = raw.get("type", raw.get("errorType", "UNSPECIFIED"))
    error_message = raw.get("message", raw.get("errorMessage", "Unknown error"))
    creation_time = raw.get("creationTime", datetime.now(timezone.utc).isoformat())

    instance_data = c.fetch_process_instance(instance_key) if instance_key else {}
    process_id    = (
        instance_data.get("bpmnProcessId")
        or proc_def_key
        or "unknown-process"
    )

    element_id   = str(raw.get("flowNodeId") or raw.get("elementId") or raw.get("element_id") or "").strip()
    element_name = str(raw.get("flowNodeName") or raw.get("elementName") or raw.get("element_name") or element_id).strip()
    if instance_key and not element_id:
        fn_body   = {"filter": {"processInstanceKey": int(instance_key) if instance_key.isdigit() else instance_key, "incident": True}, "size": 1}
        fn_result = c.post("/v1/flownode-instances/search", fn_body)
        if fn_result and fn_result.get("items"):
            fn_item      = fn_result["items"][0]
            element_id   = fn_item.get("flowNodeId", "")
            element_name = fn_item.get("flowNodeName") or element_id

    raw_variables = c.fetch_instance_variables(instance_key) if instance_key else {}
    variables = mask_variables(raw_variables)

    bpmn_topology: Dict[str, Any] = {}
    if proc_def_key:
        logger.info(f"  🗺️ Fetching BPMN XML topology for process def {proc_def_key}...")
        bpmn_xml = c.fetch_bpmn_xml(proc_def_key)
        if bpmn_xml:
            bpmn_topology = parse_bpmn_topology(bpmn_xml, element_id)
            warnings = bpmn_topology.get("warnings", [])
            if warnings:
                for w in warnings:
                    logger.warning(f"  ⚠️ TOPOLOGY: {w}")
            gw_count   = len(bpmn_topology.get("gateways", []))
            task_count = len(bpmn_topology.get("tasks", []))
            logger.info(f"  🗺️ Topology parsed: {gw_count} gateways, {task_count} tasks")

    camunda_ver = (
        bpmn_topology.get("camunda_version")
        or c.get_cluster_version()
        or os.getenv("CAMUNDA_VERSION")
        or "8.9"
    )

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
        "camunda_version": camunda_ver,
    }


def push_rca_to_sentinel(incident: Dict[str, Any], rca: Optional[Dict[str, Any]]) -> None:
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
            f"{SENTINEL_URL}/api/rca/record",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3):
            logger.info(f"✅ Synced RCA for incident {inc_key} (Instance {inst_key}) to Sentinel")
    except Exception as e:
        logger.warning(f"⚠️ Could not push RCA to Sentinel: {e}")


def print_rca(incident: Dict[str, Any], rca: Optional[Dict[str, Any]]) -> None:
    """Console pretty-printer for SRE Root Cause Analysis results."""
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

        if rca.get("topology_warnings"):
            print(f"\n  ⚠️  BPMN Topology Warnings:")
            for tw in rca["topology_warnings"]:
                print(f"     • {tw}")

        if rca.get("observed_facts"):
            print(f"\n  📋 Observed Facts:")
            for fact in rca["observed_facts"]:
                print(f"     • {fact}")

        if rca.get("documentation_references"):
            print(f"\n  📚 Camunda Documentation References:")
            for doc in rca["documentation_references"]:
                print(f"     • {doc.get('section', 'Doc')}: {doc.get('url', '')}")
                if doc.get("relevance"):
                    print(f"       ({doc.get('relevance')})")

        print(f"\n  🛠️  HOW to fix it?")
        print(thin)
        for i, step in enumerate(rca.get("recommended_actions", []), 1):
            print(f"     {i}. {step}")
    else:
        print(f"\n  ⚠️  DGX RCA unavailable — check SSH tunnel (localhost:8000)")

    print(f"\n{thick}\n")


def run_bridge(
    poll_interval: int = POLL_INTERVAL,
    run_once: bool = False,
    client: Optional[OperateClient] = None,
) -> None:
    """
    Main polling loop: monitors Operate for live incidents, executes DGX RCA,
    and syncs to Supabase / Sentinel.
    """
    c = client or default_client

    # Lazy imports for decoupled execution
    try:
        from sentinel.engine.dgx_client import check_dgx_alive, get_active_model, run_rca_on_dgx
    except ImportError:
        def check_dgx_alive(): return False
        def get_active_model(): return "Qwen35B"
        def run_rca_on_dgx(*a, **kw): return None

    try:
        from sentinel.knowledge.supabase_runbook import (
            lookup_instance_rca, save_instance_rca, lookup_sop_guidelines
        )
        supabase_available = True
    except ImportError:
        try:
            from supabase_runbook import (
                lookup_instance_rca, save_instance_rca, lookup_sop_guidelines
            )
            supabase_available = True
        except ImportError:
            supabase_available = False
            def lookup_instance_rca(*a, **kw): return None
            def save_instance_rca(*a, **kw): return None
            def lookup_sop_guidelines(*a, **kw): return None

    thick = "=" * 70
    print(f"\n{thick}")
    print("  GRAPHIFY — Real-Time Camunda 8 -> SRE Agent Bridge")
    print(thick)

    if c.check_alive():
        print("  ✅ Camunda Operate :8081  [CONNECTED]")
    else:
        print("  ❌ Camunda Operate :8081  [DOWN] — start with: docker compose up -d operate")

    if check_dgx_alive():
        active_model = get_active_model()
        print(f"  ✅ DGX vLLM        :8000  [CONNECTED] — {active_model}")
    else:
        print("  ❌ DGX vLLM        :8000  [DOWN] — run: ssh -L 8000:localhost:8000 truviq_domain@192.168.0.143")

    print(f"\n  Polling every {poll_interval}s for ACTIVE incidents in ALL BPMN processes.")
    print("  No BPMN file needed — watches everything running in Camunda 8.")
    print(f"{thick}\n")

    seen_incident_keys: Set[str] = set()

    while True:
        try:
            incidents = c.fetch_live_incidents()

            for raw_incident in incidents:
                inc_key = str(raw_incident.get("key", ""))
                if not inc_key or inc_key in seen_incident_keys:
                    continue

                seen_incident_keys.add(inc_key)
                payload = build_incident_payload(raw_incident, client=c)

                logger.info(
                    f"NEW INCIDENT [{inc_key}] "
                    f"process={payload['process_id']} "
                    f"element={payload['element_name']} "
                    f"error={payload['error_type']}"
                )

                inst_key   = str(payload.get("instance_key", ""))
                error_type = payload.get("error_type", "UNSPECIFIED")
                process_id = payload.get("process_id", "*")

                # 1. Check if THIS SPECIFIC INSTANCE already has an RCA in Supabase
                rca = lookup_instance_rca(inst_key, inc_key) if supabase_available else None

                if rca:
                    logger.info(
                        f"  🔁 INSTANCE MATCH: Re-using existing RCA for Instance [{inst_key}] "
                        f"— 100% consistent story for this instance."
                    )
                else:
                    sop = lookup_sop_guidelines(error_type, process_id) if supabase_available else None
                    if sop:
                        logger.info(f"  📖 SOP RUNBOOK [{error_type}] (process: {process_id}) loaded")

                    logger.info(f"  🤖 NEW INSTANCE [{inst_key}]: Running DGX analysis...")
                    rca = run_rca_on_dgx(payload, sop) if check_dgx_alive() else None

                    if rca and supabase_available:
                        save_instance_rca(inst_key, inc_key, error_type, process_id, rca, payload)

                print_rca(payload, rca)
                push_rca_to_sentinel(payload, rca)

        except Exception as e:
            logger.error(f"Error in Camunda Bridge polling loop: {e}", exc_info=True)

        if run_once:
            break
        time.sleep(poll_interval)
