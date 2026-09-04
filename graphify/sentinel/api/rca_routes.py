"""
sentinel/api/rca_routes.py
==========================
FastAPI endpoints for SRE incident ingestion and Root Cause Analysis investigations.
"""

import os
import logging
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, HTTPException

from sentinel.core.models import IncidentAlert, ErrorEvent
from sentinel.core.incident_builder import build_incident_from_error
from sentinel.core.investigator import run_investigation
from sentinel.core.state_store import store

logger = logging.getLogger("sentinel.api.rca")

router = APIRouter(tags=["rca"])


def _run_in_background(inv_id: str, incident: IncidentAlert) -> None:
    """Executes the investigation asynchronously in the background."""
    store.set_status(inv_id, "running")
    try:
        res = run_investigation(incident)
        store.set_result(
            inv_id,
            res.model_dump(),
            additional_keys=[incident.instance_key, incident.incident_key],
        )
        logger.info(f"Investigation {inv_id} completed (status={res.status})")
    except Exception as e:
        logger.error(f"Investigation {inv_id} failed: {e}", exc_info=True)
        store.set_result(
            inv_id,
            {"status": "error", "incident": incident.alert_name, "error": str(e)},
            additional_keys=[incident.instance_key, incident.incident_key],
        )


@router.get("/health")
def health():
    """Service health check endpoint."""
    from datetime import datetime, timezone
    return {
        "status": "healthy",
        "service": "sentinel",
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/investigate", status_code=202)
def investigate(incident: IncidentAlert, background_tasks: BackgroundTasks):
    """
    Submit a fully-formed IncidentAlert for RCA.
    Runs asynchronously in the background. Poll /investigations/{id} for result.
    """
    inv_id = str(uuid4())[:8]
    ver = incident.camunda_version or os.getenv("CAMUNDA_VERSION", "8.9")
    logger.info(f"[investigate] {incident.alert_name} (Camunda {ver}) -> id={inv_id}")
    store.set_status(inv_id, "running")
    background_tasks.add_task(_run_in_background, inv_id, incident)
    return {
        "status": "accepted",
        "investigation_id": inv_id,
        "incident": incident.alert_name,
        "camunda_version": ver,
        "message": "Investigation started. Poll /investigations/{id} for results.",
        "poll_url": f"/investigations/{inv_id}",
    }


@router.post("/investigate/from-error", status_code=202)
def investigate_from_error(event: ErrorEvent, background_tasks: BackgroundTasks):
    """
    Build an IncidentAlert from a raw ErrorEvent and trigger RCA investigation.
    Primary entry point for Camunda external workers and error hooks.
    """
    ver = event.camunda_version or os.getenv("CAMUNDA_VERSION", "8.9")
    logger.info(f"[from-error] {event.service} - {event.error_type} (Camunda {ver})")
    incident = build_incident_from_error(event)
    inv_id = str(uuid4())[:8]
    store.set_status(inv_id, "running")
    background_tasks.add_task(_run_in_background, inv_id, incident)
    return {
        "status": "accepted",
        "investigation_id": inv_id,
        "incident": incident.alert_name,
        "camunda_version": ver,
        "message": "RCA investigation started in background.",
        "poll_url": f"/investigations/{inv_id}",
    }


@router.get("/investigations")
def list_investigations():
    """List all investigations recorded in memory this session."""
    summary = store.list_all()
    return {"count": len(summary), "investigations": summary}


@router.get("/investigations/{inv_id}")
def get_investigation(inv_id: str):
    """
    Retrieve the result or status of a specific investigation.
    Checks Supabase instance store first, then in-memory results.
    """
    # 1. Authoritative check: Supabase Instance Store
    try:
        from sentinel.knowledge.supabase_runbook import lookup_instance_rca, is_configured as sb_configured
        if sb_configured():
            sb_rca = lookup_instance_rca(inv_id)
            if sb_rca and sb_rca.get("root_cause"):
                res_obj = {
                    "instance_key": inv_id,
                    "processInstanceKey": inv_id,
                    "incident_key": sb_rca.get("_incident_key") or inv_id,
                    "status": "success",
                    "incident": sb_rca.get("error_type", "Camunda Incident"),
                    "rca": {
                        "summary": sb_rca.get("summary"),
                        "root_cause": sb_rca.get("root_cause"),
                        "confidence": sb_rca.get("confidence", "HIGH"),
                        "observed_facts": sb_rca.get("observed_facts") or [],
                        "evidence": sb_rca.get("evidence") or [sb_rca.get("root_cause")],
                        "recommended_actions": sb_rca.get("recommended_actions") or [],
                        "topology_warnings": sb_rca.get("topology_warnings") or [],
                        "documentation_references": sb_rca.get("documentation_references") or [],
                    },
                    "source": "supabase_dgx",
                }
                store.set_result(inv_id, res_obj)
                return res_obj
    except Exception as e:
        logger.debug(f"Supabase lookup error for {inv_id}: {e}")

    # 2. Check in-memory store
    status = store.get_status(inv_id)
    result = store.get_result(inv_id)

    if result is None and status is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if status == "running":
        return {"status": "running", "message": "Investigation in progress..."}

    return result or {"status": status}


@router.post("/api/rca/record")
def record_external_rca(payload: dict):
    """Save an RCA produced by camunda_bridge or external worker."""
    inst_key = str(payload.get("instance_key") or payload.get("processInstanceKey") or "")
    inc_key  = str(payload.get("incident_key") or payload.get("incidentKey") or "")
    inv_id   = inst_key or inc_key or str(uuid4())[:16]

    store.set_result(inv_id, payload, additional_keys=[inst_key, inc_key])
    return {"status": "saved", "id": inv_id}
