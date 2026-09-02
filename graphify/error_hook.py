"""
error_hook.py — Graphify Auto-Error Interceptor
================================================
Import this into ANY Python application to auto-send errors to the
Sentinel RCA investigation pipeline the moment an exception occurs.

Usage (2 lines in your app):
    from error_hook import GraphifyHook
    GraphifyHook.install()

That's it. Now any unhandled exception in your app will:
  1. Be caught automatically
  2. Sent to Sentinel FastAPI → opensre investigate → RCA in terminal
  3. The original exception still propagates normally (app doesn't break)
"""
import sys
import os
import json
import logging
import platform
import traceback
import threading
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

logger = logging.getLogger("graphify.hook")

# ── Config (reads from env or uses defaults) ───────────────────────────────────
SENTINEL_URL  = os.getenv("SENTINEL_URL",  "http://localhost:5000")
SERVICE_NAME  = os.getenv("SERVICE_NAME",  "unknown-service")
ENVIRONMENT   = os.getenv("ENVIRONMENT",   "development")
GRAPHIFY_ROOT = Path(__file__).parent


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _send_to_sentinel(payload: dict) -> None:
    """Send the error event to Sentinel's /investigate/from-error endpoint."""
    try:
        import urllib.request
        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            f"{SENTINEL_URL}/investigate/from-error",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            logger.info(f"[Graphify] RCA started for {payload['service']}: {result.get('status')}")
    except Exception as e:
        logger.warning(f"[Graphify] Could not reach Sentinel ({SENTINEL_URL}): {e}")
        # Fallback: save to incoming/ for watcher to pick up
        _save_to_incoming(payload)


def _save_to_incoming(payload: dict) -> None:
    """Fallback: save incident JSON to incidents/incoming/ for watcher.py."""
    try:
        incoming = GRAPHIFY_ROOT / "incidents" / "incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        ts   = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        name = payload.get("service", "unknown").replace(" ", "-")
        path = incoming / f"{name}-{ts}.json"
        incident = {
            "alert_name":    f"{name}-auto-error",
            "service":       payload["service"],
            "environment":   payload.get("environment", ENVIRONMENT),
            "error":         payload.get("error_type",  "Exception"),
            "error_message": payload.get("error_message", ""),
            "logs":          payload.get("logs", []),
            "timeline":      payload.get("timeline", []),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(incident, f, indent=2)
        logger.info(f"[Graphify] Incident saved to {path.name} (watcher will pick up)")
    except Exception as e:
        logger.error(f"[Graphify] Could not save incident: {e}")


def _build_payload(exc_type, exc_value, exc_tb, service: str, env: str) -> dict:
    """Build the error payload from a Python exception."""
    tb_lines  = traceback.format_exception(exc_type, exc_value, exc_tb)
    tb_str    = "".join(tb_lines).strip()
    ts        = _now()

    # Extract the most relevant frames (last 5 lines of traceback)
    tb_short  = tb_lines[-1].strip() if tb_lines else str(exc_value)
    log_lines = [
        f"{ts} ERROR {service}  {exc_type.__name__}: {exc_value}",
        f"{ts} TRACE {service}  {tb_short}",
    ]

    return {
        "service":       service,
        "error_type":    exc_type.__name__,
        "error_message": str(exc_value),
        "environment":   env,
        "logs":          log_lines,
        "timeline":      [
            f"{datetime.now(timezone.utc).strftime('%H:%M:%S')} {exc_type.__name__} raised in {service}",
        ],
    }


class GraphifyHook:
    """
    Installs a global exception hook that forwards all unhandled exceptions
    to the Graphify/Sentinel RCA pipeline automatically.
    """

    _original_excepthook: Callable | None = None
    _installed: bool = False

    @classmethod
    def install(
        cls,
        service:     str = SERVICE_NAME,
        environment: str = ENVIRONMENT,
        async_mode:  bool = True,
    ) -> None:
        """
        Install the global exception hook.

        Args:
            service:     Name of your service/app (e.g. 'payment-service')
            environment: 'development', 'staging', or 'production'
            async_mode:  If True, sends to Sentinel in a background thread
                         so it doesn't block your app's crash output.
        """
        if cls._installed:
            logger.warning("[Graphify] Hook already installed.")
            return

        cls._original_excepthook = sys.excepthook

        def _hook(exc_type, exc_value, exc_tb):
            # Always print the original traceback first
            if cls._original_excepthook:
                cls._original_excepthook(exc_type, exc_value, exc_tb)

            # Skip KeyboardInterrupt and SystemExit
            if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
                return

            border = "=" * 60
            print(f"\n{border}")
            print(f"  [Graphify] Error detected in '{service}'")
            print(f"  Auto-triggering RCA investigation...")
            print(f"{border}\n")

            payload = _build_payload(exc_type, exc_value, exc_tb, service, environment)

            if async_mode:
                thread = threading.Thread(
                    target=_send_to_sentinel,
                    args=(payload,),
                    # daemon=False so this thread survives the app crash
                    # and completes the Sentinel request before process exits
                    daemon=False,
                    name="graphify-rca",
                )
                thread.start()
                # Give it up to 10 seconds to send before process exits
                thread.join(timeout=10)
            else:
                _send_to_sentinel(payload)

        sys.excepthook = _hook
        cls._installed = True

        print(f"[Graphify] Hook installed for service='{service}' env='{environment}'")
        print(f"[Graphify] Errors will auto-trigger RCA at: {SENTINEL_URL}")

    @classmethod
    def uninstall(cls) -> None:
        """Remove the hook and restore original excepthook."""
        if cls._original_excepthook:
            sys.excepthook = cls._original_excepthook
            cls._installed = False
            logger.info("[Graphify] Hook uninstalled.")

    @classmethod
    def trigger_manual(cls, error_type: str, error_message: str,
                        service: str = SERVICE_NAME,
                        environment: str = ENVIRONMENT,
                        logs: list[str] | None = None) -> None:
        """
        Manually trigger an RCA investigation without raising an exception.
        Useful for caught exceptions you still want to investigate.

        Example:
            try:
                db.connect()
            except ConnectionError as e:
                GraphifyHook.trigger_manual(
                    error_type="ConnectionError",
                    error_message=str(e),
                    service="payment-service",
                )
        """
        ts = _now()
        payload = {
            "service":       service,
            "error_type":    error_type,
            "error_message": error_message,
            "environment":   environment,
            "logs": logs or [f"{ts} ERROR {service}  {error_type}: {error_message}"],
            "timeline": [
                f"{datetime.now(timezone.utc).strftime('%H:%M:%S')} {error_type} in {service}",
            ],
        }
        _send_to_sentinel(payload)
