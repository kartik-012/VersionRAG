from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Tuple
from app.core.database import get_db
from app.core.deps import get_current_user, get_project_and_membership
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.project import Project
from app.models.conversation import Conversation, Message, Citation
from app.schemas.rag import QueryRequest, QueryResponse, ConversationRead, MessageRead, CitationRead
from app.services.rag_service import rag_service

router = APIRouter(prefix="/query", tags=["AI Query & RAG"])

@router.post("", response_model=QueryResponse)
def execute_version_aware_query(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a version-aware RAG query against project documentation.
    Preserves version context, validates evidence, and generates verified citations.
    """
    # 1. Validate project membership
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Get or create conversation session
    if req.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == req.conversation_id,
            Conversation.project_id == req.project_id
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation session not found")
    else:
        conv = Conversation(
            project_id=req.project_id,
            user_id=current_user.id,
            title=req.question[:60] + ("..." if len(req.question) > 60 else "")
        )
        db.add(conv)
        db.flush()

    # 3. Store user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.question,
        target_version=req.target_version,
        scope=req.scope
    )
    db.add(user_msg)
    db.flush()

    # 4. Execute VersionRAG Pipeline
    result = rag_service.execute_query(
        db=db,
        project_id=req.project_id,
        question=req.question,
        conversation_id=conv.id,
        user_id=current_user.id,
        target_version=req.target_version,
        scope=req.scope,
        compare_to_version=req.compare_to_version
    )

    # 5. Store Assistant Message & Citations
    asst_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=result["answer"],
        query_type=result["query_type"],
        target_version=result["target_version"],
        scope=req.scope,
        confidence_level=result["confidence_level"],
        confidence_score=result["confidence_score"],
        confidence_reason=result["confidence_reason"],
        has_conflict="true" if result["has_conflict"] else "false",
        conflict_summary=result["conflict_summary"],
        latency_ms=result["latency_ms"],
        tokens_used=result["tokens_used"],
        model_name="VersionRAG-v1-HybridEngine"
    )
    db.add(asst_msg)
    db.flush()

    citations_resp = []
    created_cit_objs = []
    for cit in result["citations"]:
        cit_obj = Citation(
            message_id=asst_msg.id,
            chunk_id=cit.get("chunk_id"),
            document_title=cit["document_title"],
            version_tag=cit["version_tag"],
            section_title=cit.get("section_title"),
            page_number=cit.get("page_number", 1),
            snippet=cit["snippet"],
            similarity_score=cit["similarity_score"],
            citation_order=cit["citation_order"]
        )
        db.add(cit_obj)
        created_cit_objs.append(cit_obj)

    db.flush()
    for cit_obj in created_cit_objs:
        citations_resp.append(CitationRead.model_validate(cit_obj))

    db.commit()

    return QueryResponse(
        conversation_id=conv.id,
        message_id=asst_msg.id,
        question=req.question,
        answer=result["answer"],
        query_type=result["query_type"],
        target_version=result["target_version"],
        related_versions=result["related_versions"],
        confidence_level=result["confidence_level"],
        confidence_score=result["confidence_score"],
        confidence_reason=result["confidence_reason"],
        has_conflict=result["has_conflict"],
        conflict_summary=result["conflict_summary"],
        citations=citations_resp,
        latency_ms=result["latency_ms"],
        tokens_used=result["tokens_used"]
    )

@router.get("/conversations/{project_id}", response_model=List[ConversationRead])
def list_conversations(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all previous query sessions for a project."""
    convs = (
        db.query(Conversation)
        .filter(Conversation.project_id == project_id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return [ConversationRead.model_validate(c) for c in convs]
