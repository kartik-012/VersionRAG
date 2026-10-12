import numpy as np
from app.models.chunk import DocumentChunk
from app.services.embedding_service import embedding_service
from app.services.hybrid_index_service import (
    tokenize_code_aware,
    extract_api_symbols,
    BM25SparseIndex,
    DenseMatrixIndex,
    CrossEncoderReranker,
    PartitionedHybridIndex,
    PartitionedIndexManager,
)


def _make_dummy_chunk(
    chunk_id: str,
    version_tag: str,
    section_title: str,
    content: str,
    chunk_index: int = 0,
) -> DocumentChunk:
    emb = embedding_service.get_embedding(content)
    return DocumentChunk(
        id=chunk_id,
        workspace_id="ws-1",
        project_id="proj-1",
        document_id="doc-1",
        version_id=f"ver-{version_tag}",
        version_tag=version_tag,
        chunk_index=chunk_index,
        section_title=section_title,
        page_number=1,
        content=content,
        token_count=len(content.split()),
        embedding=emb,
        chunk_metadata={},
    )


def test_code_aware_tokenization_and_symbol_extraction():
    text = "In v16.0.0, use assert.partialDeepStrictEqual(actual, expected) or CallTracker.verify()."
    tokens = tokenize_code_aware(text)

    # Full dotted symbols preserved
    assert "assert.partialdeepstrictequal" in tokens
    assert "calltracker.verify" in tokens
    # Decomposed camelCase sub-tokens preserved
    assert "partial" in tokens
    assert "deep" in tokens
    assert "strict" in tokens
    assert "equal" in tokens
    # Version prefix normalization
    assert "v16.0.0" in tokens
    assert "v16" in tokens

    symbols = extract_api_symbols(text)
    assert "assert.partialdeepstrictequal" in symbols
    assert "partialdeepstrictequal" in symbols
    assert "calltracker.verify" in symbols


def test_vectorized_dense_matrix_cosine_accuracy():
    texts = [
        "assert.deepEqual(actual, expected) tests for deep equality using coercive comparison.",
        "assert.partialDeepStrictEqual(actual, expected) verifies subset structural properties in v16.",
        "CallTracker is an experimental feature introduced in v14.0.0 and deprecated in v15.14.0.",
    ]
    embeddings = [embedding_service.get_embedding(t) for t in texts]
    query_vec = embedding_service.get_embedding("How does partialDeepStrictEqual verify subset properties?")

    matrix_index = DenseMatrixIndex(dimension=embedding_service.dimension)
    matrix_index.build(embeddings)
    vectorized_scores = matrix_index.score_all(query_vec)

    assert len(vectorized_scores) == 3
    for i, emb in enumerate(embeddings):
        scalar_sim = max(0.0, embedding_service.cosine_similarity(query_vec, emb))
        assert np.isclose(vectorized_scores[i], scalar_sim, atol=1e-5)


def test_okapi_bm25_idf_and_ranking():
    docs = [
        tokenize_code_aware("General overview of the Node.js assertion module and standard usage."),
        tokenize_code_aware("assert.partialDeepStrictEqual(actual, expected[, message]) subset deep comparison."),
        tokenize_code_aware("Legacy assertion helper methods and general error throwing notes."),
    ]
    bm25 = BM25SparseIndex(k1=1.5, b=0.75)
    bm25.build(docs)

    query_tokens = tokenize_code_aware("How to use assert.partialDeepStrictEqual for subset comparison?")
    scores = bm25.score_all(query_tokens)

    # Document 1 containing the exact rare API symbol must strictly outscore generic documents
    assert scores[1] > scores[0]
    assert scores[1] > scores[2]
    assert scores[1] > 0.0


def test_semantic_ontology_synonym_matching():
    """
    Verifies Solution 2: Even when zero literal keywords overlap ('retired and phased out' vs 'Deprecated'),
    the Semantic Ontology Vectorizer maps both to CONCEPT_DEPRECATION and produces strong cosine similarity.
    """
    query_vec = embedding_service.get_embedding("Which feature was retired and phased out as obsolete?")
    deprecated_doc_vec = embedding_service.get_embedding("CallTracker was deprecated in v15.14.0.")
    unrelated_doc_vec = embedding_service.get_embedding("Regular expression pattern matching for strings.")

    sim_deprecated = embedding_service.cosine_similarity(query_vec, deprecated_doc_vec)
    sim_unrelated = embedding_service.cosine_similarity(query_vec, unrelated_doc_vec)

    assert sim_deprecated > sim_unrelated
    assert sim_deprecated > 0.30


