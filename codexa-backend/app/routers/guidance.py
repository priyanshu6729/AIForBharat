from __future__ import annotations

import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.deps import get_current_user, get_db
from app.models.models import GuidanceLog, Session as DbSession, User
from app.schemas.guidance import GuidanceRequest, GuidanceResponse
from app.services.model_router import route_chat, route_chat_stream, route_guidance
from app.services.nlp_engine import engine

logger = logging.getLogger(__name__)
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


def _load_conversation_history(session: Session, session_id: int) -> list[dict]:
    """Load previous Q&A from DB to give mentor context."""
    logs = (
        session.query(GuidanceLog)
        .filter(GuidanceLog.session_id == session_id)
        .order_by(GuidanceLog.created_at.asc())
        .limit(10)
        .all()
    )
    return [{"question": log.question, "response": log.response} for log in logs]


def _safe_save_guidance_log(
    session: Session,
    *,
    db_session_id: int,
    question: str,
    response: str,
) -> None:
    """Persist chat/guidance log without breaking endpoint responses."""
    if not response:
        return
    try:
        log = GuidanceLog(
            session_id=db_session_id,
            question=question,
            response=response,
        )
        session.add(log)
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.warning("Failed to persist guidance log session_id=%s err=%s", db_session_id, exc)


def _log_mentor_outcome(
    *,
    endpoint: str,
    session_id: int,
    route_meta: dict,
    latency_ms: int,
) -> None:
    logger.info(
        "mentor_request endpoint=%s session_id=%s attempted_models=%s final_source=%s final_model=%s fallback_used=%s error_summary=%s latency_ms=%s",
        endpoint,
        session_id,
        route_meta.get("attempted_models"),
        route_meta.get("selected_source"),
        route_meta.get("selected_model"),
        route_meta.get("fallback_used"),
        route_meta.get("last_error"),
        latency_ms,
    )


