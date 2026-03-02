"""Authentication service using AWS Cognito."""
import logging
from app.services.cognito_client import (
    sign_up,
    login,
    verify_jwt_token,
    get_user,
    refresh_token,
    confirm_sign_up,
    resend_confirmation_code,
)
import boto3
from botocore.exceptions import ClientError
import os

logger = logging.getLogger(__name__)

# Cognito configuration
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
REGION = os.getenv("COGNITO_REGION", "us-east-1")

cognito_client = boto3.client('cognito-idp', region_name=REGION)


class AuthService:
    """Service for handling authentication operations."""

    def register(self, email: str, password: str) -> dict:
        """Register a new user."""
        try:
            response = sign_up(email, password)
            return {
                "message": "User registered successfully. Please check your email for verification code.",
                "user_sub": response.get("UserSub"),
                "email": email,
                "confirmation_required": not response.get("UserConfirmed", False)
            }
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise ValueError(str(e))

    def login(self, email: str, password: str) -> dict:
        """Login user and return tokens."""
        try:
            auth_result = login(email, password)
            return {
                "access_token": auth_result["AccessToken"],
                "id_token": auth_result["IdToken"],
                "refresh_token": auth_result["RefreshToken"],
                "token_type": "Bearer",
                "expires_in": auth_result["ExpiresIn"]
            }
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise ValueError(str(e))

    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return claims."""
        try:
            return verify_jwt_token(token)
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(str(e))

    def get_user_info(self, access_token: str) -> dict:
        """Get user information."""
        try:
            user_data = get_user(access_token)
            return {
                "username": user_data["Username"],
                "attributes": {attr["Name"]: attr["Value"] for attr in user_data["UserAttributes"]}
            }
        except Exception as e:
            logger.error(f"Get user info failed: {e}")
            raise ValueError(str(e))

    def refresh_access_token(self, refresh_token_value: str) -> dict:
        """Refresh access token."""
        try:
            auth_result = refresh_token(refresh_token_value)
            return {
                "access_token": auth_result["AccessToken"],
                "id_token": auth_result["IdToken"],
                "token_type": "Bearer",
                "expires_in": auth_result["ExpiresIn"]
            }
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise ValueError(str(e))

    def confirm_sign_up(self, email: str, code: str) -> dict:
        """Confirm user registration with verification code."""
        try:
            response = confirm_sign_up(email, code)
            return {
                "message": "Email verified successfully",
                "email": email
            }
        except Exception as e:
            logger.error(f"Confirmation failed: {e}")
            raise ValueError(str(e))

    def resend_confirmation_code(self, email: str) -> dict:
        """Resend confirmation code to user."""
        try:
            response = resend_confirmation_code(email)
            return {
                "message": "Confirmation code sent",
                "email": email
            }
        except Exception as e:
            logger.error(f"Resend confirmation failed: {e}")
            raise ValueError(str(e))

    def forgot_password(self, email: str) -> dict:
        """Initiate forgot password flow."""
        try:
            response = cognito_client.forgot_password(
                ClientId=CLIENT_ID,
                Username=email
            )
            return {
                "message": "Password reset code sent to your email",
                "email": email
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Forgot password error: {error_code} - {error_message}")
            
            if error_code == 'UserNotFoundException':
                raise ValueError("User not found")
            elif error_code == 'InvalidParameterException':
                raise ValueError("Invalid email address")
            else:
                raise ValueError(f"Password reset failed: {error_message}")

    def confirm_forgot_password(self, email: str, code: str, new_password: str) -> dict:
        """Confirm forgot password with code and new password."""
        try:
            response = cognito_client.confirm_forgot_password(
                ClientId=CLIENT_ID,
                Username=email,
                ConfirmationCode=code,
                Password=new_password
            )
            return {
                "message": "Password reset successfully",
                "email": email
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Confirm forgot password error: {error_code} - {error_message}")
            
            if error_code == 'CodeMismatchException':
                raise ValueError("Invalid verification code")
            elif error_code == 'ExpiredCodeException':
                raise ValueError("Verification code expired")
            elif error_code == 'InvalidPasswordException':
                raise ValueError("Password does not meet requirements")
            else:
                raise ValueError(f"Password reset failed: {error_message}")