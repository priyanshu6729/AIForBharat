from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from libs.common.db import get_session
from libs.common.models import AnalysisJob
from services.analysis.app.workers.analysis_worker import run_job

router = APIRouter()


@router.post("/jobs/{job_id}/run")
def run(job_id: int, session: Session = Depends(get_session)):
    job = session.get(AnalysisJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    run_job(job_id, session)
    return {"job_id": job_id, "status": "completed"}


@router.post("/jobs/run-next")
def run_next(session: Session = Depends(get_session)):
    job = (
        session.query(AnalysisJob)
        .filter(AnalysisJob.status == "queued")
        .order_by(AnalysisJob.created_at.asc())
        .first()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="no queued jobs")
    run_job(job.id, session)
    return {"job_id": job.id, "status": "completed"}
