from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db import SessionLocal
from app.services.cognito_client import verify_jwt_token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token and return user claims.
    Used for endpoints that need user authentication.
    """
    token = credentials.credentials
    try:
        claims = verify_jwt_token(token)
        return claims
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Add this alias for compatibility
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Alias for get_current_user - verifies token and returns claims.
    """
    return get_current_user(credentials)
