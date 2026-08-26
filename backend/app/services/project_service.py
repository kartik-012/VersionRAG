from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.document import Document
from app.models.change import DocumentChange
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.services.workspace_service import slugify

class ProjectService:
    @staticmethod
    def create_project(db: Session, workspace: Workspace, project_in: ProjectCreate) -> ProjectRead:
        base_slug = slugify(project_in.name) or "project"
        slug = base_slug
        counter = 1
        while db.query(Project).filter(Project.workspace_id == workspace.id, Project.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        project = Project(
            workspace_id=workspace.id,
            name=project_in.name,
            slug=slug,
            description=project_in.description
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        res = ProjectRead.model_validate(project)
        res.documents_count = 0
        res.versions_count = 0
        res.changes_count = 0
        return res

    @staticmethod
    def list_workspace_projects(db: Session, workspace: Workspace) -> List[ProjectRead]:
        projects = db.query(Project).filter(Project.workspace_id == workspace.id).all()
        result = []
        for p in projects:
            docs = p.documents
            versions_count = sum(len(d.versions) for d in docs)
            changes_count = db.query(DocumentChange).join(Document, DocumentChange.document_id == Document.id).filter(Document.project_id == p.id).count()
            
            item = ProjectRead.model_validate(p)
            item.documents_count = len(docs)
            item.versions_count = versions_count
            item.changes_count = changes_count
            result.append(item)
        return result

    @staticmethod
    def get_project_detail(db: Session, project: Project) -> ProjectRead:
        docs = project.documents
        versions_count = sum(len(d.versions) for d in docs)
        changes_count = db.query(DocumentChange).join(Document, DocumentChange.document_id == Document.id).filter(Document.project_id == project.id).count()

        item = ProjectRead.model_validate(project)
        item.documents_count = len(docs)
        item.versions_count = versions_count
        item.changes_count = changes_count
        return item

    @staticmethod
    def update_project(db: Session, project: Project, project_in: ProjectUpdate) -> ProjectRead:
        if project_in.name is not None:
            project.name = project_in.name
        if project_in.description is not None:
            project.description = project_in.description
        db.commit()
        db.refresh(project)
        return ProjectService.get_project_detail(db, project)

    @staticmethod
    def delete_project(db: Session, project: Project):
        db.delete(project)
        db.commit()
        return {"message": "Project deleted successfully"}

project_service = ProjectService()
