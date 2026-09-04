"""
sentinel/api/camunda_proxy.py
=============================
CORS Proxy Gateway routes for Camunda 8.9 / 8.6 Operate REST APIs.
Enables the frontend (Incident Insights Hub) to query incidents, instances,
definitions, variables, and BPMN XML without CORS blocks.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from fastapi import APIRouter, HTTPException

logger = logging.getLogger("sentinel.api.camunda_proxy")

router = APIRouter(prefix="/api/camunda", tags=["proxy"])

CAMUNDA_BASE = os.getenv("ZEEBE_REST", "http://localhost:8080").rstrip("/")


def _forward_camunda_post(path: str, body: dict) -> dict:
    """Helper to forward POST requests to Camunda REST API."""
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


@router.post("/incidents/search")
@router.post("/v2/incidents/search")
def proxy_camunda_incidents(body: dict = None):
    """Proxy for /v2/incidents/search with CORS support."""
    return _forward_camunda_post("/v2/incidents/search", body or {})


@router.post("/process-instances/search")
@router.post("/v2/process-instances/search")
def proxy_camunda_process_instances(body: dict = None):
    """Proxy for /v2/process-instances/search with CORS support."""
    return _forward_camunda_post("/v2/process-instances/search", body or {})


@router.post("/process-definitions/search")
@router.post("/v2/process-definitions/search")
def proxy_camunda_process_definitions(body: dict = None):
    """Proxy for /v2/process-definitions/search with CORS support."""
    return _forward_camunda_post("/v2/process-definitions/search", body or {})


@router.get("/process-definitions/{key}/xml")
@router.get("/v2/process-definitions/{key}/xml")
def proxy_camunda_process_definition_xml(key: str):
    """Proxy to fetch BPMN 2.0 XML from Camunda."""
    url = f"{CAMUNDA_BASE}/v2/process-definitions/{key}/xml"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=8) as r:
            xml_text = r.read().decode("utf-8")
            return {"xml": xml_text}
    except Exception as e:
        logger.error(f"Failed to fetch XML for process {key}: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/variables/search")
@router.post("/v2/variables/search")
def proxy_camunda_variables(body: dict = None):
    """Proxy for /v2/variables/search with CORS support."""
    return _forward_camunda_post("/v2/variables/search", body or {})


@router.post("/incidents/{incident_key}/resolution")
@router.post("/v2/incidents/{incident_key}/resolution")
def proxy_camunda_incident_resolution(incident_key: str, body: dict = None):
    """Proxy for Camunda incident resolution with CORS support."""
    return _forward_camunda_post(f"/v2/incidents/{incident_key}/resolution", body or {})
