import re
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceRead,
    WorkspaceMemberRead, WorkspaceMemberAdd, WorkspaceMemberUpdateRole
)

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text

class WorkspaceService:
    @staticmethod
    def create_workspace(db: Session, user: User, workspace_in: WorkspaceCreate) -> WorkspaceRead:
        base_slug = slugify(workspace_in.name) or "workspace"
        slug = base_slug
        counter = 1
        while db.query(Workspace).filter(Workspace.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        workspace = Workspace(
            name=workspace_in.name,
            slug=slug,
            description=workspace_in.description
        )
        db.add(workspace)
        db.flush()

        # Creator becomes OWNER
        owner_member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceRole.OWNER
        )
        db.add(owner_member)
        db.commit()
        db.refresh(workspace)

        res = WorkspaceRead.model_validate(workspace)
        res.current_user_role = WorkspaceRole.OWNER
        res.members_count = 1
        res.projects_count = 0
        return res

    @staticmethod
    def list_user_workspaces(db: Session, user: User) -> List[WorkspaceRead]:
        memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).all()
        result = []
        for mem in memberships:
            ws = mem.workspace
            item = WorkspaceRead.model_validate(ws)
            item.current_user_role = mem.role
            item.members_count = len(ws.members)
            item.projects_count = len(ws.projects)
            result.append(item)
        return result

    @staticmethod
    def get_workspace_detail(db: Session, workspace: Workspace, user: User) -> WorkspaceRead:
        mem = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id
        ).first()
        res = WorkspaceRead.model_validate(workspace)
        res.current_user_role = mem.role if mem else None
        res.members_count = len(workspace.members)
        res.projects_count = len(workspace.projects)
        return res

    @staticmethod
    def update_workspace(db: Session, workspace: Workspace, update_in: WorkspaceUpdate) -> WorkspaceRead:
        if update_in.name is not None:
            workspace.name = update_in.name
        if update_in.description is not None:
            workspace.description = update_in.description
        db.commit()
        db.refresh(workspace)
        return WorkspaceRead.model_validate(workspace)

    @staticmethod
    def delete_workspace(db: Session, workspace: Workspace):
        db.delete(workspace)
        db.commit()
        return {"message": "Workspace deleted successfully"}

    @staticmethod
    def list_members(db: Session, workspace: Workspace) -> List[WorkspaceMemberRead]:
        members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id).all()
        return [WorkspaceMemberRead.model_validate(m) for m in members]

    @staticmethod
    def add_member(db: Session, workspace: Workspace, member_in: WorkspaceMemberAdd) -> WorkspaceMemberRead:
        target_user = db.query(User).filter(User.email == member_in.email.lower()).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with that email address not found"
            )
        existing = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == target_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this workspace"
            )
        new_mem = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=target_user.id,
            role=member_in.role
        )
        db.add(new_mem)
        db.commit()
        db.refresh(new_mem)
        return WorkspaceMemberRead.model_validate(new_mem)

    @staticmethod
    def update_member_role(
        db: Session,
        workspace: Workspace,
        member_id: str,
        role_update: WorkspaceMemberUpdateRole,
        actor_user: User
    ) -> WorkspaceMemberRead:
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.id == member_id,
            WorkspaceMember.workspace_id == workspace.id
        ).first()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        
        # Protect against removing the only OWNER
        if member.role == WorkspaceRole.OWNER and role_update.role != WorkspaceRole.OWNER:
            owners_count = db.query(WorkspaceMember).filter(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.role == WorkspaceRole.OWNER
            ).count()
            if owners_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot downgrade the only workspace owner."
                )

        member.role = role_update.role
        db.commit()
        db.refresh(member)
        return WorkspaceMemberRead.model_validate(member)

    @staticmethod
    def remove_member(db: Session, workspace: Workspace, member_id: str, actor_user: User):
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.id == member_id,
            WorkspaceMember.workspace_id == workspace.id
        ).first()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        if member.role == WorkspaceRole.OWNER:
            owners_count = db.query(WorkspaceMember).filter(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.role == WorkspaceRole.OWNER
            ).count()
            if owners_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the only workspace owner."
                )
        db.delete(member)
        db.commit()
        return {"message": "Member removed"}

workspace_service = WorkspaceService()
