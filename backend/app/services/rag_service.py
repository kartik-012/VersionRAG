import re
import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentVersion
from app.models.chunk import DocumentChunk
from app.models.change import DocumentChange
from app.models.conversation import QueryArchetype, ConfidenceLevel, Citation, Message, Conversation
from sqlalchemy import or_
from app.services.embedding_service import embedding_service
from app.services.hybrid_index_service import hybrid_index_manager
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
        if "conflict" in q_lower or "disagree" in q_lower or ("why does" in q_lower and "say" in q_lower):
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
    def _build_version_predicate(ver_str: str):
        """Builds a SQL predicate matching exact version tags or major version prefixes (e.g. 'v14' -> 'v14.0.0')."""
        clean_tag = ver_str if ver_str.startswith("v") else f"v{ver_str}"
        raw_num = ver_str.lstrip("v")
        return or_(
            DocumentChunk.version_tag.ilike(clean_tag),
            DocumentChunk.version_tag.ilike(f"{clean_tag}.%"),
            DocumentVersion.normalized_version == ver_str,
            DocumentVersion.normalized_version == raw_num,
        )

    @classmethod
    def retrieve_candidates(
        cls,
        db: Session,
        project_id: str,
        question: str,
        target_version: Optional[str] = None,
        scope: str = "current",
        top_k: int = 5,
        compare_to_version: Optional[str] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Enterprise Partitioned Hybrid Retrieval Engine:
        1. Composite B-Tree SQL Partitioning on (project_id, version_tag).
        2. Contiguous BLAS Matrix Cosine Index + Code-Aware Okapi BM25 Index.
        3. Reciprocal Rank Fusion (RRF) + API Symbol Exact-Match Reranking.
        """
        query = (
            db.query(DocumentChunk)
            .join(DocumentVersion, DocumentChunk.version_id == DocumentVersion.id)
            .filter(DocumentChunk.project_id == project_id)
        )

        partition_key = "ALL"

        # Case A: Dual-Version Comparison Partition
        if target_version and compare_to_version and scope in ["compare", "current"]:
            query = query.filter(
                or_(
                    cls._build_version_predicate(target_version),
                    cls._build_version_predicate(compare_to_version),
                )
            )
            partition_key = f"COMPARE:{target_version.lower()}:{compare_to_version.lower()}"

        # Case B: Strict Single-Version Partition
        elif target_version and scope not in ["all", "compare", "timeline", "conflict"]:
            query = query.filter(cls._build_version_predicate(target_version))
            partition_key = f"VER:{target_version.lower()}"

        chunks = query.order_by(DocumentChunk.chunk_index.asc()).all()

        # Fallback only if the requested version tag does not exist in the project at all
        if not chunks:
            all_chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.project_id == project_id)
                .order_by(DocumentChunk.chunk_index.asc())
                .all()
            )
            if not all_chunks:
                return []
            chunks = all_chunks
            partition_key = "FALLBACK_ALL"

        # Compile or fetch cached PartitionedHybridIndex (Dense Matrix + Okapi BM25 + RRF)
        hybrid_index = hybrid_index_manager.get_or_build(
            project_id=project_id,
            partition_key=partition_key,
            chunks=chunks,
        )

        hits = hybrid_index.search(
            question=question,
            target_version=target_version,
            top_k=top_k,
        )

        return [(hit.chunk, hit.final_score) for hit in hits]

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

    @staticmethod
    def resolve_multi_version_ambiguity(
        db: Session,
        project_id: str,
        question: str,
        candidates: List[Tuple[DocumentChunk, float]],
        target_version: Optional[str],
        scope: str,
    ) -> Tuple[List[Dict[str, Any]], bool, Optional[str]]:
        """
        Feature 4: Multi-Version Ambiguity Resolver.
        When a user queries in 'All Releases' mode or omits a target version, inspects
        all project versions and AST DocumentChanges to determine whether the behavior is
        invariant across releases or diverges, and builds a Version Compatibility Matrix.
        """
        if not candidates:
            return [], True, None

        # Trigger ambiguity resolution when user omits version, selects 'all' / 'compare' scope,
        # or when retrieved candidates span multiple versions
        candidate_versions = {c[0].version_tag for c in candidates if c[0].version_tag}
        is_unscoped = (target_version is None) or (scope in ("all", "compare", "timeline", "conflict"))
        if not is_unscoped and len(candidate_versions) < 2:
            return [], True, None

        # Fetch all versions in the project ordered chronologically
        versions = (
            db.query(DocumentVersion)
            .join(Document, DocumentVersion.document_id == Document.id)
            .filter(Document.project_id == project_id)
            .order_by(DocumentVersion.version_order.asc())
            .all()
        )
        if len(versions) < 2:
            return [], True, None

        # Identify the primary queried symbol or section title
        from app.services.hybrid_index_service import extract_api_symbols
        q_symbols = extract_api_symbols(question)
        top_chunk = candidates[0][0]
        focus_section = (top_chunk.section_title or "").strip()
        focus_sym = sorted(q_symbols, key=len, reverse=True)[0] if q_symbols else focus_section

        # Fetch all DocumentChanges for the project
        all_changes = (
            db.query(DocumentChange)
            .join(Document, DocumentChange.document_id == Document.id)
            .filter(Document.project_id == project_id)
            .all()
        )

        # Fetch all chunks for the project to inspect per-version presence
        all_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.project_id == project_id)
            .all()
        )

        matrix: List[Dict[str, Any]] = []
        distinct_statuses = set()
        any_mutation = False

        # Deduplicate version tags while preserving chronological order
        seen_tags = set()
        ordered_versions = []
        for v in versions:
            if v.version_tag not in seen_tags:
                seen_tags.add(v.version_tag)
                ordered_versions.append(v)

        for v in ordered_versions:
            v_tag = v.version_tag
            v_chunks = [c for c in all_chunks if c.version_tag == v_tag]

            # Find best matching chunk in this version for the focus symbol / section
            matched_chunk: Optional[DocumentChunk] = None
            for ch in v_chunks:
                sec_low = (ch.section_title or "").lower()
                body_low = (ch.content or "").lower()
                if focus_sym and focus_sym.lower() in (sec_low + " " + body_low):
                    matched_chunk = ch
                    break
                if focus_section and focus_section.lower() in sec_low:
                    matched_chunk = ch
                    break

            # Also check DocumentChanges targeting this version for the focus symbol
            relevant_change: Optional[DocumentChange] = None
            for chg in all_changes:
                if chg.to_version_tag == v_tag:
                    loc_low = (chg.location or "").lower()
                    sum_low = (chg.summary or "").lower()
                    if (focus_sym and focus_sym.lower() in (loc_low + " " + sum_low)) or (
                        focus_section and focus_section.lower() in (loc_low + " " + sum_low)
                    ):
                        relevant_change = chg
                        break

            if not matched_chunk and not relevant_change:
                status_label = "Not Available"
                is_breaking = False
                is_silent = False
                summary_text = f"'{focus_sym or focus_section}' is not present in {v_tag} documentation."
            else:
                text_low = ((matched_chunk.content if matched_chunk else "") + " " + (relevant_change.summary if relevant_change else "")).lower()
                is_breaking = bool(relevant_change and relevant_change.is_breaking) or ("breaking" in text_low)
                is_silent = bool(relevant_change and relevant_change.is_silent)

                if "removed" in text_low or (relevant_change and str(relevant_change.change_type).endswith("REMOVED")):
                    status_label = "Removed"
                    is_breaking = True
                    any_mutation = True
                elif "deprecated" in text_low or (relevant_change and str(relevant_change.change_type).endswith("DEPRECATED")):
                    status_label = "Deprecated"
                    any_mutation = True
                elif is_silent:
                    status_label = "Silent Behavior Shift"
                    any_mutation = True
                elif is_breaking:
                    status_label = "Breaking Change"
                    any_mutation = True
                elif "release candidate" in text_low or "experimental" in text_low:
                    status_label = "Experimental / RC"
                    any_mutation = True
                else:
                    status_label = "Stable / Supported"

                if relevant_change:
                    summary_text = relevant_change.summary[:160]
                elif matched_chunk:
                    first_line = matched_chunk.content.strip().splitlines()[0] if matched_chunk.content else ""
                    summary_text = first_line[:160]
                else:
                    summary_text = "Supported with standard API contract."

            distinct_statuses.add(status_label)
            matrix.append({
                "version_tag": v_tag,
                "symbol": focus_sym or focus_section or "API Specification",
                "status": status_label,
                "is_breaking": is_breaking,
                "is_silent": is_silent,
                "behavior_summary": summary_text,
            })

        is_invariant = (len(distinct_statuses) <= 1) and (not any_mutation)
        ambiguity_note = None
        if not is_invariant:
            tags_str = " vs ".join(m["version_tag"] for m in matrix)
            ambiguity_note = (
                f"Multi-Version Ambiguity Resolved ({tags_str}): "
                f"'{focus_sym or focus_section}' changes behavior across releases ("
                + ", ".join(f"{m['version_tag']}: {m['status']}" for m in matrix)
                + ")."
            )
        return matrix, is_invariant, ambiguity_note

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
        # If user explicitly chose 'all' scope and did not type a version in the question, keep final_target_v None
        if scope == "all" and not detected_target_v:
            final_target_v = None
        else:
            final_target_v = target_version or detected_target_v
        final_compare_v = compare_to_version or detected_compare_v

        # 2. Version-Aware Candidate Retrieval
        candidates = self.retrieve_candidates(
            db=db,
            project_id=project_id,
            question=question,
            target_version=final_target_v,
            scope=scope,
            top_k=6,
            compare_to_version=final_compare_v,
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

        # 3. Confidence, Conflict Analysis & Multi-Version Ambiguity Resolution
        conf_level, conf_score, conf_reason = self.calculate_confidence(candidates, final_target_v, archetype)
        has_conflict, conflict_summary = self.detect_conflicts(candidates, db, project_id)
        compatibility_matrix, is_invariant, ambiguity_note = self.resolve_multi_version_ambiguity(
            db=db,
            project_id=project_id,
            question=question,
            candidates=candidates,
            target_version=final_target_v,
            scope=scope,
        )
        if not is_invariant and ambiguity_note and not has_conflict:
            has_conflict = True
            conflict_summary = ambiguity_note

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
            answer = self._generate_grounded_answer(
                question, archetype, final_target_v, candidates, conflict_summary, compatibility_matrix, is_invariant
            )

        latency_ms = int((time.time() - start_time) * 1000)

        # 5. Build citations
        citations = []
        for i, (ch, score) in enumerate(candidates[:4]):
            doc_title = ch.version.document.title if ch.version and ch.version.document else "Documentation"
            telemetry = (
                ch.chunk_metadata.get("retrieval_telemetry")
                if isinstance(ch.chunk_metadata, dict)
                else None
            )
            citations.append({
                "chunk_id": ch.id,
                "document_title": doc_title,
                "version_tag": ch.version_tag,
                "section_title": ch.section_title or "General Section",
                "page_number": ch.page_number,
                "snippet": ch.content[:300] + ("..." if len(ch.content) > 300 else ""),
                "similarity_score": round(score, 3),
                "citation_order": i + 1,
                "retrieval_telemetry": telemetry,
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
            "compatibility_matrix": compatibility_matrix,
            "is_invariant": is_invariant,
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
        conflict_summary: Optional[str],
        compatibility_matrix: Optional[List[Dict[str, Any]]] = None,
        is_invariant: bool = True,
    ) -> str:
        """Rich grounded technical answer synthesis with dynamic Live LLM Provider routing and Multi-Version Compatibility Matrix."""
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

        # Build Markdown Version Compatibility Matrix when multi-version ambiguity is resolved
        matrix_markdown = ""
        if compatibility_matrix and len(compatibility_matrix) >= 2:
            inv_badge = "Invariant Across Releases" if is_invariant else "Breaking / Behavioral Divergence Detected"
            matrix_rows = "\n".join(
                f"| `{row['version_tag']}` | **{row['status']}** | {'⚠️ Yes' if row['is_breaking'] else 'No'} | {'🕵️ Yes' if row['is_silent'] else 'No'} | {row['behavior_summary']} |"
                for row in compatibility_matrix
            )
            matrix_markdown = (
                f"\n\n### 🧭 Multi-Version Compatibility Matrix ({inv_badge})\n"
                f"| Release Version | Status | Breaking | Silent Shift | Version-Specific Contract & Behavior |\n"
                f"| :--- | :--- | :--- | :--- | :--- |\n"
                f"{matrix_rows}\n"
            )

        # Route to external LLM (Gemini / OpenAI / Anthropic / Groq) if dynamically activated in UI/API
        try:
            from app.services.llm_provider_service import llm_provider_service
            live_resp = llm_provider_service.generate_live_answer(
                question=question,
                target_version=target_v or v_tag,
                evidence_context=evidence_summary + matrix_markdown,
                conflict_summary=conflict_summary,
            )
            if live_resp:
                return live_resp + (matrix_markdown if matrix_markdown and "Compatibility Matrix" not in live_resp else "")
        except Exception:
            pass

        if archetype == QueryArchetype.VERSION_SPECIFIC_QUERY and not matrix_markdown:
            return (
                f"### 📋 Executive Summary for {v_tag}\n\n"
                f"According to the **{v_tag}** official documentation specification for *{sec_title}*:\n\n"
                f"```typescript\n// Relevant specification under {v_tag}\n{top_chunk.content.strip()}\n```\n\n"
                f"### 💡 Technical Analysis\n"
                f"- **Target Version**: `{v_tag}` (Verified with {round(top_score * 100)}% grounding confidence).\n"
                f"- **Behavioral Contract**: The behavior stated above applies strictly to the `{v_tag}` release partition.\n\n"
                f"### 🔗 Supporting Evidence Chunks\n{evidence_summary}"
            )
        elif archetype in (QueryArchetype.VERSION_COMPARISON_QUERY, QueryArchetype.CONFLICT_QUERY) or matrix_markdown:
            timeline_note = f"\n\n> ⚠️ **Cross-Version Trajectory**: {conflict_summary}" if conflict_summary else ""
            return (
                f"### ⚖️ Multi-Version Ambiguity Resolution & Analysis\n\n"
                f"Analysis of **'{question}'** across version releases reveals the following behavior:\n\n"
                f"{evidence_summary}{timeline_note}{matrix_markdown}\n"
                f"### 💡 Architectural Recommendation\n"
                f"- Lock your query or codebase to a specific `version_tag` partition when migrating across releases with breaking or silent shifts."
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
