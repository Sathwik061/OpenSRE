"""
sentinel/investigator.py
========================
Backward-compatibility facade re-exporting from sentinel.core.investigator.
"""

from sentinel.core.investigator import (
    run_investigation,
    _make_safe_filename,
    _build_env,
    INCIDENTS_DIR,
)

__all__ = [
    "run_investigation",
    "_make_safe_filename",
    "_build_env",
    "INCIDENTS_DIR",
]
