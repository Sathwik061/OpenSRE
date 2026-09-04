"""
sentinel/knowledge
==================
Knowledge retrieval modules: local Camunda 8 documentation RAG and Supabase runbook store.
"""

from sentinel.knowledge.camunda_knowledge import (
    retrieve_camunda_context,
    retrieve_camunda_knowledge,
    build_camunda_knowledge_prompt_section,
    get_indexed_documents,
    format_versioned_doc_url,
)
from sentinel.knowledge.kapa_mcp_client import query_kapa_mcp, is_kapa_configured
from sentinel.knowledge.supabase_runbook import (
    lookup_instance_rca,
    save_instance_rca,
    lookup_sop_guidelines,
    lookup_runbook,
    save_runbook,
    list_runbooks,
    delete_runbook,
    health_check as sb_health,
    is_configured as sb_configured,
)

__all__ = [
    "retrieve_camunda_context",
    "retrieve_camunda_knowledge",
    "build_camunda_knowledge_prompt_section",
    "get_indexed_documents",
    "format_versioned_doc_url",
    "query_kapa_mcp",
    "is_kapa_configured",
    "lookup_instance_rca",
    "save_instance_rca",
    "lookup_sop_guidelines",
    "lookup_runbook",
    "save_runbook",
    "list_runbooks",
    "delete_runbook",
    "sb_health",
    "sb_configured",
]
