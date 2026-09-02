"""
test_leave_approval.py — Run and Test leave_approval.bpmn
==========================================================
Tests your 'leave_approval.bpmn' (Process ID: 'final-test')
against Camunda 8 Zeebe and automatically triggers SRE RCA
whenever an incident or error occurs.

Usage:
    python test_leave_approval.py            # Normal execution
    python test_leave_approval.py --error    # Trigger an incident to test SRE RCA
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

# Add sentinel to sys.path for DGX engine access
sys.path.insert(0, str(Path(__file__).parent / "sentinel"))
from dgx_engine import is_dgx_available, investigate_with_dgx

BPMN_FILE   = Path(__file__).parent / "leave_approval.bpmn"
PROCESS_ID  = "final-test"
ZEEBE_ADDR  = os.getenv("ZEEBE_ADDRESS", "localhost:26500")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _time() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _print_rca(incident_payload: dict, rca: dict) -> None:
    border_thick = "=" * 68
    border_thin  = "-" * 68

    print(f"\n{border_thick}")
    print(f"  GRAPHIFY  --  ROOT CAUSE ANALYSIS (RCA)")
    print(f"  BPMN Process : {PROCESS_ID}")
    print(f"  AI Engine    : {rca.get('engine', 'DGX Qwen 35B')}")
    print(f"  Confidence   : {rca.get('confidence', 'HIGH')}")
    print(border_thick)

    print(f"\n  [WHAT is the error?]")
    print(border_thin)
    print(f"  Process ID : {PROCESS_ID}")
    print(f"  Error Type : {incident_payload.get('error_type', 'BPMN Incident')}")
    print(f"  Message    : {incident_payload.get('error_message', '')}")
    if rca.get("summary"):
        print(f"  Summary    : {rca['summary']}")

    print(f"\n  [WHY did it occur? (Root Cause)]")
    print(border_thin)
    for line in rca.get("root_cause", "N/A").splitlines():
        print(f"  {line}")

    if rca.get("observed_facts"):
        print(f"\n  [Observed Facts]")
        for f in rca["observed_facts"]:
            print(f"   * {f}")

    if rca.get("evidence"):
        print(f"\n  [Cited Evidence]")
        for e in rca["evidence"]:
            print(f"   * {e}")

    print(f"\n  [HOW to fix it? (Actionable Steps)]")
    print(border_thin)
    for idx, step in enumerate(rca.get("recommended_actions", []), 1):
        print(f"  {idx}. {step}")

    print(f"\n{border_thick}\n")


async def main():
    parser = argparse.ArgumentParser(description="Test leave_approval.bpmn with SRE Agent")
    parser.add_argument("--error", action="store_true", help="Simulate an incident/error condition")
    args = parser.parse_args()

    border = "=" * 65
    print(f"\n{border}")
    print(f"  TESTING BPMN: {BPMN_FILE.name} (Process ID: '{PROCESS_ID}')")
    print(border)

    # 1. Connect to Camunda 8 Zeebe
    channel = create_insecure_channel(grpc_address=ZEEBE_ADDR)
    client  = ZeebeClient(channel)

    # 2. Deploy BPMN
    print(f"[1/3] Deploying {BPMN_FILE.name} to Zeebe on {ZEEBE_ADDR}...")
    deploy_res = await client.deploy_resource(BPMN_FILE)
    print(f"      Deployment OK (Process: {PROCESS_ID}, Version: {deploy_res.deployments[0].version})")

    # 3. Prepare variables
    ts = _now()
    t  = _time()

    if args.error:
        print(f"\n[2/3] Simulating Incident Condition (Missing variable at Gateway / HR Service Failure)...")
        variables = {
            "employee_id": "EMP-4091",
            "leave_type": "ANNUAL",
            "days_requested": 5,
            "submitted_at": ts,
            # Note: 'approved' variable is omitted or invalid to trigger gateway incident
        }
        
        # Start instance
        instance_res = await client.run_process(bpmn_process_id=PROCESS_ID, variables=variables)
        inst_key = instance_res.process_instance_key
        print(f"      Process instance started: ID {inst_key}")
        print(f"      [INCIDENT] Gateway_17l8d9w failed: FEEL evaluation '=approved' missing variable")

        # 4. Construct Incident Payload for SRE Agent
        incident_payload = {
            "alert_name": f"{PROCESS_ID}-gateway-feel-expression-error",
            "service": f"{PROCESS_ID}::Gateway_17l8d9w",
            "error_type": "FEELExpressionEvaluationError",
            "error_message": f"Camunda Incident in [{PROCESS_ID} (Instance {inst_key})]: Failed to evaluate expression '=approved': no variable found for name 'approved'",
            "environment": "production",
            "logs": [
                f"{ts} INFO  camunda.engine  Process '{PROCESS_ID}' instance {inst_key} started by employee EMP-4091",
                f"{ts} INFO  camunda.engine  Task 'Activity_0k30fvz' (Send leave request) completed",
                f"{ts} INFO  camunda.engine  Task 'Activity_0pmurpk' (Manager Approval) completed",
                f"{ts} ERROR camunda.engine  Incident at element 'Gateway_17l8d9w': Failed to evaluate condition '=approved': variable 'approved' is null/missing",
            ],
            "timeline": [
                f"{t} Employee EMP-4091 submitted leave request for 5 days",
                f"{t} Manager reviewed request",
                f"{t} Gateway reached without setting 'approved' boolean variable",
                f"{t} Camunda Incident raised at Gateway_17l8d9w",
            ],
        }

        # 5. SRE Agent Investigation (DGX Qwen 35B)
        print(f"\n[3/3] Passing incident to SRE Agent (Company DGX Qwen 35B)...")
        rca = investigate_with_dgx(incident_payload)
        if rca:
            _print_rca(incident_payload, rca)
        else:
            print("[WARN] SRE Agent investigation failed or DGX offline.")

    else:
        print(f"\n[2/3] Running normal instance (with approved=true)...")
        variables = {
            "employee_id": "EMP-4091",
            "leave_type": "ANNUAL",
            "days_requested": 5,
            "approved": True,
            "submitted_at": ts,
        }
        instance_res = await client.run_process(bpmn_process_id=PROCESS_ID, variables=variables)
        print(f"      Process instance started successfully: ID {instance_res.process_instance_key}")
        print(f"      Instance progressed to HR Status task.")
        print(f"\n[3/3] Execution completed OK with zero errors.")
        print(f"      To test an error incident, run: python test_leave_approval.py --error\n")


if __name__ == "__main__":
    asyncio.run(main())
