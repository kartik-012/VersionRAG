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
