from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.document import VersionStatus

class DocumentFamilyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category: str = "technical_documentation"

class DocumentFamilyCreate(DocumentFamilyBase):
    pass

class DocumentFamilyRead(DocumentFamilyBase):
    id: str
    project_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentVersionBase(BaseModel):
    version_tag: str
    normalized_version: Optional[str] = None
    release_date: Optional[datetime] = None

class DocumentVersionRead(DocumentVersionBase):
    id: str
    document_id: str
    version_order: int
    source_filename: Optional[str] = None
    file_size_bytes: int = 0
    mime_type: Optional[str] = None
    status: VersionStatus
    status_message: Optional[str] = None
    previous_version_id: Optional[str] = None
    next_version_id: Optional[str] = None
    extracted_metadata: Dict[str, Any] = {}
    change_summary: Dict[str, Any] = {}
    created_at: datetime
    chunks_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class DocumentVersionDetail(DocumentVersionRead):
    raw_content: Optional[str] = None

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    doc_type: str = "documentation"
    source_url: Optional[str] = None
    description: Optional[str] = None

class DocumentCreate(DocumentBase):
    family_id: Optional[str] = None

class DocumentRead(DocumentBase):
    id: str
    project_id: str
    family_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    versions: List[DocumentVersionRead] = []
    latest_version: Optional[str] = None
    total_versions: int = 0
    status: Optional[str] = "ready"

    model_config = ConfigDict(from_attributes=True)

class DocumentChunkRead(BaseModel):
    id: str
    version_id: str
    document_id: str
    version_tag: str
    chunk_index: int
    section_title: Optional[str] = None
    page_number: int
    content: str
    token_count: int
    chunk_metadata: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)
