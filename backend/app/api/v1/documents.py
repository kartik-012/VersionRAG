from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app.core.database import get_db
from app.core.deps import get_project_and_membership, get_workspace_membership
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.models.project import Project
from app.models.document import Document, DocumentVersion, DocumentFamily, VersionStatus
from app.schemas.document import (
    DocumentRead, DocumentCreate, DocumentVersionRead, DocumentVersionDetail, DocumentChunkRead
)
from app.services.storage_service import storage_service
from app.services.job_service import job_service
from app.services.parser_service import parser_service

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload/{project_id}", status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    version_tag: Optional[str] = Form(None),
    document_id: Optional[str] = Form(None),
    family_name: Optional[str] = Form(None),
    project_workspace_member: Tuple[Project, Workspace, WorkspaceMember] = Depends(get_project_and_membership),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, Markdown, TXT, HTML, DOCX) and trigger the 10-stage ingestion pipeline.
    """
    project, workspace, _ = project_workspace_member

    # 1. Save uploaded file to storage
    rel_path, filename, size_bytes, checksum = storage_service.save_upload(
        file=file,
        workspace_id=workspace.id,
        project_id=project.id
    )

    # 2. Extract quick hints from filename
    parsed_tag, norm_v, order_v = parser_service.parse_version_string(version_tag or filename)

    # 3. Locate or create parent Document
    if document_id:
        doc = db.query(Document).filter(Document.id == document_id, Document.project_id == project.id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Parent document not found")
    else:
        doc = Document(
            project_id=project.id,
            title="New Document",
            doc_type="documentation"
        )
        db.add(doc)
        db.flush()

    # 4. Create DocumentVersion record
    version = DocumentVersion(
        document_id=doc.id,
        version_tag=parsed_tag,
        normalized_version=norm_v,
        version_order=order_v,
        source_filename=filename,
        storage_path=rel_path,
        file_size_bytes=size_bytes,
        mime_type=file.content_type,
        status=VersionStatus.PROCESSING,
        status_message="Ingestion pipeline queued."
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    # 5. Create asynchronous tracking job
    job = job_service.create_ingestion_job(
        db=db,
        workspace_id=workspace.id,
        project_id=project.id,
        document_id=doc.id,
        version_id=version.id
    )

    # 6. Execute pipeline in background
    background_tasks.add_task(job_service.run_ingestion_pipeline, db, job.id)

    return {
        "message": "Document uploaded successfully. Processing pipeline started.",
        "document_id": doc.id,
        "version_id": version.id,
        "job_id": job.id,
        "status": "processing"
    }

@router.get("/project/{project_id}", response_model=List[DocumentRead])
def list_project_documents(
    project_id: str,
    project_workspace_member: Tuple[Project, Workspace, WorkspaceMember] = Depends(get_project_and_membership),
    db: Session = Depends(get_db)
):
    """List all documents and nested version summaries in a project."""
    project, _, _ = project_workspace_member
    docs = db.query(Document).filter(Document.project_id == project.id).all()
    result = []
    for d in docs:
        item = DocumentRead.model_validate(d)
        item.versions = [DocumentVersionRead.model_validate(v) for v in d.versions]
        item.total_versions = len(d.versions)
        item.latest_version = d.versions[-1].version_tag if d.versions else None
        result.append(item)
    return result

@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get single document detail with all versions."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    item = DocumentRead.model_validate(doc)
    item.versions = [DocumentVersionRead.model_validate(v) for v in doc.versions]
    item.total_versions = len(doc.versions)
    item.latest_version = doc.versions[-1].version_tag if doc.versions else None
    return item

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document and all its versions."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully"}
