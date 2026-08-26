from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Tuple
from app.core.database import get_db
from app.core.deps import get_current_user, get_workspace_membership, require_workspace_role
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceRead,
    WorkspaceMemberRead, WorkspaceMemberAdd, WorkspaceMemberUpdateRole
)
from app.services.workspace_service import workspace_service

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workspace (creator becomes Owner)."""
    return workspace_service.create_workspace(db, current_user, workspace_in)

@router.get("", response_model=List[WorkspaceRead])
def list_my_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all workspaces the authenticated user belongs to."""
    return workspace_service.list_user_workspaces(db, current_user)

@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(
    workspace_and_member: Tuple[Workspace, WorkspaceMember] = Depends(get_workspace_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workspace details."""
    workspace, _ = workspace_and_member
    return workspace_service.get_workspace_detail(db, workspace, current_user)

@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def update_workspace(
    update_in: WorkspaceUpdate,
    workspace_and_member: Tuple[Workspace, WorkspaceMember] = Depends(require_workspace_role(WorkspaceRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update workspace name or description (requires Admin or Owner role)."""
    workspace, _ = workspace_and_member
    return workspace_service.update_workspace(db, workspace, update_in)

@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_and_member: Tuple[Workspace, WorkspaceMember] = Depends(require_workspace_role(WorkspaceRole.OWNER)),
    db: Session = Depends(get_db)
):
    """Delete a workspace (strictly requires Owner role)."""
    workspace, _ = workspace_and_member
    return workspace_service.delete_workspace(db, workspace)

@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberRead])
def list_workspace_members(
    workspace_and_member: Tuple[Workspace, WorkspaceMember] = Depends(get_workspace_membership),
    db: Session = Depends(get_db)
):
    """List all members of a workspace."""
    workspace, _ = workspace_and_member
    return workspace_service.list_members(db, workspace)

@router.post("/{workspace_id}/members", response_model=WorkspaceMemberRead, status_code=status.HTTP_201_CREATED)
def add_workspace_member(
    member_in: WorkspaceMemberAdd,
    workspace_and_member: Tuple[Workspace, WorkspaceMember] = Depends(require_workspace_role(WorkspaceRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Add a member to workspace (requires Admin or Owner)."""
    workspace, _ = workspace_and_member
    return workspace_service.add_member(db, workspace, member_in)

@router.patch("/{workspace_id}/members/{member_id}", response_model=WorkspaceMemberRead)
def update_member_role(
    member_id: str,
    role_update: WorkspaceMemberUpdateRole,
    workspace_and_member: Tuple[Workspace, WorkspaceMember] = Depends(require_workspace_role(WorkspaceRole.ADMIN)),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a member's role (requires Admin or Owner)."""
    workspace, _ = workspace_and_member
    return workspace_service.update_member_role(db, workspace, member_id, role_update, current_user)

@router.delete("/{workspace_id}/members/{member_id}")
def remove_member(
    member_id: str,
    workspace_and_member: Tuple[Workspace, WorkspaceMember] = Depends(require_workspace_role(WorkspaceRole.ADMIN)),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from the workspace (requires Admin or Owner)."""
    workspace, _ = workspace_and_member
    return workspace_service.remove_member(db, workspace, member_id, current_user)
