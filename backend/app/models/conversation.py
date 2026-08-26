import enum
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Text, JSON, Float, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

class QueryArchetype(str, enum.Enum):
    CONTENT_QUERY = "content_query"
    VERSION_SPECIFIC_QUERY = "version_specific_query"
    VERSION_COMPARISON_QUERY = "version_comparison_query"
    CHANGE_QUERY = "change_query"
    TIMELINE_QUERY = "timeline_query"
    HISTORICAL_QUERY = "historical_query"
    CONFLICT_QUERY = "conflict_query"
    SILENT_CHANGE_QUERY = "silent_change_query"
    AMBIGUOUS_QUERY = "ambiguous_query"

class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INSUFFICIENT = "insufficient_evidence"

class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Query Session", nullable=False)

    # Relationships
    project = relationship("Project", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

class Message(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)

    # AI Query Metadata
    query_type = Column(
        SQLEnum(QueryArchetype, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    target_version = Column(String(100), nullable=True)
    scope = Column(String(50), default="current", nullable=False)
    
    confidence_level = Column(
        SQLEnum(ConfidenceLevel, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    confidence_score = Column(Float, nullable=True)
    confidence_reason = Column(Text, nullable=True)

    # Conflict explanation if versions clash
    has_conflict = Column(String(10), default="false", nullable=False)
    conflict_summary = Column(Text, nullable=True)

    # Execution telemetry
    latency_ms = Column(Integer, default=0, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    model_name = Column(String(100), nullable=True)
    raw_response_meta = Column(JSON, default=dict, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("Citation", back_populates="message", cascade="all, delete-orphan")

class Citation(Base, UUIDMixin, TimestampMixin):
    """Provides mathematically verified evidence grounding for each claim."""
    __tablename__ = "citations"

    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(36), ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True, index=True)
    
    document_title = Column(String(255), nullable=False)
    version_tag = Column(String(100), nullable=False)
    section_title = Column(String(255), nullable=True)
    page_number = Column(Integer, default=1, nullable=False)
    
    snippet = Column(Text, nullable=False)
    similarity_score = Column(Float, default=0.0, nullable=False)
    citation_order = Column(Integer, default=1, nullable=False)

    # Relationships
    message = relationship("Message", back_populates="citations")
    chunk = relationship("DocumentChunk", back_populates="citations")
