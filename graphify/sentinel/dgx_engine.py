"""
sentinel/dgx_engine.py
======================
Backward-compatibility facade re-exporting from sentinel.engine.
"""

from sentinel.engine.dgx_client import (
    is_dgx_available,
    check_dgx_alive,
    get_active_model,
    run_rca_on_dgx,
    investigate_with_dgx,
    _parse_llm_json,
    DGX_URL,
    DGX_MODEL,
)
from sentinel.engine.prompt_builder import SRE_SYSTEM_PROMPT as SYSTEM_PROMPT, build_rca_prompt

__all__ = [
    "is_dgx_available",
    "check_dgx_alive",
    "get_active_model",
    "run_rca_on_dgx",
    "investigate_with_dgx",
    "_parse_llm_json",
    "DGX_URL",
    "DGX_MODEL",
    "SYSTEM_PROMPT",
    "build_rca_prompt",
]
