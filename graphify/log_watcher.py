"""
log_watcher.py — Graphify Log File Auto-Watcher
================================================
Watches ANY log file on your system for ERROR lines.
When it finds one, it automatically triggers an RCA investigation.

Usage:
    python log_watcher.py --log path/to/app.log --service my-service

Or watch multiple files:
    python log_watcher.py --log app.log --log worker.log --service payment-service

What it does:
  1. Tails the log file (like 'tail -f')
  2. Detects lines containing ERROR, CRITICAL, EXCEPTION, FATAL
  3. Batches nearby error lines together (within 5 seconds)
  4. Sends to Sentinel /investigate/from-error
  5. RCA investigation starts automatically
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import argparse
import json
import os
import re
import time
import threading
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
SENTINEL_URL = os.getenv("SENTINEL_URL", "http://localhost:5000")
ENVIRONMENT  = os.getenv("ENVIRONMENT",  "development")

# Patterns that indicate an error in log lines
ERROR_PATTERNS = re.compile(
    r'\b(ERROR|CRITICAL|EXCEPTION|FATAL|TRACEBACK|500|connection refused|'
    r'out of memory|oomkilled|disk full|timeout|certificate expired|'
    r'connection reset|econnrefused|panic|segfault)\b',
    re.IGNORECASE,
)

# How long to wait and collect related error lines before sending (seconds)
BATCH_WINDOW_SECONDS = 5


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _time() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _send_to_sentinel(service: str, error_lines: list[str], environment: str) -> None:
    """Send collected error lines to Sentinel for RCA investigation."""
    if not error_lines:
        return

    first_line = error_lines[0]

    # Extract error type from the log line
    error_type = "Unknown Error"
    for pattern in ["ERROR", "CRITICAL", "EXCEPTION", "FATAL"]:
        if pattern in first_line.upper():
            error_type = pattern
            break

    # Extract error message (everything after the log level keyword)
    msg_match = re.search(r'(?:ERROR|CRITICAL|EXCEPTION|FATAL)\s+\S*\s+(.*)', first_line, re.IGNORECASE)
    error_message = msg_match.group(1).strip() if msg_match else first_line.strip()

    payload = {
        "service":       service,
        "error_type":    error_type,
        "error_message": error_message[:200],   # trim long messages
        "environment":   environment,
        "logs":          error_lines[:20],       # send max 20 lines
        "timeline": [
            f"{_time()} {error_type} detected in {service}",
            f"{_time()} Auto-triggered RCA investigation",
        ],
    }

    border = "=" * 60
    print(f"\n{border}")
    print(f"  [LogWatcher] ERROR detected in '{service}'!")
    print(f"  Sending to Sentinel for RCA...")
    print(f"  Error: {error_message[:80]}")
    print(f"{border}\n")

    try:
        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            f"{SENTINEL_URL}/investigate/from-error",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            print(f"  [LogWatcher] RCA started: status={result.get('status')} incident={result.get('incident')}\n")
    except Exception as e:
        print(f"  [LogWatcher] Could not reach Sentinel: {e}")
        print(f"  [LogWatcher] Saving to incidents/incoming/ for watcher.py\n")
        # Fallback to file drop
        incoming = Path(__file__).parent / "incidents" / "incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        incident = {
            "alert_name":    f"{service}-log-error-{ts}",
            "service":       service,
            "environment":   environment,
            "error":         error_type,
            "error_message": error_message,
            "logs":          error_lines[:20],
            "timeline":      payload["timeline"],
        }
        path = incoming / f"{service}-{ts}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(incident, f, indent=2)


class LogFileTailer:
    """
    Tails a log file and triggers RCA when error patterns are detected.
    Buffers error lines for BATCH_WINDOW_SECONDS before sending.
    """

    def __init__(self, log_path: Path, service: str, environment: str):
        self.log_path   = log_path
        self.service    = service
        self.environment = environment
        self._buffer: list[str] = []
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def _flush(self) -> None:
        """Send buffered error lines to Sentinel."""
        with self._lock:
            lines = list(self._buffer)
            self._buffer.clear()
            self._timer = None
        if lines:
            _send_to_sentinel(self.service, lines, self.environment)

    def _schedule_flush(self) -> None:
        """Start or reset the batch timer."""
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(BATCH_WINDOW_SECONDS, self._flush)
        self._timer.daemon = True
        self._timer.start()

    def process_line(self, line: str) -> None:
        """Check if line is an error; buffer it if so."""
        line = line.rstrip()
        if not line:
            return
        if ERROR_PATTERNS.search(line):
            with self._lock:
                self._buffer.append(line)
            self._schedule_flush()

    def tail(self) -> None:
        """Tail the log file, processing new lines as they appear."""
        print(f"  [LogWatcher] Watching: {self.log_path}")

        # Open and seek to end (don't replay old logs)
        with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(0, 2)  # seek to end
            while True:
                line = f.readline()
                if line:
                    self.process_line(line)
                else:
                    time.sleep(0.2)

    def tail_thread(self) -> threading.Thread:
        t = threading.Thread(target=self.tail, daemon=True, name=f"tail-{self.log_path.name}")
        t.start()
        return t


# ── Demo log generator (for testing without a real app) ──────────────────────

def generate_demo_log(log_path: Path, service: str) -> None:
    """
    Generate a demo log file with a simulated error after 5 seconds.
    Used for testing the log watcher without a real application.
    """
    print(f"  [Demo] Generating demo log at: {log_path}")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def _write():
        with open(log_path, "a", encoding="utf-8") as f:
            # Normal lines first
            for i in range(3):
                f.write(f"{_now()} INFO  {service}  Request processed OK (req-{i})\n")
                f.flush()
                time.sleep(1)
            # Then an error (this will trigger the watcher)
            time.sleep(2)
            f.write(f"{_now()} ERROR {service}  connection refused to postgres:5432\n")
            f.write(f"{_now()} ERROR {service}  database restarting unexpectedly\n")
            f.flush()
            print(f"\n  [Demo] ERROR written to log → RCA should trigger automatically!\n")

    t = threading.Thread(target=_write, daemon=True)
    t.start()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description="Graphify Log Watcher — auto-trigger RCA on log errors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python log_watcher.py --log app.log --service payment-service
  python log_watcher.py --log app.log --log worker.log --service my-app
  python log_watcher.py --demo --service demo-service
        """,
    )
    p.add_argument("--log",         "-l", action="append", help="Path to log file to watch (can repeat)")
    p.add_argument("--service",     "-s", default=SERVICE_NAME, help="Service name for RCA context")
    p.add_argument("--environment", "-e", default=ENVIRONMENT,  help="Environment (dev/staging/prod)")
    p.add_argument("--demo",               action="store_true",   help="Run a demo with generated log errors")
    args = p.parse_args()

    border = "=" * 60
    print(f"\n{border}")
    print("  GRAPHIFY LOG WATCHER  --  Auto-trigger RCA on Errors")
    print(border)
    print(f"  Sentinel  : {SENTINEL_URL}")
    print(f"  Service   : {args.service}")
    print(f"  Env       : {args.environment}")
    print(border)
    print()

    if args.demo:
        demo_log = Path("logs") / "demo-app.log"
        generate_demo_log(demo_log, args.service)
        tailers = [LogFileTailer(demo_log, args.service, args.environment)]
    elif args.log:
        tailers = [LogFileTailer(Path(lp), args.service, args.environment) for lp in args.log]
    else:
        print("  Usage: python log_watcher.py --log <file> --service <name>")
        print("         python log_watcher.py --demo --service my-service")
        sys.exit(1)

    # Start all tailers
    threads = [t.tail_thread() for t in tailers]

    print("  Watching for errors... (Ctrl+C to stop)\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n  [LogWatcher] Stopped.\n")


if __name__ == "__main__":
    main()
