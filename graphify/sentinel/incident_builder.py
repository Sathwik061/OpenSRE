"""
sentinel/incident_builder.py
============================
Backward-compatibility facade re-exporting from sentinel.core.incident_builder.
"""

from sentinel.core.incident_builder import build_incident_from_error

__all__ = ["build_incident_from_error"]
