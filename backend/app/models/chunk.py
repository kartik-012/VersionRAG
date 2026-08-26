from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    """Represents an atomic, version-tagged content chunk."""
    __tablename__ = "document_chunks"

    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    version_tag = Column(String(100), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, index=True)
    
    section_title = Column(String(255), nullable=True)
    page_number = Column(Integer, default=1, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    
    # Embedding vector stored as JSON array of floats for maximum portability
    embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(100), default="text-embedding-3-small", nullable=False)
    
    # Metadata for rich citations
    chunk_metadata = Column(JSON, default=dict, nullable=False)

    # Relationships
    version = relationship("DocumentVersion", back_populates="chunks")
    citations = relationship("Citation", back_populates="chunk", cascade="all, delete-orphan")
