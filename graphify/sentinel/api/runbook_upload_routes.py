"""
sentinel/api/runbook_upload_routes.py
=====================================
FastAPI endpoints for uploading and indexing multi-format enterprise runbooks (PDF, Word .docx/.doc, Markdown, YAML).
Connects uploaded SOPs to the local document parser and links them to Project Passports.
"""

import os
import shutil
import logging
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from sentinel.knowledge.document_parsers import parse_runbook_document
from sentinel.core.project_store import project_store
from sentinel.core.project_models import ProjectRunbookRef

logger = logging.getLogger("sentinel.api.runbook_upload")

router = APIRouter(prefix="/api/runbooks", tags=["runbooks"])

_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "knowledge",
    "runbooks",
    "uploaded"
)
os.makedirs(_UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_runbook(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
):
    """
    Upload an enterprise runbook in Adobe PDF (.pdf) or Microsoft Word (.docx/.doc).
    Extracts text, headings, root cause, and remediation steps 100% locally.
    Optionally links the runbook to a Project Passport.
    """
    filename = file.filename or f"runbook-{str(uuid4())[:8]}.docx"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".pdf", ".docx", ".doc", ".md", ".markdown", ".yml", ".yaml", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. OpenSRE supports .pdf, .docx, .doc, .md, and .yml runbooks."
        )

    clean_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename.replace(' ', '_')}"
    dest_path = os.path.join(_UPLOAD_DIR, clean_filename)

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Parse document using local 100% offline parser
    try:
        parsed_doc = parse_runbook_document(dest_path)
    except Exception as e:
        logger.error(f"Failed to parse runbook document: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to parse document: {str(e)}")

    doc_title = title or parsed_doc.get("title") or filename
    runbook_id = f"rb-{str(uuid4())[:8]}"

    runbook_ref = ProjectRunbookRef(
        id=runbook_id,
        filename=clean_filename,
        title=doc_title,
        format=ext.lstrip("."),
        uploaded_at=datetime.now(timezone.utc).isoformat(),
        file_path=dest_path,
        size_bytes=os.path.getsize(dest_path) if os.path.exists(dest_path) else 0,
    )

    # If linked to a project, attach to Project Passport
    linked_project = None
    if project_id:
        linked_project = project_store.attach_runbook(project_id, runbook_ref)

    return {
        "status": "success",
        "runbook_id": runbook_id,
        "title": doc_title,
        "format": ext.lstrip("."),
        "filename": clean_filename,
        "extracted_sop": parsed_doc.get("extracted_sop", {}),
        "sections_count": len(parsed_doc.get("sections", [])),
        "chunks_indexed": len(parsed_doc.get("sections", [])) or 1,
        "linked_project": linked_project.name if linked_project else None,
        "message": f"Successfully parsed and indexed {doc_title} ({ext.lstrip('.').upper()})",
    }


@router.get("/uploaded")
def list_uploaded_runbooks():
    """Lists all user-uploaded multi-format runbooks."""
    if not os.path.exists(_UPLOAD_DIR):
        return []

    files = []
    for f in os.listdir(_UPLOAD_DIR):
        f_path = os.path.join(_UPLOAD_DIR, f)
        if os.path.isfile(f_path):
            ext = os.path.splitext(f)[1].lower().lstrip(".")
            files.append({
                "filename": f,
                "format": ext,
                "size_bytes": os.path.getsize(f_path),
                "modified_at": datetime.fromtimestamp(os.path.getmtime(f_path), tz=timezone.utc).isoformat(),
            })
    return sorted(files, key=lambda x: x["modified_at"], reverse=True)


@router.delete("/uploaded/{filename}")
def delete_uploaded_runbook(filename: str):
    """Deletes an uploaded runbook file."""
    f_path = os.path.join(_UPLOAD_DIR, filename)
    if os.path.exists(f_path):
        os.remove(f_path)
        return {"status": "deleted", "filename": filename}
    raise HTTPException(status_code=404, detail="Runbook file not found")
