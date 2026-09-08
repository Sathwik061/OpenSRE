"""
sentinel/api/project_routes.py
==============================
FastAPI endpoints for Project Intake & Context Profiling Framework ("Project Passport").
Allows teams to register project profiles, configure business intent,
manage dependencies, and attach multi-format runbooks.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from sentinel.core.project_models import (
    ProjectProfile,
    CreateProjectRequest,
    UpdateProjectRequest,
)
from sentinel.core.project_store import project_store

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
def list_projects():
    """Lists all registered Project Passports."""
    projs = project_store.list_all()
    return {"count": len(projs), "projects": projs}



@router.post("", response_model=ProjectProfile, status_code=201)
def create_project(req: CreateProjectRequest):
    """Registers a new Project Passport with business purpose, stack, and dependencies."""
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    if not req.business_purpose.strip():
        raise HTTPException(status_code=400, detail="Project business purpose/moto is required")
    return project_store.create(req)


@router.get("/match", response_model=Optional[ProjectProfile])
def match_project(service: str = Query(..., description="Service name or log snippet to match")):
    """Fuzzy-matches a project profile based on service name or error log text."""
    proj = project_store.find_matching_project(service)
    return proj


@router.get("/{project_id}", response_model=ProjectProfile)
def get_project(project_id: str):
    """Retrieves a single Project Passport by ID or slug."""
    proj = project_store.get_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return proj


@router.put("/{project_id}", response_model=ProjectProfile)
def update_project(project_id: str, req: UpdateProjectRequest):
    """Updates an existing Project Passport."""
    updated = project_store.update(project_id, req)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return updated


@router.delete("/{project_id}", status_code=200)
def delete_project(project_id: str):
    """Deletes a Project Passport."""
    success = project_store.delete(project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return {"status": "deleted", "id": project_id}
