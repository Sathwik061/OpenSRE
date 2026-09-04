"""
sentinel/api/runbook_routes.py
==============================
CRUD API endpoints for Supabase-backed SRE Runbook Playbooks.
"""

import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger("sentinel.api.runbooks")

router = APIRouter(prefix="/api/runbooks", tags=["runbooks"])


@router.get("")
def get_runbooks():
    """List all canonical runbooks stored in Supabase."""
    try:
        from sentinel.knowledge.supabase_runbook import list_runbooks
        rows = list_runbooks()
        return {"count": len(rows), "runbooks": rows}
    except Exception as e:
        logger.warning(f"Error listing runbooks: {e}")
        return {"count": 0, "runbooks": []}


@router.post("")
def create_runbook(payload: dict):
    """
    Save a runbook to Supabase manually (e.g. from Frontend 'Save as Runbook' button).
    """
    try:
        from sentinel.knowledge.supabase_runbook import save_runbook
        error_type = payload.get("error_type") or payload.get("errorType", "")
        process_id = payload.get("process_id") or payload.get("processId", "*")
        rca        = payload.get("rca") or payload
        if not error_type:
            raise HTTPException(status_code=400, detail="error_type is required")
        result = save_runbook(error_type, process_id, rca)
        if not result:
            raise HTTPException(status_code=502, detail="Failed to save to Supabase — check credentials")
        return {"status": "saved", "runbook": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating runbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{runbook_id}")
def remove_runbook(runbook_id: str):
    """Delete a runbook from Supabase by UUID."""
    try:
        from sentinel.knowledge.supabase_runbook import delete_runbook
        ok = delete_runbook(runbook_id)
        if not ok:
            raise HTTPException(status_code=502, detail="Failed to delete from Supabase")
        return {"status": "deleted", "id": runbook_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting runbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
