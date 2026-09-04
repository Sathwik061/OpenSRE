"""
sentinel/supabase_runbook.py
============================
Backward-compatibility facade re-exporting from sentinel.knowledge.supabase_runbook.
"""

from sentinel.knowledge.supabase_runbook import (
    is_configured,
    health_check,
    lookup_instance_rca,
    save_instance_rca,
    lookup_sop_guidelines,
    lookup_runbook,
    save_runbook,
    list_runbooks,
    delete_runbook,
    SUPABASE_URL,
    SUPABASE_KEY,
    TABLE,
)

# Aliases for backward compatibility
get_instance_rca = lookup_instance_rca
record_instance_rca = save_instance_rca

__all__ = [
    "is_configured",
    "health_check",
    "lookup_instance_rca",
    "save_instance_rca",
    "get_instance_rca",
    "record_instance_rca",
    "lookup_sop_guidelines",
    "lookup_runbook",
    "save_runbook",
    "list_runbooks",
    "delete_runbook",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "TABLE",
]
