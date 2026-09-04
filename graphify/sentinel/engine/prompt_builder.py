"""
sentinel/engine/prompt_builder.py
=================================
Assembles structured, authoritative SRE prompts incorporating:
  1. Live Incident Error & Process Variables
  2. BPMN 2.0 Graph Topology & Reachability Summaries
  3. Dynamic Version-Pinned Official Camunda Documentation (Kapa MCP + Local RAG)
  4. Predefined SRE SOP Guidelines & Remediation Playbooks
"""

import os
import json
from typing import Dict, Any, Optional, Tuple, List


def build_sre_system_prompt(version: str = "8.9") -> str:
    """Dynamically builds a version-strict SRE system prompt."""
    return f"""\
You are a senior SRE engineer and BPMN 2.0 specialist performing Root Cause Analysis on a Camunda {version} BPMN incident.

TARGET ENGINE VERSION: Camunda {version}
CRITICAL VERSION INVARIANT:
- Evaluate this incident STRICTLY against Camunda {version} engine semantics, execution rules, and API capabilities.
- DO NOT recommend features, syntax, job worker protocols, or BPMN constructs that do not exist in Camunda {version}.
- Substantiate root causes using the provided official Camunda {version} documentation rules.

You have access to:
  1. The live incident error (type, message, element, variables)
  2. The BPMN process flow TOPOLOGY (gateways, branches, boundary events, sequence flows)
  3. Authoritative OFFICIAL CAMUNDA {version} DOCUMENTATION & ENGINE RULES

Rules:
- Base EVERY claim on the supplied evidence and authoritative Camunda documentation.
- Never invent variable values, process names, or infrastructure facts not in the data.
- If cause is unclear, say UNKNOWN.
- Provide concrete, actionable fix steps tailored specifically to Camunda {version}.

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

Documentation Reference Rules:
  - When Camunda documentation sections are provided, use their exact rules to substantiate the root cause and remediation.
  - Return a "documentation_references" array with the cited doc section, URL (pinned to Camunda {version}), and relevance.

Return ONLY valid JSON (no markdown fences):
{{
  "summary": "one-line summary",
  "root_cause": "precise root cause from evidence and topology",
  "confidence": "HIGH"|"MEDIUM"|"LOW",
  "documentation_references": [
    {{
      "section": "Error Events",
      "url": "https://docs.camunda.io/docs/{version}/components/modeler/bpmn/error-events/",
      "relevance": "Confirms unhandled error event occurs when no matching error boundary catch event is attached"
    }}
  ],
  "topology_warnings": ["e.g. PARALLEL_DEADLOCK: Parallel Join X waits for token from branch Y which is bypassed by error flow"],
  "observed_facts": ["fact from data"],
  "evidence": ["exact error message or log line cited from evidence"],
  "recommended_actions": ["concrete step 1", "step 2"]
}}"""


# Default system prompt for backwards compatibility
SRE_SYSTEM_PROMPT = build_sre_system_prompt(os.getenv("CAMUNDA_VERSION", "8.9"))


def build_rca_prompt(
    incident_payload: Dict[str, Any],
    sop_runbook: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str, List[Dict[str, str]]]:
    """
    Constructs the system and user prompt for DGX Qwen 35B with dynamic version pinning.
    Returns (system_prompt, user_content, citations_catalog).
    """
    camunda_version = str(incident_payload.get("camunda_version") or os.getenv("CAMUNDA_VERSION", "8.9")).strip()
    system_prompt = build_sre_system_prompt(camunda_version)

    # 1. SOP Instructions section
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

    # 2. Topology section
    topology = incident_payload.get("bpmn_topology") or {}
    topology_section = ""
    if topology and not topology.get("parse_error"):
        lines = [
            "\n\n============================================================",
            "🗺️  BPMN PROCESS TOPOLOGY (use for structural analysis)",
            "============================================================",
        ]
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

        gateways = topology.get("gateways", [])
        if gateways:
            lines.append("\n🔀 Gateways:")
            for gw in gateways:
                lines.append(
                    f"  [{gw['type']} {gw['role']}] id={gw['id']} name='{gw['name']}' "
                    f"in={len(gw['incoming_sources'])} out={len(gw['outgoing_targets'])}"
                )

        boundary_events = topology.get("boundary_events", [])
        if boundary_events:
            lines.append("\n🔔 Boundary Events:")
            for be in boundary_events:
                lines.append(
                    f"  [{be['type']}] id={be['id']} attached_to={be['attached_to']} "
                    f"interrupting={be['interrupting']}"
                )

        parallel_branches = topology.get("parallel_fork_branches", [])
        if parallel_branches:
            lines.append("\n⚡ Parallel Fork Branches:")
            for pb in parallel_branches:
                lines.append(f"  Fork '{pb['fork_name']}' → branches: {pb['branch_entry_elements']}")

        warnings = topology.get("warnings", [])
        if warnings:
            lines.append("\n🚨 Topology Warnings:")
            for w in warnings:
                lines.append(f"  ⚠️  {w}")

        topology_section = "\n".join(lines)

    # 3. Retrieve Official Camunda Documentation with exact version pinning
    try:
        from sentinel.knowledge.camunda_knowledge import retrieve_camunda_context
    except ImportError:
        try:
            from camunda_knowledge import retrieve_camunda_context
        except ImportError:
            def retrieve_camunda_context(*a, **kw): return {"prompt_section": "", "citations_catalog": []}

    error_type = incident_payload.get("error_type", incident_payload.get("error", incident_payload.get("type", "")))
    element_id = incident_payload.get("element_id", "")
    error_msg  = incident_payload.get("error_message", "")
    elem_type  = ""
    if topology and not topology.get("parse_error"):
        ctx = topology.get("incident_element_context", {})
        elem_type = ctx.get("element_type", "")

    knowledge_res = retrieve_camunda_context(
        error_type=error_type,
        element_type=elem_type or element_id,
        error_message=error_msg,
        bpmn_topology=topology,
        version=camunda_version,
        top_k=3,
    )
    docs_section = knowledge_res.get("prompt_section", "")
    citations_catalog = knowledge_res.get("citations_catalog", [])

    # 4. Strip bpmn_topology from the raw JSON payload to prevent redundancy
    payload_for_prompt = {k: v for k, v in incident_payload.items() if k != "bpmn_topology"}

    user_content = (
        f"Camunda {camunda_version} BPMN Incident — Perform Root Cause Analysis:\n\n"
        + json.dumps(payload_for_prompt, indent=2)
        + topology_section
        + docs_section
        + sop_instructions
    )

    return system_prompt, user_content, citations_catalog
