import json
import re
import time
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Tuple, Iterator
from app.core.database import get_db
from app.core.deps import get_current_user, get_project_and_membership
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.project import Project
from app.models.conversation import Conversation, Message, Citation
from app.schemas.rag import (
    QueryRequest, QueryResponse, ConversationRead, MessageRead, CitationRead, ConfidenceLevel
)
from app.services.rag_service import rag_service

router = APIRouter(prefix="/query", tags=["AI Query & RAG"])


def _persist_query_exchange(
    db: Session,
    req: QueryRequest,
    current_user: User,
    result: dict
) -> QueryResponse:
    """Persist Conversation, User Message, Assistant Message, and Citations in DB."""
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

    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.question,
        target_version=req.target_version,
        scope=req.scope
    )
    db.add(user_msg)
    db.flush()

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
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = rag_service.execute_query(
        db=db,
        project_id=req.project_id,
        question=req.question,
        conversation_id=req.conversation_id,
        user_id=current_user.id,
        target_version=req.target_version,
        scope=req.scope,
        compare_to_version=req.compare_to_version
    )

    return _persist_query_exchange(db=db, req=req, current_user=current_user, result=result)


@router.post("/stream")
def stream_version_aware_query(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events (SSE) streaming endpoint for VersionRAG.
    Streams live 4-stage reasoning telemetry followed by token-by-token grounded synthesis
    and the final persisted QueryResponse with verified citations.
    """
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    def sse_event_generator() -> Iterator[str]:
        start_time = time.time()

        # Stage 1: Query Classification & Version Lock
        archetype, detected_target_v, detected_compare_v = rag_service.classify_query(req.question)
        final_target_v = req.target_version or detected_target_v
        final_compare_v = req.compare_to_version or detected_compare_v

        yield f"data: {json.dumps({'type': 'stage', 'stage': 1, 'title': 'Query Classification & Version Lock', 'detail': f'Routed to {archetype.value} | Target Version: {final_target_v or req.scope}', 'query_type': archetype.value, 'target_version': final_target_v})}\n\n"

        # Stage 2: Partitioned Hybrid Index Retrieval (BM25 + BLAS Dense RRF)
        candidates = rag_service.retrieve_candidates(
            db=db,
            project_id=req.project_id,
            question=req.question,
            target_version=final_target_v,
            scope=req.scope,
            top_k=6,
            compare_to_version=final_compare_v,
        )
        if not candidates:
            candidates = rag_service.retrieve_candidates(
                db=db,
                project_id=req.project_id,
                question=req.question,
                target_version=None,
                scope="all",
                top_k=4,
            )

        related_versions = (
            sorted(list(set(c[0].version_tag for c in candidates)))
            if candidates
            else ([final_target_v] if final_target_v else ["v15.14.0"])
        )
        yield f"data: {json.dumps({'type': 'stage', 'stage': 2, 'title': 'Hybrid BM25 + Dense BLAS RRF Retrieval', 'detail': f'Retrieved {len(candidates)} candidate chunks across partitions {related_versions}', 'candidate_count': len(candidates), 'related_versions': related_versions})}\n\n"

        # Stage 3: Cross-Encoder Reranking & Temporal AST Diff Verification
        conf_level, conf_score, conf_reason = rag_service.calculate_confidence(
            candidates, final_target_v, archetype
        )
        has_conflict, conflict_summary = rag_service.detect_conflicts(
            candidates, db, req.project_id
        )

        yield f"data: {json.dumps({'type': 'stage', 'stage': 3, 'title': 'Cross-Encoder Reranking & Temporal Diff Check', 'detail': f'Confidence: {round(conf_score * 100)}% ({conf_level.value}) | Conflict: {bool(has_conflict)}', 'confidence_score': conf_score, 'confidence_level': conf_level.value, 'has_conflict': has_conflict})}\n\n"

        # Stage 4: Grounded Answer Synthesis & Token Streaming
        if not candidates:
            answer = (
                f"I searched the indexed documentation for **{final_target_v or 'all versions'}**, "
                f"but no direct chunk matches were found for *'{req.question}'*.\n\n"
                "**Recommendation:** Try asking about standard API functions such as `assert.deepEqual()`, `assert.strictEqual()`, `assert.match()`, `assert.CallTracker`, or version differences between v14, v15, and v16."
            )
            conf_level = ConfidenceLevel.INSUFFICIENT
            conf_score = 0.20
            conf_reason = "No matching documentation chunks found for this query in the active project."
        else:
            answer = rag_service._generate_grounded_answer(
                req.question, archetype, final_target_v, candidates, conflict_summary
            )

        yield f"data: {json.dumps({'type': 'stage', 'stage': 4, 'title': 'Grounded Token Synthesis', 'detail': 'Streaming citation-backed response tokens...'})}\n\n"

        # Stream answer tokens in word/whitespace groups
        tokens = re.findall(r"\S+\s*", answer)
        chunk_size = 4
        for idx in range(0, len(tokens), chunk_size):
            delta = "".join(tokens[idx : idx + chunk_size])
            yield f"data: {json.dumps({'type': 'token', 'delta': delta})}\n\n"

        latency_ms = int((time.time() - start_time) * 1000)

        citations = []
        for i, (ch, score) in enumerate(candidates[:4]):
            doc_title = ch.version.document.title if ch.version and ch.version.document else "Documentation"
            citations.append({
                "chunk_id": ch.id,
                "document_title": doc_title,
                "version_tag": ch.version_tag,
                "section_title": ch.section_title or "General Section",
                "page_number": ch.page_number,
                "snippet": ch.content[:300] + ("..." if len(ch.content) > 300 else ""),
                "similarity_score": round(score, 3),
                "citation_order": i + 1
            })

        result_dict = {
            "answer": answer,
            "query_type": archetype,
            "target_version": final_target_v,
            "related_versions": related_versions,
            "confidence_level": conf_level,
            "confidence_score": conf_score,
            "confidence_reason": conf_reason,
            "has_conflict": has_conflict,
            "conflict_summary": conflict_summary,
            "citations": citations,
            "latency_ms": latency_ms,
            "tokens_used": max(25, len(answer) // 4 + sum(len(c["snippet"]) // 4 for c in citations)),
        }

        persisted_response = _persist_query_exchange(
            db=db, req=req, current_user=current_user, result=result_dict
        )
        yield f"data: {json.dumps({'type': 'done', 'response': persisted_response.model_dump(mode='json')})}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
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

