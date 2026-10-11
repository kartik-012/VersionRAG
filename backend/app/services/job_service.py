import logging
import time
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.core.database import SessionLocal, get_db
from app.models.job import ProcessingJob, JobStatus, ProcessingStage
from app.models.document import Document, DocumentVersion, DocumentFamily, VersionStatus
from app.models.chunk import DocumentChunk
from app.models.change import DocumentChange
from app.services.storage_service import storage_service
from app.services.parser_service import parser_service
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.diff_service import diff_service
from app.services.hybrid_index_service import hybrid_index_manager

logger = logging.getLogger("versionrag.jobs")


class JobService:
    @staticmethod
    def create_ingestion_job(
        db: Session,
        workspace_id: str,
        project_id: str,
        document_id: str,
        version_id: str
    ) -> ProcessingJob:
        """Create a new asynchronous tracking job with initialized telemetry."""
        job = ProcessingJob(
            workspace_id=workspace_id,
            project_id=project_id,
            document_id=document_id,
            version_id=version_id,
            job_type="document_ingest",
            status=JobStatus.PENDING,
            current_stage=ProcessingStage.QUEUED,
            stage_progress=0.0,
            execution_meta={
                "stage_history": ["0.00:queued"],
                "checkpoints": [],
            }
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def _update_checkpoint(
        db: Session,
        job: ProcessingJob,
        stage: ProcessingStage,
        progress: float,
        meta_updates: Optional[dict] = None
    ):
        """Atomically persist stage transition, progress float, and execution telemetry."""
        job.current_stage = stage
        job.stage_progress = round(progress, 2)
        meta = dict(job.execution_meta or {})
        history = list(meta.get("stage_history", []))
        checkpoint_tag = f"{progress:.2f}:{stage.value}"
        if checkpoint_tag not in history:
            history.append(checkpoint_tag)
        meta["stage_history"] = history
        if meta_updates:
            meta.update(meta_updates)
        job.execution_meta = meta
        flag_modified(job, "execution_meta")
        db.commit()

    @staticmethod
    def run_ingestion_pipeline_background(job_id: str):
        """
        Thread-safe background task entrypoint for FastAPI BackgroundTasks.
        Uses dependency_overrides[get_db] when running inside TestClient, or opens
        an isolated SessionLocal() in production so request-scoped sessions are never leaked.
        """
        try:
            from app.main import app as fastapi_app
            override_fn = fastapi_app.dependency_overrides.get(get_db)
        except Exception:
            override_fn = None

        if override_fn is not None:
            gen = override_fn()
            db = next(gen)
            try:
                JobService.run_ingestion_pipeline(db, job_id)
            finally:
                try:
                    next(gen)
                except StopIteration:
                    pass
        else:
            db = SessionLocal()
            try:
                JobService.run_ingestion_pipeline(db, job_id)
            finally:
                db.close()

    @staticmethod
    def run_ingestion_pipeline(db: Session, job_id: str):
        """
        Executes the non-blocking ingestion pipeline with 5 core telemetry milestones
        (0.20 -> 0.45 -> 0.70 -> 0.90 -> 1.00) and full stage auditability.
        """
        t0 = time.perf_counter()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return

        version = db.query(DocumentVersion).filter(DocumentVersion.id == job.version_id).first()
        if not version:
            job.status = JobStatus.FAILED
            job.current_stage = ProcessingStage.FAILED
            job.error_message = "Target document version record not found"
            db.commit()
            return

        document = version.document

        try:
            job.status = JobStatus.PROCESSING

            # =========================================================================
            # MILESTONE 1 (20%): FILE VALIDATION & TEXT PARSING
            # =========================================================================
            file_bytes = storage_service.get_file_bytes(version.storage_path)
            raw_text = parser_service.extract_text_from_file(
                file_bytes, version.source_filename or "doc.txt"
            )
            version.raw_content = raw_text

            JobService._update_checkpoint(
                db=db,
                job=job,
                stage=ProcessingStage.PARSING,
                progress=0.20,
                meta_updates={
                    "char_count": len(raw_text),
                    "line_count": len(raw_text.splitlines()),
                    "source_filename": version.source_filename,
                }
            )

            # =========================================================================
            # MILESTONE 2 (45%): METADATA, VERSION RESOLUTION & STRUCTURE CHUNKING
            # =========================================================================
            meta = parser_service.extract_metadata_and_version(
                raw_text, version.source_filename or ""
            )
            version.extracted_metadata = meta
            if meta.get("title") and document.title == "New Document":
                document.title = meta["title"]

            if not version.version_tag or version.version_tag == "v1.0":
                version.version_tag = meta.get("version_tag", "v1.0")
                version.normalized_version = meta.get("normalized_version", "1.0.0")
                version.version_order = meta.get("version_order", 1000)

            family_name = meta.get("doc_family") or document.title
            family = (
                db.query(DocumentFamily)
                .filter(
                    DocumentFamily.project_id == job.project_id,
                    DocumentFamily.name.ilike(family_name)
                )
                .first()
            )
            if not family:
                family = DocumentFamily(
                    project_id=job.project_id,
                    name=family_name,
                    description=f"Automated family cluster for {family_name}"
                )
                db.add(family)
                db.flush()
            document.family_id = family.id

            raw_chunks = chunking_service.chunk_document(raw_text, document.title)

            # Clear old chunks if re-processing
            db.query(DocumentChunk).filter(DocumentChunk.version_id == version.id).delete()

            JobService._update_checkpoint(
                db=db,
                job=job,
                stage=ProcessingStage.CHUNKING,
                progress=0.45,
                meta_updates={
                    "detected_version": version.version_tag,
                    "normalized_version": version.normalized_version,
                    "family_name": family_name,
                    "chunks_created": len(raw_chunks),
                }
            )

            # =========================================================================
            # MILESTONE 3 (70%): SEMANTIC EMBEDDINGS & HYBRID PARTITION INDEXING
            # =========================================================================
            created_chunks = []
            for item in raw_chunks:
                emb = embedding_service.get_embedding(item["content"])
                chunk_obj = DocumentChunk(
                    workspace_id=job.workspace_id,
                    project_id=job.project_id,
                    document_id=document.id,
                    version_id=version.id,
                    version_tag=version.version_tag,
                    chunk_index=item["chunk_index"],
                    section_title=item["section_title"],
                    page_number=item["page_number"],
                    content=item["content"],
                    token_count=item["token_count"],
                    embedding=emb,
                    chunk_metadata=item["chunk_metadata"]
                )
                db.add(chunk_obj)
                created_chunks.append(chunk_obj)
            db.flush()

            # Invalidate stale project index partitions and warm up the new version partition
            hybrid_index_manager.invalidate_project(job.project_id)
            hybrid_index_manager.get_or_build(
                project_id=job.project_id,
                partition_key=version.version_tag,
                chunks=created_chunks
            )

            JobService._update_checkpoint(
                db=db,
                job=job,
                stage=ProcessingStage.GENERATING_EMBEDDINGS,
                progress=0.70,
                meta_updates={
                    "embedding_provider": embedding_service.provider_name,
                    "indexed_vectors": len(created_chunks),
                    "hybrid_partition_warmed": f"{job.project_id}:{version.version_tag}",
                }
            )

            # =========================================================================
            # MILESTONE 4 (90%): AST & IMPLICIT SEMANTIC DIFF ENGINE
            # =========================================================================
            prev_ver = (
                db.query(DocumentVersion)
                .filter(
                    DocumentVersion.document_id == document.id,
                    DocumentVersion.id != version.id,
                    DocumentVersion.version_order < version.version_order,
                    DocumentVersion.status == VersionStatus.READY
                )
                .order_by(DocumentVersion.version_order.desc())
                .first()
            )

            changes_count = 0
            breaking_count = 0
            silent_count = 0

            if prev_ver and prev_ver.raw_content:
                version.previous_version_id = prev_ver.id
                prev_ver.next_version_id = version.id

                # Clear old changes between these two versions if re-running
                db.query(DocumentChange).filter(
                    DocumentChange.from_version_id == prev_ver.id,
                    DocumentChange.to_version_id == version.id
                ).delete()

                changes, summary_counts = diff_service.compute_all_changes(
                    old_content=prev_ver.raw_content,
                    new_content=raw_text,
                    from_tag=prev_ver.version_tag,
                    to_tag=version.version_tag
                )
                version.change_summary = summary_counts
                changes_count = len(changes)
                breaking_count = summary_counts.get("breaking", 0)
                silent_count = summary_counts.get("silent", 0)

                for ch in changes:
                    change_record = DocumentChange(
                        document_id=document.id,
                        from_version_id=prev_ver.id,
                        to_version_id=version.id,
                        from_version_tag=prev_ver.version_tag,
                        to_version_tag=version.version_tag,
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
                    db.add(change_record)

            JobService._update_checkpoint(
                db=db,
                job=job,
                stage=ProcessingStage.DETECTING_CHANGES,
                progress=0.90,
                meta_updates={
                    "compared_against_version": prev_ver.version_tag if prev_ver else None,
                    "changes_detected": changes_count,
                    "breaking_changes": breaking_count,
                    "silent_changes": silent_count,
                }
            )

            # =========================================================================
            # MILESTONE 5 (100%): PIPELINE COMPLETED & READY
            # =========================================================================
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            job.status = JobStatus.COMPLETED
            version.status = VersionStatus.READY
            version.status_message = "Ingestion completed successfully."

            JobService._update_checkpoint(
                db=db,
                job=job,
                stage=ProcessingStage.READY,
                progress=1.0,
                meta_updates={
                    "duration_ms": elapsed_ms,
                }
            )

        except Exception as e:
            logger.exception(f"Pipeline error processing job {job_id}: {str(e)}")
            job.status = JobStatus.FAILED
            job.current_stage = ProcessingStage.FAILED
            job.error_message = str(e)
            version.status = VersionStatus.FAILED
            version.status_message = f"Processing failed: {str(e)}"
            db.commit()


job_service = JobService()

