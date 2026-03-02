import os
import time
from typing import Any

import boto3
import requests
from botocore.exceptions import ClientError
import jwt
from jwt import PyJWKClient
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

# Cognito configuration from .env
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
REGION = os.getenv("COGNITO_REGION", "us-east-1")

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name=REGION)

# JWK URL for token verification
JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"

_jwks_cache: dict[str, Any] | None = None
_jwks_time: float = 0

if not USER_POOL_ID or not CLIENT_ID:
    logger.warning("Cognito configuration missing!")


def _validate_cognito_config():
    """Validate Cognito configuration"""
    if not USER_POOL_ID or not CLIENT_ID:
        raise RuntimeError("Cognito is not configured. Please set COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID")

def sign_up(email: str, password: str):
    """Register a new user with Cognito"""
    _validate_cognito_config()
    try:
        response = cognito_client.sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email}
            ]
        )
        logger.info(f"User {email} registered successfully")
        return response
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Cognito sign_up error: {error_code} - {error_message}")
        
        # Return user-friendly error messages
        if error_code == 'UsernameExistsException':
            raise ValueError("User already exists")
        elif error_code == 'InvalidPasswordException':
            raise ValueError("Password does not meet requirements (min 8 chars, uppercase, lowercase, number, special char)")
        elif error_code == 'InvalidParameterException':
            raise ValueError(f"Invalid parameter: {error_message}")
        else:
            raise ValueError(f"Registration failed: {error_message}")


def login(email: str, password: str):
    """Authenticate user and get tokens"""
    _validate_cognito_config()
    try:
        logger.info(f"Attempting login for user: {email}")
        response = cognito_client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        logger.info(f"User {email} logged in successfully")
        return response['AuthenticationResult']
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Cognito login error for {email}: {error_code} - {error_message}")
        
        if error_code == 'NotAuthorizedException':
            raise ValueError("Invalid email or password")
        elif error_code == 'UserNotFoundException':
            raise ValueError("User not found")
        elif error_code == 'UserNotConfirmedException':
            raise ValueError("Please verify your email first")
        else:
            raise ValueError(f"Login failed: {error_message}")
    except Exception as e:
        logger.error(f"Unexpected login error for {email}: {str(e)}", exc_info=True)
        raise ValueError(f"Login failed: {str(e)}")


def verify_jwt_token(token: str) -> dict:
    """
    Verify JWT token from Cognito and return claims.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Token claims (user info)
        
    Raises:
        ValueError: If token is invalid
    """
    if not USER_POOL_ID or not CLIENT_ID:
        raise ValueError("Cognito is not configured")
    try:
        # Get public keys from Cognito
        jwks_client = PyJWKClient(JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Verify and decode token
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            options={"verify_exp": True}
        )
        
        return claims
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")


def get_user(access_token: str):
    """Get user details using access token"""
    if not USER_POOL_ID or not CLIENT_ID:
        raise ValueError("Cognito is not configured")
    try:
        response = cognito_client.get_user(
            AccessToken=access_token
        )
        return response
    except ClientError as e:
        logger.error(f"Get user error: {e}")
        raise ValueError("Failed to get user information")


def refresh_token(refresh_token_value: str):
    """Refresh access token using refresh token"""
    if not USER_POOL_ID or not CLIENT_ID:
        raise ValueError("Cognito is not configured")
    try:
        response = cognito_client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token_value
            }
        )
        return response['AuthenticationResult']
    except ClientError as e:
        raise ValueError(f"Token refresh failed: {e.response['Error']['Message']}")


def confirm_sign_up(email: str, confirmation_code: str):
    """Confirm user registration with code"""
    if not USER_POOL_ID or not CLIENT_ID:
        raise ValueError("Cognito is not configured")
    try:
        response = cognito_client.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            ConfirmationCode=confirmation_code
        )
        logger.info(f"User {email} confirmed successfully")
        return response
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Confirm sign up error: {error_code} - {error_message}")
        
        if error_code == 'CodeMismatchException':
            raise ValueError("Invalid verification code")
        elif error_code == 'ExpiredCodeException':
            raise ValueError("Verification code expired")
        elif error_code == 'NotAuthorizedException':
            raise ValueError("User already confirmed")
        else:
            raise ValueError(f"Confirmation failed: {error_message}")


def resend_confirmation_code(email: str):
    """Resend confirmation code for a Cognito user"""
    if not USER_POOL_ID or not CLIENT_ID:
        raise ValueError("Cognito is not configured")
    try:
        response = cognito_client.resend_confirmation_code(
            ClientId=CLIENT_ID,
            Username=email,
        )
        logger.info(f"Confirmation code resent to {email}")
        return response
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Resend confirmation error: {error_code} - {error_message}")
        
        if error_code == 'UserNotFoundException':
            raise ValueError("User not found")
        elif error_code == 'InvalidParameterException':
            raise ValueError("User already confirmed")
        else:
            raise ValueError(f"Resend failed: {error_message}")
