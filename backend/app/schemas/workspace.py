from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.workspace import WorkspaceRole
from app.schemas.auth import UserRead

class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class WorkspaceMemberRead(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: WorkspaceRole
    created_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)

class WorkspaceMemberAdd(BaseModel):
    email: str
    role: WorkspaceRole = WorkspaceRole.MEMBER

class WorkspaceMemberUpdateRole(BaseModel):
    role: WorkspaceRole

class WorkspaceRead(WorkspaceBase):
    id: str
    slug: str
    created_at: datetime
    updated_at: datetime
    current_user_role: Optional[WorkspaceRole] = None
    members_count: Optional[int] = 0
    projects_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
