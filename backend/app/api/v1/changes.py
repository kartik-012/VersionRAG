from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.document import Document, DocumentVersion
from app.models.change import DocumentChange
from app.schemas.change import DocumentChangeRead, VersionComparisonResponse
from app.services.diff_service import diff_service

router = APIRouter(prefix="/changes", tags=["Changes & Diffing"])

@router.get("/compare", response_model=VersionComparisonResponse)
def compare_versions(
    from_version_id: str = Query(...),
    to_version_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Compare two versions directly and return structured changes plus unified diff string.
    """
    v_from = db.query(DocumentVersion).filter(DocumentVersion.id == from_version_id).first()
    v_to = db.query(DocumentVersion).filter(DocumentVersion.id == to_version_id).first()

    if not v_from or not v_to:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    # Fetch stored changes or compute on the fly
    changes = (
        db.query(DocumentChange)
        .filter(
            DocumentChange.from_version_id == from_version_id,
            DocumentChange.to_version_id == to_version_id
        )
        .all()
    )

    if not changes and v_from.raw_content and v_to.raw_content:
        computed_changes, summary_counts = diff_service.compute_all_changes(
            old_content=v_from.raw_content,
            new_content=v_to.raw_content,
            from_tag=v_from.version_tag,
            to_tag=v_to.version_tag
        )
    else:
        computed_changes = [DocumentChangeRead.model_validate(c) for c in changes]
        summary_counts = {
            "total": len(changes),
            "added": sum(1 for c in changes if c.change_type == "added"),
            "modified": sum(1 for c in changes if c.change_type == "modified"),
            "removed": sum(1 for c in changes if c.change_type == "removed"),
            "deprecated": sum(1 for c in changes if c.change_type == "deprecated"),
            "breaking": sum(1 for c in changes if c.is_breaking),
            "silent": sum(1 for c in changes if c.is_silent)
        }

    unified_diff = diff_service.generate_unified_diff(
        old_text=v_from.raw_content or "",
        new_text=v_to.raw_content or "",
        from_tag=v_from.version_tag,
        to_tag=v_to.version_tag
    )

    return VersionComparisonResponse(
        document_id=v_from.document_id,
        from_version_tag=v_from.version_tag,
        to_version_tag=v_to.version_tag,
        summary=summary_counts,
        changes=computed_changes,
        unified_diff=unified_diff
    )

@router.get("/document/{document_id}/timeline", response_model=List[DocumentChangeRead])
def get_document_timeline(document_id: str, db: Session = Depends(get_db)):
    """Fetch complete chronological change history for a document across all versions."""
    changes = (
        db.query(DocumentChange)
        .filter(DocumentChange.document_id == document_id)
        .order_by(DocumentChange.created_at.asc())
        .all()
    )
    return [DocumentChangeRead.model_validate(c) for c in changes]

@router.post("/migration-guide")
def get_migration_guide(
    from_version_id: str = Query(...),
    to_version_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Synthesize an automated step-by-step migration guide with code refactor transformation snippets.
    """
    v_from = db.query(DocumentVersion).filter(DocumentVersion.id == from_version_id).first()
    v_to = db.query(DocumentVersion).filter(DocumentVersion.id == to_version_id).first()
    if not v_from or not v_to:
        raise HTTPException(status_code=404, detail="Version not found")

    changes = (
        db.query(DocumentChange)
        .filter(
            DocumentChange.from_version_id == from_version_id,
            DocumentChange.to_version_id == to_version_id
        )
        .all()
    )
    raw_changes = [
        {
            "location": c.location,
            "change_type": c.change_type,
            "severity": c.severity,
            "is_breaking": c.is_breaking,
            "is_silent": c.is_silent,
            "summary": c.summary,
            "old_content": c.old_content,
            "new_content": c.new_content
        }
        for c in changes
    ]

    return diff_service.generate_migration_guide(
        from_tag=v_from.version_tag,
        to_tag=v_to.version_tag,
        changes=raw_changes
    )

@router.get("/symbol-history")
def get_symbol_history(
    document_id: str = Query(...),
    symbol: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Track the exact signature, behavior, and deprecation status of an API symbol across all releases.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    versions = sorted(doc.versions, key=lambda v: v.version_order)
    return diff_service.extract_symbol_history(symbol, versions)

@router.post("/generate-changelog")
def generate_changelog(
    version_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Synthesizes executive summary and structured release notes from detected version diffs.
    """
    ver = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")

    changes = db.query(DocumentChange).filter(DocumentChange.to_version_id == version_id).all()
    raw_changes = [
        {
            "summary": c.summary,
            "change_type": c.change_type,
            "is_breaking": c.is_breaking,
            "is_silent": c.is_silent
        }
        for c in changes
    ]
    return diff_service.synthesize_release_notes(ver.version_tag, raw_changes)

