"""
camunda/worker.py — Camunda 8 Zeebe Job Worker (pyzeebe)
=========================================================
Polls Camunda 8's Zeebe engine for 'rca-investigation' jobs.
When a job arrives, it calls Sentinel → opensre → OpenRouter LLM
and prints the full RCA in terminal:
  - WHAT is the error?
  - WHY did it occur?
  - HOW to fix it?

Start this BEFORE triggering incidents:
    python camunda/worker.py

Environment variables:
    ZEEBE_ADDRESS   gRPC host:port  (default: localhost:26500)
    SENTINEL_URL    Sentinel API    (default: http://localhost:5000)
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import asyncio
import json
import logging
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── pyzeebe ───────────────────────────────────────────────────────────────────
try:
    from pyzeebe import ZeebeWorker, create_insecure_channel
except ImportError:
    print("[ERROR] pyzeebe not installed. Run: pip install pyzeebe")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
ZEEBE_HOST   = os.getenv("ZEEBE_HOST",   "localhost")
ZEEBE_PORT   = int(os.getenv("ZEEBE_PORT",   "26500"))
SENTINEL_URL = os.getenv("SENTINEL_URL", "http://localhost:5000")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("graphify.worker")


# ── Output formatter ──────────────────────────────────────────────────────────

def _print_rca_result(service: str, error_type: str, raw: dict) -> None:
    """
    Print the investigation result in clear What / Why / How format.
    This is shown directly in the worker terminal.
    """
    border_thick = "=" * 68
    border_thin  = "-" * 68

    rca         = raw.get("rca") or {}
    report      = raw.get("raw_output") or rca.get("report", "")
    root_cause  = rca.get("root_cause") or raw.get("root_cause", "")
    status      = raw.get("status", "unknown")
    is_noise    = rca.get("is_noise", False)
    score       = rca.get("validity_score", 0.0)
    incident    = raw.get("incident", "")

    print(f"\n{border_thick}")
    print(f"  GRAPHIFY  --  RCA INVESTIGATION RESULT")
    print(f"  Incident : {incident}")
    print(f"  Service  : {service}")
    print(border_thick)

    if status == "error" or "error" in raw:
        err = raw.get("error", "Investigation failed")
        print(f"\n  [ERROR]  {err}")
        print(f"\n  The investigation encountered an error.")
        print(f"  This usually means: OpenRouter credits exhausted OR Python sandbox blocked.")
        print(f"  Action: Check opensre config or add credits at openrouter.ai/settings/credits")
        print(f"\n{border_thick}\n")
        return

    if is_noise:
        print(f"\n  [NOISE]  This alert is likely a false positive (not a real incident).")
        print(f"\n{border_thick}\n")
        return

    print(f"\n  WHAT is the error?")
    print(border_thin)
    print(f"  Service    : {service}")
    print(f"  Error Type : {error_type}")
    print(f"  Confidence : {int(score * 100)}%")

    print(f"\n  WHY did it occur?")
    print(border_thin)
    if root_cause and root_cause.lower() not in ("unable to determine root cause", ""):
        # Print each line of root cause indented
        for line in root_cause.splitlines():
            print(f"  {line}")
    else:
        print("  OpenSRE could not determine root cause from available data.")
        print("  Possible reasons:")
        print("   1. Python sandbox blocked (add Windows Defender exclusion for C:\\Temp)")
        print("   2. OpenRouter credits exhausted (visit openrouter.ai/settings/credits)")
        print("   3. More context needed (add real logs to the incident)")

    print(f"\n  HOW to fix it?")
    print(border_thin)
    if report and "unable to determine" not in report.lower():
        # Extract recommendations section from report if it exists
        lines = report.splitlines()
        in_fix = False
        for line in lines:
            low = line.lower()
            if any(kw in low for kw in ["recommend", "fix", "solution", "action", "resolve", "remediat", "step"]):
                in_fix = True
            if in_fix or (report and not any(l.strip() for l in lines[:3])):
                print(f"  {line}")
        if not in_fix:
            # Print the full report if no fix section found
            for line in lines:
                print(f"  {line}")
    else:
        print("  [Manual steps while AI investigation resolves:]")
        print(f"  1. Check logs for service '{service}' immediately")
        print(f"  2. Verify infrastructure dependencies (DB, network, disk)")
        print(f"  3. Roll back last deployment if error started recently")
        print(f"  4. Escalate to on-call team if not resolved in 15 min")

    print(f"\n{border_thick}\n")


def _call_sentinel(job_variables: dict) -> dict:
    """POST to Sentinel /investigate/from-error and poll for result."""
    service       = job_variables.get("service",       "unknown-service")
    error_type    = job_variables.get("error_type",    "Unknown Error")
    error_message = job_variables.get("error_message", "")
    environment   = job_variables.get("environment",   "production")
    logs_raw      = job_variables.get("logs",          "[]")

    try:
        logs = json.loads(logs_raw) if isinstance(logs_raw, str) else (logs_raw or [])
    except (json.JSONDecodeError, TypeError):
        logs = [logs_raw] if logs_raw else []

    payload = {
        "service":       service,
        "error_type":    error_type,
        "error_message": error_message,
        "environment":   environment,
        "logs":          logs,
    }

    logger.info(f"[rca-investigation] {service} - {error_type}")

    # POST to Sentinel (returns 202 immediately with investigation_id)
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        f"{SENTINEL_URL}/investigate/from-error",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        accepted = json.loads(resp.read().decode())

    inv_id   = accepted.get("investigation_id", "")
    incident = accepted.get("incident", "")
    logger.info(f"[rca-investigation] started id={inv_id} incident={incident}")

    # Poll for result (up to 5 minutes, every 10 seconds)
    poll_url = f"{SENTINEL_URL}/investigations/{inv_id}"
    deadline = time.monotonic() + 300

    while time.monotonic() < deadline:
        time.sleep(10)
        try:
            poll_req = urllib.request.Request(poll_url, method="GET")
            with urllib.request.urlopen(poll_req, timeout=10) as r:
                result = json.loads(r.read().decode())
            status = result.get("status", "")
            if status == "running":
                logger.info(f"[rca-investigation] id={inv_id} still running...")
                continue
            # Done (success or error)
            return {"service": service, "error_type": error_type, "result": result}
        except Exception as poll_err:
            logger.warning(f"Poll error: {poll_err}")
            continue

    logger.warning(f"[rca-investigation] id={inv_id} timed out after 5 minutes")
    return {"service": service, "error_type": error_type, "result": {"status": "timeout"}}


# ── Zeebe Job Handler ─────────────────────────────────────────────────────────

async def main() -> None:
    border = "=" * 60
    print(f"\n{border}")
    print("  GRAPHIFY  --  Camunda 8 Zeebe Worker")
    print(border)
    print(f"  Zeebe    : {ZEEBE_HOST}:{ZEEBE_PORT}")
    print(f"  Sentinel : {SENTINEL_URL}")
    print(f"  Job Type : rca-investigation")
    print(border + "\n")
    print("  Polling for incident jobs... (Ctrl+C to stop)\n")

    channel = create_insecure_channel(grpc_address=f"{ZEEBE_HOST}:{ZEEBE_PORT}")
    worker  = ZeebeWorker(channel)

    @worker.task(task_type="rca-investigation", timeout_ms=360_000, max_jobs_to_activate=5)
    async def handle_rca_investigation(**kwargs):
        """
        Zeebe job handler for 'rca-investigation' task type.
        kwargs contains all process variables set when the instance was created.
        Returns output variables that Zeebe maps back to the process.
        """
        service    = kwargs.get("service",       "unknown-service")
        error_type = kwargs.get("error_type",    "Unknown Error")

        logger.info(f"[JOB] rca-investigation: {service} - {error_type}")

        try:
            outcome = _call_sentinel(kwargs)
            result  = outcome.get("result", {})
            _print_rca_result(service, error_type, result)

            # Return output variables to Zeebe process
            return {
                "rca_result":   json.dumps(result),
                "rca_status":   result.get("status", "unknown"),
                "rca_incident": result.get("incident", ""),
            }

        except Exception as exc:
            logger.error(f"[JOB] handler error: {exc}")
            _print_rca_result(service, error_type, {"status": "error", "error": str(exc)})
            raise   # Let Zeebe retry

    await worker.work()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  [Worker] Stopped.\n")
