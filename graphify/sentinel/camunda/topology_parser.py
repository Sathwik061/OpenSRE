"""
sentinel/camunda/topology_parser.py
===================================
BPMN 2.0 XML graph parser, BFS traversal engine, and topology deadlock detector.
Extracts gateways, fork-join branches, boundary catch events, sequence flow
conditions, and structural failure hazards.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("sentinel.camunda.topology_parser")


def parse_bpmn_topology(xml_content: str, incident_element_id: str = "") -> Dict[str, Any]:
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
        # Extract execution platform version from definitions root tag (e.g. 8.9.0 -> 8.9)
        camunda_version = None
        for k, v in root.attrib.items():
            if "executionPlatformVersion" in k:
                parts = str(v).strip().split(".")
                if len(parts) >= 2:
                    camunda_version = f"{parts[0]}.{parts[1]}"
                else:
                    camunda_version = str(v).strip()
                break

        topology: Dict[str, Any] = {
            "gateways": [],
            "boundary_events": [],
            "sequence_flows": [],
            "tasks": [],
            "incident_element_context": {},
            "parallel_fork_branches": [],
            "warnings": [],
            "camunda_version": camunda_version,
        }

        # Collect all sequence flows: {flow_id: {sourceRef, targetRef}}
        flow_map: Dict[str, Any] = {}
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
        outgoing_map: Dict[str, List[str]] = {}
        incoming_map: Dict[str, List[str]] = {}
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

                default_flow = el.get("default", "")
                entry = {
                    "id": gw_id,
                    "name": gw_name,
                    "type": gw_types[lt],
                    "role": role,
                    "default_flow": default_flow,
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

                if gw_types[lt] == "EXCLUSIVE" and role == "FORK" and not default_flow and len(out_targets) > 1:
                    xor_warn = (
                        f"EXCLUSIVE GATEWAY RISK: Exclusive Gateway '{gw_name}' ({gw_id}) has {len(out_targets)} branches with no Default Sequence Flow configured. "
                        f"RECOMMENDATION: In Camunda Modeler, select Exclusive Gateway '{gw_name}' and designate one outgoing sequence flow as the 'Default flow' to prevent CONDITION_ERROR incidents."
                    )
                    if xor_warn not in topology["warnings"]:
                        topology["warnings"].append(xor_warn)

        # Collect boundary events (error, timer, message, signal)
        boundary_event_types = {
            "errorEventDefinition": "ERROR",
            "timerEventDefinition": "TIMER",
            "messageEventDefinition": "MESSAGE",
            "signalEventDefinition": "SIGNAL",
            "escalationEventDefinition": "ESCALATION",
            "compensateEventDefinition": "COMPENSATION",
        }
        for el in process_el.iter():
            if _local_tag(el) == "boundaryEvent":
                be_id       = el.get("id", "")
                attached_to = el.get("attachedToRef", "")
                interrupting = el.get("cancelActivity", "true") != "false"
                be_type = "GENERIC"
                for child in el:
                    ct = _local_tag(child)
                    if ct in boundary_event_types:
                        be_type = boundary_event_types[ct]
                        break

                topology["boundary_events"].append({
                    "id": be_id,
                    "name": el.get("name", be_id),
                    "type": be_type,
                    "attached_to": attached_to,
                    "interrupting": interrupting,
                })

        # Collect tasks / service tasks / call activities
        task_types = {
            "serviceTask", "userTask", "sendTask", "receiveTask",
            "businessRuleTask", "scriptTask", "callActivity", "task", "subProcess"
        }
        for el in process_el.iter():
            lt = _local_tag(el)
            if lt in task_types:
                tid   = el.get("id", "")
                tname = el.get("name", tid)
                topology["tasks"].append({
                    "id": tid,
                    "name": tname,
                    "type": lt,
                    "incoming": incoming_map.get(tid, []),
                    "outgoing": outgoing_map.get(tid, []),
                })

        # ── Context Analysis for the Failing Element ─────────────────────────
        target_el_id = incident_element_id
        if not target_el_id and topology["tasks"]:
            # If element_id wasn't provided, identify first task in parallel branch or first service task
            for t in topology["tasks"]:
                if t["type"] in ("serviceTask", "callActivity", "task"):
                    target_el_id = t["id"]
                    break

        if target_el_id:
            ctx: Dict[str, Any] = {
                "element_id": target_el_id,
                "inside_parallel_branch": False,
                "parallel_join_name": None,
                "has_error_boundary_event": False,
                "deadlock_risk": None,
                "missing_boundary_warning": None,
            }

            # 1. Check if failing element has an Error Boundary Event attached
            attached_bes = [
                be for be in topology["boundary_events"]
                if be["attached_to"] == target_el_id
            ]
            has_error_be = any(be["type"] == "ERROR" for be in attached_bes)
            ctx["has_error_boundary_event"] = has_error_be
            if not has_error_be:
                missing_msg = (
                    f"MISSING_ERROR_BOUNDARY_EVENT: Task '{target_el_id}' has NO Error Boundary Catch Event configured. "
                    f"RECOMMENDATION: In Camunda Modeler, attach an Error Boundary Catch Event with matching errorCode (e.g. 'PROCESS_ERROR') to task '{target_el_id}'."
                )
                ctx["missing_boundary_warning"] = missing_msg
                topology["warnings"].append(missing_msg)

            # 2. Parallel Fork / Join Deadlock analysis
            for pb in topology["parallel_fork_branches"]:
                fork_id = pb["fork_id"]

                def _reaches(start: str, target: str, visited: set) -> bool:
                    if start == target:
                        return True
                    if start in visited:
                        return False
                    visited.add(start)
                    for nxt in outgoing_map.get(start, []):
                        if _reaches(nxt, target, visited):
                            return True
                    return False

                # Is incident element reachable from this fork?
                if _reaches(fork_id, target_el_id, set()):
                    ctx["inside_parallel_branch"] = True
                    ctx["fork_name"] = pb["fork_name"]

                    # Find downstream Parallel Join
                    parallel_joins = [
                        gw for gw in topology["gateways"]
                        if gw["type"] == "PARALLEL" and gw["role"] == "JOIN"
                    ]
                    for join in parallel_joins:
                        if _reaches(fork_id, join["id"], set()):
                            ctx["parallel_join_name"] = join["name"]
                            task_obj = next((t for t in topology["tasks"] if t["id"] == target_el_id), None)
                            task_label = f"'{task_obj['name']}' ({target_el_id})" if task_obj else f"'{target_el_id}'"
                            fork_label = f"'{pb['fork_name']}'" if pb.get('fork_name') else f"'{pb['fork_id']}'"
                            join_label = f"'{join['name']}'" if join.get('name') else f"'{join['id']}'"

                            deadlock_msg = (
                                f"PARALLEL GATEWAY DEADLOCK RISK: Task {task_label} is on a concurrent branch spawned by Parallel Fork {fork_label} leading to Parallel Join {join_label}. "
                                f"If this task fails or its token is diverted by an error event without reaching the join, the Parallel Join {join_label} will wait indefinitely for a token that will never arrive (Token Starvation Deadlock). "
                                f"CRITICAL RECOMMENDATION: In Camunda Modeler, attach an Error Boundary Catch Event to {task_label} and route its outgoing sequence flow to a Terminate End Event (to cleanly cancel all concurrent parallel tokens and terminate the process), or route an error path directly into the Parallel Join."
                            )
                            ctx["deadlock_risk"] = deadlock_msg
                            if deadlock_msg not in topology["warnings"]:
                                topology["warnings"].append(deadlock_msg)

            topology["incident_element_context"] = ctx

        return topology

    except Exception as e:
        logger.warning(f"BPMN topology parse failed: {e}")
        return {"parse_error": str(e), "warnings": []}
