from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.job import ProcessingJob, JobStatus
from app.schemas.job import ProcessingJobRead
from app.services.job_service import job_service

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])

@router.get("/{job_id}", response_model=ProcessingJobRead)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Check asynchronous document ingestion stage and progress percentage."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return ProcessingJobRead.model_validate(job)

@router.post("/{job_id}/retry", response_model=ProcessingJobRead)
def retry_failed_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry a failed or stuck ingestion pipeline job."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    
    job.status = JobStatus.PENDING
    job.retry_count += 1
    job.error_message = None
    db.commit()

    background_tasks.add_task(job_service.run_ingestion_pipeline, db, job.id)
    return ProcessingJobRead.model_validate(job)
