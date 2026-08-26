from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class ProjectRead(ProjectBase):
    id: str
    workspace_id: str
    slug: str
    created_at: datetime
    updated_at: datetime
    documents_count: Optional[int] = 0
    versions_count: Optional[int] = 0
    changes_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
