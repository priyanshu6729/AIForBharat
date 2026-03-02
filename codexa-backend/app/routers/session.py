import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.models import User, Session as DbSession, CodeSnapshot, GuidanceLog
from app.schemas.session import (
    SessionSaveRequest,
    SessionSaveResponse,
    SessionResponse,
    SessionListResponse,
    SessionListItem,
)
from app.services.s3_client import put_json, get_json

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


@router.post("/api/session/save", response_model=SessionSaveResponse)
def save_session(
    payload: SessionSaveRequest,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    user = _get_or_create_user(session, claims)
    db_session = None
    if payload.session_id:
        db_session = session.get(DbSession, payload.session_id)
        if db_session and db_session.user_id != user.id:
            raise HTTPException(status_code=403, detail="forbidden")
    if db_session is None:
        db_session = DbSession(user_id=user.id, title=payload.title)
        session.add(db_session)
        session.commit()
        session.refresh(db_session)
    else:
        db_session.title = payload.title
        session.commit()

    viz_key = f"snapshots/session-{db_session.id}-{int(time.time())}.json"
    s3_url = put_json(viz_key, {"code": payload.code, "visualization": payload.visualization})

    snapshot = CodeSnapshot(
        session_id=db_session.id,
        language=payload.language,
        code=payload.code,
        s3_url=s3_url,
    )
    session.add(snapshot)

    for item in payload.chat_log:
        question = item.get("question", "")
        response = item.get("response", "")
        if question and response:
            session.add(GuidanceLog(session_id=db_session.id, question=question, response=response))

    session.commit()
    return SessionSaveResponse(session_id=db_session.id)


@router.get("/api/session/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    user = _get_or_create_user(session, claims)
    db_session = session.get(DbSession, session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="session not found")
    if db_session.user_id != user.id:
        raise HTTPException(status_code=403, detail="forbidden")

    snapshot = (
        session.query(CodeSnapshot)
        .filter(CodeSnapshot.session_id == db_session.id)
        .order_by(CodeSnapshot.created_at.desc())
        .first()
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="snapshot not found")

    logs = (
        session.query(GuidanceLog)
        .filter(GuidanceLog.session_id == db_session.id)
        .order_by(GuidanceLog.created_at.asc())
        .all()
    )

    chat_log = [{"question": log.question, "response": log.response} for log in logs]

    snapshot_payload = get_json(snapshot.s3_url) if snapshot.s3_url else {}
    visualization = snapshot_payload.get("visualization", snapshot_payload if isinstance(snapshot_payload, dict) else {})

    return SessionResponse(
        session_id=db_session.id,
        title=db_session.title,
        language=snapshot.language,
        code=snapshot.code,
        visualization=visualization,
        chat_log=chat_log,
    )


@router.get("/api/session", response_model=SessionListResponse)
def list_sessions(
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    user = _get_or_create_user(session, claims)
    sessions = (
        session.query(DbSession)
        .filter(DbSession.user_id == user.id)
        .order_by(DbSession.created_at.desc())
        .limit(50)
        .all()
    )
    payload = [
        SessionListItem(
            session_id=item.id,
            title=item.title,
            created_at=item.created_at.isoformat(),
        )
        for item in sessions
    ]
    return SessionListResponse(sessions=payload)
