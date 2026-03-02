from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from libs.common.db import get_session
from libs.common.models import AnalysisJob

router = APIRouter()


@router.get("/status/{job_id}")
def status(job_id: int, session: Session = Depends(get_session)):
    job = session.get(AnalysisJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": job.id,
        "status": job.status,
        "stage": job.stage,
        "error": job.error,
    }
