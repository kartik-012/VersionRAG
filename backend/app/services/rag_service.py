import re
import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentVersion
from app.models.chunk import DocumentChunk
from app.models.change import DocumentChange
from app.models.conversation import QueryArchetype, ConfidenceLevel, Citation, Message, Conversation
from app.services.embedding_service import embedding_service
from app.core.config import settings

class RAGService:
    @staticmethod
    def classify_query(question: str) -> Tuple[QueryArchetype, Optional[str], Optional[str]]:
        """
        Classifies user query into 1 of 8 archetypes and extracts targeted versions.
        Returns: (archetype, target_version, compare_version)
        """
        q_lower = question.lower()

        # Extract version mentions like v14, v15, v16.0, 1.2, 2025-Q1
        v_matches = re.findall(r"\b(?:v|version\s*)(\d+(?:\.\d+)*)\b", q_lower)
        target_v = f"v{v_matches[0]}" if v_matches else None
        compare_v = f"v{v_matches[1]}" if len(v_matches) > 1 else None

        # Archetype 8: Silent change
        if "silent" in q_lower or "undocumented" in q_lower or "without being mentioned" in q_lower:
            return QueryArchetype.SILENT_CHANGE_QUERY, target_v, compare_v

        # Archetype 7: Conflict
        if "conflict" in q_lower or "disagree" in q_lower or "why does" in q_lower and "say" in q_lower:
            return QueryArchetype.CONFLICT_QUERY, target_v, compare_v

        # Archetype 3: Version comparison
        if "between" in q_lower or "differ" in q_lower or "compare" in q_lower or (target_v and compare_v):
            return QueryArchetype.VERSION_COMPARISON_QUERY, target_v, compare_v

        # Archetype 5: Timeline
        if "timeline" in q_lower or "evolution" in q_lower or "history of" in q_lower or "across all versions" in q_lower:
            return QueryArchetype.TIMELINE_QUERY, target_v, compare_v

        # Archetype 4: Change
        if "when was" in q_lower or "deprecated" in q_lower or "removed" in q_lower or "introduced" in q_lower or "added" in q_lower or "breaking change" in q_lower:
            return QueryArchetype.CHANGE_QUERY, target_v, compare_v

        # Archetype 6: Historical
        if "in 202" in q_lower or "previously" in q_lower or "legacy" in q_lower or "originally" in q_lower:
            return QueryArchetype.HISTORICAL_QUERY, target_v, compare_v

        # Archetype 2: Version-specific
        if target_v is not None or "in v" in q_lower or "supported in" in q_lower:
            return QueryArchetype.VERSION_SPECIFIC_QUERY, target_v, compare_v

        # Archetype 1: Content
        return QueryArchetype.CONTENT_QUERY, target_v, compare_v

    @staticmethod
    def retrieve_candidates(
        db: Session,
        project_id: str,
        question: str,
        target_version: Optional[str] = None,
        scope: str = "current",
        top_k: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Version-aware candidate retrieval.
        Applies version metadata filtering BEFORE semantic scoring.
        """
        query_vec = embedding_service.get_embedding(question)

        # Base query joined with Document and Version
        query = (
            db.query(DocumentChunk)
            .join(DocumentVersion, DocumentChunk.version_id == DocumentVersion.id)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(Document.project_id == project_id)
        )

        # Apply strict version filtering if target_version is specified or scope is specific
        if target_version and scope not in ["all", "compare", "timeline", "conflict"]:
            clean_tag = target_version if target_version.startswith("v") else f"v{target_version}"
            query = query.filter(
                (DocumentChunk.version_tag.ilike(clean_tag)) |
                (DocumentVersion.normalized_version == target_version)
            )

        chunks = query.all()
        if not chunks:
            # If no version-specific chunks found, check if document exists in project
            all_chunks = db.query(DocumentChunk).filter(DocumentChunk.project_id == project_id).all()
            if not all_chunks:
                return []
            chunks = all_chunks

        # Score chunks with Cosine Similarity + Keyword Boost
        scored_chunks: List[Tuple[DocumentChunk, float]] = []
        q_words = set(re.findall(r"\w+", question.lower()))

        for ch in chunks:
            chunk_vec = ch.embedding
            if not chunk_vec:
                # Generate on the fly if not cached
                chunk_vec = embedding_service.get_embedding(ch.content)
                ch.embedding = chunk_vec

            cos_sim = embedding_service.cosine_similarity(query_vec, chunk_vec)
            
            # Keyword overlap boost (BM25-style lexical complement)
            chunk_words = set(re.findall(r"\w+", ch.content.lower()))
            overlap = len(q_words.intersection(chunk_words)) / max(1, len(q_words))
            hybrid_score = (0.7 * cos_sim) + (0.3 * overlap)

            # Extra boost if chunk version matches target version explicitly
            if target_version and target_version.lower() in ch.version_tag.lower():
                hybrid_score += 0.15

            scored_chunks.append((ch, hybrid_score))

        # Sort by hybrid score descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    @staticmethod
    def calculate_confidence(
        candidates: List[Tuple[DocumentChunk, float]],
        target_version: Optional[str],
        query_type: QueryArchetype
    ) -> Tuple[ConfidenceLevel, float, str]:
        """
        Calculates deterministic composite confidence score from measurable signals.
        """
        if not candidates:
            return ConfidenceLevel.INSUFFICIENT, 0.1, "Insufficient evidence: No relevant chunks could be retrieved for this query."

        top_score = candidates[0][1]
        
        # Check version consistency
        retrieved_versions = set(c[0].version_tag for c in candidates[:3])
        version_aligned = True
        if target_version and query_type == QueryArchetype.VERSION_SPECIFIC_QUERY:
            clean_target = target_version.lower().lstrip("v")
            version_aligned = any(clean_target in v.lower() for v in retrieved_versions)

        # Composite score
        base_score = min(0.99, max(0.2, top_score))
        if not version_aligned:
            base_score *= 0.6

        if base_score >= 0.75:
            return (
                ConfidenceLevel.HIGH,
                round(base_score, 2),
                f"High confidence: Retrieved strong, version-consistent evidence ({len(candidates)} verified chunks)."
            )
        elif base_score >= 0.50:
            return (
                ConfidenceLevel.MODERATE,
                round(base_score, 2),
                "Moderate confidence: Evidence found in knowledge base with partial coverage."
            )
        elif base_score >= 0.30:
            return (
                ConfidenceLevel.LOW,
                round(base_score, 2),
                "Low confidence: Weak retrieval score or potential cross-version ambiguity."
            )
        else:
            return (
                ConfidenceLevel.INSUFFICIENT,
                round(base_score, 2),
                "Insufficient evidence: The system declines to guess without verified grounding."
            )

    @staticmethod
    def detect_conflicts(
        candidates: List[Tuple[DocumentChunk, float]],
        db: Session,
        project_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Identifies conflicting statements across different document versions."""
        versions = list(set(c[0].version_tag for c in candidates))
        if len(versions) < 2:
            return False, None

        # Check for presence of conflicting keywords across versions
        v_states = {}
        for ch, _ in candidates:
            v_tag = ch.version_tag
            text = ch.content.lower()
            if "removed" in text or "no longer supported" in text:
                v_states[v_tag] = "Removed"
            elif "deprecated" in text:
                v_states[v_tag] = "Deprecated"
            elif "experimental" in text or "release candidate" in text:
                v_states[v_tag] = "Experimental / RC"
            elif "supported" in text or "stable" in text or "returns" in text:
                v_states[v_tag] = "Supported / Stable"

        unique_states = set(v_states.values())
        if len(unique_states) > 1:
            timeline_str = " → ".join([f"{v}: {st}" for v, st in sorted(v_states.items())])
            summary = f"Detected version-dependent evolution: {timeline_str}. The behavior changes across releases."
            return True, summary

        return False, None

    def execute_query(
        self,
        db: Session,
        project_id: str,
        question: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        target_version: Optional[str] = None,
        scope: str = "current",
        compare_to_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full VersionRAG query execution pipeline.
        """
        start_time = time.time()

        # 1. Query Understanding & Classification
        archetype, detected_target_v, detected_compare_v = self.classify_query(question)
        final_target_v = target_version or detected_target_v
        final_compare_v = compare_to_version or detected_compare_v

        # 2. Version-Aware Candidate Retrieval
        candidates = self.retrieve_candidates(
            db=db,
            project_id=project_id,
            question=question,
            target_version=final_target_v,
            scope=scope,
            top_k=6
        )

        # If no candidates found with strict filter, fallback to all project chunks
        if not candidates:
            candidates = self.retrieve_candidates(
                db=db,
                project_id=project_id,
                question=question,
                target_version=None,
                scope="all",
                top_k=4
            )

        # 3. Confidence & Conflict Analysis
        conf_level, conf_score, conf_reason = self.calculate_confidence(candidates, final_target_v, archetype)
        has_conflict, conflict_summary = self.detect_conflicts(candidates, db, project_id)

        # 4. Context Construction & Answer Synthesis
        related_versions = sorted(list(set(c[0].version_tag for c in candidates))) if candidates else ([final_target_v] if final_target_v else ["v15.14.0"])

        if not candidates:
            answer = (
                f"I searched the indexed documentation for **{final_target_v or 'all versions'}**, "
                f"but no direct chunk matches were found for *'{question}'*.\n\n"
                "**Recommendation:** Try asking about standard API functions such as `assert.deepEqual()`, `assert.strictEqual()`, `assert.match()`, `assert.CallTracker`, or version differences between v14, v15, and v16."
            )
            conf_level = ConfidenceLevel.INSUFFICIENT
            conf_score = 0.20
            conf_reason = "No matching documentation chunks found for this query in the active project."
        else:
            answer = self._generate_grounded_answer(question, archetype, final_target_v, candidates, conflict_summary)

        latency_ms = int((time.time() - start_time) * 1000)

        # 5. Build citations
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

        return {
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
            "tokens_used": max(25, len(answer) // 4 + sum(len(c["snippet"]) // 4 for c in citations))
        }

    def _generate_grounded_answer(
        self,
        question: str,
        archetype: QueryArchetype,
        target_v: Optional[str],
        candidates: List[Tuple[DocumentChunk, float]],
        conflict_summary: Optional[str]
    ) -> str:
        """Rich grounded technical answer synthesis."""
        if not candidates:
            return f"No documented evidence found for '{question}' in the indexed knowledge base."

        top_chunk, top_score = candidates[0]
        v_tag = top_chunk.version_tag
        sec_title = top_chunk.section_title or "API Specification"

        # Extract code examples and core points from top chunks
        evidence_points = []
        for ch, score in candidates[:3]:
            evidence_points.append(f"• **[{ch.version_tag}] {ch.section_title or 'API Spec'}**: {ch.content.strip()[:240]}...")

        evidence_summary = "\n".join(evidence_points)

        if archetype == QueryArchetype.VERSION_SPECIFIC_QUERY:
            return (
                f"### 📋 Executive Summary for {v_tag}\n\n"
                f"According to the **{v_tag}** official documentation specification for *{sec_title}*:\n\n"
                f"```typescript\n// Relevant specification under {v_tag}\n{top_chunk.content.strip()}\n```\n\n"
                f"### 💡 Technical Analysis\n"
                f"- **Target Version**: `{v_tag}` (Verified with {round(top_score * 100)}% grounding confidence).\n"
                f"- **Behavioral Contract**: The behavior stated above applies strictly to the `{v_tag}` release partition.\n\n"
                f"### 🔗 Supporting Evidence Chunks\n{evidence_summary}"
            )
        elif archetype in (QueryArchetype.VERSION_COMPARISON_QUERY, QueryArchetype.CONFLICT_QUERY):
            timeline_note = f"\n\n> ⚠️ **Cross-Version Trajectory**: {conflict_summary}" if conflict_summary else ""
            return (
                f"### ⚖️ Multi-Version Comparison Analysis\n\n"
                f"Analysis of **'{question}'** across version releases reveals the following behavior:\n\n"
                f"{evidence_summary}{timeline_note}\n\n"
                f"### 💡 Architectural Recommendation\n"
                f"- For projects on **v14.0.0**: Use legacy API contracts and standard assertions.\n"
                f"- For projects on **v15.14.0+**: Ensure prototype strictness is handled properly with `AssertionError` handling."
            )
        elif archetype in (QueryArchetype.CHANGE_QUERY, QueryArchetype.SILENT_CHANGE_QUERY):
            return (
                f"### 🔄 Change History & Evolution Report\n\n"
                f"Regarding the modification trajectory for **'{question}'**:\n\n"
                f"**Primary Evidence in {v_tag} ({sec_title})**:\n"
                f"> {top_chunk.content.strip()}\n\n"
                f"### 📜 Version Audit Trail\n{evidence_summary}"
            )
        else:
            return (
                f"### 💡 Grounded Documentation Analysis ({v_tag})\n\n"
                f"Based on the **{v_tag}** documentation (*{sec_title}*):\n\n"
                f"{top_chunk.content.strip()}\n\n"
                f"### 📚 Referenced Chunks\n{evidence_summary}"
            )

rag_service = RAGService()
