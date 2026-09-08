"""
Sentinel RCA Service — FastAPI Application Entry Point
======================================================
Assembles domain API routers (RCA, Camunda Proxy, Runbooks, DGX) and
manages the background real-time Camunda incident watcher thread.
"""

import sys
import os
import logging
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure sentinel and graphify root are in Python path
_sentinel_dir = os.path.dirname(os.path.abspath(__file__))
_graphify_dir = os.path.dirname(_sentinel_dir)
for p in [_sentinel_dir, _graphify_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sentinel.api import (
    rca_router,
    camunda_proxy_router,
    runbook_upload_router,
    runbook_router,
    dgx_router,
    project_router,
    integration_router,
)
from sentinel.camunda.bridge_watcher import run_bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("sentinel")

app = FastAPI(
    title="Sentinel RCA Service",
    description="SRE Root Cause Analysis service with embedded real-time Camunda watcher.",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount Domain API Routers ──────────────────────────────────────────────────
app.include_router(rca_router)
app.include_router(camunda_proxy_router)
app.include_router(runbook_upload_router)
app.include_router(runbook_router)
app.include_router(dgx_router)
app.include_router(project_router)
app.include_router(integration_router)


# ── Embedded Camunda Watcher Background Thread ────────────────────────────────
_bridge_thread: threading.Thread = None

@app.on_event("startup")
def startup_event():
    """Start embedded real-time Camunda bridge watcher in a background thread."""
    global _bridge_thread
    logger.info("🚀 Starting embedded Camunda Real-Time Incident Watcher...")
    try:
        _bridge_thread = threading.Thread(
            target=run_bridge,
            kwargs={"poll_interval": 5, "run_once": False},
            daemon=True,
            name="CamundaWatcherThread",
        )
        _bridge_thread.start()
    except Exception as e:
        logger.warning(f"Could not start embedded Camunda watcher: {e}")
