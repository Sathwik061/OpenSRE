"""
sentinel/core
=============
Core data models, investigation logic, and state management.
"""

from sentinel.core.models import (
    IncidentAlert,
    ErrorEvent,
    InvestigationResult,
    RcaReport,
    DocumentationReference,
)
from sentinel.core.incident_builder import build_incident_from_error
from sentinel.core.investigator import run_investigation
from sentinel.core.state_store import store, StateStore

__all__ = [
    "IncidentAlert",
    "ErrorEvent",
    "InvestigationResult",
    "RcaReport",
    "DocumentationReference",
    "build_incident_from_error",
    "run_investigation",
    "store",
    "StateStore",
]
