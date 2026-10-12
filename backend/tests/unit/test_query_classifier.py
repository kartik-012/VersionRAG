from app.services.rag_service import rag_service
from app.models.conversation import QueryArchetype, ConfidenceLevel

def test_query_archetype_routing():
    # 1. Version-specific
    q1 = "Is function X supported in v15?"
    arch1, target1, _ = rag_service.classify_query(q1)
    assert arch1 == QueryArchetype.VERSION_SPECIFIC_QUERY
    assert target1 == "v15"

    # 2. Version comparison
    q2 = "What changed between v14 and v15?"
    arch2, target2, compare2 = rag_service.classify_query(q2)
    assert arch2 == QueryArchetype.VERSION_COMPARISON_QUERY
    assert target2 == "v14"
    assert compare2 == "v15"

    # 3. Timeline
    q3 = "Show me the timeline and evolution of error handling"
    arch3, _, _ = rag_service.classify_query(q3)
    assert arch3 == QueryArchetype.TIMELINE_QUERY

    # 4. Silent change
    q4 = "Was this changed silently without being mentioned in the changelog?"
    arch4, _, _ = rag_service.classify_query(q4)
    assert arch4 == QueryArchetype.SILENT_CHANGE_QUERY

def test_confidence_insufficient_evidence():
    level, score, reason = rag_service.calculate_confidence([], "v15", QueryArchetype.VERSION_SPECIFIC_QUERY)
    assert level == ConfidenceLevel.INSUFFICIENT
    assert "insufficient" in reason.lower()


def test_multi_version_ambiguity_resolver_compatibility_matrix(db_session):
    """
    Verifies Feature 4: Multi-Version Ambiguity Resolver.
    When a user asks an unscoped question in 'All Releases' mode without specifying a version,
    the engine checks across versions and automatically generates a Version Compatibility Matrix.
    """
    from app.models.document import Document, DocumentVersion
    from app.models.chunk import DocumentChunk
    from app.models.change import DocumentChange, ChangeType, ChangeSeverity

    doc = Document(
        id="doc-ambig-1", project_id="proj-ambig-1",
        title="Node.js Assert Docs", doc_type="markdown"
    )
    db_session.add(doc)

    v14 = DocumentVersion(id="ver-14", document_id=doc.id, version_tag="v14.0.0", version_order=1, status="ready")
    v15 = DocumentVersion(id="ver-15", document_id=doc.id, version_tag="v15.14.0", version_order=2, status="ready")
    v16 = DocumentVersion(id="ver-16", document_id=doc.id, version_tag="v16.0.0", version_order=3, status="ready")
    db_session.add_all([v14, v15, v16])

    c14 = DocumentChunk(
        id="chk-14", workspace_id="ws-1", project_id="proj-ambig-1", document_id=doc.id,
        version_id="ver-14", version_tag="v14.0.0",
        chunk_index=0, section_title="assert.CallTracker",
        content="assert.CallTracker is supported for tracking callback invocations.",
    )
    c15 = DocumentChunk(
        id="chk-15", workspace_id="ws-1", project_id="proj-ambig-1", document_id=doc.id,
        version_id="ver-15", version_tag="v15.14.0",
        chunk_index=0, section_title="assert.CallTracker",
        content="Deprecated: assert.CallTracker is deprecated in v15.14.0.",
    )
    c16 = DocumentChunk(
        id="chk-16", workspace_id="ws-1", project_id="proj-ambig-1", document_id=doc.id,
        version_id="ver-16", version_tag="v16.0.0",
        chunk_index=0, section_title="assert.CallTracker",
        content="Removed: assert.CallTracker has been removed in v16.0.0.",
    )
    db_session.add_all([c14, c15, c16])

    chg = DocumentChange(
        document_id=doc.id,
        from_version_id="ver-14",
        to_version_id="ver-15",
        from_version_tag="v14.0.0",
        to_version_tag="v15.14.0",
        location="assert.CallTracker",
        change_type=ChangeType.DEPRECATED,
        severity=ChangeSeverity.HIGH,
        is_breaking=False,
        is_silent=False,
        summary="assert.CallTracker was deprecated in v15.14.0.",
    )
    db_session.add(chg)
    db_session.commit()

    res = rag_service.execute_query(
        db=db_session,
        project_id="proj-ambig-1",
        question="How does assert.CallTracker work?",
        target_version=None,
        scope="all",
    )

    assert "compatibility_matrix" in res
    matrix = res["compatibility_matrix"]
    assert len(matrix) == 3
    assert res["is_invariant"] is False
    assert res["has_conflict"] is True
    statuses = {row["version_tag"]: row["status"] for row in matrix}
    assert statuses["v14.0.0"] == "Stable / Supported"
    assert statuses["v15.14.0"] == "Deprecated"
    assert statuses["v16.0.0"] == "Removed"
    assert "Multi-Version Compatibility Matrix" in res["answer"]

