"""
Sentinel RCA Service — FastAPI application
Receives error events (from Camunda worker, error_hook, or HTTP webhook),
builds an OpenSRE incident, and triggers RCA investigation.

Key design: investigations run as BACKGROUND TASKS.
Endpoints return immediately with an investigation ID.
This prevents timeouts when multiple errors hit simultaneously.
"""
import json
import logging
import threading
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import IncidentAlert, ErrorEvent, InvestigationResult
from incident_builder import build_incident_from_error
from investigator import run_investigation

# Supabase runbook store (optional — graceful degradation if unavailable)
try:
    from supabase_runbook import (
        lookup_instance_rca, save_instance_rca,
        lookup_runbook, save_runbook, list_runbooks,
        delete_runbook, health_check as sb_health, is_configured as sb_configured,
    )
    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False
    def list_runbooks(): return []          # type: ignore
    def delete_runbook(rid): return False   # type: ignore
    def sb_health(): return False           # type: ignore
    def sb_configured(): return False      # type: ignore

# ── Embedded Real-time Camunda Watcher ─────────────────────────────────────────
import sys
import os
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    from camunda_bridge import run_bridge
    _BRIDGE_AVAILABLE = True
except Exception as e:
    _BRIDGE_AVAILABLE = False

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("sentinel")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sentinel RCA Service",
    description=(
        "SRE Root Cause Analysis service with embedded real-time Camunda watcher. "
        "Receives incidents or raw error events, watches Camunda Operate live, "
        "and produces structured RCA via DGX Qwen 35B."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_bridge_thread: threading.Thread = None

@app.on_event("startup")
def startup_event():
    """Start embedded real-time Camunda bridge watcher in a background thread."""
    global _bridge_thread
    if _BRIDGE_AVAILABLE:
        logger.info("🚀 Starting embedded Camunda Real-Time Incident Watcher...")
        _bridge_thread = threading.Thread(
            target=run_bridge,
            kwargs={"poll_interval": 5, "run_once": False},
            daemon=True,
            name="CamundaWatcherThread"
        )
        _bridge_thread.start()
    else:
        logger.warning("Camunda bridge module not available for embedded watcher.")

# ── In-memory result store ────────────────────────────────────────────────────
# Keyed by investigation_id (uuid).
# In production, replace with Redis or a database.
_results:  dict[str, dict] = {}   # id -> result dict
_status:   dict[str, str]  = {}   # id -> "running" | "done" | "error"
_lock = threading.Lock()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_rca(result: InvestigationResult, inv_id: str) -> None:
    """Print RCA to terminal in a readable format."""
    border = "=" * 65
    print(f"\n{border}")
    print(f"  [RCA]  INVESTIGATION COMPLETE")
    print(f"  ID     : {inv_id}")
    print(f"  Alert  : {result.incident}")
    print(f"  Status : {result.status.upper()}")
    print(border)
    if result.status == "success":
        if result.rca:
            # Pretty-print the key RCA fields
            rca = result.rca
            print(f"  Root Cause : {rca.get('root_cause', 'See raw output')}")
            if rca.get("report"):
                print(f"\n{rca['report']}")
            else:
                print(json.dumps(rca, indent=2))
        elif result.raw_output:
            print(result.raw_output)
    else:
        print(f"  [ERROR]  {result.error}")
    print(f"{border}\n")


def _run_in_background(inv_id: str, incident: IncidentAlert) -> None:
    """
    Worker function: runs the investigation and stores the result.
    Called in a background thread so the API returns immediately.
    """
    try:
        with _lock:
            _status[inv_id] = "running"

        result = run_investigation(incident)

        with _lock:
            _results[inv_id]        = result.model_dump()
            _results[incident.alert_name] = result.model_dump()   # also by name
            _status[inv_id]         = "done"

        _print_rca(result, inv_id)

    except Exception as exc:
        logger.error(f"Investigation {inv_id} failed: {exc}")
        with _lock:
            _status[inv_id] = "error"
            _results[inv_id] = {"error": str(exc), "incident": incident.alert_name}


_last_sb_check: float = 0.0
_sb_reachable: bool = True

def _check_sb_cached() -> bool:
    global _last_sb_check, _sb_reachable
    import time
    now = time.time()
    if now - _last_sb_check > 60:  # check once per minute max
        _last_sb_check = now
        try:
            _sb_reachable = sb_health() if sb_configured() else False
        except Exception:
            _sb_reachable = False
    return _sb_reachable


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health():
    """Service liveness check — fast, non-blocking."""
    return {
        "status":  "healthy",
        "service": "sentinel",
        "version": "2.0.0",
        "ts":      datetime.now(timezone.utc).isoformat(),
        "active_investigations": sum(1 for s in _status.values() if s == "running"),
        "supabase": {
            "configured": sb_configured(),
            "reachable":  _sb_reachable,
        },
    }


@app.post("/investigate", tags=["rca"], status_code=202)
def investigate(incident: IncidentAlert, background_tasks: BackgroundTasks):
    """
    Run an RCA investigation on a fully-formed IncidentAlert.
    Returns immediately with an investigation ID (202 Accepted).
    Poll GET /investigations/{id} for results.
    """
    inv_id = str(uuid4())[:8]
    logger.info(f"[investigate] {incident.alert_name} -> id={inv_id}")

    background_tasks.add_task(_run_in_background, inv_id, incident)

    return {
        "status":         "accepted",
        "investigation_id": inv_id,
        "incident":       incident.alert_name,
        "message":        "Investigation started. Poll /investigations/{id} for results.",
        "poll_url":       f"/investigations/{inv_id}",
    }


@app.post("/investigate/from-error", tags=["rca"], status_code=202)
def investigate_from_error(event: ErrorEvent, background_tasks: BackgroundTasks):
    """
    Build an incident from a raw ErrorEvent, then start investigation.
    PRIMARY endpoint used by:
      - Camunda external task worker
      - error_hook.py (auto-catches Python exceptions)
      - log_watcher.py (tails log files for errors)

    Returns immediately (202 Accepted). Investigation runs in background.
    """
    logger.info(f"[from-error] {event.service} - {event.error_type}")
    incident = build_incident_from_error(event)
    inv_id   = str(uuid4())[:8]

    background_tasks.add_task(_run_in_background, inv_id, incident)

    return {
        "status":           "accepted",
        "investigation_id": inv_id,
        "incident":         incident.alert_name,
        "message":          "RCA investigation started in background.",
        "poll_url":         f"/investigations/{inv_id}",
    }


@app.get("/investigations", tags=["rca"])
def list_investigations():
    """List all investigations this session with their status."""
    with _lock:
        summary = [
            {"id": inv_id, "status": _status.get(inv_id, "unknown")}
            for inv_id in _status
        ]
    return {
        "count":         len(summary),
        "investigations": summary,
    }

@app.get("/investigations/{inv_id}", tags=["rca"])
def get_investigation(inv_id: str):
    """
    Retrieve the result or status of a specific investigation.
    Returns authoritative DGX RCA from Supabase if stored, otherwise in-memory result.
    """
    # 1. Authoritative check: Supabase Instance Store (contains rich DGX Qwen 35B analysis)
    if _SUPABASE_OK:
        try:
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
                    },
                    "source": "supabase_dgx",
                }
                with _lock:
                    _results[inv_id] = res_obj
                    _status[inv_id] = "done"
                return res_obj
        except Exception as e:
            logger.debug(f"Supabase lookup error for {inv_id}: {e}")

    with _lock:
        status = _status.get(inv_id)
        result = _results.get(inv_id)

        if result is None:
            # Look up by instance key or incident key in saved results
            for v in _results.values():
                if isinstance(v, dict):
                    if (
                        str(v.get("instance_key", "")) == inv_id
                        or str(v.get("incident_key", "")) == inv_id
                        or str(v.get("processInstanceKey", "")) == inv_id
                        or str(v.get("incidentKey", "")) == inv_id
                    ):
                        result = v
                        status = "done"
                        break

    if result is None and status is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if status == "running":
        return {"status": "running", "message": "Investigation in progress..."}

    if isinstance(result, dict):
        rca = result.get("rca")
        if isinstance(rca, dict) and not rca.get("evidence"):
            err = result.get("error_message") or result.get("errorMessage")
            if err:
                rca["evidence"] = [err]

    return result or {"status": status}


