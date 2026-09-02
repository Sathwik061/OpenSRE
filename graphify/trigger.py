#!/usr/bin/env python3
"""
trigger.py — Graphify Interactive RCA Trigger
=============================================
Run it: python trigger.py

Pick an incident key from the menu → system auto-generates a fresh incident
(all timestamps = right now) → runs Root Cause Analysis → prints in terminal:
  - WHAT is the error?
  - WHY did it occur?
  - HOW to fix it?

Supports:
  1. Company DGX Server (Qwen 35B on localhost:8000 via SSH tunnel) -> Preferred & Free!
  2. OpenSRE CLI (`opensre investigate`) -> Fallback

No hardcoded dates or timestamps anywhere. Everything is dynamic.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from incident_registry import INCIDENT_REGISTRY, build_incident, list_keys

# Add sentinel to sys.path for DGX engine access
sys.path.insert(0, str(Path(__file__).parent / "sentinel"))
try:
    from dgx_engine import is_dgx_available, investigate_with_dgx
except ImportError:
    def is_dgx_available(): return False
    def investigate_with_dgx(_): return None

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
HISTORY_DIR   = BASE_DIR / "incidents" / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    """Replace characters invalid in Windows filenames."""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "-")
    return name


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _print_formatted_rca(incident: dict, rca_data: dict, engine_name: str) -> None:
    """Print clean What / Why / How format to terminal."""
    border_thick = "=" * 68
    border_thin  = "-" * 68

    summary    = rca_data.get("summary", "")
    root_cause = rca_data.get("root_cause", "Unable to determine root cause")
    confidence = rca_data.get("confidence", "HIGH")
    facts      = rca_data.get("observed_facts", [])
    evidence   = rca_data.get("evidence", [])
    recs       = rca_data.get("recommended_actions", [])

    print(f"\n{border_thick}")
    print(f"  GRAPHIFY  --  ROOT CAUSE ANALYSIS (RCA)")
    print(f"  Engine     : {engine_name}")
    print(f"  Alert      : {incident['alert_name']}")
    print(f"  Service    : {incident['service']}")
    print(f"  Confidence : {confidence}")
    print(border_thick)

    err_type = incident.get('error', 'Unknown Error')
    if isinstance(err_type, dict):
        err_type = err_type.get('type', 'Unknown Error')
    err_msg = incident.get('error_message', '')
    if not err_msg and isinstance(incident.get('error'), dict):
        err_msg = incident['error'].get('message', '')

    print(f"\n  [WHAT is the error?]")
    print(border_thin)
    print(f"  Service    : {incident['service']}")
    print(f"  Error Type : {err_type}")
    if err_msg:
        print(f"  Message    : {err_msg}")
    if summary:
        print(f"  Summary    : {summary}")

    print(f"\n  [WHY did it occur? (Root Cause)]")
    print(border_thin)
    for line in root_cause.splitlines():
        print(f"  {line}")

    if facts:
        print(f"\n  [Observed Facts]")
        for f in facts:
            print(f"   * {f}")

    if evidence:
        print(f"\n  [Cited Evidence]")
        for e in evidence:
            print(f"   * {e}")

    print(f"\n  [HOW to fix it? (Actionable Steps)]")
    print(border_thin)
    if recs:
        for idx, step in enumerate(recs, 1):
            print(f"  {idx}. {step}")
    else:
        print("  1. Verify service connectivity and configuration")
        print("  2. Check upstream database and dependent microservices")
        print("  3. Review recent deployments or infrastructure changes")

    print(f"\n{border_thick}\n")


def run_investigation(incident: dict) -> int:
    """
    Saves incident to history and performs RCA using DGX or OpenSRE CLI.
    """
    filename      = f"{_safe_filename(incident['alert_name'])}-{_timestamp()}.json"
    incident_path = HISTORY_DIR / filename

    with open(incident_path, "w", encoding="utf-8") as f:
        json.dump(incident, f, indent=2)

    border = "=" * 65
    print(f"\n{border}")
    print("  [RCA]  GRAPHIFY -- SRE RCA INVESTIGATION")
    print(border)
    print(f"  Alert     : {incident['alert_name']}")
    print(f"  Service   : {incident['service']}")
    err_display = incident.get('error', 'Unknown Error')
    if isinstance(err_display, dict):
        err_display = err_display.get('type', 'Unknown Error')
    print(f"  Error     : {err_display}")
    print(f"  Env       : {incident['environment']}")
    print(f"  Timestamp : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Saved to  : {incident_path.name}")
    print(f"{border}\n")

    # ── Option 1: Company DGX Server (Free, unlimited, high accuracy) ─────────
    if is_dgx_available():
        print("  [Engine] Connected to Company DGX Server (Qwen 35B vLLM on :8000)")
        print("  Running deep Root Cause Analysis on GPU...")
        dgx_rca = investigate_with_dgx(incident)
        if dgx_rca:
            _print_formatted_rca(incident, dgx_rca, dgx_rca.get("engine", "DGX (Qwen 35B)"))
            return 0
        print("  [WARN] DGX query failed, falling back to OpenSRE CLI...\n")

    # ── Option 2: Fallback to OpenSRE CLI ──────────────────────────────────────
    print("  [Engine] Running OpenSRE CLI (`opensre investigate`)...")
    env = {**os.environ, "TEMP": "C:\\Temp", "TMP": "C:\\Temp"}
    proc = subprocess.run(
        ["opensre", "investigate", "-i", str(incident_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    if proc.stdout:
        print(proc.stdout)
    if proc.stderr and proc.returncode != 0:
        print(proc.stderr)
    return proc.returncode


# ── Menu ──────────────────────────────────────────────────────────────────────

def show_menu() -> None:
    dgx_status = "[ONLINE]" if is_dgx_available() else "[OFFLINE - Run SSH Tunnel]"

    border = "=" * 65
    print(f"\n{border}")
    print("  GRAPHIFY  --  SRE RCA Investigation System")
    print(f"  AI Engine  : Company DGX vLLM (Qwen 35B) {dgx_status}")
    print("  Select an incident key to auto-generate and investigate")
    print(border)
    print()
    for entry in list_keys():
        print(f"  [{entry['number']}]  {entry['key']}")
        print(f"        {entry['description']}")
        print()
    print("  [f]  Load from custom JSON file")
    print("  [r]  Refresh / re-run last incident")
    print("  [q]  Quit")
    print(f"{border}")


def interactive_loop() -> None:
    last_incident: dict | None = None

    while True:
        show_menu()

        try:
            choice = input("\n  > Enter incident key: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Exiting Graphify. Goodbye!\n")
            break

        print()

        if choice in ("q", "quit", "exit"):
            print("  Exiting Graphify. Goodbye!\n")
            break

        elif choice == "f":
            try:
                path_str = input("  Path to JSON file: ").strip().strip('"')
                if not path_str:
                    print("  [INFO] No file path provided.\n")
                    continue
                path = Path(path_str)
                if not path.is_file():
                    print(f"\n  [ERROR] File not found: {path}\n")
                    continue
                with open(path, encoding="utf-8") as fp:
                    incident = json.load(fp)
                last_incident = incident
                run_investigation(incident)
            except Exception as exc:
                print(f"\n  [ERROR] {exc}\n")

        elif choice == "r":
            if last_incident is None:
                print("  [INFO] No previous incident to re-run.\n")
                continue
            key = last_incident.get("alert_name", "")
            rebuilt = build_incident(key)
            incident = rebuilt if rebuilt else last_incident
            run_investigation(incident)

        else:
            incident = build_incident(choice)
            if incident is None:
                print(f"  [ERROR] Unknown key '{choice}'.")
                print(f"          Choose 1-{len(INCIDENT_REGISTRY)}, a key name, 'f', 'r', or 'q'.\n")
                continue
            last_incident = incident
            run_investigation(incident)

        try:
            input("\n  [Press Enter to return to menu, or Ctrl+C to quit]")
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Exiting Graphify. Goodbye!\n")
            break


def main() -> None:
    p = argparse.ArgumentParser(
        description="Graphify -- Interactive OpenSRE RCA Trigger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--key",      "-k", help="Incident key number or name from registry")
    p.add_argument("--incident", "-i", help="Path to an existing incident JSON file")
    p.add_argument("--list",     "-l", action="store_true", help="List all incident keys and exit")
    args = p.parse_args()

    if args.list:
        show_menu()
        return

    if args.incident:
        path = Path(args.incident)
        if not path.exists():
            print(f"[ERROR] File not found: {path}")
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            incident = json.load(f)
        sys.exit(run_investigation(incident))

    if args.key:
        incident = build_incident(args.key)
        if incident is None:
            print(f"[ERROR] Unknown key: '{args.key}'. Run with --list to see options.")
            sys.exit(1)
        sys.exit(run_investigation(incident))

    interactive_loop()


if __name__ == "__main__":
    main()
