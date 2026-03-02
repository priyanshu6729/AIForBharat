from __future__ import annotations

import hashlib
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from libs.common.aws import s3_put_bytes, sqs_send
from libs.common.config import settings
from libs.common.db import get_session
from libs.common.models import Artifact, AnalysisJob

router = APIRouter()


@router.post("/upload")
async def upload_code(
    project_id: Annotated[int, Form()],
    file: UploadFile | None = File(None),
    snippet: Annotated[str | None, Form()] = None,
    repo_url: Annotated[str | None, Form()] = None,
    language_hints: Annotated[str | None, Form()] = None,
    session: Session = Depends(get_session),
):
    if not any([repo_url, snippet, file]):
        raise HTTPException(status_code=400, detail="Provide repo_url, snippet, or file")

    payload = b""
    artifact_type = "repo_url"
    if repo_url:
        payload = repo_url.encode("utf-8")
        artifact_type = "repo_url"
    elif snippet:
        payload = snippet.encode("utf-8")
        artifact_type = "snippet"
    elif file:
        payload = await file.read()
        artifact_type = "zip" if file.filename and file.filename.endswith(".zip") else "file"

    checksum = hashlib.sha256(payload).hexdigest()
    size = len(payload)
    key = f"{settings.s3_prefix}/project-{project_id}/{uuid.uuid4()}"
    s3_uri = s3_put_bytes(settings.s3_bucket, key, payload)

    artifact = Artifact(
        project_id=project_id,
        type=artifact_type,
        s3_uri=s3_uri,
        checksum=checksum,
        size=size,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)

    job = AnalysisJob(project_id=project_id, artifact_id=artifact.id, status="queued", stage="ingestion")
    session.add(job)
    session.commit()
    session.refresh(job)

    if settings.sqs_queue_url:
        sqs_send(settings.sqs_queue_url, {"job_id": job.id})

    return {"job_id": job.id, "status_url": f"/status/{job.id}"}


@router.post("/analyze")
def analyze(artifact_id: int, session: Session = Depends(get_session)):
    artifact = session.get(Artifact, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="artifact not found")

    job = AnalysisJob(project_id=artifact.project_id, artifact_id=artifact.id, status="queued", stage="ingestion")
    session.add(job)
    session.commit()
    session.refresh(job)

    if settings.sqs_queue_url:
        sqs_send(settings.sqs_queue_url, {"job_id": job.id})

    return {"job_id": job.id, "status_url": f"/status/{job.id}"}
