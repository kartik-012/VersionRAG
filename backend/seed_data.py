import sys
import os

# Ensure app is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.models.project import Project
from app.models.document import DocumentFamily, Document, DocumentVersion, VersionStatus
from app.models.chunk import DocumentChunk
from app.models.change import DocumentChange, ChangeType, ChangeSeverity
from app.core.security import get_password_hash
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.diff_service import diff_service
from app.services.evaluation_service import evaluation_service

DOC_V14_CONTENT = """# Node.js Assert Module — Version 14.0.0

## Overview
The `assert` module provides a set of assertion functions for verifying invariants in code.

## Functions

### assert.deepEqual(actual, expected[, message])
Tests for deep equality between the `actual` and `expected` parameters.
Primitive values are compared with the Abstract Equality Comparison (`==`).
Object wrappers are compared as their primitive values.

### assert.equal(actual, expected[, message])
Tests shallow, coercive equality between the `actual` and `expected` parameters using `==`.

### assert.match(string, regexp[, message])
Expects the `string` input to match the regular expression `regexp`. Returns `undefined` if successful, and throws an `AssertionError` if no match occurs.

### Legacy Error Handling
In version 14, assertions throw standard `Error` instances containing basic assertion messages.
"""

DOC_V15_CONTENT = """# Node.js Assert Module — Version 15.14.0

## Overview
The `assert` module provides a set of assertion functions for verifying invariants in code.

## Changelog
- **[Breaking]**: `assert.deepEqual()` now compares prototypes strictly. Object prototypes must match.
- **[Deprecated]**: `assert.CallTracker` is deprecated in favor of diagnostics_channel.
- **[Added]**: Introduced `assert.partialDeepStrictEqual()` as a Release Candidate.

## Functions

### assert.deepEqual(actual, expected[, message])
Tests for deep equality between the `actual` and `expected` parameters.
Prototypes of objects are strictly compared. If prototypes differ, `assert.deepEqual()` throws an `AssertionError`.

### assert.partialDeepStrictEqual(actual, expected[, message])
Tests for partial deep strict equality. `assert.partialDeepStrictEqual` is 1_2 - Release candidate.
Verifies that all properties present in `expected` match properties in `actual`.

### assert.CallTracker
[DEPRECATED] Tracks function call counts for unit testing. Will be removed in future versions.
"""

