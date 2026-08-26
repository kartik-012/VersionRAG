import logging
from sqlalchemy.orm import Session
from app.models.job import ProcessingJob, JobStatus, ProcessingStage
from app.models.document import Document, DocumentVersion, DocumentFamily, VersionStatus
from app.models.chunk import DocumentChunk
from app.models.change import DocumentChange
from app.services.storage_service import storage_service
from app.services.parser_service import parser_service
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.diff_service import diff_service

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
        """Create a new asynchronous tracking job."""
        job = ProcessingJob(
            workspace_id=workspace_id,
            project_id=project_id,
            document_id=document_id,
            version_id=version_id,
            job_type="document_ingest",
            status=JobStatus.PENDING,
            current_stage=ProcessingStage.QUEUED,
            stage_progress=0.0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def run_ingestion_pipeline(db: Session, job_id: str):
        """
        Executes the 10-stage ingestion pipeline with atomic stage tracking.
        """
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

            # Stage 1: VALIDATING
            job.current_stage = ProcessingStage.VALIDATING
            job.stage_progress = 0.10
            db.commit()

            file_bytes = storage_service.get_file_bytes(version.storage_path)

            # Stage 2: PARSING
            job.current_stage = ProcessingStage.PARSING
            job.stage_progress = 0.20
            db.commit()

            raw_text = parser_service.extract_text_from_file(file_bytes, version.source_filename or "doc.txt")
            version.raw_content = raw_text

            # Stage 3: EXTRACTING_METADATA
            job.current_stage = ProcessingStage.EXTRACTING_METADATA
            job.stage_progress = 0.35
            db.commit()

            meta = parser_service.extract_metadata_and_version(raw_text, version.source_filename or "")
            version.extracted_metadata = meta
            if meta.get("title") and document.title == "New Document":
                document.title = meta["title"]

            # Stage 4: DETECTING_VERSION
            job.current_stage = ProcessingStage.DETECTING_VERSION
            job.stage_progress = 0.45
            db.commit()

            if not version.version_tag or version.version_tag == "v1.0":
                version.version_tag = meta.get("version_tag", "v1.0")
                version.normalized_version = meta.get("normalized_version", "1.0.0")
                version.version_order = meta.get("version_order", 1000)

            # Stage 5: CLUSTERING_FAMILY
            job.current_stage = ProcessingStage.CLUSTERING_FAMILY
            job.stage_progress = 0.55
            db.commit()

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

            # Stage 6: CHUNKING
            job.current_stage = ProcessingStage.CHUNKING
            job.stage_progress = 0.65
            db.commit()

            raw_chunks = chunking_service.chunk_document(raw_text, document.title)
            
            # Clear old chunks if re-processing
            db.query(DocumentChunk).filter(DocumentChunk.version_id == version.id).delete()

            # Stage 7: GENERATING_EMBEDDINGS
            job.current_stage = ProcessingStage.GENERATING_EMBEDDINGS
            job.stage_progress = 0.75
            db.commit()

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

            # Stage 8: DETECTING_CHANGES (Against previous version if exists)
            job.current_stage = ProcessingStage.DETECTING_CHANGES
            job.stage_progress = 0.85
            db.commit()

            # Find predecessor version in document
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

            if prev_ver and prev_ver.raw_content:
                version.previous_version_id = prev_ver.id
                prev_ver.next_version_id = version.id

                changes, summary_counts = diff_service.compute_all_changes(
                    old_content=prev_ver.raw_content,
                    new_content=raw_text,
                    from_tag=prev_ver.version_tag,
                    to_tag=version.version_tag
                )
                version.change_summary = summary_counts

                # Store change records
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

            # Stage 9 & 10: INDEXING & READY
            job.current_stage = ProcessingStage.READY
            job.stage_progress = 1.0
            job.status = JobStatus.COMPLETED
            version.status = VersionStatus.READY
            version.status_message = "Ingestion completed successfully."
            db.commit()

        except Exception as e:
            logger.exception(f"Pipeline error processing job {job_id}: {str(e)}")
            job.status = JobStatus.FAILED
            job.current_stage = ProcessingStage.FAILED
            job.error_message = str(e)
            version.status = VersionStatus.FAILED
            version.status_message = f"Processing failed: {str(e)}"
            db.commit()

job_service = JobService()