@router.post("/api/guidance", response_model=GuidanceResponse)
def guidance(
    payload: GuidanceRequest,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    start = time.perf_counter()
    user = _get_or_create_user(session, claims)
    ast_context = payload.ast_context or {}
    guidance_level = min(payload.guidance_level or 0, 4)

    db_session = None
    if payload.session_id:
        db_session = session.get(DbSession, payload.session_id)
    if db_session is None:
        db_session = DbSession(user_id=user.id, title="Guidance Session")
        session.add(db_session)
        session.commit()
        session.refresh(db_session)

    conversation_history = _load_conversation_history(session, db_session.id)

    try:
        response, route_meta = route_guidance(
            question=payload.user_question,
            code=payload.code_context,
            ast=ast_context,
            goal=payload.goal,
            guidance_level=guidance_level,
            explicit_full=False,
            conversation_history=conversation_history,
        )
    except Exception as exc:
        logger.exception("Guidance model routing failed session_id=%s", db_session.id)
        try:
            response = engine.generate(
                payload.user_question,
                payload.code_context,
                ast_context,
                payload.goal,
                guidance_level,
            )
        except Exception as local_exc:
            logger.exception("Guidance local fallback failed session_id=%s", db_session.id)
            raise HTTPException(status_code=500, detail="Unable to generate guidance") from local_exc

        route_meta = {
            "selected_source": "local",
            "selected_model": settings.mentor_local_chat_fallback_mode,
            "attempt_count": 0,
            "attempted_models": [],
            "fallback_used": True,
            "last_error": {
                "class": exc.__class__.__name__,
                "category": "provider_error",
                "message": str(exc),
            },
        }

    if _is_full_solution(response):
        logger.warning("Full solution detected, replacing with hint")
        response = (
            "I noticed you might be looking for a complete solution. "
            "Let me guide you instead:\n\n"
            "🤔 What's the first step you need to take?\n"
            "💡 Try breaking this into smaller parts.\n\n"
            "Ask me about specific parts you're stuck on!"
        )

    _safe_save_guidance_log(
        session,
        db_session_id=db_session.id,
        question=payload.user_question,
        response=response,
    )

    _log_mentor_outcome(
        endpoint="/api/guidance",
        session_id=db_session.id,
        route_meta=route_meta,
        latency_ms=int((time.perf_counter() - start) * 1000),
    )

    return GuidanceResponse(response=response, session_id=db_session.id)


@router.post("/api/chat")
def chat(
    payload: GuidanceRequest,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """General chat endpoint with model routing and fallback."""
    start = time.perf_counter()
    user = _get_or_create_user(session, claims)

    db_session = None
    if payload.session_id:
        db_session = session.get(DbSession, payload.session_id)
    if db_session is None:
        db_session = DbSession(user_id=user.id, title="Chat Session")
        session.add(db_session)
        session.commit()
        session.refresh(db_session)

    conversation_history = _load_conversation_history(session, db_session.id)

    try:
        response, route_meta = route_chat(
            question=payload.user_question,
            code_context=payload.code_context,
            conversation_history=conversation_history,
        )
    except Exception as exc:
        logger.exception("Chat model routing failed session_id=%s", db_session.id)
        try:
            response = engine.generate_chat_fallback(payload.user_question, payload.code_context)
        except Exception as local_exc:
            logger.exception("Chat local fallback failed session_id=%s", db_session.id)
            raise HTTPException(status_code=500, detail="Unable to generate chat response") from local_exc

        route_meta = {
            "selected_source": "local",
            "selected_model": settings.mentor_local_chat_fallback_mode,
            "attempt_count": 0,
            "attempted_models": [],
            "fallback_used": True,
            "last_error": {
                "class": exc.__class__.__name__,
                "category": "provider_error",
                "message": str(exc),
            },
        }

    _safe_save_guidance_log(
        session,
        db_session_id=db_session.id,
        question=payload.user_question,
        response=response,
    )

    _log_mentor_outcome(
        endpoint="/api/chat",
        session_id=db_session.id,
        route_meta=route_meta,
        latency_ms=int((time.perf_counter() - start) * 1000),
    )

    return {"response": response, "session_id": db_session.id}


@router.post("/api/chat/stream")
def chat_stream(
    payload: GuidanceRequest,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Streaming chat endpoint with resilient routing/fallback.
    Always emits terminal done event.
    """
    user = _get_or_create_user(session, claims)

    db_session = None
    if payload.session_id:
        db_session = session.get(DbSession, payload.session_id)
    if db_session is None:
        db_session = DbSession(user_id=user.id, title="Chat Session")
        session.add(db_session)
        session.commit()
        session.refresh(db_session)

    conversation_history = _load_conversation_history(session, db_session.id)
    request_started = time.perf_counter()

    def generate():
        full_response: list[str] = []
        route_meta: dict = {}
        stream_started = False

        try:
            for event_type, payload_data in route_chat_stream(
                question=payload.user_question,
                code_context=payload.code_context,
                conversation_history=conversation_history,
            ):
                if event_type == "chunk":
                    text = payload_data.get("text", "")
                    if text:
                        stream_started = True
                        full_response.append(text)
                        yield f"data: {json.dumps({'text': text})}\n\n"
                elif event_type == "meta":
                    route_meta = payload_data

        except Exception as exc:
            logger.exception("Chat stream routing failed session_id=%s", db_session.id)
            route_meta = {
                "selected_source": route_meta.get("selected_source"),
                "selected_model": route_meta.get("selected_model"),
                "attempted_models": route_meta.get("attempted_models", []),
                "fallback_used": route_meta.get("fallback_used", False),
                "last_error": {
                    "class": exc.__class__.__name__,
                    "category": "provider_error",
                    "message": str(exc),
                },
                "stream_interrupted": stream_started,
            }

            if not stream_started and settings.mentor_stream_fallback_enabled:
                try:
                    for chunk in engine.stream_chat_fallback(payload.user_question, payload.code_context):
                        if not chunk:
                            continue
                        stream_started = True
                        full_response.append(chunk)
                        yield f"data: {json.dumps({'text': chunk})}\n\n"

                    route_meta["selected_source"] = "local"
                    route_meta["selected_model"] = settings.mentor_local_chat_fallback_mode
                    route_meta["fallback_used"] = True
                except Exception as local_exc:
                    logger.exception(
                        "Chat stream local fallback failed session_id=%s", db_session.id
                    )
                    route_meta["last_error"] = {
                        "class": local_exc.__class__.__name__,
                        "category": "local_error",
                        "message": str(local_exc),
                    }

        complete_response = "".join(full_response).strip()
        _safe_save_guidance_log(
            session,
            db_session_id=db_session.id,
            question=payload.user_question,
            response=complete_response,
        )

        _log_mentor_outcome(
            endpoint="/api/chat/stream",
            session_id=db_session.id,
            route_meta=route_meta,
            latency_ms=int((time.perf_counter() - request_started) * 1000),
        )

        # Terminal SSE event required by frontend consumers.
        yield f"data: {json.dumps({'done': True, 'session_id': db_session.id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _is_full_solution(response: str) -> bool:
    indicators = [
        response.count("\n") > 20,
        "def " in response and "return" in response and len(response) > 300,
        response.count("if ") > 3 and response.count("for ") > 2,
        "class " in response and len(response) > 250,
    ]
    return any(indicators)
