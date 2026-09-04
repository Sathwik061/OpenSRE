"""
sentinel/engine
===============
AI reasoning & LLM inference engine: prompt assembly, DGX vLLM client, and JSON parsing.
"""

from sentinel.engine.prompt_builder import SRE_SYSTEM_PROMPT, build_rca_prompt
from sentinel.engine.dgx_client import (
    is_dgx_available,
    check_dgx_alive,
    get_active_model,
    run_rca_on_dgx,
    investigate_with_dgx,
)

__all__ = [
    "SRE_SYSTEM_PROMPT",
    "build_rca_prompt",
    "is_dgx_available",
    "check_dgx_alive",
    "get_active_model",
    "run_rca_on_dgx",
    "investigate_with_dgx",
]
