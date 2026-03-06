from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.deps import get_current_user, get_db
from app.models.models import User, Session as DbSession, GuidanceLog
from app.schemas.guidance import GuidanceRequest, GuidanceResponse
from app.services.nlp_engine import engine
from app.services.nova_client import guidance_with_nova, chat_with_nova, stream_chat_with_nova
import json
import logging

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
    """Load previous Q&A from DB to give Nova conversation context"""
    logs = (
        session.query(GuidanceLog)
        .filter(GuidanceLog.session_id == session_id)
        .order_by(GuidanceLog.created_at.asc())
        .limit(10)  # Last 10 exchanges
        .all()
    )
    return [{"question": log.question, "response": log.response} for log in logs]


@router.post("/api/guidance", response_model=GuidanceResponse)
def guidance(
    payload: GuidanceRequest,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    user = _get_or_create_user(session, claims)
    ast_context = payload.ast_context or {}

    guidance_level = min(payload.guidance_level or 0, 4)

    # Get or create session
    db_session = None
    if payload.session_id:
        db_session = session.get(DbSession, payload.session_id)
    if db_session is None:
        db_session = DbSession(user_id=user.id, title="Guidance Session")
        session.add(db_session)
        session.commit()
        session.refresh(db_session)

    # Load conversation history for context-aware responses
    conversation_history = _load_conversation_history(session, db_session.id)
    logger.info(f"Loaded {len(conversation_history)} previous messages for context")

    # Try Nova with full conversation history
    response = guidance_with_nova(
        question=payload.user_question,
        code=payload.code_context,
        ast=ast_context,
        goal=payload.goal,
        guidance_level=guidance_level,
        explicit_full=False,
        conversation_history=conversation_history,  # Pass history
    )

    # Fallback to local engine
    if not response:
        response = engine.generate(
            payload.user_question,
            payload.code_context,
            ast_context,
            payload.goal,
            guidance_level,
        )

    if _is_full_solution(response):
        logger.warning("Full solution detected, replacing with hint")
        response = (
            "I noticed you might be looking for a complete solution. "
            "Let me guide you instead:\n\n"
            "🤔 What's the first step you need to take?\n"
            "💡 Try breaking this into smaller parts.\n\n"
            "Ask me about specific parts you're stuck on!"
        )

    # Save to DB
    log = GuidanceLog(
        session_id=db_session.id,
        question=payload.user_question,
        response=response
    )
    session.add(log)
    session.commit()

    return GuidanceResponse(response=response, session_id=db_session.id)


@router.post("/api/chat")
def chat(
    payload: GuidanceRequest,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Full ChatGPT-like chat endpoint - no Socratic restrictions.
    Answers questions directly with full context awareness.
    """
    user = _get_or_create_user(session, claims)

    # Get or create session
    db_session = None
    if payload.session_id:
        db_session = session.get(DbSession, payload.session_id)
    if db_session is None:
        db_session = DbSession(user_id=user.id, title="Chat Session")
        session.add(db_session)
        session.commit()
        session.refresh(db_session)

    # Load full conversation history
    conversation_history = _load_conversation_history(session, db_session.id)

    # Get response with full context
    response = chat_with_nova(
        question=payload.user_question,
        code=payload.code_context,
        conversation_history=conversation_history,
    )

    if not response:
        response = "I'm having trouble connecting to the AI service. Please try again."

    # Save exchange to DB
    log = GuidanceLog(
        session_id=db_session.id,
        question=payload.user_question,
        response=response
    )
    session.add(log)
    session.commit()

    return {"response": response, "session_id": db_session.id}


@router.post("/api/chat/stream")
def chat_stream(
    payload: GuidanceRequest,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Streaming chat - returns text chunks like ChatGPT typing effect.
    Frontend should use EventSource or fetch with ReadableStream.
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
    full_response = []

    def generate():
        for chunk in stream_chat_with_nova(
            question=payload.user_question,
            code=payload.code_context,
            conversation_history=conversation_history,
        ):
            full_response.append(chunk)
            # Send as SSE (Server-Sent Events)
            yield f"data: {json.dumps({'text': chunk})}\n\n"

        # Save complete response to DB after streaming
        complete_response = "".join(full_response)
        log = GuidanceLog(
            session_id=db_session.id,
            question=payload.user_question,
            response=complete_response
        )
        session.add(log)
        session.commit()

        # Signal end of stream
        yield f"data: {json.dumps({'done': True, 'session_id': db_session.id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


def _is_full_solution(response: str) -> bool:
    indicators = [
        response.count('\n') > 20,
        'def ' in response and 'return' in response and len(response) > 300,
        response.count('if ') > 3 and response.count('for ') > 2,
        'class ' in response and len(response) > 250,
    ]
    return any(indicators)