# ── CORS Proxy Gateway Routes for Frontend ────────────────────────────────────
import urllib.request
import urllib.error

CAMUNDA_BASE = "http://localhost:8080"
DGX_BASE     = "http://localhost:8000/v1"


def _forward_camunda_post(path: str, body: dict) -> dict:
    """Helper to forward POST requests to Camunda 8.9 REST API."""
    url = f"{CAMUNDA_BASE}{path}"
    try:
        data = json.dumps(body or {}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            res_text = r.read().decode("utf-8")
            return json.loads(res_text) if res_text else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=e.code, detail=err_msg or str(e))
    except Exception as e:
        logger.error(f"Camunda proxy error on {path}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to connect to Camunda: {e}")


@app.post("/api/camunda/incidents/search", tags=["proxy"])
@app.post("/api/camunda/v2/incidents/search", tags=["proxy"])
def proxy_camunda_incidents(body: dict = None):
    """Proxy for Camunda 8.9 /v2/incidents/search with CORS support."""
    return _forward_camunda_post("/v2/incidents/search", body or {})


@app.post("/api/camunda/process-instances/search", tags=["proxy"])
@app.post("/api/camunda/v2/process-instances/search", tags=["proxy"])
def proxy_camunda_process_instances(body: dict = None):
    """Proxy for Camunda 8.9 /v2/process-instances/search with CORS support."""
    return _forward_camunda_post("/v2/process-instances/search", body or {})


