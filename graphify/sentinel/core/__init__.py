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
from sentinel.core.masking import (
    mask_variables,
    mask_string_value,
    mask_incident_payload,
    is_sensitive_key,
)

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
    "mask_variables",
    "mask_string_value",
    "mask_incident_payload",
    "is_sensitive_key",
]
