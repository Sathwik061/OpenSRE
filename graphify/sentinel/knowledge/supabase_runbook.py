"""
sentinel/knowledge/supabase_runbook.py
======================================
Compatibility bridge mapping previous Supabase calls to the native,
high-performance local SRE Runbook Knowledge Engine (sentinel/knowledge/runbook_knowledge.py).
Zero external network calls required.
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from sentinel.knowledge.runbook_knowledge import (
    lookup_sop_guidelines as native_lookup_sop,
    list_all_runbooks as native_list_runbooks,
    get_runbook as native_get_runbook,
    save_runbook as native_save_runbook,
)

log = logging.getLogger("sentinel.knowledge.supabase")

SUPABASE_URL = "local://runbooks"
SUPABASE_KEY = "local_key"
TABLE = "runbooks"


def is_configured() -> bool:
    """Always returns True to signify runbook knowledge engine is active."""
    return True


def health_check() -> bool:
    """Verify local runbook index is healthy."""
    return len(native_list_runbooks()) > 0


def lookup_sop_guidelines(error_type: str, process_id: str = "*", **kwargs) -> Optional[dict]:
    """Look up standard team SOP guidelines for an error type using native Runbook Engine."""
    return native_lookup_sop(
        error_type=error_type,
        service=process_id,
        **kwargs,
    )


def lookup_runbook(error_type: str, process_id: str = "*") -> Optional[dict]:
    """Alias for lookup_sop_guidelines."""
    return lookup_sop_guidelines(error_type, process_id)


def list_runbooks() -> list[dict]:
    """List all canonical runbooks stored in the local runbook catalog."""
    return native_list_runbooks()


def save_runbook(error_type: str, process_id: str, rca: dict) -> Optional[dict]:
    """Save a runbook into the local runbook knowledge catalog."""
    runbook_data = {
        "id": error_type.lower().replace("_", "-"),
        "title": f"{error_type} Playbook",
        "error_types": [error_type],
        "services": [process_id],
        "summary": rca.get("summary", ""),
        "recommended_actions": rca.get("recommended_actions", []),
        "content": f"# {error_type} Playbook\n\n## Root Cause\n{rca.get('root_cause', '')}\n\n## Recommended Actions\n" + "\n".join(f"- {a}" for a in rca.get("recommended_actions", [])),
    }
    ok = native_save_runbook(runbook_data)
    return runbook_data if ok else None


def delete_runbook(runbook_id: str) -> bool:
    """Stub for deleting a runbook."""
    return True


def lookup_instance_rca(instance_key: str, incident_key: str = "") -> Optional[dict]:
    """Instance lookup stub."""
    return None


def save_instance_rca(*args, **kwargs) -> Optional[dict]:
    """Instance save stub."""
    return None
