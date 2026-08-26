import enum
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

class WorkspaceRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

    @property
    def rank(self) -> int:
        """Higher number means higher privilege."""
        ranks = {
            WorkspaceRole.VIEWER: 1,
            WorkspaceRole.MEMBER: 2,
            WorkspaceRole.ADMIN: 3,
            WorkspaceRole.OWNER: 4
        }
        return ranks[self]

    def can_perform(self, minimum_role: "WorkspaceRole") -> bool:
        return self.rank >= minimum_role.rank

class Workspace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspaces"

    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(1000), nullable=True)

    # Relationships
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="workspace", cascade="all, delete-orphan")
    evaluation_runs = relationship("EvaluationRun", back_populates="workspace", cascade="all, delete-orphan")

class WorkspaceMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),)

    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(
        SQLEnum(WorkspaceRole, values_callable=lambda x: [e.value for e in x]),
        default=WorkspaceRole.MEMBER,
        nullable=False
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspace_memberships")
