"""
sentinel/models.py
==================
Backward-compatibility facade re-exporting from sentinel.core.models.
"""

from sentinel.core.models import (
    IncidentAlert,
    ErrorEvent,
    InvestigationResult,
    RcaReport,
    DocumentationReference,
)

__all__ = [
    "IncidentAlert",
    "ErrorEvent",
    "InvestigationResult",
    "RcaReport",
    "DocumentationReference",
]
