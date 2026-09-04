"""
sentinel/core/models.py
=======================
Pydantic data models representing SRE incidents, errors, investigations,
and structured root cause analysis outputs.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentationReference(BaseModel):
    """Reference link to official Camunda documentation."""
    section: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    relevance: Optional[str] = None
    camunda_version: Optional[str] = None


class RcaReport(BaseModel):
    """Structured SRE Root Cause Analysis report schema."""
    summary: str
    root_cause: str
    confidence: str = "HIGH"
    observed_facts: List[str] = Field(default_factory=list)
    inferences: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    topology_warnings: List[str] = Field(default_factory=list)
    documentation_references: List[DocumentationReference] = Field(default_factory=list)
    camunda_version: Optional[str] = "8.9"
    validity_score: Optional[float] = 0.9
    is_noise: Optional[bool] = False
    report: Optional[str] = None
    engine: Optional[str] = None


class IncidentAlert(BaseModel):
    """Fully-formed OpenSRE-compatible incident alert."""
    alert_name: str
    service: str
    environment: str = "production"
    error: str
    error_message: str
    logs: List[str] = Field(default_factory=list)
    timeline: List[str] = Field(default_factory=list)
    severity: Optional[str] = "high"
    timestamp: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    bpmn_topology: Optional[Dict[str, Any]] = None
    element_id: Optional[str] = None
    element_name: Optional[str] = None
    process_id: Optional[str] = None
    instance_key: Optional[str] = None
    incident_key: Optional[str] = None
    camunda_version: Optional[str] = "8.9"
    request: str = (
        "Determine what failed, identify the most likely root cause using the supplied evidence, "
        "explain the evidence, and recommend a safe remediation. Do not execute any remediation."
    )


class ErrorEvent(BaseModel):
    """Raw error event received from Camunda worker or webhook."""
    service: str
    error_type: str
    error_message: str
    environment: str = "production"
    logs: List[str] = Field(default_factory=list)
    camunda_version: Optional[str] = "8.9"
    additional_context: Optional[dict] = None


class InvestigationResult(BaseModel):
    """Result returned after an SRE investigation."""
    status: str                  # "success" | "error" | "timeout"
    incident: str
    rca: Optional[dict] = None
    raw_output: Optional[str] = None
    incident_file: Optional[str] = None
    camunda_version: Optional[str] = "8.9"
    error: Optional[str] = None
