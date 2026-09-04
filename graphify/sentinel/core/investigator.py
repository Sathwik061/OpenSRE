"""
sentinel/core/investigator.py
=============================
Orchestrates Root Cause Analysis on IncidentAlerts.
Prefers local DGX vLLM (localhost:8000), falls back to OpenSRE CLI.
"""

import os
import subprocess
import json
import logging
import platform
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from sentinel.core.models import IncidentAlert, InvestigationResult

logger = logging.getLogger("sentinel.core.investigator")

INCIDENTS_DIR = Path(__file__).resolve().parent.parent.parent / "incidents" / "history"
INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)


def _make_safe_filename(name: str) -> str:
    """Replace characters that are invalid in Windows filenames."""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "-")
    return name


def _build_env() -> dict:
    """Build subprocess environment with safe temp dir on Windows."""
    env = os.environ.copy()
    if platform.system() == "Windows":
        safe_temp = "C:\\Temp"
        Path(safe_temp).mkdir(exist_ok=True)
        env["TEMP"] = safe_temp
        env["TMP"]  = safe_temp
    return env


def run_investigation(incident: IncidentAlert) -> InvestigationResult:
    """
    Persists the incident as a JSON file, then runs RCA.
    Prefers DGX (company Qwen vLLM) if available; falls back to OpenSRE CLI.
    """
    # Lazy import to avoid circular dependencies
    try:
        from sentinel.engine.dgx_client import is_dgx_available, investigate_with_dgx
    except ImportError:
        try:
            from dgx_engine import is_dgx_available, investigate_with_dgx
        except ImportError:
            def is_dgx_available(): return False
            def investigate_with_dgx(_): return None

    ts        = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = _make_safe_filename(incident.alert_name)
    incident_file = INCIDENTS_DIR / f"{safe_name}-{ts}.json"

    # Write incident to disk for history
    with open(incident_file, "w", encoding="utf-8") as f:
        json.dump(incident.model_dump(), f, indent=2)

    logger.info(f"Investigating: {incident.alert_name}")

    ver = incident.camunda_version or os.getenv("CAMUNDA_VERSION", "8.9")

    # ── Option 1: Company DGX Server (vLLM / Qwen 3.6 35B) ────────────────────
    if is_dgx_available():
        logger.info(f"[ENGINE] Active: Company DGX Server (Qwen 35B vLLM on :8000) [Camunda {ver}]")
        dgx_result = investigate_with_dgx(incident.model_dump())
        if dgx_result:
            return InvestigationResult(
                status="success",
                incident=incident.alert_name,
                rca=dgx_result,
                incident_file=str(incident_file),
                camunda_version=ver,
            )
        logger.warning("[ENGINE] DGX query failed, falling back to OpenSRE CLI...")

    # ── Option 2: Fallback to OpenSRE CLI ──────────────────────────────────────
    logger.info("[ENGINE] Using OpenSRE CLI (`opensre investigate`)")
    try:
        proc = subprocess.run(
            ["opensre", "investigate", "-i", str(incident_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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
                camunda_version=ver,
                error=stderr or f"opensre exited with code {proc.returncode}",
            )

        try:
            rca = json.loads(stdout)
            return InvestigationResult(
                status="success",
                incident=incident.alert_name,
                rca=rca,
                incident_file=str(incident_file),
                camunda_version=ver,
            )
        except json.JSONDecodeError:
            return InvestigationResult(
                status="success",
                incident=incident.alert_name,
                raw_output=stdout,
                incident_file=str(incident_file),
                camunda_version=ver,
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