def test_cross_encoder_reranker_pairwise_scoring():
    """Verifies Stage-2 Cross-Encoder pairwise interaction scoring."""
    question = "Which class was phased out and deprecated in v15?"
    q_tokens = tokenize_code_aware(question)
    q_concepts = embedding_service.expand_semantic_concepts(question)
    q_symbols = extract_api_symbols(question)

    relevant_chunk = _make_dummy_chunk(
        "c-rel",
        "v15.14.0",
        "Class: assert.CallTracker",
        "Deprecated in v15.14.0: CallTracker is scheduled for removal.",
    )
    irrelevant_chunk = _make_dummy_chunk(
        "c-irrel",
        "v15.14.0",
        "assert.ok(value)",
        "Tests if value is truthy. Equivalent to assert.equal(!!value, true).",
    )

    score_rel = CrossEncoderReranker.score_pair(
        question=question,
        query_tokens=q_tokens,
        query_concepts=q_concepts,
        query_symbols=q_symbols,
        chunk=relevant_chunk,
        chunk_tokens=tokenize_code_aware(relevant_chunk.content),
        chunk_concepts=embedding_service.expand_semantic_concepts(relevant_chunk.content),
        chunk_symbols=extract_api_symbols(relevant_chunk.content),
    )
    score_irrel = CrossEncoderReranker.score_pair(
        question=question,
        query_tokens=q_tokens,
        query_concepts=q_concepts,
        query_symbols=q_symbols,
        chunk=irrelevant_chunk,
        chunk_tokens=tokenize_code_aware(irrelevant_chunk.content),
        chunk_concepts=embedding_service.expand_semantic_concepts(irrelevant_chunk.content),
        chunk_symbols=extract_api_symbols(irrelevant_chunk.content),
    )

    assert score_rel > score_irrel
    assert score_rel >= 0.35


def test_reciprocal_rank_fusion_and_telemetry():
    chunks = [
        _make_dummy_chunk(
            "c1",
            "v15.14.0",
            "Overview",
            "The assert module provides a set of assertion functions for verifying invariants.",
            0,
        ),
        _make_dummy_chunk(
            "c2",
            "v15.14.0",
            "Class: assert.CallTracker",
            "Deprecated in v15.14.0: CallTracker is scheduled for removal. Use mock timers and functions instead.",
            1,
        ),
        _make_dummy_chunk(
            "c3",
            "v15.14.0",
            "assert.deepStrictEqual",
            "Tests for deep equality between the actual and expected parameters using Object.is.",
            2,
        ),
    ]

    hybrid_idx = PartitionedHybridIndex(signature="sig-test", chunks=chunks)
    hits = hybrid_idx.search(
        question="Why is assert.CallTracker deprecated in v15.14.0?",
        target_version="v15.14.0",
        top_k=3,
    )

    assert len(hits) == 3
    # Top hit must be the CallTracker chunk
    assert hits[0].chunk.id == "c2"
    assert hits[0].symbol_boost > 0.0
    assert hits[0].cross_encoder_score > 0.0
    assert hits[0].final_score > hits[1].final_score

    # Verify telemetry was injected into chunk_metadata
    telemetry = hits[0].chunk.chunk_metadata.get("retrieval_telemetry")
    assert telemetry is not None
    assert telemetry["engine"] == "hybrid_bm25_dense_rrf_cross_encoder"
    assert telemetry["dense_rank"] >= 1
    assert telemetry["bm25_rank"] == 1
    assert telemetry["cross_encoder_score"] > 0.0
    assert 0.0 < telemetry["rrf_score"] <= 1.0
    assert telemetry["raw_rrf_score"] > 0.0
    assert "1/(60+" in telemetry["rrf_formula"]
    assert telemetry["ast_symbol_matched"] is not None


def test_partitioned_index_cache_and_invalidation():
    manager = PartitionedIndexManager(max_partitions=16)
    c1 = _make_dummy_chunk("c1", "v14.0.0", "Intro", "Node.js v14 assert documentation", 0)
    c2 = _make_dummy_chunk("c2", "v14.0.0", "DeepEqual", "assert.deepEqual behavior in v14", 1)

    idx_first = manager.get_or_build("proj-1", "VER:v14.0.0", [c1])
    idx_cached = manager.get_or_build("proj-1", "VER:v14.0.0", [c1])
    assert idx_first is idx_cached

    # Adding a chunk must invalidate the signature and rebuild the index automatically
    idx_rebuilt = manager.get_or_build("proj-1", "VER:v14.0.0", [c1, c2])
    assert idx_rebuilt is not idx_first
    assert len(idx_rebuilt.chunks) == 2

    # Verify PostgreSQL pgvector HNSW DDL and automatic SQLite fallback hook
    ddl = PartitionedIndexManager.get_pgvector_hnsw_ddl(embedding_dim=256)
    assert "CREATE EXTENSION IF NOT EXISTS vector" in ddl
    assert "USING hnsw (embedding_vec vector_cosine_ops)" in ddl
    assert PartitionedIndexManager.query_pgvector_hnsw_candidates(
        db=None, project_id="proj-1", query_vector=[0.1] * 256, version_tag="v14.0.0"
    ) is None

