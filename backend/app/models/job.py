import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum, JSON, Text, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class ProcessingStage(str, enum.Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    PARSING = "parsing"
    EXTRACTING_METADATA = "extracting_metadata"
    DETECTING_VERSION = "detecting_version"
    CLUSTERING_FAMILY = "clustering_family"
    CHUNKING = "chunking"
    GENERATING_EMBEDDINGS = "generating_embeddings"
    DETECTING_CHANGES = "detecting_changes"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"

class ProcessingJob(Base, UUIDMixin, TimestampMixin):
    """Tracks asynchronous ingestion pipelines with honest stage transitions."""
    __tablename__ = "processing_jobs"

    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=True, index=True)

    job_type = Column(String(50), default="document_ingest", nullable=False)
    status = Column(
        SQLEnum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.PENDING,
        nullable=False,
        index=True
    )
    current_stage = Column(
        SQLEnum(ProcessingStage, values_callable=lambda x: [e.value for e in x]),
        default=ProcessingStage.QUEUED,
        nullable=False
    )
    stage_progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 1.0 based on stage count
    
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    execution_meta = Column(JSON, default=dict, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="jobs")
    project = relationship("Project", back_populates="jobs")
