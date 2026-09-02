"""
watcher.py — Graphify Auto-trigger File Watcher
================================================
Watches the incidents/incoming/ folder.
When ANY .json file is dropped into it:
  1. Reads the file
  2. Auto-runs: opensre investigate -i <file>
  3. Saves result to incidents/history/
  4. Moves processed file to incidents/processed/

Usage:
  python watcher.py

Then drop any incident JSON file into:  incidents/incoming/
"""
import sys
import os
os.environ["PYTHONUNBUFFERED"] = "1"  # Ensure real-time stdout flushing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
except ImportError:
    print("[ERROR] watchdog not installed. Run: pip install watchdog")
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
INCOMING_DIR   = BASE_DIR / "incidents" / "incoming"
HISTORY_DIR    = BASE_DIR / "incidents" / "history"
PROCESSED_DIR  = BASE_DIR / "incidents" / "processed"

for d in (INCOMING_DIR, HISTORY_DIR, PROCESSED_DIR):
    d.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _safe(name: str) -> str:
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "-")
    return name


def run_investigation(incident_path: Path) -> None:
    """Run opensre investigate on the given file and display the RCA."""
    # Validate JSON
    try:
        with open(incident_path, encoding="utf-8") as f:
            incident = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"\n[WATCHER] Invalid JSON in {incident_path.name}: {exc}")
        return

    alert_name = incident.get("alert_name", incident_path.stem)
    service    = incident.get("service",    "unknown-service")
    ts         = _timestamp()

    # Save a timestamped copy to history
    history_file = HISTORY_DIR / f"{_safe(alert_name)}-{ts}.json"
    shutil.copy2(incident_path, history_file)

    border = "=" * 65
    print(f"\n{border}")
    print("  [AUTO-RCA]  GRAPHIFY WATCHER -- New incident detected!")
    print(border)
    print(f"  File      : {incident_path.name}")
    print(f"  Alert     : {alert_name}")
    print(f"  Service   : {service}")
    print(f"  Detected  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Saved to  : {history_file.name}")
    print(f"{border}\n")

    # ── AI Engine: Company DGX Server (Qwen 35B GPU) ─────────────────────────
    # The opensre CLI is routed to your company's NVIDIA DGX server via the
    # SSH tunnel you keep open:  ssh -L 8000:localhost:8000 truviq_domain@192.168.0.143
    #
    # DGX endpoint : http://localhost:8000/v1  (OpenAI-compatible vLLM API)
    # Model        : nvidia/Qwen3.6-35B-A3B-NVFP4
    #
    # NO OpenRouter / NO cloud credits needed — all inference runs on-prem GPU.
    env = {
        **os.environ,
        "TEMP": "C:\\Temp",
        "TMP": "C:\\Temp",
        # Force opensre to use DGX (custom OpenAI-compatible endpoint)
        "LLM_PROVIDER":           "custom-openai",
        "CUSTOM_OPENAI_API_KEY":  "dummy-not-needed-local-vllm",
        "CUSTOM_OPENAI_API_BASE": "http://localhost:8000/v1",
        "CUSTOM_OPENAI_MODEL":    "nvidia/Qwen3.6-35B-A3B-NVFP4",
    }
    try:
        result = subprocess.run(
            ["opensre", "--no-interactive", "-y", "investigate", "-i", str(history_file)],
            text=True,
            stdin=subprocess.DEVNULL,
            env=env,
            timeout=300,   # 5-minute safety timeout
        )
        if result.returncode != 0:
            print(f"[WATCHER] opensre exited with code {result.returncode}")
    except subprocess.TimeoutExpired:
        print("[WATCHER] ERROR: opensre investigate timed out after 5 minutes.")
    except FileNotFoundError:
        print("[WATCHER] ERROR: 'opensre' not found on PATH. Run: pip install opensre")

    # Move original to processed/
    processed_dest = PROCESSED_DIR / f"{_safe(alert_name)}-{ts}{incident_path.suffix}"
    shutil.move(str(incident_path), str(processed_dest))
    print(f"\n[WATCHER] Processed file moved to: {processed_dest.name}\n")


# ── Watchdog event handler ────────────────────────────────────────────────────

class IncidentHandler(FileSystemEventHandler):
    """Triggers an RCA investigation whenever a new JSON file appears."""

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() != ".json":
            return

        # Small delay to ensure the file is fully written before reading
        time.sleep(0.5)

        print(f"\n[WATCHER] New incident file detected: {path.name}")
        run_investigation(path)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    border = "=" * 65
    print(f"\n{border}")
    print("  GRAPHIFY WATCHER  --  Auto-Trigger RCA System")
    print(border)
    print(f"  Watching: {INCOMING_DIR}")
    print()
    print("  DROP any incident .json file into the folder above.")
    print("  The investigation will start automatically.")
    print()
    print("  History  : incidents/history/")
    print("  Processed: incidents/processed/")
    print(f"{border}")
    print("\n  Waiting for incidents... (Ctrl+C to stop)\n")

    handler  = IncidentHandler()
    observer = Observer()
    observer.schedule(handler, str(INCOMING_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n[WATCHER] Stopped. Goodbye!\n")

    observer.join()


if __name__ == "__main__":
    main()
