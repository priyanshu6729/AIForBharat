from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.services.auth_service import AuthService
from app.deps import get_current_user  # FIX: Import from app.deps
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ConfirmRequest(BaseModel):
    email: EmailStr
    code: str

class ResendRequest(BaseModel):
    email: EmailStr

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

@router.post("/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        logger.info(f"Registration attempt for email: {request.email}")
        result = auth_service.register(request.email, request.password)
        logger.info(f"Registration successful for: {request.email}")
        return result
    except ValueError as e:
        logger.error(f"Registration failed for {request.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/confirm")
async def confirm_sign_up(request: ConfirmRequest):
    """Confirm user email with verification code"""
    try:
        logger.info(f"Email confirmation attempt for: {request.email}")
        result = auth_service.confirm_sign_up(request.email, request.code)
        logger.info(f"Email confirmed successfully for: {request.email}")
        return {"message": "Email verified successfully", "email": request.email}
    except ValueError as e:
        logger.error(f"Confirmation failed for {request.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during confirmation: {str(e)}")
        raise HTTPException(status_code=500, detail="Confirmation failed")

@router.post("/resend")
async def resend_confirmation(request: ResendRequest):
    """Resend confirmation code"""
    try:
        logger.info(f"Resend confirmation for: {request.email}")
        result = auth_service.resend_confirmation_code(request.email)
        logger.info(f"Confirmation code resent to: {request.email}")
        return {"message": "Confirmation code sent", "email": request.email}
    except ValueError as e:
        logger.error(f"Resend failed for {request.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during resend: {str(e)}")
        raise HTTPException(status_code=500, detail="Resend failed")

@router.post("/login")
async def login(request: LoginRequest):
    """Login user"""
    try:
        logger.info(f"Login attempt for email: {request.email}")
        result = auth_service.login(request.email, request.password)
        logger.info(f"Login successful for: {request.email}")
        return result
    except ValueError as e:
        logger.error(f"Login failed for {request.email}: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/me")
async def get_current_user_info(claims: dict = Depends(get_current_user)):
    """Get current user information from JWT token claims"""
    try:
        # Return user info from JWT claims
        return {
            "sub": claims.get("sub"),
            "email": claims.get("email"),
            "email_verified": claims.get("email_verified", False),
            "cognito_username": claims.get("cognito:username")
        }
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user information")

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset"""
    try:
        logger.info(f"Password reset requested for: {request.email}")
        result = auth_service.forgot_password(request.email)
        logger.info(f"Password reset code sent to: {request.email}")
        return result
    except ValueError as e:
        logger.error(f"Password reset failed for {request.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during password reset: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password with code"""
    try:
        logger.info(f"Password reset confirmation for: {request.email}")
        result = auth_service.confirm_forgot_password(
            request.email, 
            request.code, 
            request.new_password
        )
        logger.info(f"Password reset successful for: {request.email}")
        return result
    except ValueError as e:
        logger.error(f"Password reset confirmation failed for {request.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during password reset confirmation: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset confirmation failed")

@router.post("/logout")
async def logout(claims: dict = Depends(get_current_user)):
    """Logout user (client-side clears tokens)"""
    return {"message": "Logged out successfully"}