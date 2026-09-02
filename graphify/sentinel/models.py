from pydantic import BaseModel, Field
from typing import List, Optional


class IncidentAlert(BaseModel):
    """Fully-formed OpenSRE-compatible incident alert."""
    alert_name: str
    service: str
    environment: str = "production"
    error: str
    error_message: str
    logs: List[str] = []
    timeline: List[str] = []
    severity: Optional[str] = "high"
    timestamp: Optional[str] = None
    request: str = (
        "Determine what failed, identify the most likely root cause using the supplied evidence, "
        "explain the evidence, and recommend a safe remediation. Do not execute any remediation."
    )


class ErrorEvent(BaseModel):
    """Raw error event received from Camunda or any external system."""
    service: str
    error_type: str
    error_message: str
    environment: str = "production"
    logs: List[str] = []
    additional_context: Optional[dict] = None


class InvestigationResult(BaseModel):
    """Result returned after an OpenSRE investigation."""
    status: str                  # "success" | "error" | "timeout"
    incident: str
    rca: Optional[dict] = None
    raw_output: Optional[str] = None
    incident_file: Optional[str] = None
    error: Optional[str] = None
