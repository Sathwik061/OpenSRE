"""
sentinel/camunda_knowledge.py
=============================
Backward-compatibility facade re-exporting from sentinel.knowledge.camunda_knowledge.
"""

from sentinel.knowledge.camunda_knowledge import (
    retrieve_camunda_knowledge,
    retrieve_camunda_context,
    build_camunda_knowledge_prompt_section,
    get_indexed_documents,
    format_versioned_doc_url,
    score_document,
    _load_index,
    DOCS_DIR,
    INDEX_FILE,
)
from sentinel.knowledge.kapa_mcp_client import query_kapa_mcp, is_kapa_configured

__all__ = [
    "retrieve_camunda_knowledge",
    "retrieve_camunda_context",
    "build_camunda_knowledge_prompt_section",
    "get_indexed_documents",
    "format_versioned_doc_url",
    "score_document",
    "_load_index",
    "query_kapa_mcp",
    "is_kapa_configured",
    "DOCS_DIR",
    "INDEX_FILE",
]
