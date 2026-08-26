import enum
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Text, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

class ChangeType(str, enum.Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    RENAMED = "renamed"
    DEPRECATED = "deprecated"
    RESTORED = "restored"
    BEHAVIORAL = "behavioral"
    BREAKING = "breaking"
    DOC_ONLY = "doc_only"
    SILENT = "silent"

class ChangeSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DocumentChange(Base, UUIDMixin, TimestampMixin):
    """Represents a structured diff change between two consecutive versions."""
    __tablename__ = "document_changes"

    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    from_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    to_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)

    from_version_tag = Column(String(100), nullable=False)
    to_version_tag = Column(String(100), nullable=False)

    location = Column(String(500), nullable=False)  # Section or symbol name (e.g. "assert.deepEqual()")
    change_type = Column(
        SQLEnum(ChangeType, values_callable=lambda x: [e.value for e in x]),
        default=ChangeType.MODIFIED,
        nullable=False,
        index=True
    )
    severity = Column(
        SQLEnum(ChangeSeverity, values_callable=lambda x: [e.value for e in x]),
        default=ChangeSeverity.MEDIUM,
        nullable=False
    )
    
    is_silent = Column(Boolean, default=False, nullable=False, index=True)
    is_breaking = Column(Boolean, default=False, nullable=False, index=True)

    old_content = Column(Text, nullable=True)
    new_content = Column(Text, nullable=True)
    summary = Column(Text, nullable=False)
    
    confidence = Column(Float, default=1.0, nullable=False)
    source = Column(String(100), default="implicit_diff", nullable=False)  # "explicit_changelog" or "implicit_diff"
    details = Column(JSON, default=dict, nullable=False)

    # Relationships
    from_version = relationship("DocumentVersion", foreign_keys=[from_version_id], back_populates="changes_as_source")
    to_version = relationship("DocumentVersion", foreign_keys=[to_version_id], back_populates="changes_as_target")