@app.post("/api/camunda/process-definitions/search", tags=["proxy"])
@app.post("/api/camunda/v2/process-definitions/search", tags=["proxy"])
def proxy_camunda_process_definitions(body: dict = None):
    """Proxy for Camunda 8.9 /v2/process-definitions/search with CORS support."""
    return _forward_camunda_post("/v2/process-definitions/search", body or {})


@app.get("/api/camunda/process-definitions/{key}/xml", tags=["proxy"])
@app.get("/api/camunda/v2/process-definitions/{key}/xml", tags=["proxy"])
def proxy_camunda_process_definition_xml(key: str):
    """Proxy to fetch BPMN 2.0 XML from Camunda 8.9."""
    url = f"{CAMUNDA_BASE}/v2/process-definitions/{key}/xml"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=8) as r:
            xml_text = r.read().decode("utf-8")
            return {"xml": xml_text}
    except Exception as e:
        logger.error(f"Failed to fetch XML for process {key}: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/camunda/variables/search", tags=["proxy"])
@app.post("/api/camunda/v2/variables/search", tags=["proxy"])
def proxy_camunda_variables(body: dict = None):
    """Proxy for Camunda 8.9 /v2/variables/search with CORS support."""
    return _forward_camunda_post("/v2/variables/search", body or {})


@app.post("/api/camunda/incidents/{incident_key}/resolution", tags=["proxy"])
@app.post("/api/camunda/v2/incidents/{incident_key}/resolution", tags=["proxy"])
def proxy_camunda_incident_resolution(incident_key: str, body: dict = None):
    """Proxy for Camunda 8.9 incident resolution with CORS support."""
    return _forward_camunda_post(f"/v2/incidents/{incident_key}/resolution", body or {})


@app.get("/api/dgx/models", tags=["proxy"])
def proxy_dgx_models():
    """Proxy for DGX vLLM /models endpoint with CORS support."""
    try:
        req = urllib.request.Request(f"{DGX_BASE}/models", method="GET")
        with urllib.request.urlopen(req, timeout=4) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"data": [], "status": "offline", "error": str(e)}


@app.post("/api/rca/record", tags=["rca"])
def record_external_rca(payload: dict):
    """Save an RCA produced by camunda_bridge or external worker."""
    inst_key = str(payload.get("instance_key") or payload.get("processInstanceKey") or "")
    inc_key  = str(payload.get("incident_key") or payload.get("incidentKey") or "")
    inv_id   = inst_key or inc_key or str(uuid4())[:16]
    with _lock:
        _results[inv_id] = payload
        _status[inv_id]  = "done"
        if inst_key:
            _results[inst_key] = payload
            _status[inst_key]  = "done"
        if inc_key:
            _results[inc_key] = payload
            _status[inc_key]  = "done"
    return {"status": "saved", "id": inv_id}


# ── Supabase Runbook API ───────────────────────────────────────────────────────

@app.get("/api/runbooks", tags=["runbooks"])
def get_runbooks():
    """List all canonical runbooks stored in Supabase."""
    rows = list_runbooks()
    return {"count": len(rows), "runbooks": rows}


@app.post("/api/runbooks", tags=["runbooks"])
def create_runbook(payload: dict):
    """
    Save a runbook to Supabase manually (e.g. from Frontend 'Save as Runbook' button).
    Accepts either a full runbook payload or an RCA dict with error_type.
    """
    error_type = payload.get("error_type") or payload.get("errorType", "")
    process_id = payload.get("process_id") or payload.get("processId", "*")
    rca        = payload.get("rca") or payload
    if not error_type:
        raise HTTPException(status_code=400, detail="error_type is required")
    result = save_runbook(error_type, process_id, rca)
    if not result:
        raise HTTPException(status_code=502, detail="Failed to save to Supabase — check credentials")
    return {"status": "saved", "runbook": result}


@app.delete("/api/runbooks/{runbook_id}", tags=["runbooks"])
def remove_runbook(runbook_id: str):
    """Delete a runbook from Supabase by UUID."""
    ok = delete_runbook(runbook_id)
    if not ok:
        raise HTTPException(status_code=502, detail="Failed to delete from Supabase")
    return {"status": "deleted", "id": runbook_id}
