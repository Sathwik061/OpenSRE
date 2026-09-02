"""
investigator.py
===============
Runs Root Cause Analysis on IncidentAlerts.

Execution Strategy:
1. Checks if Company DGX vLLM (localhost:8000 / Qwen 35B) is active via SSH tunnel.
   -> If active: uses DGX vLLM directly (100% free, no credit limits, verified What/Why/How).
2. Otherwise: falls back to `opensre investigate -i <file>`.
"""
import os
import subprocess
import json
import logging
import platform
from pathlib import Path
from datetime import datetime, timezone

from models import IncidentAlert, InvestigationResult
from dgx_engine import is_dgx_available, investigate_with_dgx

logger = logging.getLogger(__name__)

# Where incident JSON files are saved before being passed to opensre
INCIDENTS_DIR = Path(__file__).parent.parent / "incidents" / "history"
INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)


def _make_safe_filename(name: str) -> str:
    """Replace characters that are invalid in Windows filenames."""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "-")
    return name


def _build_env() -> dict:
    """
    Build the subprocess environment.
    On Windows, force TEMP/TMP to C:\\Temp to prevent PyInstaller from
    failing when the username contains a space.
    """
    env = os.environ.copy()
    if platform.system() == "Windows":
        safe_temp = "C:\\Temp"
        Path(safe_temp).mkdir(exist_ok=True)
        env["TEMP"] = safe_temp
        env["TMP"]  = safe_temp
    return env


def _check_memory_warning() -> None:
    """Log a warning if available RAM is critically low."""
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength",                ctypes.c_ulong),
                ("dwMemoryLoad",            ctypes.c_ulong),
                ("ullTotalPhys",            ctypes.c_ulonglong),
                ("ullAvailPhys",            ctypes.c_ulonglong),
                ("ullTotalPageFile",        ctypes.c_ulonglong),
                ("ullAvailPageFile",        ctypes.c_ulonglong),
                ("ullTotalVirtual",         ctypes.c_ulonglong),
                ("ullAvailVirtual",         ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual",ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        avail_gb = stat.ullAvailPhys / (1024 ** 3)
        if avail_gb < 1.0:
            logger.warning(
                f"LOW MEMORY: Only {avail_gb:.1f} GB available. "
                "Close unnecessary apps to free RAM."
            )
    except Exception:
        pass


def run_investigation(incident: IncidentAlert) -> InvestigationResult:
    """
    Persists the incident as a JSON file, then runs RCA.
    Prefers DGX (company Qwen vLLM) if available; falls back to OpenSRE CLI.
    """
    _check_memory_warning()

    ts        = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = _make_safe_filename(incident.alert_name)
    incident_file = INCIDENTS_DIR / f"{safe_name}-{ts}.json"

    # Write incident to disk for history
    with open(incident_file, "w", encoding="utf-8") as f:
        json.dump(incident.model_dump(), f, indent=2)

    logger.info(f"Investigating: {incident.alert_name}")
    logger.info(f"Incident file: {incident_file}")

    # ── Option 1: Company DGX Server (vLLM / Qwen 3.6 35B) ────────────────────
    if is_dgx_available():
        logger.info("[ENGINE] Active: Company DGX Server (Qwen 35B vLLM on :8000)")
        dgx_result = investigate_with_dgx(incident.model_dump())
        if dgx_result:
            return InvestigationResult(
                status="success",
                incident=incident.alert_name,
                rca=dgx_result,
                incident_file=str(incident_file),
            )
        logger.warning("[ENGINE] DGX query failed, falling back to OpenSRE CLI...")

    # ── Option 2: Fallback to OpenSRE CLI ──────────────────────────────────────
    logger.info("[ENGINE] Using OpenSRE CLI (`opensre investigate`)")
    try:
        proc = subprocess.run(
            ["opensre", "investigate", "-i", str(incident_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Force UTF-8 on Windows
            encoding="utf-8",
            errors="replace",
            timeout=300,
            env=_build_env(),
        )

        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()

        if proc.returncode != 0:
            logger.error(f"opensre exited {proc.returncode}: {stderr}")
            return InvestigationResult(
                status="error",
                incident=incident.alert_name,
                raw_output=stderr or stdout,
                incident_file=str(incident_file),
                error=stderr or f"opensre exited with code {proc.returncode}",
            )

        # Try to parse JSON output; fall back to raw text
        try:
            rca = json.loads(stdout)
            return InvestigationResult(
                status="success",
                incident=incident.alert_name,
                rca=rca,
                incident_file=str(incident_file),
            )
        except json.JSONDecodeError:
            return InvestigationResult(
                status="success",
                incident=incident.alert_name,
                raw_output=stdout,
                incident_file=str(incident_file),
            )

    except subprocess.TimeoutExpired:
        logger.error("opensre investigation timed out after 5 minutes")
        return InvestigationResult(
            status="timeout",
            incident=incident.alert_name,
            incident_file=str(incident_file),
            error="Investigation timed out after 5 minutes",
        )

    except FileNotFoundError:
        logger.error("'opensre' not found — is OpenSRE installed and on PATH?")
        return InvestigationResult(
            status="error",
            incident=incident.alert_name,
            incident_file=str(incident_file),
            error="'opensre' command not found.",
        )
