from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.job import JobStatus, ProcessingStage

class ProcessingJobRead(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    document_id: Optional[str] = None
    version_id: Optional[str] = None
    job_type: str
    status: JobStatus
    current_stage: ProcessingStage
    stage_progress: float
    error_message: Optional[str] = None
    retry_count: int
    execution_meta: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
