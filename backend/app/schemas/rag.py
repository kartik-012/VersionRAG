from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.conversation import QueryArchetype, ConfidenceLevel

class CitationRead(BaseModel):
    id: str
    chunk_id: Optional[str] = None
    document_title: str
    version_tag: str
    section_title: Optional[str] = None
    page_number: int = 1
    snippet: str
    similarity_score: float = 0.0
    citation_order: int = 1

    model_config = ConfigDict(from_attributes=True)

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    project_id: str
    conversation_id: Optional[str] = None
    target_version: Optional[str] = None
    scope: str = Field(default="current", description="current | specific | compare | all | temporal")
    compare_to_version: Optional[str] = None

class MessageRead(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    query_type: Optional[QueryArchetype] = None
    target_version: Optional[str] = None
    scope: str
    confidence_level: Optional[ConfidenceLevel] = None
    confidence_score: Optional[float] = None
    confidence_reason: Optional[str] = None
    has_conflict: str = "false"
    conflict_summary: Optional[str] = None
    latency_ms: int = 0
    tokens_used: int = 0
    model_name: Optional[str] = None
    citations: List[CitationRead] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationRead(BaseModel):
    id: str
    project_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead] = []

    model_config = ConfigDict(from_attributes=True)

class QueryResponse(BaseModel):
    conversation_id: str
    message_id: str
    question: str
    answer: str
    query_type: QueryArchetype
    target_version: Optional[str] = None
    related_versions: List[str] = []
    confidence_level: ConfidenceLevel
    confidence_score: float
    confidence_reason: str
    has_conflict: bool
    conflict_summary: Optional[str] = None
    citations: List[CitationRead] = []
    latency_ms: int
    tokens_used: int
