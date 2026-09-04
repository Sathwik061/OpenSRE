#!/usr/bin/env python3
"""
camunda_bridge.py — Real-Time Camunda 8 -> SRE Agent Bridge (CLI Entry Point)
============================================================================
Polls Camunda 8 Operate in real time for ACTIVE workflow incidents, performs
topology-aware Root Cause Analysis via company DGX Qwen 35B, and synchronizes
investigations with Supabase and the Sentinel Incident Insights Hub.

Usage:
  python camunda_bridge.py               # poll every 10s (default)
  python camunda_bridge.py --interval 5  # poll every 5s
  python camunda_bridge.py --once        # run a single check and exit
"""

import sys
import os
import argparse
from pathlib import Path

# Setup paths so sentinel package is importable
_sentinel_dir = Path(__file__).resolve().parent / "sentinel"
if str(_sentinel_dir) not in sys.path:
    sys.path.insert(0, str(_sentinel_dir))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

# Modular imports
from sentinel.camunda.client import OperateClient, default_client
from sentinel.camunda.topology_parser import parse_bpmn_topology
from sentinel.camunda.bridge_watcher import (
    run_bridge,
    build_incident_payload,
    print_rca,
    push_rca_to_sentinel,
)
from sentinel.engine.dgx_client import (
    check_dgx_alive,
    is_dgx_available,
    get_active_model,
    run_rca_on_dgx,
    investigate_with_dgx,
)

# Export legacy helper aliases
def check_operate_alive() -> bool:
    return default_client.check_alive()


def main():
    parser = argparse.ArgumentParser(description="Real-Time Camunda 8 -> SRE Agent Bridge")
    parser.add_argument("--interval", type=int, default=10, help="Polling interval in seconds (default: 10)")
    parser.add_argument("--once", action="store_true", help="Run a single poll cycle and exit")
    args = parser.parse_args()

    run_bridge(poll_interval=args.interval, run_once=args.once)


if __name__ == "__main__":
    main()
