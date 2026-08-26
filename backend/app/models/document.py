import enum
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Enum as SQLEnum, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

class VersionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"

class DocumentFamily(Base, UUIDMixin, TimestampMixin):
    """Represents a logical family of evolving documents (e.g. Node.js Assert API)."""
    __tablename__ = "document_families"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    category = Column(String(100), default="technical_documentation", nullable=False)

    # Relationships
    project = relationship("Project", back_populates="document_families")
    documents = relationship("Document", back_populates="family", cascade="all, delete-orphan")

class Document(Base, UUIDMixin, TimestampMixin):
    """Represents a specific document container with versions."""
    __tablename__ = "documents"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    family_id = Column(String(36), ForeignKey("document_families.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(String(50), default="documentation", nullable=False)
    source_url = Column(String(1000), nullable=True)
    description = Column(String(1000), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="documents")
    family = relationship("DocumentFamily", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", order_by="DocumentVersion.version_order")

class DocumentVersion(Base, UUIDMixin, TimestampMixin):
    """Represents a single immutable version release of a document."""
    __tablename__ = "document_versions"

    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_tag = Column(String(100), nullable=False, index=True)  # e.g. "v15.14.0", "1.0", "2025-Q1"
    normalized_version = Column(String(100), nullable=True, index=True)
    version_order = Column(Integer, default=0, nullable=False, index=True)
    
    release_date = Column(DateTime, nullable=True)
    source_filename = Column(String(255), nullable=True)
    storage_path = Column(String(1000), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    
    status = Column(
        SQLEnum(VersionStatus, values_callable=lambda x: [e.value for e in x]),
        default=VersionStatus.PENDING,
        nullable=False,
        index=True
    )
    status_message = Column(String(1000), nullable=True)

    # Version graph pointers
    previous_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True)
    next_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True)

    # Rich metadata & summary
    extracted_metadata = Column(JSON, default=dict, nullable=False)
    change_summary = Column(JSON, default=dict, nullable=False)
    raw_content = Column(Text, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="versions")
    chunks = relationship("DocumentChunk", back_populates="version", cascade="all, delete-orphan")
    
    changes_as_source = relationship(
        "DocumentChange",
        foreign_keys="DocumentChange.from_version_id",
        back_populates="from_version",
        cascade="all, delete-orphan"
    )
    changes_as_target = relationship(
        "DocumentChange",
        foreign_keys="DocumentChange.to_version_id",
        back_populates="to_version",
        cascade="all, delete-orphan"
    )
