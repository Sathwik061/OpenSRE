"""
sentinel/core/project_models.py
================================
Pydantic data models for the Project Intake & Context Profiling Framework ("Project Passport").
Captures project identity, business purpose ("moto"), platform stack, architecture dependencies,
and attached multi-format runbooks (PDF/Word).
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone


class ServiceDependency(BaseModel):
    """External or internal dependency (database, queue, cache, API)."""
    name: str
    dep_type: str = Field("database", description="database | cache | queue | upstream_api | downstream_api | service")
    description: Optional[str] = None
    endpoint: Optional[str] = None
    critical: bool = True

    @model_validator(mode="before")
    @classmethod
    def _coerce_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "type" in data and "dep_type" not in data:
                data["dep_type"] = data.pop("type")
        return data


class ProjectRunbookRef(BaseModel):
    """Reference to an attached runbook document (PDF, Word, Markdown, YAML)."""
    id: str
    filename: str
    title: str
    format: str = Field("pdf", description="pdf | docx | doc | yml | md")
    uploaded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    file_path: Optional[str] = None
    size_bytes: Optional[int] = 0


class ProjectProfile(BaseModel):
    """
    Project Passport: Defines project identity, operational purpose,
    technology stack, architecture dependencies, and attached SOPs.
    """
    id: str
    name: str = Field(..., description="Human-readable service or process name")
    service_id: Optional[str] = None
    slug: Optional[str] = None
    business_purpose: str = Field(
        "",
        description="Detailed business purpose, intent, and what the project does"
    )
    platform: str = Field("camunda-8", description="camunda_8 | camunda-8 | camunda-7 | pega | kubernetes | spring-boot | custom")
    platform_version: Optional[str] = "8.9"
    tier: str = Field("tier-1", description="tier-1 | tier-2 | tier-3")
    environment: str = Field("production", description="production | staging | development | dr")
    owner_team: Optional[str] = "SRE Core Team"
    notification_channels: List[str] = Field(default_factory=lambda: ["#sre-critical"])
    dependencies: List[ServiceDependency] = Field(default_factory=list)

    @property
    def target_platform(self) -> str:
        return self.platform

    attached_runbooks: List[ProjectRunbookRef] = Field(default_factory=list)
    attached_runbook_ids: List[str] = Field(default_factory=list)
    active_integrations: List[str] = Field(default_factory=lambda: ["camunda", "slack"])
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Fallback business_purpose from purpose
            if not data.get("business_purpose") and data.get("purpose"):
                data["business_purpose"] = data["purpose"]
            elif not data.get("business_purpose"):
                data["business_purpose"] = data.get("name", "Enterprise Service")
            # Fallback slug from name or service_id or id
            if not data.get("slug"):
                raw_n = data.get("service_id") or data.get("name") or data.get("id") or "proj"
                data["slug"] = raw_n.lower().replace(" ", "-").replace("_", "-")
            # Fallback service_id
            if not data.get("service_id"):
                data["service_id"] = data.get("name")
        return data


class CreateProjectRequest(BaseModel):
    """Payload to register a new Project Passport."""
    name: str
    business_purpose: str
    platform: str = "camunda-8"
    platform_version: Optional[str] = "8.9"
    environment: str = "production"
    owner_team: Optional[str] = "SRE Core Team"
    notification_channels: Optional[List[str]] = None
    dependencies: Optional[List[ServiceDependency]] = None
    active_integrations: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateProjectRequest(BaseModel):
    """Payload to update an existing Project Passport."""
    name: Optional[str] = None
    business_purpose: Optional[str] = None
    platform: Optional[str] = None
    platform_version: Optional[str] = None
    environment: Optional[str] = None
    owner_team: Optional[str] = None
    notification_channels: Optional[List[str]] = None
    dependencies: Optional[List[ServiceDependency]] = None
    active_integrations: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
