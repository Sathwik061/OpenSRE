"""
sentinel/api/dgx_routes.py
==========================
Proxy endpoint for inspecting active DGX vLLM AI models.
"""

import os
import json
import logging
import urllib.request
from fastapi import APIRouter

logger = logging.getLogger("sentinel.api.dgx_routes")

router = APIRouter(prefix="/api/dgx", tags=["proxy"])

DGX_BASE = os.getenv("DGX_URL", "http://localhost:8000/v1").rstrip("/")


@router.get("/models")
def proxy_dgx_models():
    """Proxy for DGX vLLM /models endpoint with CORS support."""
    try:
        req = urllib.request.Request(f"{DGX_BASE}/models", method="GET")
        with urllib.request.urlopen(req, timeout=4) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"data": [], "status": "offline", "error": str(e)}
