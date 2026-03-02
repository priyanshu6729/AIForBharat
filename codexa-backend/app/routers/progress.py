from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.models import User, Progress, Lesson
from app.schemas.progress import (
    ProgressUpdateRequest,
    ProgressUpdateResponse,
    ProgressItem,
    ProgressListResponse,
)

router = APIRouter()


def _get_or_create_user(session: Session, claims: dict) -> User:
    sub = claims.get("sub")
    email = claims.get("email")
    user = session.query(User).filter(User.cognito_sub == sub).first()
    if user:
        return user
    user = User(cognito_sub=sub, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/api/progress", response_model=ProgressUpdateResponse)
def update_progress(
    payload: ProgressUpdateRequest,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    user = _get_or_create_user(session, claims)
    lesson = session.get(Lesson, payload.lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="lesson not found")

    progress = (
        session.query(Progress)
        .filter(Progress.user_id == user.id, Progress.lesson_id == lesson.id)
        .first()
    )
    now = datetime.now(timezone.utc)
    if progress:
        progress.status = payload.status
        progress.updated_at = now
    else:
        progress = Progress(
            user_id=user.id,
            lesson_id=lesson.id,
            status=payload.status,
            updated_at=now,
        )
        session.add(progress)

    session.commit()

    return ProgressUpdateResponse(
        lesson_id=progress.lesson_id,
        status=progress.status,
        updated_at=progress.updated_at.isoformat(),
    )


@router.get("/api/progress", response_model=ProgressListResponse)
def list_progress(
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    user = _get_or_create_user(session, claims)
    rows = (
        session.query(Progress)
        .filter(Progress.user_id == user.id)
        .order_by(Progress.updated_at.desc())
        .all()
    )
    payload = [
        ProgressItem(
            lesson_id=row.lesson_id,
            status=row.status,
            updated_at=row.updated_at.isoformat(),
        )
        for row in rows
    ]
    return ProgressListResponse(progress=payload)
