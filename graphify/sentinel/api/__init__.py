"""
sentinel/api
============
FastAPI API routers for RCA investigation, Camunda proxy, runbooks, and DGX status.
"""

from sentinel.api.rca_routes import router as rca_router
from sentinel.api.camunda_proxy import router as camunda_proxy_router
from sentinel.api.runbook_upload_routes import router as runbook_upload_router
from sentinel.api.runbook_routes import router as runbook_router
from sentinel.api.dgx_routes import router as dgx_router
from sentinel.api.project_routes import router as project_router
from sentinel.api.integration_routes import router as integration_router

__all__ = [
    "rca_router",
    "camunda_proxy_router",
    "runbook_upload_router",
    "runbook_router",
    "dgx_router",
    "project_router",
    "integration_router",
]


