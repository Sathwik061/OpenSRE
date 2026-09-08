"""
sentinel/core/project_store.py
===============================
Persistent thread-safe storage engine for Project Passports.
Stores project profiles, business intent, architecture dependencies,
and links to attached PDF/Word runbooks.
"""

import json
import os
import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

from sentinel.core.project_models import (
    ProjectProfile,
    CreateProjectRequest,
    UpdateProjectRequest,
    ProjectRunbookRef,
    ServiceDependency,
)

logger = logging.getLogger("sentinel.core.project_store")

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_PROJECTS_FILE = os.path.join(_DATA_DIR, "projects.json")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", text.lower()).strip("-")
    return slug or str(uuid4())[:8]


class ProjectStore:
    """Thread-safe persistent store for Project Passports."""

    def __init__(self, file_path: str = _PROJECTS_FILE):
        self.file_path = file_path
        self._ensure_file_and_seeds()

    def _ensure_file_and_seeds(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            seeds = self._get_seed_projects()
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([p.model_dump() for p in seeds], f, indent=2)

    def _get_seed_projects(self) -> List[ProjectProfile]:
        now = datetime.now(timezone.utc).isoformat()
        return [
            ProjectProfile(
                id="proj-order-fulfillment",
                name="orderFulfillmentProcess",
                slug="order-fulfillment-process",
                business_purpose=(
                    "End-to-end e-commerce order fulfillment workflow, orchestrating customer payment authorization, "
                    "inventory reservation, warehouse parcel packaging, and delivery tracking notifications."
                ),
                platform="camunda-8",
                platform_version="8.9",
                environment="production",
                owner_team="Checkout & Fulfillment SRE",
                notification_channels=["#sre-critical", "#orders-eng"],
                dependencies=[
                    ServiceDependency(
                        name="Redis Session Cache",
                        dep_type="cache",
                        description="Cluster-backed Redis cache for payment idempotency tokens and worker session locks.",
                        endpoint="redis-cluster:6379",
                        critical=True,
                    ),
                    ServiceDependency(
                        name="PostgreSQL Orders DB",
                        dep_type="database",
                        description="Primary ACID transactional database storing customer orders and line items.",
                        endpoint="postgres-orders-db:5432/orders",
                        critical=True,
                    ),
                    ServiceDependency(
                        name="Payment Gateway API",
                        dep_type="upstream_api",
                        description="External upstream credit card authorization and payment settlement gateway.",
                        endpoint="https://api.payment-gateway.internal/v2",
                        critical=True,
                    ),
                ],
                active_integrations=["camunda", "slack", "datadog", "kubernetes"],
                created_at=now,
                updated_at=now,
            ),
            ProjectProfile(
                id="proj-underwriting-issuance",
                name="underwritingPolicyIssuance",
                slug="underwriting-policy-issuance",
                business_purpose=(
                    "Automated insurance policy underwriting and actuarial risk score evaluation using DMN decision tables "
                    "and automated background credit check integrations."
                ),
                platform="camunda-8",
                platform_version="8.9",
                environment="production",
                owner_team="Insurance Core Platforms",
                notification_channels=["#policy-sre"],
                dependencies=[
                    ServiceDependency(
                        name="Credit Bureau API",
                        dep_type="upstream_api",
                        description="External credit scoring and applicant identity verification service.",
                        endpoint="https://api.credit-bureau.internal/score",
                        critical=True,
                    ),
                    ServiceDependency(
                        name="Policy Document Repository",
                        dep_type="database",
                        description="S3 document bucket and metadata repository storing signed policy certificates.",
                        endpoint="s3://insurance-policies-prod",
                        critical=False,
                    ),
                ],
                active_integrations=["camunda", "slack", "jira"],
                created_at=now,
                updated_at=now,
            ),
            ProjectProfile(
                id="proj-pega-claims-review",
                name="pegaClaimsReviewWorkflow",
                slug="pega-claims-review-workflow",
                business_purpose=(
                    "Pega Systems PRPC enterprise customer dispute claims review and auto-adjudication system "
                    "handling high-volume customer transaction dispute cases."
                ),
                platform="pega",
                platform_version="8.8",
                environment="production",
                owner_team="Claims Ops SRE",
                notification_channels=["#claims-alerts"],
                dependencies=[
                    ServiceDependency(
                        name="Pega Rules Database",
                        dep_type="database",
                        description="Enterprise Oracle DB storing Pega RuleSets and clipboard case snapshots.",
                        endpoint="oracle-claims-db:1521/pega_cases",
                        critical=True,
                    ),
                ],
                active_integrations=["pega", "slack", "servicenow"],
                created_at=now,
                updated_at=now,
            ),
        ]

    def _read_all(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading projects file: {e}")
            return []

    def _write_all(self, projects: List[Dict[str, Any]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(projects, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing projects file: {e}")

    def list_all(self) -> List[ProjectProfile]:
        """Returns all registered Project Passports."""
        raw_list = self._read_all()
        return [ProjectProfile(**p) for p in raw_list]

    def get_by_id(self, project_id: str) -> Optional[ProjectProfile]:
        """Look up a project by ID or slug."""
        for p in self._read_all():
            if p.get("id") == project_id or p.get("slug") == project_id or p.get("name") == project_id:
                return ProjectProfile(**p)
        return None

    def get(self, project_id: str) -> Optional[ProjectProfile]:
        """Alias for get_by_id."""
        return self.get_by_id(project_id)

    def find_matching_project(self, query: str) -> Optional[ProjectProfile]:
        """Fuzzy match project by service name, log snippet, or process definition name."""
        if not query:
            return None
        low_q = query.lower()
        projects = self.list_all()
        # 1. Exact name/id match
        for p in projects:
            if p.name.lower() == low_q or p.slug == low_q or p.id == low_q:
                return p
        # 2. Substring match
        for p in projects:
            if p.name.lower() in low_q or p.slug in low_q or low_q in p.name.lower():
                return p
        return None

    def fuzzy_match(self, query: str) -> Optional[ProjectProfile]:
        """Alias for find_matching_project."""
        return self.find_matching_project(query)


    def create(self, req: CreateProjectRequest) -> ProjectProfile:
        """Registers a new Project Passport."""
        now = datetime.now(timezone.utc).isoformat()
        proj_id = f"proj-{_slugify(req.name)}-{str(uuid4())[:6]}"
        profile = ProjectProfile(
            id=proj_id,
            name=req.name,
            slug=_slugify(req.name),
            business_purpose=req.business_purpose,
            platform=req.platform,
            platform_version=req.platform_version or "8.9",
            environment=req.environment,
            owner_team=req.owner_team or "SRE Core Team",
            notification_channels=req.notification_channels or ["#sre-critical"],
            dependencies=req.dependencies or [],
            active_integrations=req.active_integrations or ["camunda", "slack"],
            metadata=req.metadata or {},
            created_at=now,
            updated_at=now,
        )
        all_projs = self._read_all()
        all_projs.append(profile.model_dump())
        self._write_all(all_projs)
        return profile

    def update(self, project_id: str, req: UpdateProjectRequest) -> Optional[ProjectProfile]:
        """Updates an existing Project Passport."""
        all_projs = self._read_all()
        now = datetime.now(timezone.utc).isoformat()
        for i, p in enumerate(all_projs):
            if p.get("id") == project_id or p.get("slug") == project_id:
                existing = ProjectProfile(**p)
                updated_data = existing.model_dump()
                req_dict = req.model_dump(exclude_unset=True)
                for k, v in req_dict.items():
                    if v is not None:
                        if k == "dependencies":
                            updated_data[k] = [d.model_dump() if hasattr(d, "model_dump") else d for d in v]
                        else:
                            updated_data[k] = v
                updated_data["updated_at"] = now
                all_projs[i] = updated_data
                self._write_all(all_projs)
                return ProjectProfile(**updated_data)
        return None

    def delete(self, project_id: str) -> bool:
        """Deletes a Project Passport by ID."""
        all_projs = self._read_all()
        new_list = [p for p in all_projs if p.get("id") != project_id and p.get("slug") != project_id]
        if len(new_list) < len(all_projs):
            self._write_all(new_list)
            return True
        return False

    def attach_runbook(self, project_id: str, runbook_ref: ProjectRunbookRef) -> Optional[ProjectProfile]:
        """Attaches a parsed runbook document (PDF/Word) to a project."""
        all_projs = self._read_all()
        for i, p in enumerate(all_projs):
            if p.get("id") == project_id or p.get("slug") == project_id:
                profile = ProjectProfile(**p)
                # Avoid duplicate attachments by filename
                profile.attached_runbooks = [r for r in profile.attached_runbooks if r.filename != runbook_ref.filename]
                profile.attached_runbooks.append(runbook_ref)
                profile.updated_at = datetime.now(timezone.utc).isoformat()
                all_projs[i] = profile.model_dump()
                self._write_all(all_projs)
                return profile
        return None


# Global singleton instance
project_store = ProjectStore()
