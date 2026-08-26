from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.change import ChangeType, ChangeSeverity

class DocumentChangeRead(BaseModel):
    id: str
    document_id: str
    from_version_id: str
    to_version_id: str
    from_version_tag: str
    to_version_tag: str
    location: str
    change_type: ChangeType
    severity: ChangeSeverity
    is_silent: bool
    is_breaking: bool
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    summary: str
    confidence: float
    source: str
    details: Dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VersionComparisonResponse(BaseModel):
    document_id: str
    from_version_tag: str
    to_version_tag: str
    summary: Dict[str, int]  # e.g. {"added": 3, "modified": 2, "removed": 1, "deprecated": 1, "breaking": 1, "silent": 1}
    changes: List[DocumentChangeRead]
    unified_diff: Optional[str] = None
