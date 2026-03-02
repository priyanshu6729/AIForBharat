from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ConfirmRequest,
    ResendConfirmRequest,
    AuthResponse,
    MeResponse,
)
from app.services.cognito_client import sign_up, login, get_user, confirm_sign_up, resend_confirmation_code
from app.deps import get_current_user, verify_token

router = APIRouter()


@router.post("/api/auth/register")
def register(payload: RegisterRequest):
    try:
        sign_up(payload.email, payload.password)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "registered"}


@router.post("/api/auth/login", response_model=AuthResponse)
def auth_login(payload: LoginRequest):
    try:
        result = login(payload.email, payload.password)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return AuthResponse(
        access_token=result.get("AccessToken", ""),
        id_token=result.get("IdToken", ""),
        refresh_token=result.get("RefreshToken"),
    )


@router.post("/api/auth/confirm")
def confirm(payload: ConfirmRequest):
    try:
        confirm_sign_up(payload.email, payload.code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "confirmed"}


@router.post("/api/auth/resend")
def resend(payload: ResendConfirmRequest):
    try:
        resend_confirmation_code(payload.email)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "resent"}


@router.get("/api/auth/me", response_model=MeResponse)
def me(claims=Depends(get_current_user)):
    # Handle missing email field in Cognito token
    email = claims.get("email") or claims.get("username") or claims.get("cognito:username") or "unknown"
    return MeResponse(
        sub=claims.get("sub"),
        email=email
    )
