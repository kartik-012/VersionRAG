from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.document import DocumentVersion, Document
from app.models.chunk import DocumentChunk
from app.schemas.document import DocumentVersionDetail, DocumentVersionRead, DocumentChunkRead

router = APIRouter(prefix="/versions", tags=["Document Versions"])

@router.get("/{version_id}", response_model=DocumentVersionDetail)
def get_version_detail(version_id: str, db: Session = Depends(get_db)):
    """Fetch complete version information including raw document content for the Document Reader."""
    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    res = DocumentVersionDetail.model_validate(version)
    res.chunks_count = len(version.chunks)
    return res

@router.get("/{version_id}/chunks", response_model=List[DocumentChunkRead])
def list_version_chunks(version_id: str, db: Session = Depends(get_db)):
    """List all version-tagged atomic chunks for inspection."""
    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    chunks = db.query(DocumentChunk).filter(DocumentChunk.version_id == version_id).order_by(DocumentChunk.chunk_index).all()
    return [DocumentChunkRead.model_validate(c) for c in chunks]

@router.patch("/{version_id}")
def update_version_tag(
    version_id: str,
    version_tag: str,
    db: Session = Depends(get_db)
):
    """Manual override for version tag if detection required user correction."""
    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    version.version_tag = version_tag
    # Update chunk tags
    for ch in version.chunks:
        ch.version_tag = version_tag
    db.commit()
    return {"message": "Version tag updated", "version_tag": version_tag}