DOC_V16_CONTENT = """# Node.js Assert Module — Version 16.0.0

## Overview
The `assert` module provides a set of assertion functions for verifying invariants in code.

## Changelog
- **[Breaking]**: Removed `assert.CallTracker`.
- **[Added]**: `assert.partialDeepStrictEqual()` is now declared fully stable.
- **[Added]**: Full support for error cause chaining across all assertion failures.

## Functions

### assert.deepEqual(actual, expected[, message])
Tests for deep equality with strict prototype validation. Throws `AssertionError` with chained `cause` property on failure.

### assert.partialDeepStrictEqual(actual, expected[, message])
Tests for partial deep strict equality. Fully stable in v16.0.0.

### Error Cause Chaining
Assertion failures now attach the underlying error under the `.cause` property, enabling full trace visibility.
"""

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("[SEED] Seeding VersionRAG Database with Enterprise Test Data...")

        # 1. Create Demo User
        user = db.query(User).filter(User.email == "demo@versionrag.dev").first()
        if not user:
            user = User(
                email="demo@versionrag.dev",
                hashed_password=get_password_hash("VersionRAG2026!"),
                full_name="Alex Mercer (Staff Architect)",
                is_active=True,
                is_verified=True,
                is_superuser=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"  [OK] User created: {user.email} (Password: VersionRAG2026!)")

        # 2. Create Workspace
        ws = db.query(Workspace).filter(Workspace.slug == "core-engineering").first()
        if not ws:
            ws = Workspace(
                name="Core Platform Engineering",
                slug="core-engineering",
                description="Production API & Documentation Knowledge Base"
            )
            db.add(ws)
            db.flush()

            member = WorkspaceMember(
                workspace_id=ws.id,
                user_id=user.id,
                role=WorkspaceRole.OWNER
            )
            db.add(member)
            db.commit()
            db.refresh(ws)
            print(f"  [OK] Workspace created: {ws.name}")

        # 3. Create Project
        proj = db.query(Project).filter(Project.workspace_id == ws.id, Project.slug == "nodejs-runtime-specs").first()
        if not proj:
            proj = Project(
                workspace_id=ws.id,
                name="Node.js Runtime & API Specifications",
                slug="nodejs-runtime-specs",
                description="Version-aware documentation and migration tracks for Node.js APIs."
            )
            db.add(proj)
            db.commit()
            db.refresh(proj)
            print(f"  [OK] Project created: {proj.name}")

        # 4. Create Document Family
        family = db.query(DocumentFamily).filter(DocumentFamily.project_id == proj.id).first()
        if not family:
            family = DocumentFamily(
                project_id=proj.id,
                name="Assert Module",
                description="Node.js Assert API documentation family",
                category="technical_documentation"
            )
            db.add(family)
            db.flush()

        # 5. Create Document
        doc = db.query(Document).filter(Document.project_id == proj.id).first()
        if not doc:
            doc = Document(
                project_id=proj.id,
                family_id=family.id,
                title="Node.js Assert Documentation",
                doc_type="technical_documentation",
                source_url="https://nodejs.org/api/assert.html",
                description="Evolving assertion specifications across Node.js runtime versions."
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            print(f"  [OK] Document created: {doc.title}")

        # 6. Ingest 3 Versions: v14, v15, v16
        version_data = [
            ("v14.0.0", "14.0.0", 140000, DOC_V14_CONTENT, "assert_v14.md"),
            ("v15.14.0", "15.14.0", 151400, DOC_V15_CONTENT, "assert_v15.md"),
            ("v16.0.0", "16.0.0", 160000, DOC_V16_CONTENT, "assert_v16.md"),
        ]

        created_versions = []
        for tag, norm, order, content, filename in version_data:
            v_obj = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == doc.id,
                DocumentVersion.version_tag == tag
            ).first()

            if not v_obj:
                v_obj = DocumentVersion(
                    document_id=doc.id,
                    version_tag=tag,
                    normalized_version=norm,
                    version_order=order,
                    source_filename=filename,
                    storage_path=f"seeded/{filename}",
                    file_size_bytes=len(content.encode('utf-8')),
                    mime_type="text/markdown",
                    status=VersionStatus.READY,
                    status_message="Seeded successfully.",
                    raw_content=content,
                    extracted_metadata={
                        "title": "Node.js Assert Module",
                        "version_tag": tag,
                        "normalized_version": norm,
                        "doc_family": "Assert Module",
                        "confidence": 1.0,
                        "source": "verified_release"
                    }
                )
                db.add(v_obj)
                db.flush()

                # Chunking & Embeddings
                chunks = chunking_service.chunk_document(content, doc.title)
                for ch in chunks:
                    emb = embedding_service.get_embedding(ch["content"])
                    chunk_entity = DocumentChunk(
                        workspace_id=ws.id,
                        project_id=proj.id,
                        document_id=doc.id,
                        version_id=v_obj.id,
                        version_tag=tag,
                        chunk_index=ch["chunk_index"],
                        section_title=ch["section_title"],
                        page_number=ch["page_number"],
                        content=ch["content"],
                        token_count=ch["token_count"],
                        embedding=emb,
                        chunk_metadata=ch["chunk_metadata"]
                    )
                    db.add(chunk_entity)
                db.commit()
                db.refresh(v_obj)
                print(f"  [OK] Version indexed: {tag} ({len(chunks)} chunks)")

            created_versions.append(v_obj)

        # 7. Compute & Link Changes between consecutive versions (v14 -> v15, v15 -> v16)
        for i in range(len(created_versions) - 1):
            v_from = created_versions[i]
            v_to = created_versions[i + 1]

            v_to.previous_version_id = v_from.id
            v_from.next_version_id = v_to.id

            existing_changes = db.query(DocumentChange).filter(
                DocumentChange.from_version_id == v_from.id,
                DocumentChange.to_version_id == v_to.id
            ).all()

            if not existing_changes and v_from.raw_content and v_to.raw_content:
                changes, summary = diff_service.compute_all_changes(
                    old_content=v_from.raw_content,
                    new_content=v_to.raw_content,
                    from_tag=v_from.version_tag,
                    to_tag=v_to.version_tag
                )
                v_to.change_summary = summary

                for ch in changes:
                    change_rec = DocumentChange(
                        document_id=doc.id,
                        from_version_id=v_from.id,
                        to_version_id=v_to.id,
                        from_version_tag=v_from.version_tag,
                        to_version_tag=v_to.version_tag,
                        location=ch["location"],
                        change_type=ch["change_type"],
                        severity=ch["severity"],
                        is_silent=ch.get("is_silent", False),
                        is_breaking=ch.get("is_breaking", False),
                        old_content=ch.get("old_content"),
                        new_content=ch.get("new_content"),
                        summary=ch["summary"],
                        confidence=ch["confidence"],
                        source=ch["source"]
                    )
                    db.add(change_rec)
                db.commit()
                print(f"  [OK] Changes detected ({v_from.version_tag} -> {v_to.version_tag}): {len(changes)} changes")

        # 8. Run initial benchmark evaluation
        eval_run = evaluation_service.run_benchmark(
            db=db,
            workspace_id=ws.id,
            project_id=proj.id,
            user_id=user.id,
            run_name="Baseline Seed Reproduction Benchmark"
        )
        print(f"  [OK] Benchmark completed: Naive RAG {int(eval_run.naive_rag_accuracy*100)}% vs VersionRAG {int(eval_run.versionrag_accuracy*100)}%")

        print("\n[DONE] Seed completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
