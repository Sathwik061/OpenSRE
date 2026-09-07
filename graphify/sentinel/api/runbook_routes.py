"""
sentinel/api/runbook_routes.py
==============================
CRUD and lookup API endpoints for native SRE Runbook Documentation.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from sentinel.knowledge.runbook_knowledge import (
    list_all_runbooks,
    get_runbook,
    save_runbook,
    lookup_sop_guidelines,
)

logger = logging.getLogger("sentinel.api.runbooks")

router = APIRouter(prefix="/api/runbooks", tags=["runbooks"])


@router.get("")
def get_runbooks():
    """List all canonical SRE runbooks stored in the local knowledge engine."""
    try:
        rows = list_all_runbooks()
        return {"count": len(rows), "runbooks": rows}
    except Exception as e:
        logger.warning(f"Error listing runbooks: {e}")
        return {"count": 0, "runbooks": []}


@router.get("/lookup/{error_type}")
def lookup_runbook_by_error(
    error_type: str,
    service: str = Query(default="*"),
    message: str = Query(default=""),
):
    """Dynamic lookup for tailored SRE SOP guidelines based on incident parameters."""
    sop = lookup_sop_guidelines(
        error_type=error_type,
        service=service,
        error_message=message,
    )
    if not sop:
        raise HTTPException(status_code=404, detail=f"No runbook found for error type '{error_type}'")
    return {"status": "found", "sop": sop}


@router.get("/{runbook_id}")
def get_single_runbook(runbook_id: str):
    """Retrieve a specific SRE runbook with full markdown documentation."""
    rb = get_runbook(runbook_id)
    if not rb:
        raise HTTPException(status_code=404, detail=f"Runbook '{runbook_id}' not found")
    return {"status": "found", "runbook": rb}


@router.post("")
def create_or_update_runbook(payload: dict):
    """
    Save or update an SRE runbook in the local documentation repository.
    """
    try:
        error_type = payload.get("error_type") or payload.get("errorType", "")
        service    = payload.get("service") or payload.get("process_id", "*")
        title      = payload.get("title") or f"{error_type} Playbook"
        rca        = payload.get("rca") or payload

        runbook_data = {
            "id": payload.get("id") or error_type.lower().replace("_", "-"),
            "title": title,
            "error_types": [error_type] if error_type else ["APPLICATION_ERROR"],
            "services": [service],
            "summary": rca.get("summary") or payload.get("summary", ""),
            "recommended_actions": rca.get("recommended_actions") or payload.get("recommended_actions", []),
            "content": payload.get("content") or f"# {title}\n\n## Root Cause\n{rca.get('root_cause', '')}\n\n## Recommended Actions\n" + "\n".join(f"- {a}" for a in rca.get("recommended_actions", [])),
        }

        ok = save_runbook(runbook_data)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to save runbook locally")
        return {"status": "saved", "runbook": runbook_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving runbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
