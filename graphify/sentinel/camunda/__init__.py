"""
sentinel/camunda
================
Camunda 8 integration package: REST API client, BPMN topology parser, and incident watcher.
"""

from sentinel.camunda.client import OperateClient, default_client
from sentinel.camunda.topology_parser import parse_bpmn_topology
from sentinel.camunda.bridge_watcher import (
    build_incident_payload,
    push_rca_to_sentinel,
    print_rca,
    run_bridge,
)

__all__ = [
    "OperateClient",
    "default_client",
    "parse_bpmn_topology",
    "build_incident_payload",
    "push_rca_to_sentinel",
    "print_rca",
    "run_bridge",
]
