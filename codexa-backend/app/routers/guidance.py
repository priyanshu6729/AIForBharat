from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_current_user, get_db
from app.models.models import User, Session as DbSession, GuidanceLog
from app.schemas.guidance import GuidanceRequest, GuidanceResponse
from app.services.nlp_engine import engine
from app.services.nova_client import guidance_with_nova
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


@router.post("/api/guidance", response_model=GuidanceResponse)
def guidance(
    payload: GuidanceRequest,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    user = _get_or_create_user(session, claims)
    ast_context = payload.ast_context or {}
    question_lower = payload.user_question.lower()
    
    # STRICT: Never allow level 5 full solutions
    guidance_level = payload.guidance_level or 0
    if guidance_level >= 5:
        guidance_level = 4
        logger.info(f"User requested level {payload.guidance_level}, capped at 4")
    
    # Maximum level is 4, never give full solutions
    guidance_level = min(guidance_level, 4)
    
    # Try Nova first (with built-in safeguards)
    response = guidance_with_nova(
        payload.user_question,
        payload.code_context,
        ast_context,
        payload.goal,
        guidance_level,
        explicit_full=False,  # Always False - never give full solutions
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
    
    # Safety check: if response looks like full solution, truncate
    if _is_full_solution(response):
        logger.warning("Response detected as full solution, replacing with hint")
        response = (
            "I noticed you might be looking for a complete solution. "
            "Instead, let me guide you:\n\n"
            "🤔 What's the first step you need to take?\n"
            "💡 Try breaking this problem into smaller parts.\n\n"
            "Ask me about specific parts you're stuck on!"
        )
    
    db_session = None
    if payload.session_id:
        db_session = session.get(DbSession, payload.session_id)
    if db_session is None:
        db_session = DbSession(user_id=user.id, title="Guidance Session")
        session.add(db_session)
        session.commit()
        session.refresh(db_session)
    
    log = GuidanceLog(session_id=db_session.id, question=payload.user_question, response=response)
    session.add(log)
    session.commit()
    
    return GuidanceResponse(response=response, session_id=db_session.id)

def _is_full_solution(response: str) -> bool:
    """Detect if response contains a full solution"""
    indicators = [
        response.count('\n') > 20,  # Too many lines
        'def ' in response and 'return' in response and len(response) > 300,
        response.count('if ') > 3 and response.count('for ') > 2,
        'class ' in response and len(response) > 250,
    ]
    return any(indicators)
