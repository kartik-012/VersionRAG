import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class TimestampMixin:
    """Provides created_at and updated_at UTC timestamps."""
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

class UUIDMixin:
    """Provides standard UUID string primary key."""
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
