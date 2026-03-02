from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ConfirmRequest(BaseModel):
    email: EmailStr
    code: str


class ResendConfirmRequest(BaseModel):
    email: EmailStr


class AuthResponse(BaseModel):
    access_token: str
    id_token: str
    refresh_token: str | None = None


class MeResponse(BaseModel):
    sub: str
    email: str
