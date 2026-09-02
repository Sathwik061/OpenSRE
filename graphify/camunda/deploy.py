"""
camunda/deploy.py — Camunda 8 Zeebe Deploy & Trigger
===================================================
Deploys rca_investigation.bpmn to Camunda 8 (Zeebe gRPC on :26500)
and triggers an RCA process instance by incident key.

Usage:
    python camunda/deploy.py                     # Deploy BPMN
    python camunda/deploy.py --trigger --key 1   # Deploy + Trigger key 1
    python camunda/deploy.py --trigger --key 2   # Deploy + Trigger key 2
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import asyncio
import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timezone

from pyzeebe import ZeebeClient, create_insecure_channel

# ── Config ────────────────────────────────────────────────────────────────────
ZEEBE_ADDRESS = os.getenv("ZEEBE_ADDRESS", "localhost:26500")
BPMN_FILE     = Path(__file__).parent / "bpmn" / "rca_investigation.bpmn"
PROCESS_ID    = "RCA_Investigation"

# Add project root to path for incident_registry import
sys.path.insert(0, str(Path(__file__).parent.parent))
from incident_registry import INCIDENT_REGISTRY, build_incident, list_keys


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def deploy_bpmn(client: ZeebeClient) -> None:
    """Deploy the BPMN definition to Zeebe via gRPC."""
    print(f"Deploying {BPMN_FILE.name} to Zeebe ({ZEEBE_ADDRESS}) ...")
    try:
        res = await client.deploy_resource(BPMN_FILE)
        print(f"[OK]  BPMN deployed successfully to Zeebe!")
        print(f"      Process ID: {PROCESS_ID}")
    except Exception as exc:
        import traceback
        print(f"[FAIL] Deployment failed: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        sys.exit(1)


async def trigger_incident(client: ZeebeClient, key: str) -> None:
    """Create a process instance in Zeebe with dynamic incident variables."""
    incident = build_incident(key)
    if incident is None:
        print(f"[FAIL] Unknown incident key '{key}'. Available keys:")
        for k in list_keys():
            print(f"  [{k['number']}] {k['key']} - {k['description']}")
        sys.exit(1)

    service       = incident.get("service", "unknown-service")
    error_type    = incident.get("error", "Unknown Error")
    error_message = incident.get("error_message", "")

    print(f"\nStarting RCA Investigation Process for: {incident['alert_name']}")
    print(f"  Service   : {service}")
    print(f"  Error     : {error_type}")
    print(f"  Message   : {error_message[:65]}...")

    variables = {
        "service":       service,
        "error_type":    error_type,
        "error_message": error_message,
        "environment":   incident.get("environment", "production"),
        "logs":          json.dumps(incident.get("logs", [])),
        "alert_name":    incident["alert_name"],
        "triggered_at":  _now(),
    }

    try:
        instance_key = await client.run_process(
            bpmn_process_id=PROCESS_ID,
            variables=variables,
        )
        print(f"\n[OK]  Process instance started in Camunda 8 Zeebe!")
        print(f"      Instance Key : {instance_key}")
        print(f"      Incident     : {incident['alert_name']}")
        print(f"\n  Zeebe Worker will pick up the task and print:")
        print(f"  - WHAT is the error")
        print(f"  - WHY it occurred")
        print(f"  - HOW to fix it\n")
    except Exception as exc:
        import traceback
        print(f"[FAIL] Could not start process instance: {exc}")
        traceback.print_exc()
        sys.exit(1)


async def async_main():
    p = argparse.ArgumentParser(description="Camunda 8 Zeebe Deploy & Trigger")
    p.add_argument("--trigger", action="store_true", help="Start a process instance after deploy")
    p.add_argument("--key",     default="1",         help="Incident key from registry (1-7)")
    p.add_argument("--address", default=ZEEBE_ADDRESS, help="Zeebe gRPC address (host:port)")
    args = p.parse_args()

    zeebe_address = args.address

    border = "=" * 60
    print(f"\n{border}")
    print("  GRAPHIFY  --  Camunda 8 Zeebe Deploy & Trigger")
    print(border)
    print(f"  Zeebe Target : {zeebe_address}")
    print(f"  BPMN File    : {BPMN_FILE.name}")
    print(f"  Process ID   : {PROCESS_ID}")
    print(border + "\n")

    channel = create_insecure_channel(grpc_address=zeebe_address)
    client  = ZeebeClient(channel)

    await deploy_bpmn(client)

    if args.trigger:
        await trigger_incident(client, args.key)


if __name__ == "__main__":
    asyncio.run(async_main())
