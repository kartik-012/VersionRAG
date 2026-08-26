from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Tuple
from app.core.database import get_db
from app.core.deps import get_workspace_membership, require_workspace_role, get_project_and_membership
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.services.project_service import project_service

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/workspace/{workspace_id}", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    workspace_id: str,
    project_in: ProjectCreate,
    workspace_and_member: Tuple[Workspace, WorkspaceMember] = Depends(require_workspace_role(WorkspaceRole.MEMBER)),
    db: Session = Depends(get_db)
):
    """Create a new project within a workspace."""
    workspace, _ = workspace_and_member
    return project_service.create_project(db, workspace, project_in)

@router.get("/workspace/{workspace_id}", response_model=List[ProjectRead])
def list_workspace_projects(
    workspace_id: str,
    workspace_and_member: Tuple[Workspace, WorkspaceMember] = Depends(get_workspace_membership),
    db: Session = Depends(get_db)
):
    """List all projects in a workspace."""
    workspace, _ = workspace_and_member
    return project_service.list_workspace_projects(db, workspace)

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_workspace_member: Tuple[Project, Workspace, WorkspaceMember] = Depends(get_project_and_membership),
    db: Session = Depends(get_db)
):
    """Get project details."""
    project, _, _ = project_workspace_member
    return project_service.get_project_detail(db, project)

@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    update_in: ProjectUpdate,
    project_workspace_member: Tuple[Project, Workspace, WorkspaceMember] = Depends(get_project_and_membership),
    db: Session = Depends(get_db)
):
    """Update project name or description."""
    project, _, member = project_workspace_member
    if not member.role.can_perform(WorkspaceRole.ADMIN):
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires Admin role")
    return project_service.update_project(db, project, update_in)

@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    project_workspace_member: Tuple[Project, Workspace, WorkspaceMember] = Depends(get_project_and_membership),
    db: Session = Depends(get_db)
):
    """Delete a project."""
    project, _, member = project_workspace_member
    if not member.role.can_perform(WorkspaceRole.ADMIN):
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires Admin role")
    return project_service.delete_project(db, project)

